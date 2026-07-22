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
from contextlib import contextmanager


SCHEMA_VERSION = 2
SUPPORTED_SCHEMA_VERSIONS = (1, SCHEMA_VERSION)
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


@contextmanager
def _settings_snapshot_guard(root):
    """Drain and block live settings writes while their files are archived."""
    guarded = False
    live_options = None
    try:
        expected = os.path.abspath(os.path.join(root, "ospy", "data"))
        actual = os.path.abspath(os.environ.get("OSPY_DATA_DIR", "./ospy/data"))
        if os.path.normcase(expected) == os.path.normcase(actual):
            from ospy.options import options
            if not options.flush():
                raise BackupError(_("Pending settings could not be saved before backup."))
            live_options = options
            live_options._lock.acquire()
            guarded = True
        yield
    finally:
        if guarded:
            live_options._lock.release()


def _sqlite_backup_snapshot(source, destination):
    """Create and independently verify one transactionally consistent copy."""
    import sqlite3
    from ospy.settings_storage import sqlite_mirror_store

    source_connection = sqlite3.connect(
        "file:{}?mode=ro".format(os.path.abspath(source)), uri=True
    )
    target_connection = sqlite3.connect(destination)
    try:
        source_connection.backup(target_connection)
        target_connection.commit()
        integrity = target_connection.execute("PRAGMA integrity_check").fetchone()
        if integrity != ("ok",):
            raise BackupError(_("The SQLite backup snapshot failed its integrity check."))
    finally:
        target_connection.close()
        source_connection.close()

    recovered = sqlite_mirror_store.read_recovery_candidate(destination)
    return {
        "included": True,
        "path": "ospy/data/default/{}".format(sqlite_mirror_store.filename),
        "schema_version": sqlite_mirror_store.schema_version,
        "settings_count": len(recovered),
    }


def _settings_storage_manifest(root, sources, snapshot_root):
    from ospy.settings_storage import sqlite_mirror_store

    storage = {
        "authoritative_backend": "shelve/DBM",
        "settings_mode": "compatible",
        "sqlite_snapshot": {"included": False},
        "primary_marker": "",
    }
    shelve_path = os.path.join(root, "ospy", "data", "default", "options.db")
    try:
        from ospy.settings_storage import settings_store
        values = settings_store.read(shelve_path) or {}
        mode = values.get("settings_storage_mode", "compatible")
        if mode in ("compatible", "verification", "custom", "sqlite_primary"):
            storage["settings_mode"] = mode
        if mode == "sqlite_primary":
            storage["authoritative_backend"] = "SQLite"
    except Exception:
        # A backup can still preserve a legacy or partially damaged shelve
        # database. Restore-time validation decides whether it can be used.
        pass

    sqlite_path = sqlite_mirror_store.path_for(shelve_path)
    if os.path.isfile(sqlite_path):
        snapshot_path = os.path.join(snapshot_root, sqlite_mirror_store.filename)
        storage["sqlite_snapshot"] = _sqlite_backup_snapshot(
            sqlite_path, snapshot_path
        )
        archive_name = storage["sqlite_snapshot"]["path"]
        sources = [
            (name, snapshot_path if name == archive_name else path)
            for name, path in sources
        ]
    elif storage["authoritative_backend"] == "SQLite":
        raise BackupError(_("SQLite is authoritative but no settings database is available for backup."))
    if storage["authoritative_backend"] == "SQLite":
        marker_name = "ospy/data/sqlite_primary.enabled"
        marker_path = os.path.join(root, *marker_name.split("/"))
        try:
            if os.path.islink(marker_path):
                raise OSError("symbolic link")
            with open(marker_path, "r", encoding="ascii") as marker:
                enabled = marker.read(32).strip() == "enabled-v1"
        except (OSError, UnicodeError):
            enabled = False
        if not enabled:
            raise BackupError(_("SQLite primary is active but its activation marker is invalid."))
        storage["primary_marker"] = marker_name
    return storage, sources


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

    fd, temporary = tempfile.mkstemp(prefix=".ospy-backup-", suffix=".zip",
                                     dir=os.path.dirname(destination))
    os.close(fd)
    try:
        with _settings_snapshot_guard(root):
            with tempfile.TemporaryDirectory(prefix="ospy-backup-snapshot-") as snapshot_root:
                sources = _backup_sources(root)
                storage, sources = _settings_storage_manifest(
                    root, sources, snapshot_root
                )
                from ospy import version
                manifest = {
                    "schema_version": SCHEMA_VERSION,
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "reason": str(reason),
                    "ospy_version": version.ver_str,
                    "ospy_revision": version.revision,
                    "settings_storage": storage,
                    "files": [],
                    "excludes": [
                        "SSL certificates", "plug-in code", "Python caches",
                        "active web sessions",
                    ],
                }

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
        if (not isinstance(manifest, dict) or
                manifest.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS):
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
        if manifest.get("schema_version") >= 2:
            storage = manifest.get("settings_storage")
            if not isinstance(storage, dict):
                raise BackupError(_("The backup settings-storage metadata is invalid."))
            if storage.get("authoritative_backend") not in ("shelve/DBM", "SQLite"):
                raise BackupError(_("The backup settings backend is invalid."))
            if storage.get("settings_mode") not in (
                    "compatible", "verification", "custom", "sqlite_primary"):
                raise BackupError(_("The backup settings-storage mode is invalid."))
            snapshot = storage.get("sqlite_snapshot")
            if not isinstance(snapshot, dict) or not isinstance(snapshot.get("included"), bool):
                raise BackupError(_("The backup SQLite snapshot metadata is invalid."))
            if snapshot.get("included"):
                if snapshot.get("path") != "ospy/data/default/options.sqlite3":
                    raise BackupError(_("The backup SQLite snapshot path is invalid."))
                if snapshot["path"].casefold() not in declared:
                    raise BackupError(_("The backup SQLite snapshot is missing."))
                if not isinstance(snapshot.get("schema_version"), int):
                    raise BackupError(_("The backup SQLite schema version is invalid."))
                if not isinstance(snapshot.get("settings_count"), int):
                    raise BackupError(_("The backup SQLite settings count is invalid."))
            elif storage.get("authoritative_backend") == "SQLite":
                raise BackupError(_("An SQLite-primary backup does not contain its settings database."))
            if storage.get("authoritative_backend") == "SQLite":
                marker = storage.get("primary_marker")
                if marker != "ospy/data/sqlite_primary.enabled":
                    raise BackupError(_("The SQLite-primary backup marker metadata is invalid."))
                if marker.casefold() not in declared:
                    raise BackupError(_("The SQLite-primary backup marker is missing."))
        manifest["legacy"] = False
        return manifest


def _validate_staged_settings_storage(staging, manifest):
    if manifest.get("legacy") or manifest.get("schema_version", 0) < 2:
        return
    storage = manifest["settings_storage"]
    snapshot = storage["sqlite_snapshot"]
    if not snapshot.get("included"):
        return
    from ospy.settings_storage import sqlite_mirror_store
    path = os.path.join(staging, *snapshot["path"].split("/"))
    try:
        values = sqlite_mirror_store.read_recovery_candidate(path)
    except Exception as error:
        raise BackupError(_("The backup SQLite settings snapshot is invalid: {}").format(error))
    if snapshot.get("schema_version") != sqlite_mirror_store.schema_version:
        raise BackupError(_("The backup SQLite schema is not supported."))
    if snapshot.get("settings_count") != len(values):
        raise BackupError(_("The backup SQLite settings count does not match."))
    mode = values.get("settings_storage_mode", "compatible")
    if mode != storage.get("settings_mode"):
        raise BackupError(_("The backup settings-storage mode does not match its database."))
    if storage.get("authoritative_backend") == "SQLite":
        marker_path = os.path.join(staging, *storage["primary_marker"].split("/"))
        try:
            with open(marker_path, "r", encoding="ascii") as marker:
                marker_enabled = marker.read(32).strip() == "enabled-v1"
        except (OSError, UnicodeError):
            marker_enabled = False
        if not marker_enabled:
            raise BackupError(_("The backup SQLite-primary activation marker is invalid."))


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
        _validate_staged_settings_storage(staging, manifest)
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
