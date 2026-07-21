#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Settings storage backends and optional database capability checks.

Shelve/DBM remains the only active settings backend.  The SQLite probe is
deliberately read/write-free: it opens an in-memory database only so a future
migration can be prepared without changing existing installations.
"""

import shelve
import threading
import time


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
