#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Storage backends and durable database outbox for built-in sensor history."""

import base64
import calendar
import json
import os
import re
import sqlite3
import threading
import time
import uuid

from ospy.helpers import mkdir_p
from ospy.log import log
from ospy.options import options


STORAGE_JSON = 0
STORAGE_DATABASE = 1
STORAGE_BOTH = 2
SOURCE_JSON = 0
SOURCE_DATABASE = 1
TABLE_NAME = 'ospy_sensor_logs'
KINDS = ('slog', 'elog')
OUTBOX_PATH = None
OUTBOX_MAX_OPERATIONS = 100000
OUTBOX_MAX_BYTES = 64 * 1024 * 1024
WORKER_BATCH_SIZE = 25
WORKER_IDLE_SECONDS = 5.0

_UID_RE = re.compile(r'^[0-9a-f]{32}$')
_local_lock = threading.RLock()
_outbox_lock = threading.RLock()
_delete_lock = threading.RLock()
_deleting_uids = set()
_schema_lock = threading.RLock()
_schema_connector = None
_status_lock = threading.RLock()
_status_cache = {'checked': 0.0, 'connector': None, 'available': False, 'summary': ''}


def new_sensor_uid():
    return uuid.uuid4().hex


def valid_sensor_uid(value):
    return bool(_UID_RE.match(str(value or '').lower()))


def normalize_storage(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = STORAGE_JSON
    return value if value in (STORAGE_JSON, STORAGE_DATABASE, STORAGE_BOTH) else STORAGE_JSON


def normalize_source(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = SOURCE_JSON
    return value if value in (SOURCE_JSON, SOURCE_DATABASE) else SOURCE_JSON


def _connector():
    try:
        import plugins
        if 'database_connector' not in plugins.running():
            return None
        connector = plugins.get('database_connector')
        if not getattr(connector, 'is_installed_ok', False):
            return None
        if not getattr(connector, 'plugin_options', {}).get('use', False):
            return None
        return connector
    except Exception:
        return None


def database_status(refresh=False):
    connector = _connector()
    if connector is None:
        return False, _('Database Connector is not available or is disabled.')
    if not _connector_supports_safe_changes(connector):
        return False, _('Database Connector does not support safe direct sensor operations.')
    now_value = time.time()
    with _status_lock:
        if (not refresh and _status_cache['connector'] is connector and
                now_value - _status_cache['checked'] < 10):
            return _status_cache['available'], _status_cache['summary']
    available = False
    summary = _('Database connection is not available.')
    try:
        rows = connector.execute_db('SELECT 1', commit=False, test=False, fetch=True)
        available = bool(rows and rows[0] and int(rows[0][0]) == 1)
        if available:
            summary = _('Database Connector is available.')
        else:
            health = connector.health() if hasattr(connector, 'health') else {}
            summary = health.get('summary', summary)
    except Exception:
        log.debug('sensor_log_storage.py', _('Database Connector availability check failed.'))
    with _status_lock:
        _status_cache.update({
            'checked': now_value,
            'connector': connector,
            'available': available,
            'summary': summary,
        })
    return available, summary


def database_available(refresh=False):
    return database_status(refresh=refresh)[0]


def _sensor_uid(sensor):
    value = str(getattr(sensor, 'log_uid', '') or '').lower()
    return value if valid_sensor_uid(value) else None


def _log_dir(sensor):
    return os.path.join('.', 'ospy', 'data', 'sensors', str(sensor.index), 'logs')


def _log_path(sensor, kind):
    return os.path.join(_log_dir(sensor), '{}.json'.format(kind))


def _fallback_path(sensor, kind):
    return os.path.join(_log_dir(sensor), '.database_fallback_{}.json'.format(kind))


def _read_json_file(path, default):
    try:
        with open(os.path.abspath(path), 'r') as source:
            value = json.load(source)
            return value if isinstance(value, type(default)) else default
    except (IOError, OSError, ValueError, TypeError):
        return default


def _write_json_file(path, value):
    absolute_path = os.path.abspath(path)
    mkdir_p(os.path.dirname(absolute_path))
    temporary = '{}.tmp'.format(absolute_path)
    with open(temporary, 'w') as target:
        json.dump(value, target)
        target.flush()
        os.fsync(target.fileno())
    os.replace(temporary, absolute_path)


def read_local_records(sensor, kind):
    if kind not in KINDS:
        return []
    with _local_lock:
        return _read_json_file(_log_path(sensor, kind), [])


def write_local_record(sensor, kind, record):
    if kind not in KINDS or not isinstance(record, dict):
        return False
    try:
        with _local_lock:
            records = _read_json_file(_log_path(sensor, kind), [])
            records.insert(0, dict(record))
            if options.run_sensor_entries > 0:
                records = records[:options.run_sensor_entries]
            _write_json_file(_log_path(sensor, kind), records)
        return True
    except Exception:
        log.debug('sensor_logs.py', traceback_text())
        return False


def _write_fallback_record(sensor, kind, record, recorded_at, record_uid=None):
    if kind not in KINDS or not isinstance(record, dict):
        return False
    entry = {
        'record_uid': str(record_uid or uuid.uuid4().hex).lower(),
        'recorded_at': int(recorded_at),
        'record': dict(record),
    }
    if not valid_sensor_uid(entry['record_uid']):
        return False
    try:
        with _local_lock:
            path = _fallback_path(sensor, kind)
            entries = _read_json_file(path, [])
            entries.insert(0, entry)
            if options.run_sensor_entries > 0:
                entries = entries[:options.run_sensor_entries]
            _write_json_file(path, entries)
        return True
    except Exception:
        log.debug('sensor_logs.py', traceback_text())
        return False


def _fallback_records(sensor, kind):
    records = []
    with _local_lock:
        entries = _read_json_file(_fallback_path(sensor, kind), [])
    for entry in entries:
        try:
            record_uid = str(entry['record_uid']).lower()
            record = dict(entry['record'])
            if not valid_sensor_uid(record_uid):
                continue
            record['_record_uid'] = record_uid
            record['_timestamp'] = int(entry['recorded_at'])
            records.append(record)
        except (KeyError, TypeError, ValueError):
            continue
    return records


def _queue_fallback_records(sensor, kind):
    sensor_uid = _sensor_uid(sensor)
    if sensor_uid is None or kind not in KINDS:
        return
    try:
        with _local_lock:
            path = _fallback_path(sensor, kind)
            entries = _read_json_file(path, [])
            remaining = []
            for index, entry in enumerate(entries):
                try:
                    queued = _enqueue_insert(
                        sensor_uid,
                        kind,
                        dict(entry['record']),
                        int(entry['recorded_at']),
                        str(entry['record_uid']).lower(),
                    )
                except (KeyError, TypeError, ValueError):
                    queued = False
                if not queued:
                    remaining.extend(entries[index:])
                    break
            if remaining:
                _write_json_file(path, remaining)
            elif os.path.isfile(os.path.abspath(path)):
                os.remove(os.path.abspath(path))
    except Exception:
        log.debug('sensor_logs.py', traceback_text())


def _encoded_payload(record):
    raw = json.dumps(record, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode('utf-8')
    return base64.b64encode(raw).decode('ascii')


def _decoded_payload(payload):
    if isinstance(payload, bytes):
        payload = payload.decode('ascii')
    raw = base64.b64decode(str(payload).encode('ascii'), validate=True)
    value = json.loads(raw.decode('utf-8'))
    return value if isinstance(value, dict) else None


def outbox_path():
    if OUTBOX_PATH:
        return os.path.abspath(OUTBOX_PATH)
    data_dir = os.environ.get('OSPY_DATA_DIR', os.path.join('.', 'ospy', 'data'))
    return os.path.abspath(os.path.join(data_dir, 'sensor_log_outbox.sqlite3'))


def _outbox_exists():
    return os.path.isfile(outbox_path())


def _outbox_connection():
    path = outbox_path()
    mkdir_p(os.path.dirname(path))
    connection = sqlite3.connect(path, timeout=1)
    connection.execute(
        'CREATE TABLE IF NOT EXISTS operations ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT, operation TEXT NOT NULL, '
        'sensor_uid TEXT NOT NULL, record_uid TEXT NOT NULL UNIQUE, '
        'kind TEXT NOT NULL, recorded_at INTEGER NOT NULL, '
        'payload TEXT NOT NULL, created_at REAL NOT NULL)'
    )
    connection.execute(
        'CREATE INDEX IF NOT EXISTS operations_sensor ON operations(sensor_uid, id)'
    )
    connection.commit()
    return connection


def _outbox_usage(connection):
    count = int(connection.execute('SELECT COUNT(*) FROM operations').fetchone()[0])
    page_size = int(connection.execute('PRAGMA page_size').fetchone()[0])
    page_count = int(connection.execute('PRAGMA page_count').fetchone()[0])
    free_pages = int(connection.execute('PRAGMA freelist_count').fetchone()[0])
    return count, max(0, page_count - free_pages) * page_size


def _enqueue_insert(sensor_uid, kind, record, recorded_at, record_uid=None):
    record_uid = str(record_uid or uuid.uuid4().hex).lower()
    if not valid_sensor_uid(sensor_uid) or not valid_sensor_uid(record_uid) or kind not in KINDS:
        return False
    payload = _encoded_payload(record)
    try:
        with _outbox_lock:
            connection = _outbox_connection()
            try:
                count, used_bytes = _outbox_usage(connection)
                required_bytes = len(payload.encode('ascii')) + 256
                if count >= OUTBOX_MAX_OPERATIONS or used_bytes + required_bytes > OUTBOX_MAX_BYTES:
                    log.error('sensor_log_storage.py', _('Critical: sensor database outbox capacity was exceeded.'))
                    return False
                connection.execute(
                    'INSERT OR IGNORE INTO operations '
                    '(operation, sensor_uid, record_uid, kind, recorded_at, payload, created_at) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?)',
                    ('insert', sensor_uid, record_uid, kind, int(recorded_at), payload, time.time())
                )
                connection.commit()
            finally:
                connection.close()
        _wake_worker()
        return True
    except Exception:
        log.error('sensor_log_storage.py', _('Critical: sensor database operation could not be queued.'))
        log.debug('sensor_log_storage.py', traceback_text())
        return False


def _enqueue_delete(sensor_uid):
    return _enqueue_deletes([sensor_uid])


def _enqueue_deletes(sensor_uids):
    sensor_uids = list(sensor_uids)
    if not sensor_uids or not all(valid_sensor_uid(sensor_uid) for sensor_uid in sensor_uids):
        return False
    try:
        with _outbox_lock:
            connection = _outbox_connection()
            try:
                for sensor_uid in sensor_uids:
                    connection.execute('DELETE FROM operations WHERE sensor_uid = ?', (sensor_uid,))
                    connection.execute(
                        'INSERT INTO operations '
                        '(operation, sensor_uid, record_uid, kind, recorded_at, payload, created_at) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?)',
                        ('delete', sensor_uid, uuid.uuid4().hex, '', 0, '', time.time())
                    )
                connection.commit()
            finally:
                connection.close()
        _wake_worker()
        return True
    except Exception:
        log.error('sensor_log_storage.py', _('Critical: sensor database delete could not be queued.'))
        log.debug('sensor_log_storage.py', traceback_text())
        return False


def pending_count(sensor=None):
    if not _outbox_exists():
        return 0
    try:
        with _outbox_lock:
            connection = _outbox_connection()
            try:
                if sensor is None:
                    row = connection.execute('SELECT COUNT(*) FROM operations').fetchone()
                else:
                    sensor_uid = _sensor_uid(sensor)
                    if sensor_uid is None:
                        return 0
                    row = connection.execute(
                        'SELECT COUNT(*) FROM operations WHERE sensor_uid = ?', (sensor_uid,)
                    ).fetchone()
                return int(row[0])
            finally:
                connection.close()
    except Exception:
        log.debug('sensor_log_storage.py', traceback_text())
        return 0


def _pending_insert_records(sensor_uid, kind):
    records = []
    if not _outbox_exists():
        return records
    try:
        with _outbox_lock:
            connection = _outbox_connection()
            try:
                rows = connection.execute(
                    "SELECT record_uid, recorded_at, payload FROM operations "
                    "WHERE operation='insert' AND sensor_uid=? AND kind=? ORDER BY id DESC",
                    (sensor_uid, kind)
                ).fetchall()
            finally:
                connection.close()
        for record_uid, recorded_at, payload in rows:
            record = _decoded_payload(payload)
            if record is not None:
                record['_record_uid'] = record_uid
                record['_timestamp'] = int(recorded_at)
                records.append(record)
    except Exception:
        log.debug('sensor_log_storage.py', traceback_text())
    return records


def _pending_delete(sensor_uid):
    if not valid_sensor_uid(sensor_uid) or not _outbox_exists():
        return False
    try:
        with _outbox_lock:
            connection = _outbox_connection()
            try:
                row = connection.execute(
                    "SELECT 1 FROM operations WHERE operation='delete' AND sensor_uid=? LIMIT 1",
                    (sensor_uid,)
                ).fetchone()
                return row is not None
            finally:
                connection.close()
    except Exception:
        log.debug('sensor_logs.py', traceback_text())
        return False


def _invalidate_schema(connector=None):
    global _schema_connector
    with _schema_lock:
        if connector is None or _schema_connector is connector:
            _schema_connector = None


def _ensure_schema(connector):
    global _schema_connector
    with _schema_lock:
        if _schema_connector is connector:
            return True
        sql = (
            'CREATE TABLE IF NOT EXISTS {} ('
            'id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, '
            'record_uid CHAR(32) NOT NULL UNIQUE, sensor_uid CHAR(32) NOT NULL, '
            'kind VARCHAR(8) NOT NULL, recorded_at BIGINT NOT NULL, '
            'payload MEDIUMTEXT NOT NULL, '
            'INDEX sensor_kind_time (sensor_uid, kind, recorded_at))'
        ).format(TABLE_NAME)
        result = _execute_database_change(connector, sql, commit=False)
        if result is None:
            _schema_connector = None
            return False
        _schema_connector = connector
        return True


def _connector_supports_direct_changes(connector):
    try:
        import inspect
        parameters = inspect.signature(connector.execute_db).parameters
        return '_from_queue' in parameters or any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters.values()
        )
    except Exception:
        return False


def _connector_supports_safe_changes(connector):
    if _connector_supports_direct_changes(connector):
        return True
    try:
        return 'use_buffer' not in getattr(connector, 'plugin_options', {})
    except Exception:
        return False


def _execute_database_change(connector, sql, commit=False):
    """Execute a change without handing it to the connector's second queue."""
    if _connector_supports_direct_changes(connector):
        return connector.execute_db(
            sql, commit=commit, test=False, fetch=False, _from_queue=True)
    try:
        if 'use_buffer' not in getattr(connector, 'plugin_options', {}):
            return connector.execute_db(sql, commit=commit, test=False, fetch=False)
    except Exception:
        pass
    log.error(
        'sensor_logs.py',
        _('Database Connector cannot bypass its queue; the sensor operation remains queued in OSPy.')
    )
    return None


def _trim_database(connector, sensor_uid, kind):
    try:
        limit = int(options.run_sensor_entries)
    except (TypeError, ValueError):
        limit = 0
    if limit <= 0:
        return True
    sql = (
        "DELETE FROM {table} WHERE sensor_uid='{sensor}' AND kind='{kind}' "
        "AND id NOT IN (SELECT id FROM (SELECT id FROM {table} "
        "WHERE sensor_uid='{sensor}' AND kind='{kind}' "
        "ORDER BY recorded_at DESC, id DESC LIMIT {limit}) retained_rows)"
    ).format(table=TABLE_NAME, sensor=sensor_uid, kind=kind, limit=limit)
    result = _execute_database_change(connector, sql, commit=True)
    if result is None:
        _invalidate_schema(connector)
        log.error('sensor_log_storage.py', _('Unable to apply sensor database log retention.'))
        return False
    return True


def _write_database_operation(connector, sensor_uid, record_uid, kind, recorded_at, payload):
    if (not valid_sensor_uid(sensor_uid) or not valid_sensor_uid(record_uid) or
            kind not in KINDS or not re.match(r'^[A-Za-z0-9+/=]+$', payload or '')):
        return False
    if not _ensure_schema(connector):
        return False
    sql = (
        "INSERT INTO {} (record_uid, sensor_uid, kind, recorded_at, payload) "
        "VALUES ('{}','{}','{}',{},'{}') "
        "ON DUPLICATE KEY UPDATE record_uid=record_uid"
    ).format(TABLE_NAME, record_uid, sensor_uid, kind, max(0, int(recorded_at)), payload)
    result = _execute_database_change(connector, sql, commit=True)
    if result is None:
        _invalidate_schema(connector)
        return False
    return _trim_database(connector, sensor_uid, kind)


def _delete_database_operation(connector, sensor_uid):
    if not valid_sensor_uid(sensor_uid) or not _ensure_schema(connector):
        return False
    sql = "DELETE FROM {} WHERE sensor_uid='{}'".format(TABLE_NAME, sensor_uid)
    result = _execute_database_change(connector, sql, commit=True)
    if result is None:
        _invalidate_schema(connector)
        return False
    return True


def process_pending_batch(max_operations=WORKER_BATCH_SIZE, stop_event=None):
    if not _outbox_exists():
        return 0
    try:
        maximum = max(1, min(int(max_operations), WORKER_BATCH_SIZE))
    except (TypeError, ValueError):
        maximum = WORKER_BATCH_SIZE
    with _outbox_lock:
        connection = _outbox_connection()
        try:
            rows = connection.execute(
                'SELECT id, operation, sensor_uid, record_uid, kind, recorded_at, payload '
                'FROM operations ORDER BY id LIMIT ?', (maximum,)
            ).fetchall()
        finally:
            connection.close()
    if not rows:
        return 0
    connector = _connector()
    if connector is None:
        return 0
    try:
        probe = connector.execute_db('SELECT 1', commit=False, test=False, fetch=True)
        if not probe or not probe[0] or int(probe[0][0]) != 1:
            return 0
    except Exception:
        return 0
    processed = 0
    for row in rows:
        if stop_event is not None and stop_event.is_set():
            break
        operation_id, operation, sensor_uid, record_uid, kind, recorded_at, payload = row
        if operation == 'insert':
            success = _write_database_operation(
                connector, sensor_uid, record_uid, kind, recorded_at, payload)
        elif operation == 'delete':
            success = _delete_database_operation(connector, sensor_uid)
        else:
            log.error('sensor_log_storage.py', _('Critical: invalid sensor database outbox operation was discarded.'))
            success = True
        if not success:
            break
        with _outbox_lock:
            connection = _outbox_connection()
            try:
                connection.execute('DELETE FROM operations WHERE id = ?', (operation_id,))
                connection.commit()
            finally:
                connection.close()
        processed += 1
    return processed


class SensorLogDatabaseWorker(threading.Thread):
    def __init__(self):
        super(SensorLogDatabaseWorker, self).__init__(name='SensorLogDatabaseWorker')
        self.daemon = True
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            try:
                processed = process_pending_batch(WORKER_BATCH_SIZE, self._stop_event)
            except Exception:
                processed = 0
                log.debug('sensor_log_storage.py', traceback_text())
            if processed:
                self._stop_event.wait(0.05)
            else:
                self._wake_event.wait(WORKER_IDLE_SECONDS)
                self._wake_event.clear()

    def wake(self):
        self._wake_event.set()

    def request_stop(self):
        self._stop_event.set()
        self._wake_event.set()

    def wait_stopped(self, timeout=5.0):
        if self.is_alive() and self is not threading.current_thread():
            self.join(max(0.0, float(timeout)))
        return not self.is_alive()


database_worker = SensorLogDatabaseWorker()


def start_worker():
    global database_worker
    if database_worker.is_alive():
        return database_worker
    if database_worker.ident is not None or database_worker._stop_event.is_set():
        database_worker = SensorLogDatabaseWorker()
    database_worker.start()
    return database_worker


def _wake_worker():
    if database_worker.is_alive():
        database_worker.wake()


def request_worker_stop():
    database_worker.request_stop()


def wait_worker_stopped(timeout=5.0):
    return database_worker.wait_stopped(timeout)


def write_record(sensor, kind, record, recorded_at=None):
    sensor_uid = _sensor_uid(sensor)
    with _delete_lock:
        if sensor_uid in _deleting_uids:
            log.debug('sensor_logs.py', _('Sensor record was ignored because the sensor is being deleted.'))
            return {
                'local': False,
                'database': False,
                'queued': False,
                'fallback': False,
                'deleting': True,
                'timestamp': int(time.time()) if recorded_at is None else int(recorded_at),
            }
        return _write_record(sensor, kind, record, recorded_at)


def _write_record(sensor, kind, record, recorded_at=None):
    storage = normalize_storage(getattr(sensor, 'log_storage', STORAGE_JSON))
    timestamp = int(time.time()) if recorded_at is None else int(recorded_at)
    local_requested = storage in (STORAGE_JSON, STORAGE_BOTH)
    database_requested = storage in (STORAGE_DATABASE, STORAGE_BOTH)
    local_written = write_local_record(sensor, kind, record) if local_requested else False
    if local_requested and not local_written:
        log.error('sensor_logs.py', _('Sensor record could not be saved to local JSON.'))
    queued = False
    if database_requested:
        sensor_uid = _sensor_uid(sensor)
        if sensor_uid is not None:
            _queue_fallback_records(sensor, kind)
            queued = _enqueue_insert(sensor_uid, kind, record, timestamp)
    fallback = False
    if database_requested and not queued and not local_written:
        local_written = write_local_record(sensor, kind, record)
        fallback = local_written
    elif database_requested and not queued and local_written:
        fallback = True
    if fallback and not _write_fallback_record(sensor, kind, record, timestamp):
        log.error('sensor_logs.py', _('Critical: database fallback record could not be tracked.'))
    if database_requested and not queued:
        if local_written:
            log.error('sensor_log_storage.py', _('Database sensor log queue failed; the record was saved to local JSON.'))
        else:
            log.error('sensor_log_storage.py', _('Critical: sensor record could not be saved to database queue or local JSON.'))
    return {
        'local': local_written,
        'database': False,
        'queued': queued,
        'fallback': fallback,
        'timestamp': timestamp,
    }


def _read_remote_database_records(connector, sensor_uid, kind):
    if not _ensure_schema(connector):
        return None
    try:
        limit = int(options.run_sensor_entries)
    except (TypeError, ValueError):
        limit = 0
    limit_clause = ' LIMIT {}'.format(limit) if limit > 0 else ''
    sql = (
        "SELECT record_uid, recorded_at, payload FROM {} WHERE sensor_uid='{}' "
        "AND kind='{}' ORDER BY recorded_at DESC, id DESC{}"
    ).format(TABLE_NAME, sensor_uid, kind, limit_clause)
    rows = connector.execute_db(sql, commit=False, test=False, fetch=True)
    if rows is None:
        _invalidate_schema(connector)
        return None
    records = []
    for record_uid, recorded_at, payload in rows:
        try:
            record = _decoded_payload(payload)
            if record is not None:
                record['_record_uid'] = str(record_uid)
                record['_timestamp'] = int(recorded_at)
                records.append(record)
        except Exception:
            log.debug('sensor_log_storage.py', _('Invalid sensor log record in database.'))
    return records


def _merge_records(primary, secondary):
    result = []
    seen_uids = set()
    seen_payloads = set()
    for record in list(primary or []) + list(secondary or []):
        item = dict(record)
        record_uid = item.pop('_record_uid', None)
        comparable = dict(item)
        fingerprint = json.dumps(comparable, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        if record_uid and record_uid in seen_uids:
            continue
        if not record_uid and fingerprint in seen_payloads:
            continue
        if record_uid:
            seen_uids.add(record_uid)
        seen_payloads.add(fingerprint)
        result.append(item)
    result.sort(key=lambda item: int(item.get('_timestamp', 0)), reverse=True)
    return result


def _apply_retention(records):
    try:
        limit = int(options.run_sensor_entries)
    except (TypeError, ValueError):
        limit = 0
    return records[:limit] if limit > 0 else records


def _local_records_with_timestamps(sensor, kind):
    records = []
    for record in read_local_records(sensor, kind):
        item = dict(record)
        try:
            parsed = time.strptime(
                '{} {}'.format(item['date'], item['time']), '%Y-%m-%d %H:%M:%S')
            item['_timestamp'] = int(calendar.timegm(parsed))
        except (KeyError, TypeError, ValueError, OverflowError):
            pass
        records.append(item)
    return records


def read_database_records(sensor, kind):
    sensor_uid = _sensor_uid(sensor)
    if sensor_uid is None or kind not in KINDS:
        return None
    pending = _pending_insert_records(sensor_uid, kind)
    if _pending_delete(sensor_uid):
        return _apply_retention(pending)
    connector = _connector()
    if connector is None:
        return None
    try:
        remote = _read_remote_database_records(connector, sensor_uid, kind)
        return None if remote is None else _apply_retention(_merge_records(remote, pending))
    except Exception:
        _invalidate_schema(connector)
        log.debug('sensor_log_storage.py', traceback_text())
        return None


def read_records(sensor, kind, source=None):
    selected = normalize_source(
        getattr(sensor, 'log_source', SOURCE_JSON) if source is None else source)
    if selected == SOURCE_DATABASE:
        _queue_fallback_records(sensor, kind)
        fallback = _fallback_records(sensor, kind)
        records = read_database_records(sensor, kind)
        if records is not None:
            return _apply_retention(_merge_records(records, fallback))
        sensor_uid = _sensor_uid(sensor)
        pending = _pending_insert_records(sensor_uid, kind) if sensor_uid else []
        local = _local_records_with_timestamps(sensor, kind)
        log.error('sensor_log_storage.py', _('Database sensor log read failed; pending and local history are displayed.'))
        return _apply_retention(_merge_records(pending, local))
    return read_local_records(sensor, kind)


def graph_from_records(sensor, records):
    if sensor.multi_type == 9:
        series = [
            {'sname': '{}'.format(sensor.soil_probe_label[i]), 'balances': {}}
            for i in range(0, 16)
        ]
    else:
        series = [{'sname': '{}'.format(sensor.name), 'balances': {}}]
    series.append({
        'sname': '{}'.format(_('Battery') if sensor.manufacturer == 0 else _('Voltage')),
        'balances': {},
    })
    series.append({'sname': '{}'.format(_('Signal')), 'balances': {}})
    for record in reversed(records or []):
        try:
            timestamp = str(int(record['_timestamp']))
        except (KeyError, TypeError, ValueError):
            continue
        if sensor.multi_type == 9:
            for index in range(0, 16):
                key = 'list_{}'.format(index)
                if key in record:
                    series[index]['balances'][timestamp] = {'total': '{}'.format(record[key])}
            value_index = 16
        else:
            if 'value' in record:
                series[0]['balances'][timestamp] = {'total': '{}'.format(record['value'])}
            value_index = 1
        if 'battery' in record:
            series[value_index]['balances'][timestamp] = {'total': '{}'.format(record['battery'])}
        if 'rssi' in record:
            series[value_index + 1]['balances'][timestamp] = {'total': '{}'.format(record['rssi'])}
    return series


def _clear_local_records(sensor):
    try:
        with _local_lock:
            for kind in KINDS:
                path = os.path.abspath(_log_path(sensor, kind))
                if os.path.isfile(path):
                    os.remove(path)
                fallback_path = os.path.abspath(_fallback_path(sensor, kind))
                if os.path.isfile(fallback_path):
                    os.remove(fallback_path)
            graph_dir = os.path.abspath(os.path.join(_log_dir(sensor), 'graph'))
            if os.path.isdir(graph_dir):
                import shutil
                shutil.rmtree(graph_dir)
        return True
    except Exception:
        log.debug('sensor_log_storage.py', traceback_text())
        return False


def clear_local_records(sensor):
    return _clear_local_records(sensor)


def clear_records(sensor):
    with _delete_lock:
        storage = normalize_storage(getattr(sensor, 'log_storage', STORAGE_JSON))
        source = normalize_source(getattr(sensor, 'log_source', SOURCE_JSON))
        database_requested = storage in (STORAGE_DATABASE, STORAGE_BOTH) or source == SOURCE_DATABASE
        local_ok = _clear_local_records(sensor)
        queued = _enqueue_delete(_sensor_uid(sensor)) if database_requested else True
        return local_ok and queued


def delete_records(sensor):
    if not queue_delete_records([sensor]):
        return False
    if not _clear_local_records(sensor):
        log.error('sensor_logs.py', _('Sensor database cleanup was queued, but local history could not be removed.'))
    return True


def queue_delete_records(sensor_list):
    """Durably queue deletion for every sensor in one SQLite transaction."""
    sensor_uids = [_sensor_uid(sensor) for sensor in sensor_list]
    if not sensor_uids or not all(valid_sensor_uid(sensor_uid) for sensor_uid in sensor_uids):
        return False
    with _delete_lock:
        _deleting_uids.update(sensor_uids)
        if _enqueue_deletes(sensor_uids):
            return True
        _deleting_uids.difference_update(sensor_uids)
        return False


def cancel_delete_records(sensor_list):
    sensor_uids = [_sensor_uid(sensor) for sensor in sensor_list]
    with _delete_lock:
        _deleting_uids.difference_update(sensor_uids)


def traceback_text():
    import traceback
    return traceback.format_exc()
