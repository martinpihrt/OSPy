#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Creation, validation and staged restoration of OSPy system backups."""

import hashlib
import json
import ntpath
import os
import shutil
import stat
import tempfile
import time
import uuid
import zipfile


SCHEMA_VERSION = 1
MANIFEST_NAME = "ospy-backup.json"
MAX_FILES = 50000
MAX_EXPANDED_SIZE = 512 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200


class BackupError(ValueError):
    pass


def _root(root=None):
    return os.path.abspath(root or os.getcwd())


def _sha256_member(archive, info):
    digest = hashlib.sha256()
    with archive.open(info) as source:
        while True:
            chunk = source.read(64 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _is_session_store_file(name):
    """Return whether a backup path belongs to the disposable web session DB."""
    normalized = str(name).replace("\\", "/").lstrip("/")
    prefix = "ospy/data/"
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix):]
    return normalized == "sessions.db" or normalized.startswith("sessions.db.")


def _backup_sources(root):
    sources = []
    for relative in (os.path.join("ospy", "data"),
                     os.path.join("ospy", "images", "stations")):
        source_root = os.path.join(root, relative)
        if not os.path.isdir(source_root):
            continue
        for current, dirs, files in os.walk(source_root):
            dirs[:] = [name for name in dirs if name != "__pycache__"]
            for name in files:
                if name in (".gitignore",) or name.endswith((".pyc", ".pyo")):
                    continue
                path = os.path.join(current, name)
                if os.path.islink(path) or not os.path.isfile(path):
                    continue
                archive_name = os.path.relpath(path, root).replace(os.sep, "/")
                if _is_session_store_file(archive_name):
                    continue
                sources.append((archive_name, path))
    return sorted(sources)


def create_system_backup(destination=None, root=None, reason="manual"):
    """Create a self-describing backup and return its absolute path."""
    root = _root(root)
    backup_dir = os.path.join(root, "ospy", "backup")
    os.makedirs(backup_dir, exist_ok=True)
    if destination is None:
        filename = "ospy_system_backup_{}_{}.zip".format(
            time.strftime("%Y-%m-%d_%H-%M-%S"), uuid.uuid4().hex[:6]
        )
        destination = os.path.join(backup_dir, filename)
    destination = os.path.abspath(destination)
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    sources = _backup_sources(root)
    from ospy import version
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reason": str(reason),
        "ospy_version": version.ver_str,
        "ospy_revision": version.revision,
        "files": [],
        "excludes": [
            "SSL certificates", "plug-in code", "Python caches",
            "active web sessions",
        ],
    }

    fd, temporary = tempfile.mkstemp(prefix=".ospy-backup-", suffix=".zip",
                                     dir=os.path.dirname(destination))
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED,
                             allowZip64=True) as archive:
            for archive_name, path in sources:
                digest = hashlib.sha256()
                size = 0
                with open(path, "rb") as source, archive.open(archive_name, "w") as target:
                    while True:
                        chunk = source.read(64 * 1024)
                        if not chunk:
                            break
                        target.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
                manifest["files"].append({
                    "path": archive_name,
                    "size": size,
                    "sha256": digest.hexdigest(),
                })
            archive.writestr(MANIFEST_NAME, json.dumps(
                manifest, ensure_ascii=False, indent=2, sort_keys=True
            ).encode("utf-8"))
        inspect_backup(temporary)
        os.replace(temporary, destination)
        _prune_system_backups(backup_dir, keep=10)
    except Exception:
        if os.path.exists(temporary):
            os.remove(temporary)
        raise
    return destination


def _prune_system_backups(backup_dir, keep=10):
    archives = []
    for name in os.listdir(backup_dir):
        if not name.lower().endswith(".zip"):
            continue
        path = os.path.join(backup_dir, name)
        if os.path.isfile(path):
            archives.append((os.path.getmtime(path), path))
    for unused_mtime, path in sorted(archives, reverse=True)[max(1, int(keep)):]:
        try:
            os.remove(path)
        except OSError:
            pass


def system_backup_path(filename, root=None):
    """Resolve a stored backup name without permitting path traversal."""
    name = os.path.basename(str(filename or ""))
    if not name or name != str(filename) or not name.lower().endswith(".zip"):
        return None
    backup_dir = os.path.join(_root(root), "ospy", "backup")
    path = os.path.abspath(os.path.join(backup_dir, name))
    if os.path.commonpath([os.path.abspath(backup_dir), path]) != os.path.abspath(backup_dir):
        return None
    return path if os.path.isfile(path) else None


def list_system_backups(root=None):
    backup_dir = os.path.join(_root(root), "ospy", "backup")
    if not os.path.isdir(backup_dir):
        return []
    result = []
    for name in os.listdir(backup_dir):
        path = system_backup_path(name, root=root)
        if path is not None:
            result.append({
                "name": name,
                "size": os.path.getsize(path),
                "modified": os.path.getmtime(path),
            })
    return sorted(result, key=lambda item: item["modified"], reverse=True)


def _normalized_member(info):
    name = info.filename.replace("\\", "/")
    if not name or name.startswith("/") or "\x00" in name:
        raise BackupError(_("Unsafe path in backup ZIP: {}").format(info.filename))
    parts = name.split("/")
    if (any(part in (".", "..") for part in parts) or
            any(part == "" for part in parts[:-1])):
        raise BackupError(_("Unsafe path in backup ZIP: {}").format(info.filename))
    drive = ntpath.splitdrive(name)[0]
    if drive:
        raise BackupError(_("Unsafe path in backup ZIP: {}").format(info.filename))
    mode = info.external_attr >> 16
    file_type = stat.S_IFMT(mode)
    if file_type and file_type not in (stat.S_IFREG, stat.S_IFDIR):
        raise BackupError(_("Unsupported entry in backup ZIP: {}").format(info.filename))
    if info.flag_bits & 0x1:
        raise BackupError(_("Encrypted backup ZIP entries are not supported."))
    return "/".join(part for part in parts if part)


def inspect_backup(path):
    """Validate an archive completely and return its normalized manifest."""
    try:
        archive = zipfile.ZipFile(path, "r")
    except (OSError, zipfile.BadZipFile) as error:
        raise BackupError(_("The uploaded file is not a valid ZIP archive.")) from error
    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_FILES:
            raise BackupError(_("The backup contains too many files."))
        names = {}
        expanded = 0
        for info in infos:
            name = _normalized_member(info)
            key = name.casefold()
            if key in names:
                raise BackupError(_("Duplicate path in backup ZIP: {}").format(name))
            names[key] = info
            expanded += info.file_size
            if expanded > MAX_EXPANDED_SIZE:
                raise BackupError(_("The expanded backup is too large."))
            if (info.file_size > 1024 * 1024 and
                    info.file_size / float(max(info.compress_size, 1)) > MAX_COMPRESSION_RATIO):
                raise BackupError(_("Suspicious compression ratio in backup ZIP."))

        manifest_info = names.get(MANIFEST_NAME.casefold())
        if manifest_info is None:
            # Backward compatibility with historical OSPy backups. They contain
            # only the contents of ospy/data at the archive root.
            legacy_files = [name for name in names if not names[name].is_dir()]
            if not legacy_files:
                raise BackupError(_("The backup does not contain any files."))
            return {
                "schema_version": 0,
                "legacy": True,
                "files": [{"path": names[name].filename.replace("\\", "/")}
                          for name in legacy_files],
            }

        if manifest_info.file_size > 1024 * 1024:
            raise BackupError(_("The backup manifest is too large."))
        try:
            manifest = json.loads(archive.read(manifest_info).decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as error:
            raise BackupError(_("The backup manifest is invalid.")) from error
        if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
            raise BackupError(_("The backup format is not supported by this OSPy version."))
        file_entries = manifest.get("files")
        if not isinstance(file_entries, list) or not file_entries:
            raise BackupError(_("The backup manifest does not contain a file list."))
        declared = set()
        for entry in file_entries:
            if not isinstance(entry, dict):
                raise BackupError(_("The backup manifest contains an invalid file entry."))
            name = str(entry.get("path", "")).replace("\\", "/")
            if not (name.startswith("ospy/data/") or
                    name.startswith("ospy/images/stations/")):
                raise BackupError(_("File is outside the permitted backup locations: {}").format(name))
            info = names.get(name.casefold())
            if info is None or info.is_dir():
                raise BackupError(_("A file declared by the backup is missing: {}").format(name))
            if entry.get("size") != info.file_size:
                raise BackupError(_("Backup file size does not match its manifest: {}").format(name))
            digest = _sha256_member(archive, info)
            if digest != entry.get("sha256"):
                raise BackupError(_("Backup file checksum is invalid: {}").format(name))
            declared.add(name.casefold())
        payload = {name for name, info in names.items()
                   if not info.is_dir() and name != MANIFEST_NAME.casefold()}
        if payload != declared:
            raise BackupError(_("The backup contains files not declared in its manifest."))
        manifest["legacy"] = False
        return manifest


def stage_restore(path, staging_root=None, root=None):
    """Validate and extract a backup into a private staging directory."""
    root = _root(root)
    manifest = inspect_backup(path)
    parent = staging_root or os.path.join(root, "ospy", "upload")
    os.makedirs(parent, exist_ok=True)
    staging = os.path.join(parent, "restore-{}".format(uuid.uuid4().hex))
    os.makedirs(staging)
    try:
        with zipfile.ZipFile(path, "r") as archive:
            if manifest.get("legacy"):
                data_target = os.path.join(staging, "ospy", "data")
                os.makedirs(data_target)
                for info in archive.infolist():
                    name = _normalized_member(info)
                    if info.is_dir() or _is_session_store_file(name):
                        continue
                    destination = os.path.abspath(os.path.join(data_target, *name.split("/")))
                    if os.path.commonpath([data_target, destination]) != data_target:
                        raise BackupError(_("Unsafe path in backup ZIP: {}").format(name))
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    with archive.open(info) as source, open(destination, "wb") as target:
                        shutil.copyfileobj(source, target)
            else:
                for entry in manifest["files"]:
                    name = entry["path"]
                    if _is_session_store_file(name):
                        continue
                    destination = os.path.join(staging, *name.split("/"))
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    with archive.open(name) as source, open(destination, "wb") as target:
                        shutil.copyfileobj(source, target)
        return staging, manifest
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def apply_staged_restore(staging, root=None):
    """Atomically replace backed-up locations, restoring originals on failure."""
    root = _root(root)
    replacements = []
    for relative in (os.path.join("ospy", "data"),
                     os.path.join("ospy", "images", "stations")):
        source = os.path.join(staging, relative)
        if os.path.isdir(source):
            replacements.append((source, os.path.join(root, relative)))
    if not replacements:
        raise BackupError(_("The staged backup contains no restorable OSPy data."))

    rollback = os.path.join(root, "ospy", "upload", "restore-rollback-{}".format(uuid.uuid4().hex))
    os.makedirs(rollback)
    moved = []
    try:
        for source, target in replacements:
            old = os.path.join(rollback, os.path.relpath(target, root))
            os.makedirs(os.path.dirname(old), exist_ok=True)
            had_old = os.path.exists(target)
            if os.path.exists(target):
                os.replace(target, old)
            moved.append((target, old, had_old))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            os.replace(source, target)
    except Exception:
        for target, old, had_old in reversed(moved):
            if os.path.exists(target):
                shutil.rmtree(target, ignore_errors=True)
            if had_old and os.path.exists(old):
                os.makedirs(os.path.dirname(target), exist_ok=True)
                os.replace(old, target)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    shutil.rmtree(rollback, ignore_errors=True)
