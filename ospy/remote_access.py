#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Helpers for optional remote-access status shown by the OSPy web interface."""

import os
import re
import subprocess
import threading
import time


_CLOUDFLARE_MANAGED_SERVICE = "cloudflared.service"
_CLOUDFLARE_MANAGED_URL_FILE = "/etc/ospy/cloudflare_public_url"
_CLOUDFLARE_QUICK_SERVICE = "ospy-cloudflared-quick.service"
_CLOUDFLARE_QUICK_SERVICE_FILE = "/etc/systemd/system/ospy-cloudflared-quick.service"
_CACHE_SECONDS = 30.0
_COMMAND_TIMEOUT_SECONDS = 1.5
_QUICK_URL_RE = re.compile(
    r"https://[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.trycloudflare\.com"
    r"(?=$|[\s/\"'<>])",
    re.IGNORECASE,
)
_MANAGED_URL_RE = re.compile(
    r"^https://"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?/?$",
    re.IGNORECASE,
)

_cache_lock = threading.RLock()
_cache_url = ""
_cache_until = 0.0


def _run_command(arguments):
    """Run one bounded local command and return CompletedProcess or None."""
    try:
        return subprocess.run(
            arguments,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _service_is_active(service_name):
    active = _run_command(["systemctl", "is-active", "--quiet", service_name])
    return active is not None and active.returncode == 0


def _normalize_cloudflare_managed_url(text):
    """Return a strict HTTPS public hostname URL, or an empty string."""
    value = (text or "").strip()
    if not _MANAGED_URL_RE.fullmatch(value):
        return ""

    value = value.rstrip("/")
    hostname = value[len("https://"):]
    if len(hostname) > 253:
        return ""

    return "https://" + hostname.lower()


def _extract_cloudflare_quick_url(text):
    """Return the last strict trycloudflare.com HTTPS URL found in journal text."""
    matches = _QUICK_URL_RE.findall(text or "")
    return matches[-1] if matches else ""


def _managed_service_is_active():
    """Return True only when OSPy's managed-tunnel URL marker exists and cloudflared is active."""
    if not os.path.isfile(_CLOUDFLARE_MANAGED_URL_FILE):
        return False
    return _service_is_active(_CLOUDFLARE_MANAGED_SERVICE)


def _read_cloudflare_managed_url():
    """Read and validate the installer-stored public hostname for a managed tunnel."""
    try:
        with open(_CLOUDFLARE_MANAGED_URL_FILE, "r", encoding="utf-8") as source:
            return _normalize_cloudflare_managed_url(source.read(1024))
    except OSError:
        return ""


def _quick_service_is_active():
    """Return True only for the installer-created active Quick Tunnel service."""
    if not os.path.isfile(_CLOUDFLARE_QUICK_SERVICE_FILE):
        return False
    return _service_is_active(_CLOUDFLARE_QUICK_SERVICE)


def _read_cloudflare_quick_url():
    """Read the current Quick Tunnel URL from the bounded service journal."""
    journal = _run_command(
        [
            "journalctl",
            "-u",
            _CLOUDFLARE_QUICK_SERVICE,
            "-n",
            "50",
            "--no-pager",
            "-o",
            "cat",
        ]
    )
    if journal is None or journal.returncode != 0:
        return ""

    return _extract_cloudflare_quick_url(journal.stdout)


def _clear_quick_cache():
    global _cache_url, _cache_until
    with _cache_lock:
        _cache_url = ""
        _cache_until = 0.0


def get_cloudflare_remote_access(force=False):
    """Return active Cloudflare access as ``{'mode': ..., 'url': ...}``, or None.

    A configured managed Cloudflare Tunnel has priority over a temporary Quick
    Tunnel. The managed public URL is installer-owned metadata only; tunnel
    credentials are never read or exposed here.
    """
    global _cache_url, _cache_until

    if _managed_service_is_active():
        managed_url = _read_cloudflare_managed_url()
        if managed_url:
            _clear_quick_cache()
            return {"mode": "managed", "url": managed_url}

    if not _quick_service_is_active():
        _clear_quick_cache()
        return None

    now = time.monotonic()
    with _cache_lock:
        if not force and now < _cache_until:
            quick_url = _cache_url
        else:
            quick_url = _read_cloudflare_quick_url()
            _cache_url = quick_url
            _cache_until = now + _CACHE_SECONDS

    if quick_url:
        return {"mode": "quick", "url": quick_url}
    return None


def get_cloudflare_quick_url(force=False):
    """Backward-compatible helper that returns only an active Quick Tunnel URL."""
    access = get_cloudflare_remote_access(force=force)
    if access and access.get("mode") == "quick":
        return access.get("url", "")
    return ""
