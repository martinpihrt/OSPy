#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Settings storage, verified SQLite snapshots and migration safeguards."""

import shelve
import threading
import time
import os
import pickle
import hashlib
import json


class SettingsStore(object):
    """Interface used by the settings persistence layer."""

    name = ''

    def read(self, path):
        raise NotImplementedError

    def write(self, path, values, saved_at=None):
        raise NotImplementedError

    def last_save(self, path):
        raise NotImplementedError

    def backend(self, path):
        raise NotImplementedError


class ShelveSettingsStore(SettingsStore):
    """The existing OSPy shelve/DBM settings format."""

    name = 'shelve'

    def read(self, path):
        database = None
        try:
            database = shelve.open(path, flag='r')
            keys = list(database.keys())
            if not keys:
                return None
            return {key: database[key] for key in keys}
        finally:
            if database is not None:
                database.close()

    def write(self, path, values, saved_at=None):
        from dbm.dumb import open as dumb_open

        timestamp = time.time() if saved_at is None else float(saved_at)
        database = shelve.Shelf(dumb_open(path))
        try:
            database.clear()
            database.update(values)
            database['last_save'] = timestamp
        finally:
            database.close()
        return timestamp

    def last_save(self, path):
        database = None
        try:
            database = shelve.open(path, flag='r')
            return float(database['last_save'])
        finally:
            if database is not None:
                database.close()

    def backend(self, path):
        from dbm import whichdb
        return whichdb(path) or ''


settings_store = ShelveSettingsStore()


class SQLiteMirrorStore(object):
    """Verified SQLite settings store used as a shadow or guarded primary."""

    schema_version = 3
    filename = 'options.sqlite3'

    def path_for(self, shelve_path):
        return os.path.join(os.path.dirname(shelve_path), self.filename)

    @staticmethod
    def _snapshot_checksum(checksums):
        payload = json.dumps(
            sorted(checksums.items()),
            ensure_ascii=False,
            separators=(',', ':'),
        ).encode('utf-8')
        return hashlib.sha256(payload).hexdigest()

    def write(self, path, values, saved_at):
        import sqlite3

        temporary = path + '.new'
        connection = None
        serialized = {
            str(key): pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            for key, value in values.items()
        }
        serialized['last_save'] = pickle.dumps(
            float(saved_at), protocol=pickle.HIGHEST_PROTOCOL
        )
        checksums = {
            key: hashlib.sha256(value).hexdigest()
            for key, value in serialized.items()
        }
        try:
            if os.path.exists(temporary):
                os.remove(temporary)
            connection = sqlite3.connect(temporary)
            connection.execute('PRAGMA synchronous = FULL')
            connection.execute(
                'CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)'
            )
            connection.execute(
                'CREATE TABLE settings ('
                'key TEXT PRIMARY KEY, value BLOB NOT NULL, checksum TEXT NOT NULL)'
            )
            connection.executemany(
                'INSERT INTO settings (key, value, checksum) VALUES (?, ?, ?)',
                [
                    (key, sqlite3.Binary(value), checksums[key])
                    for key, value in serialized.items()
                ]
            )
            source_label = (
                'SQLite primary'
                if values.get('settings_storage_mode') == 'sqlite_primary'
                else 'shelve/DBM'
            )
            connection.executemany(
                'INSERT INTO metadata (key, value) VALUES (?, ?)',
                [
                    ('schema_version', str(self.schema_version)),
                    ('source', source_label),
                    ('last_save', repr(float(saved_at))),
                    ('record_count', str(len(serialized))),
                    ('snapshot_checksum', self._snapshot_checksum(checksums)),
                ]
            )
            connection.commit()
            integrity = connection.execute('PRAGMA integrity_check').fetchone()
            stored = {
                key: (bytes(value), checksum)
                for key, value, checksum in connection.execute(
                    'SELECT key, value, checksum FROM settings'
                )
            }
            if integrity != ('ok',):
                raise RuntimeError('SQLite mirror integrity check failed: {}'.format(integrity))
            if set(stored) != set(serialized):
                raise RuntimeError('SQLite mirror key verification failed.')
            for key, expected in serialized.items():
                value, checksum = stored[key]
                if value != expected:
                    raise RuntimeError('SQLite mirror value verification failed: {}'.format(key))
                if hashlib.sha256(value).hexdigest() != checksum:
                    raise RuntimeError('SQLite mirror checksum verification failed: {}'.format(key))
            connection.close()
            connection = None
            os.replace(temporary, path)
            return {
                'state': 'synchronized',
                'schema_version': self.schema_version,
                'count': len(serialized),
                'last_save': float(saved_at),
                'error': '',
            }
        finally:
            if connection is not None:
                connection.close()
            if os.path.exists(temporary):
                try:
                    os.remove(temporary)
                except OSError:
                    pass

    def read(self, path):
        """Read the mirror for verification and tests, never for OSPy startup."""
        import sqlite3

        connection = sqlite3.connect('file:{}?mode=ro'.format(path), uri=True)
        try:
            return {
                key: pickle.loads(bytes(value))
                for key, value in connection.execute(
                    'SELECT key, value FROM settings'
                )
            }
        finally:
            connection.close()

    def status(self, path):
        if not os.path.isfile(path):
            return {
                'state': 'pending', 'schema_version': self.schema_version,
                'count': 0, 'last_save': 0, 'error': '',
            }
        connection = None
        try:
            import sqlite3
            connection = sqlite3.connect('file:{}?mode=ro'.format(path), uri=True)
            integrity = connection.execute('PRAGMA integrity_check').fetchone()
            if integrity != ('ok',):
                raise RuntimeError('SQLite mirror integrity check failed: {}'.format(integrity))
            metadata = dict(connection.execute('SELECT key, value FROM metadata'))
            count = connection.execute('SELECT COUNT(*) FROM settings').fetchone()[0]
            schema_version = int(metadata.get('schema_version', 0))
            if schema_version in (1, 2):
                return {
                    'state': 'upgrade_pending',
                    'schema_version': schema_version,
                    'count': int(count),
                    'last_save': float(metadata.get('last_save', 0)),
                    'error': '',
                }
            if schema_version != self.schema_version:
                raise RuntimeError(
                    'Unsupported SQLite mirror schema: {}'.format(schema_version)
                )
            for key, value, checksum in connection.execute(
                    'SELECT key, value, checksum FROM settings'):
                if hashlib.sha256(bytes(value)).hexdigest() != checksum:
                    raise RuntimeError(
                        'SQLite mirror checksum verification failed: {}'.format(key)
                    )
            checksums = dict(connection.execute(
                'SELECT key, checksum FROM settings'
            ))
            expected_count = int(metadata.get('record_count', -1))
            if expected_count != int(count):
                raise RuntimeError(
                    'SQLite mirror record-count verification failed.'
                )
            if self._snapshot_checksum(checksums) != metadata.get('snapshot_checksum'):
                raise RuntimeError(
                    'SQLite mirror snapshot verification failed.'
                )
            return {
                'state': 'synchronized',
                'schema_version': schema_version,
                'count': int(count),
                'last_save': float(metadata.get('last_save', 0)),
                'error': '',
            }
        except Exception as error:
            return {
                'state': 'error', 'schema_version': self.schema_version,
                'count': 0, 'last_save': 0,
                'error': '{}: {}'.format(type(error).__name__, error),
            }
        finally:
            if connection is not None:
                connection.close()

    def compare(self, path, expected_values):
        """Compare hashes without unpickling data from the SQLite mirror."""
        status = self.status(path)
        if status.get('state') != 'synchronized':
            return status

        import sqlite3

        expected = {
            str(key): hashlib.sha256(
                pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            ).hexdigest()
            for key, value in expected_values.items()
        }
        connection = sqlite3.connect('file:{}?mode=ro'.format(path), uri=True)
        try:
            stored = dict(connection.execute(
                'SELECT key, checksum FROM settings'
            ))
        finally:
            connection.close()

        missing = sorted(set(expected) - set(stored))
        unexpected = sorted(set(stored) - set(expected))
        changed = sorted(
            key for key in set(expected) & set(stored)
            if expected[key] != stored[key]
        )
        differences = (
            ['missing: ' + key for key in missing] +
            ['unexpected: ' + key for key in unexpected] +
            ['changed: ' + key for key in changed]
        )
        status['state'] = 'verified' if not differences else 'diverged'
        status['differences'] = differences[:20]
        status['difference_count'] = len(differences)
        status['checked'] = time.time()
        return status

    def _verified_serialized(self, path, expected_values):
        """Return serialized rows only after complete snapshot verification."""
        import sqlite3

        expected = {
            str(key): hashlib.sha256(
                pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            ).hexdigest()
            for key, value in expected_values.items()
        }
        connection = sqlite3.connect('file:{}?mode=ro'.format(path), uri=True)
        try:
            rows = {
                key: (bytes(value), checksum)
                for key, value, checksum in connection.execute(
                    'SELECT key, value, checksum FROM settings'
                )
            }
        finally:
            connection.close()

        if set(rows) != set(expected):
            raise ValueError('SQLite shadow keys do not match authoritative settings.')
        for key, (value, checksum) in rows.items():
            actual = hashlib.sha256(value).hexdigest()
            if actual != checksum or actual != expected[key]:
                raise ValueError(
                    'SQLite shadow value is not verified against shelve/DBM: {}'.format(key)
                )

        return rows

    def read_verified(self, path, expected_values):
        """Decode only a snapshot whose hashes match authoritative values."""
        rows = self._verified_serialized(path, expected_values)

        # All bytes are held in this verified snapshot before any value is
        # decoded, so a later filesystem change cannot alter decoded input.
        return {
            key: pickle.loads(value)
            for key, (value, checksum) in rows.items()
        }

    def read_verified_value(self, path, key, expected_values):
        """Decode one value after verifying the complete SQLite snapshot."""
        rows = self._verified_serialized(path, expected_values)
        if key not in rows:
            raise KeyError(key)
        return pickle.loads(rows[key][0])

    def read_recovery_candidate(self, path):
        """Independently verify and decode one schema 3 recovery snapshot."""
        import sqlite3

        connection = sqlite3.connect('file:{}?mode=ro'.format(path), uri=True)
        try:
            connection.execute('BEGIN')
            integrity = connection.execute('PRAGMA integrity_check').fetchone()
            if integrity != ('ok',):
                raise ValueError(
                    'SQLite recovery integrity check failed: {}'.format(integrity)
                )
            metadata = dict(connection.execute(
                'SELECT key, value FROM metadata'
            ))
            if int(metadata.get('schema_version', 0)) != self.schema_version:
                raise ValueError('SQLite recovery snapshot requires schema 3.')
            rows = {
                key: (bytes(value), checksum)
                for key, value, checksum in connection.execute(
                    'SELECT key, value, checksum FROM settings'
                )
            }
        finally:
            connection.close()

        checksums = {}
        for key, (value, checksum) in rows.items():
            actual = hashlib.sha256(value).hexdigest()
            if actual != checksum:
                raise ValueError(
                    'SQLite recovery value checksum failed: {}'.format(key)
                )
            checksums[key] = checksum
        if int(metadata.get('record_count', -1)) != len(rows):
            raise ValueError('SQLite recovery record count failed.')
        if self._snapshot_checksum(checksums) != metadata.get('snapshot_checksum'):
            raise ValueError('SQLite recovery snapshot checksum failed.')

        return {
            key: pickle.loads(value)
            for key, (value, checksum) in rows.items()
        }


sqlite_mirror_store = SQLiteMirrorStore()


class SQLiteMigrationEvidence(object):
    """Non-authoritative counters proving experimental paths over time."""

    filename = 'sqlite_migration_evidence.json'
    version = 1

    def __init__(self):
        self._lock = threading.RLock()

    def path_for(self, shelve_path):
        data_root = os.path.dirname(os.path.dirname(shelve_path))
        return os.path.join(data_root, self.filename)

    def _empty(self):
        return {
            'version': self.version,
            'verified_start_streak': 0,
            'strict_write_streak': 0,
            'last_verified_start': 0,
            'last_strict_write': 0,
            'last_failure': 0,
            'last_failure_event': '',
            'last_error': '',
        }

    def read(self, path):
        result = self._empty()
        try:
            with open(path, 'r', encoding='utf-8') as source:
                stored = json.load(source)
            if not isinstance(stored, dict) or stored.get('version') != self.version:
                return result
            for key in ('verified_start_streak', 'strict_write_streak'):
                value = stored.get(key, 0)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    result[key] = value
            for key in ('last_verified_start', 'last_strict_write', 'last_failure'):
                value = stored.get(key, 0)
                if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                    result[key] = float(value)
            for key in ('last_failure_event', 'last_error'):
                value = stored.get(key, '')
                if isinstance(value, str):
                    result[key] = value[:1000]
        except (OSError, ValueError, TypeError):
            pass
        return result

    def record(self, path, event, success, error=''):
        if event not in ('verified_start', 'strict_write'):
            raise ValueError('Unsupported SQLite migration evidence event.')
        with self._lock:
            values = self.read(path)
            timestamp = time.time()
            streak_key = (
                'verified_start_streak'
                if event == 'verified_start' else 'strict_write_streak'
            )
            time_key = (
                'last_verified_start'
                if event == 'verified_start' else 'last_strict_write'
            )
            if success:
                values[streak_key] += 1
                values[time_key] = timestamp
            else:
                values[streak_key] = 0
                values['last_failure'] = timestamp
                values['last_failure_event'] = event
                values['last_error'] = str(error)[:1000]

            temporary = path + '.new'
            os.makedirs(os.path.dirname(path), exist_ok=True)
            try:
                with open(temporary, 'w', encoding='utf-8') as target:
                    json.dump(values, target, ensure_ascii=False,
                              indent=2, sort_keys=True)
                    target.flush()
                    os.fsync(target.fileno())
                try:
                    os.chmod(temporary, 0o600)
                except OSError:
                    pass
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    try:
                        os.remove(temporary)
                    except OSError:
                        pass
            return dict(values)


sqlite_migration_evidence = SQLiteMigrationEvidence()


SQLITE_PRIMARY_REQUIRED_STARTS = 5
SQLITE_PRIMARY_REQUIRED_WRITES = 20


def sqlite_primary_readiness(status):
    """Evaluate evidence for a future opt-in SQLite-primary beta mode."""
    evidence = status.get('migration_evidence') or {}
    starts = int(evidence.get('verified_start_streak', 0) or 0)
    writes = int(evidence.get('strict_write_streak', 0) or 0)
    blockers = []
    if status.get('settings_storage_mode') not in (
            'verification', 'sqlite_primary'):
        blockers.append('verification_mode')
    if status.get('state') != 'verified':
        blockers.append('current_shadow')
    if status.get('read_test') != 'passed':
        blockers.append('read_test')
    if status.get('recovery_test') != 'passed':
        blockers.append('current_recovery')
    if status.get('backup_recovery_test') != 'passed':
        blockers.append('backup_recovery')
    if status.get('restore_rehearsal') != 'passed':
        blockers.append('restore_rehearsal')
    if status.get('emergency_selection') != 'ready':
        blockers.append('emergency_selection')
    if not status.get('emergency_recovery_enabled'):
        blockers.append('emergency_recovery')
    if status.get('preferred_read') != 'used':
        blockers.append('verified_read')
    if not status.get('strict_dual_write_enabled'):
        blockers.append('strict_write')

    collecting = []
    if starts < SQLITE_PRIMARY_REQUIRED_STARTS:
        collecting.append('verified_starts')
    if writes < SQLITE_PRIMARY_REQUIRED_WRITES:
        collecting.append('strict_writes')

    state = 'blocked' if blockers else ('collecting' if collecting else 'ready')
    return {
        'state': state,
        'blockers': blockers,
        'collecting': collecting,
        'verified_starts': starts,
        'required_verified_starts': SQLITE_PRIMARY_REQUIRED_STARTS,
        'strict_writes': writes,
        'required_strict_writes': SQLITE_PRIMARY_REQUIRED_WRITES,
    }

_sqlite_capability_cache = None
_sqlite_capability_lock = threading.RLock()


def sqlite_capability(refresh=False):
    """Return availability details for Python's SQLite support.

    No filesystem database is opened or created by this probe.
    """
    global _sqlite_capability_cache
    with _sqlite_capability_lock:
        if _sqlite_capability_cache is not None and not refresh:
            return dict(_sqlite_capability_cache)

        connection = None
        try:
            import sqlite3
            connection = sqlite3.connect(':memory:')
            integrity = connection.execute('PRAGMA integrity_check').fetchone()
            if integrity != ('ok',):
                raise RuntimeError('SQLite in-memory integrity check did not return ok.')
            result = {
                'available': True,
                'version': sqlite3.sqlite_version,
                'error': '',
            }
        except Exception as error:
            result = {
                'available': False,
                'version': '',
                'error': '{}: {}'.format(type(error).__name__, error),
            }
        finally:
            if connection is not None:
                connection.close()

        _sqlite_capability_cache = result
        return dict(result)
