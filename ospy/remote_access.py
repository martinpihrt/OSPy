#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Helpers for optional remote-access status shown by the OSPy web interface."""

import os
import re
import subprocess
import threading
import time


_CLOUDFLARE_QUICK_SERVICE = "ospy-cloudflared-quick.service"
_CLOUDFLARE_QUICK_SERVICE_FILE = "/etc/systemd/system/ospy-cloudflared-quick.service"
_CACHE_SECONDS = 30.0
_COMMAND_TIMEOUT_SECONDS = 1.5
_QUICK_URL_RE = re.compile(
    r"https://[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.trycloudflare\.com"
    r"(?=$|[\s/\"'<>])",
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


def _extract_cloudflare_quick_url(text):
    """Return the last strict trycloudflare.com HTTPS URL found in journal text."""
    matches = _QUICK_URL_RE.findall(text or "")
    return matches[-1] if matches else ""


def _quick_service_is_active():
    """Return True only for the installer-created active Quick Tunnel service."""
    if not os.path.isfile(_CLOUDFLARE_QUICK_SERVICE_FILE):
        return False

    active = _run_command(
        ["systemctl", "is-active", "--quiet", _CLOUDFLARE_QUICK_SERVICE]
    )
    return active is not None and active.returncode == 0


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


def get_cloudflare_quick_url(force=False):
    """Return the active Quick Tunnel URL with a short journal-result cache."""
    global _cache_url, _cache_until

    if not _quick_service_is_active():
        with _cache_lock:
            _cache_url = ""
            _cache_until = 0.0
        return ""

    now = time.monotonic()
    with _cache_lock:
        if not force and now < _cache_until:
            return _cache_url

        _cache_url = _read_cloudflare_quick_url()
        _cache_until = now + _CACHE_SECONDS
        return _cache_url
