import base64
import json
import os
import shutil
import sqlite3
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
import web

from ospy import i18n  # noqa: F401 - installs gettext
from ospy import sensor_logs
from ospy import sensors as sensors_module
from ospy import server
from ospy import webpages


class FakeConnector(object):
    def __init__(self, rows=None, fail_insert=False, fail_delete=False,
                 probe=True):
        self.is_installed_ok = True
        self.plugin_options = {'use': True}
        self.rows = [] if rows is None else rows
        self.fail_insert = fail_insert
        self.fail_delete = fail_delete
        self.probe = probe
        self.on_insert = None
        self.calls = []

    def execute_db(self, sql, commit=False, test=False, fetch=False, _from_queue=False):
        self.calls.append({
            'sql': sql,
            'commit': commit,
            'test': test,
            'fetch': fetch,
            '_from_queue': _from_queue,
        })
        if sql == 'SELECT 1':
            return [(1,)] if self.probe else []
        if sql.startswith('SELECT record_uid, recorded_at, payload'):
            return self.rows
        if sql.startswith('INSERT INTO'):
            if self.on_insert is not None:
                callback, self.on_insert = self.on_insert, None
                callback()
            if self.fail_insert:
                return None
        if sql.startswith('DELETE FROM') and self.fail_delete:
            return None
        return -1

    def db_queue_status(self):
        return 0, 0, ''


class SensorLogStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ospy-sensor-logs-')
        self.addCleanup(self.temporary.cleanup)
        self.options_patch = mock.patch.object(
            sensor_logs, 'options', SimpleNamespace(run_sensor_entries=0)
        )
        self.options_patch.start()
        self.addCleanup(self.options_patch.stop)
        self.path_patch = mock.patch.object(
            sensor_logs,
            '_log_dir',
            side_effect=lambda sensor: os.path.join(
                self.temporary.name, str(sensor.index), 'logs'
            ),
        )
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)
        self.outbox_patch = mock.patch.object(
            sensor_logs,
            'OUTBOX_PATH',
            os.path.join(self.temporary.name, 'sensor-log-outbox.sqlite3'),
        )
        self.outbox_patch.start()
        self.addCleanup(self.outbox_patch.stop)
        sensor_logs._schema_connector = None
        sensor_logs._deleting_uids.clear()
        sensor_logs._status_cache.update({
            'checked': 0.0,
            'connector': None,
            'available': False,
            'summary': '',
        })
        self.sensor = SimpleNamespace(
            index=3,
            log_uid='a' * 32,
            log_storage=sensor_logs.STORAGE_JSON,
            log_source=sensor_logs.SOURCE_JSON,
            name='Test sensor',
            multi_type=0,
            manufacturer=0,
        )

    def local_records(self, kind='slog'):
        return sensor_logs.read_local_records(self.sensor, kind)

    def outbox_rows(self):
        if not os.path.isfile(sensor_logs.outbox_path()):
            return []
        connection = sqlite3.connect(sensor_logs.outbox_path())
        try:
            return connection.execute(
                'SELECT operation, sensor_uid, record_uid, kind, recorded_at, payload '
                'FROM operations ORDER BY id'
            ).fetchall()
        finally:
            connection.close()

    def test_legacy_defaults_use_json_without_creating_outbox(self):
        self.assertEqual(sensor_logs.normalize_storage(None), sensor_logs.STORAGE_JSON)
        self.assertEqual(sensor_logs.normalize_storage('bad'), sensor_logs.STORAGE_JSON)
        self.assertEqual(sensor_logs.normalize_source(None), sensor_logs.SOURCE_JSON)
        self.assertEqual(sensor_logs.normalize_source(99), sensor_logs.SOURCE_JSON)
        self.assertEqual(sensor_logs.pending_count(), 0)
        self.assertFalse(os.path.exists(sensor_logs.outbox_path()))

    def test_local_json_keeps_newest_first_and_applies_retention(self):
        sensor_logs.options.run_sensor_entries = 2
        for value in ('1', '2', '3'):
            result = sensor_logs.write_record(
                self.sensor, 'slog', {'value': value}, recorded_at=int(value)
            )
            self.assertTrue(result['local'])
            self.assertFalse(result['queued'])
        self.assertEqual(self.local_records(), [{'value': '3'}, {'value': '2'}])
        self.assertFalse(os.path.exists(sensor_logs.outbox_path()))

    def test_database_availability_uses_live_probe(self):
        connector = FakeConnector()
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            available, summary = sensor_logs.database_status(refresh=True)
        self.assertTrue(available)
        self.assertTrue(summary)
        self.assertEqual(connector.calls[0]['sql'], 'SELECT 1')
        self.assertTrue(connector.calls[0]['fetch'])

    def test_database_availability_is_false_without_connector(self):
        with mock.patch.object(sensor_logs, '_connector', return_value=None):
            available, summary = sensor_logs.database_status(refresh=True)
        self.assertFalse(available)
        self.assertTrue(summary)

    def test_database_availability_rejects_connector_without_direct_changes(self):
        class LegacyConnector(object):
            plugin_options = {'use_buffer': False}

            def execute_db(self, sql, commit=False, test=False, fetch=False):
                return [(1,)]

        with mock.patch.object(sensor_logs, '_connector', return_value=LegacyConnector()):
            available, summary = sensor_logs.database_status(refresh=True)
        self.assertFalse(available)
        self.assertTrue(summary)

    def test_database_availability_accepts_connector_without_buffer_feature(self):
        class LegacyConnector(object):
            plugin_options = {'use': True}

            def execute_db(self, sql, commit=False, test=False, fetch=False):
                return [(1,)] if fetch else -1

        with mock.patch.object(sensor_logs, '_connector', return_value=LegacyConnector()):
            available, unused_summary = sensor_logs.database_status(refresh=True)
        self.assertTrue(available)

    def test_database_write_only_enqueues_and_never_calls_connector(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        connector = FakeConnector()
        record = {'event': "Valve O'Brien", 'date': '2030-01-01'}
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            result = sensor_logs.write_record(
                self.sensor, 'elog', record, recorded_at=1893456000
            )
        self.assertFalse(result['database'])
        self.assertTrue(result['queued'])
        self.assertFalse(result['local'])
        self.assertEqual(connector.calls, [])
        row = self.outbox_rows()[0]
        self.assertEqual(row[0], 'insert')
        self.assertEqual(row[1], self.sensor.log_uid)
        self.assertEqual(row[3], 'elog')
        self.assertEqual(row[4], 1893456000)
        self.assertNotIn("O'Brien", row[5])
        self.assertEqual(sensor_logs._decoded_payload(row[5]), record)

    def test_both_mode_writes_json_and_enqueues_without_connector(self):
        self.sensor.log_storage = sensor_logs.STORAGE_BOTH
        connector = FakeConnector()
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            result = sensor_logs.write_record(
                self.sensor, 'slog', {'value': '8.0'}, recorded_at=101
            )
        self.assertTrue(result['local'])
        self.assertTrue(result['queued'])
        self.assertFalse(result['database'])
        self.assertFalse(result['fallback'])
        self.assertEqual(connector.calls, [])
        self.assertEqual(self.local_records(), [{'value': '8.0'}])

    def test_database_only_falls_back_to_json_when_enqueue_fails(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        self.sensor.log_source = sensor_logs.SOURCE_DATABASE
        with mock.patch.object(sensor_logs, '_enqueue_insert', return_value=False):
            result = sensor_logs.write_record(
                self.sensor, 'slog', {'value': '21.5'}, recorded_at=100
            )
        self.assertFalse(result['queued'])
        self.assertTrue(result['local'])
        self.assertTrue(result['fallback'])
        self.assertEqual(self.local_records(), [{'value': '21.5'}])
        self.assertEqual(self.sensor.log_storage, sensor_logs.STORAGE_DATABASE)
        self.assertEqual(self.sensor.log_source, sensor_logs.SOURCE_DATABASE)

    def test_capacity_failure_uses_json_fallback_and_logs_critical_error(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        with mock.patch.object(sensor_logs, 'OUTBOX_MAX_OPERATIONS', 0), \
                mock.patch.object(sensor_logs.log, 'error') as error:
            result = sensor_logs.write_record(
                self.sensor, 'slog', {'value': 'safe'}, recorded_at=100
            )
        self.assertFalse(result['queued'])
        self.assertTrue(result['fallback'])
        self.assertEqual(self.local_records(), [{'value': 'safe'}])
        self.assertGreaterEqual(error.call_count, 1)

    def test_global_outbox_survives_new_sensor_instance(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        sensor_logs.write_record(self.sensor, 'slog', {'value': '1'}, recorded_at=100)
        restarted = SimpleNamespace(index=99, log_uid=self.sensor.log_uid)
        self.assertEqual(sensor_logs.pending_count(restarted), 1)

    def test_worker_processes_bounded_batch_after_live_probe(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        for value in ('one', 'two', 'three'):
            sensor_logs.write_record(
                self.sensor, 'slog', {'value': value}, recorded_at=100
            )
        connector = FakeConnector()
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            processed = sensor_logs.process_pending_batch(max_operations=2)
        self.assertEqual(processed, 2)
        self.assertEqual(sensor_logs.pending_count(self.sensor), 1)
        self.assertEqual(connector.calls[0]['sql'], 'SELECT 1')
        self.assertEqual(len([
            call for call in connector.calls if call['sql'].startswith('INSERT INTO')
        ]), 2)

    def test_worker_bypasses_database_connector_buffer(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        sensor_logs.write_record(self.sensor, 'slog', {'value': '1'}, recorded_at=1)
        connector = FakeConnector()
        connector.plugin_options['use_buffer'] = True
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            self.assertEqual(sensor_logs.process_pending_batch(), 1)
        change_calls = [
            call for call in connector.calls
            if call['sql'].startswith(('CREATE TABLE', 'INSERT INTO', 'DELETE FROM'))
        ]
        self.assertTrue(change_calls)
        self.assertTrue(all(call['_from_queue'] for call in change_calls))
        self.assertEqual(sensor_logs.pending_count(), 0)

    def test_worker_does_nothing_when_live_probe_fails(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        sensor_logs.write_record(self.sensor, 'slog', {'value': '1'}, recorded_at=100)
        connector = FakeConnector(probe=False)
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            processed = sensor_logs.process_pending_batch()
        self.assertEqual(processed, 0)
        self.assertEqual(sensor_logs.pending_count(self.sensor), 1)

    def test_enqueue_during_database_call_is_not_lost(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        sensor_logs.write_record(
            self.sensor, 'slog', {'value': 'first'}, recorded_at=100
        )
        connector = FakeConnector()
        connector.on_insert = lambda: sensor_logs.write_record(
            self.sensor, 'slog', {'value': 'second'}, recorded_at=101
        )
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            self.assertEqual(sensor_logs.process_pending_batch(), 1)
            self.assertEqual(sensor_logs.pending_count(self.sensor), 1)
            self.assertEqual(sensor_logs.process_pending_batch(), 1)
        self.assertEqual(sensor_logs.pending_count(self.sensor), 0)

    def test_worker_reuses_record_uid_for_database_deduplication(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        sensor_logs.write_record(
            self.sensor, 'elog', {'event': 'offline'}, recorded_at=100
        )
        record_uid = self.outbox_rows()[0][2]
        connector = FakeConnector()
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            self.assertEqual(sensor_logs.process_pending_batch(), 1)
        insert = next(
            call['sql'] for call in connector.calls
            if call['sql'].startswith('INSERT INTO')
        )
        self.assertIn(record_uid, insert)
        self.assertIn('ON DUPLICATE KEY UPDATE record_uid=record_uid', insert)

    def test_worker_failure_invalidates_schema_and_keeps_operation(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        sensor_logs.write_record(self.sensor, 'slog', {'value': '1'}, recorded_at=100)
        connector = FakeConnector(fail_insert=True)
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            self.assertEqual(sensor_logs.process_pending_batch(), 0)
        self.assertIsNone(sensor_logs._schema_connector)
        self.assertEqual(sensor_logs.pending_count(self.sensor), 1)

    def test_worker_applies_database_retention(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        sensor_logs.options.run_sensor_entries = 2
        sensor_logs.write_record(self.sensor, 'slog', {'value': '1'}, recorded_at=100)
        connector = FakeConnector()
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            self.assertEqual(sensor_logs.process_pending_batch(), 1)
        retention = next(
            call for call in connector.calls
            if call['sql'].startswith('DELETE FROM')
        )
        self.assertIn('LIMIT 2', retention['sql'])

    def test_worker_retries_when_database_retention_fails(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        sensor_logs.options.run_sensor_entries = 2
        sensor_logs.write_record(self.sensor, 'slog', {'value': '1'}, recorded_at=100)
        connector = FakeConnector(fail_delete=True)
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            self.assertEqual(sensor_logs.process_pending_batch(), 0)
        self.assertEqual(sensor_logs.pending_count(self.sensor), 1)

    def test_database_read_merges_remote_and_pending_records(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        self.sensor.log_source = sensor_logs.SOURCE_DATABASE
        sensor_logs.write_record(
            self.sensor, 'slog', {'value': 'pending'}, recorded_at=200
        )
        connector = FakeConnector(rows=[(
            'd' * 32,
            100,
            sensor_logs._encoded_payload({'value': 'remote'}),
        )])
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            records = sensor_logs.read_database_records(self.sensor, 'slog')
        self.assertEqual([record['value'] for record in records], ['pending', 'remote'])
        self.assertEqual(sensor_logs.pending_count(self.sensor), 1)
        self.assertFalse(any(
            call['sql'].startswith('INSERT INTO') for call in connector.calls
        ))

    def test_successful_database_read_also_merges_local_fallback(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        self.sensor.log_source = sensor_logs.SOURCE_DATABASE
        with mock.patch.object(sensor_logs, '_enqueue_insert', return_value=False):
            result = sensor_logs.write_record(
                self.sensor, 'elog', {'event': 'fallback'}, recorded_at=200
            )
        self.assertTrue(result['fallback'])
        connector = FakeConnector(rows=[(
            'e' * 32,
            100,
            sensor_logs._encoded_payload({'event': 'remote'}),
        )])
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            records = sensor_logs.read_records(self.sensor, 'elog')
        self.assertEqual([record['event'] for record in records], ['fallback', 'remote'])

    def test_successful_database_read_does_not_mix_ordinary_json_history(self):
        sensor_logs.write_local_record(
            self.sensor,
            'elog',
            {'date': '2030-01-01', 'time': '12:00:00', 'event': 'local'},
        )
        self.sensor.log_source = sensor_logs.SOURCE_DATABASE
        connector = FakeConnector(rows=[(
            'e' * 32,
            100,
            sensor_logs._encoded_payload({'event': 'remote'}),
        )])
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            records = sensor_logs.read_records(self.sensor, 'elog')
        self.assertEqual([record['event'] for record in records], ['remote'])

    def test_pending_delete_hides_remote_history_immediately(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        self.sensor.log_source = sensor_logs.SOURCE_DATABASE
        self.assertTrue(sensor_logs.clear_records(self.sensor))
        connector = FakeConnector(rows=[(
            'e' * 32,
            100,
            sensor_logs._encoded_payload({'event': 'remote'}),
        )])
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            self.assertEqual(sensor_logs.read_records(self.sensor, 'elog'), [])
        self.assertFalse(any(
            call['sql'].startswith('SELECT record_uid') for call in connector.calls
        ))

    def test_equal_values_at_different_times_are_not_deduplicated(self):
        records = sensor_logs._merge_records(
            [{'value': '1', '_timestamp': 200}],
            [{'value': '1', '_timestamp': 100}],
        )
        self.assertEqual([record['_timestamp'] for record in records], [200, 100])

    def test_database_read_decodes_utf8_payload(self):
        payload = base64.b64encode(json.dumps(
            {'event': 'Příliš vysoká teplota'}, ensure_ascii=False
        ).encode('utf-8')).decode('ascii')
        connector = FakeConnector(rows=[('e' * 32, 1234, payload)])
        self.sensor.log_source = sensor_logs.SOURCE_DATABASE
        with mock.patch.object(sensor_logs, '_connector', return_value=connector):
            records = sensor_logs.read_records(self.sensor, 'elog')
        self.assertEqual(records, [{
            'event': 'Příliš vysoká teplota', '_timestamp': 1234
        }])

    def test_database_read_failure_merges_pending_and_local(self):
        sensor_logs.write_local_record(
            self.sensor,
            'elog',
            {'date': '2030-01-01', 'time': '12:00:00', 'event': 'local'},
        )
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        self.sensor.log_source = sensor_logs.SOURCE_DATABASE
        sensor_logs.write_record(
            self.sensor, 'elog', {'event': 'pending'}, recorded_at=200
        )
        with mock.patch.object(sensor_logs, '_connector', return_value=None):
            records = sensor_logs.read_records(self.sensor, 'elog')
        self.assertEqual([record['event'] for record in records], ['local', 'pending'])
        self.assertEqual(self.sensor.log_source, sensor_logs.SOURCE_DATABASE)

    def test_graph_from_database_samples(self):
        graph = sensor_logs.graph_from_records(self.sensor, [
            {'_timestamp': 200, 'value': '21.5', 'battery': '3.7', 'rssi': '80'},
            {'_timestamp': 100, 'value': '20.0'},
        ])
        self.assertEqual(graph[0]['balances']['100']['total'], '20.0')
        self.assertEqual(graph[0]['balances']['200']['total'], '21.5')
        self.assertEqual(graph[1]['balances']['200']['total'], '3.7')
        self.assertEqual(graph[2]['balances']['200']['total'], '80')

    def test_sixteen_probe_graph_has_eighteen_series(self):
        soil = SimpleNamespace(
            multi_type=9,
            soil_probe_label=['Probe {}'.format(index) for index in range(16)],
            manufacturer=0,
        )
        record = {'_timestamp': 300, 'battery': '3.6', 'rssi': '75'}
        record.update({'list_{}'.format(index): str(index) for index in range(16)})
        graph = sensor_logs.graph_from_records(soil, [record])
        self.assertEqual(len(graph), 18)
        for index in range(16):
            self.assertEqual(graph[index]['balances']['300']['total'], str(index))
        self.assertEqual(graph[16]['balances']['300']['total'], '3.6')
        self.assertEqual(graph[17]['balances']['300']['total'], '75')

    def test_clear_json_mode_removes_local_only(self):
        sensor_logs.write_local_record(self.sensor, 'slog', {'value': '1'})
        self.assertTrue(sensor_logs.clear_records(self.sensor))
        self.assertEqual(self.local_records(), [])
        self.assertFalse(os.path.exists(sensor_logs.outbox_path()))

    def test_clear_database_mode_queues_delete_and_clears_local_fallback(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        self.sensor.log_source = sensor_logs.SOURCE_DATABASE
        sensor_logs.write_local_record(self.sensor, 'slog', {'value': 'legacy'})
        sensor_logs.write_record(self.sensor, 'slog', {'value': 'queued'}, recorded_at=100)
        self.assertTrue(sensor_logs.clear_records(self.sensor))
        self.assertEqual(self.local_records(), [])
        rows = self.outbox_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], 'delete')

    def test_clear_both_mode_removes_local_and_queues_delete(self):
        self.sensor.log_storage = sensor_logs.STORAGE_BOTH
        sensor_logs.write_record(self.sensor, 'slog', {'value': 'queued'}, recorded_at=100)
        self.assertTrue(sensor_logs.clear_records(self.sensor))
        self.assertEqual(self.local_records(), [])
        self.assertEqual(self.outbox_rows()[0][0], 'delete')

    def test_delete_always_leaves_global_tombstone(self):
        sensor_logs.write_local_record(self.sensor, 'slog', {'value': 'local'})
        self.assertTrue(sensor_logs.delete_records(self.sensor))
        local_root = os.path.join(self.temporary.name, str(self.sensor.index))
        shutil.rmtree(local_root, ignore_errors=True)
        self.assertEqual(sensor_logs.pending_count(self.sensor), 1)
        self.assertEqual(self.outbox_rows()[0][0], 'delete')

    def test_delete_barrier_rejects_late_sensor_write(self):
        self.sensor.log_storage = sensor_logs.STORAGE_DATABASE
        sensor_logs.write_record(self.sensor, 'slog', {'value': 'before'}, recorded_at=100)
        self.assertTrue(sensor_logs.delete_records(self.sensor))
        result = sensor_logs.write_record(
            self.sensor, 'slog', {'value': 'after'}, recorded_at=101
        )
        self.assertTrue(result['deleting'])
        self.assertEqual([row[0] for row in self.outbox_rows()], ['delete'])

    def test_outbox_uses_configured_data_directory(self):
        isolated = os.path.join(self.temporary.name, 'isolated-data')
        with mock.patch.object(sensor_logs, 'OUTBOX_PATH', None), \
                mock.patch.dict(os.environ, {'OSPY_DATA_DIR': isolated}):
            expected = os.path.abspath(os.path.join(
                isolated, 'sensor_log_outbox.sqlite3'
            ))
            self.assertEqual(sensor_logs.outbox_path(), expected)
            self.assertFalse(os.path.exists(expected))

    def test_worker_thread_stops_cooperatively(self):
        worker = sensor_logs.SensorLogDatabaseWorker()
        with mock.patch.object(sensor_logs, 'process_pending_batch', return_value=0), \
                mock.patch.object(sensor_logs, 'WORKER_IDLE_SECONDS', 0.01):
            worker.start()
            worker.request_stop()
            self.assertTrue(worker.wait_stopped(1.0))


class SensorLogIdentityTests(unittest.TestCase):
    def test_legacy_sensor_uid_is_persisted_using_requested_index(self):
        collection = SimpleNamespace(get=lambda: [])
        options_type = type(sensors_module.options)
        with mock.patch.object(options_type, 'load'), \
                mock.patch.object(options_type, 'save') as save:
            sensor = sensors_module._Sensor(collection, 7)
        self.assertTrue(sensor_logs.valid_sensor_uid(sensor.log_uid))
        self.assertEqual(sensor.log_storage, sensor_logs.STORAGE_JSON)
        self.assertEqual(sensor.log_source, sensor_logs.SOURCE_JSON)
        self.assertTrue(any(
            call.args[0] is sensor and call.args[1] == 7
            for call in save.call_args_list
        ))


class SensorTimerLogIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ospy-sensor-timer-')
        self.addCleanup(self.temporary.cleanup)
        self.path_patch = mock.patch.object(
            sensor_logs,
            '_log_dir',
            side_effect=lambda sensor: os.path.join(
                self.temporary.name, str(sensor.index), 'logs'
            ),
        )
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)
        self.options_patch = mock.patch.object(
            sensor_logs, 'options', SimpleNamespace(run_sensor_entries=0)
        )
        self.options_patch.start()
        self.addCleanup(self.options_patch.stop)
        self.sensor = SimpleNamespace(
            index=2,
            name='Temperature',
            multi_type=0,
            manufacturer=0,
            log_uid='b' * 32,
            log_storage=sensor_logs.STORAGE_JSON,
            log_source=sensor_logs.SOURCE_JSON,
        )
        self.timer = sensors_module._Sensors_Timer.__new__(sensors_module._Sensors_Timer)

    def test_update_log_preserves_json_record_shape(self):
        with mock.patch.object(sensors_module.time, 'time', return_value=100), \
                mock.patch.object(self.timer, '_update_graph_log') as graph:
            self.timer.update_log(
                self.sensor, 'lgs', 21.56, action='opened',
                battery=3.74, rssi=80.25,
            )
        self.assertEqual(sensor_logs.read_local_records(self.sensor, 'slog'), [{
            'date': '1970-01-01',
            'time': '00:01:40',
            'value': '21.6',
            'battery': '3.7',
            'rssi': '80.2',
            'action': 'opened',
        }])
        graph.assert_called_once()

    def test_storage_exception_does_not_escape_sensor_timer(self):
        with mock.patch.object(
                sensor_logs, 'write_record', side_effect=RuntimeError('failed')
        ), mock.patch.object(sensors_module.log, 'debug') as debug:
            self.timer.update_log(self.sensor, 'lgs', 21.5)
        debug.assert_called()


class SensorLogWebIntegrationTests(unittest.TestCase):
    def setUp(self):
        web.ctx.clear()
        web.ctx.env = {'REMOTE_ADDR': '192.0.2.10'}
        web.ctx.headers = []
        web.ctx.path = '/sensor/0'
        web.ctx.home = 'http://localhost'
        self.original_session = server.session
        server.session = {'category': 'admin', 'visitor': 'Test administrator'}
        self.addCleanup(setattr, server, 'session', self.original_session)
        self.sensor = SimpleNamespace(
            index=0,
            name='Database sensor',
            sens_type=5,
            multi_type=0,
            manufacturer=0,
            shelly_hw_nbr=-1,
            log_uid='c' * 32,
            log_storage=sensor_logs.STORAGE_DATABASE,
            log_source=sensor_logs.SOURCE_DATABASE,
        )
        self.collection = SimpleNamespace(
            get=lambda index=None: self.sensor if index is not None else [self.sensor]
        )

    def handler(self):
        handler = object.__new__(webpages.sensor_page)
        handler.core_render = SimpleNamespace(
            sensor=lambda sensor, error: (sensor, error),
            notice=lambda path, message: (path, message),
            log_sensor=lambda *args: args,
            graph_sensor=lambda *args: args,
        )
        return handler

    def test_sample_csv_uses_storage_reader(self):
        records = [{
            'date': '2030-01-01', 'time': '12:00:00', 'value': '21.5',
            'battery': '3.7', 'rssi': '80',
        }]
        with mock.patch.object(webpages.web, 'input', return_value={'csvS': ''}), \
                mock.patch.object(webpages, 'sensors', self.collection), \
                mock.patch.object(sensor_logs, 'read_records', return_value=records) as read:
            result = self.handler().GET('0')
        read.assert_called_once_with(self.sensor, 'slog')
        self.assertIn('2030-01-01; 12:00:00; 21.5; 3.7; 80', result)

    def test_event_csv_uses_storage_reader(self):
        records = [{
            'date': '2030-01-01', 'time': '12:00:00', 'event': 'Recovered',
        }]
        with mock.patch.object(webpages.web, 'input', return_value={'csvE': ''}), \
                mock.patch.object(webpages, 'sensors', self.collection), \
                mock.patch.object(sensor_logs, 'read_records', return_value=records) as read:
            result = self.handler().GET('0')
        read.assert_called_once_with(self.sensor, 'elog')
        self.assertIn('2030-01-01; 12:00:00; Recovered', result)

    def test_graph_route_uses_database_source_and_common_conversion(self):
        records = [{'_timestamp': 100, 'value': '20.0'}]
        query = {
            'glog': '', 'dt_from': '1970-01-01T00:00',
            'dt_to': '1970-01-01T00:05',
        }
        with mock.patch.object(webpages.web, 'input', return_value=query), \
                mock.patch.object(webpages, 'sensors', self.collection), \
                mock.patch.object(sensor_logs, 'read_records', return_value=records) as read:
            result = self.handler().GET('0')
        read.assert_called_once_with(
            self.sensor, 'slog', sensor_logs.SOURCE_DATABASE
        )
        graph = json.loads(result)
        self.assertEqual(graph[0]['balances']['100']['total'], '20.0')

    def test_new_database_selection_is_rejected_when_unavailable(self):
        self.sensor.log_storage = sensor_logs.STORAGE_JSON
        self.sensor.log_source = sensor_logs.SOURCE_JSON
        with mock.patch.object(
                webpages.web, 'input', return_value={'log_storage': '1'}
        ), mock.patch.object(webpages, 'sensors', self.collection), \
                mock.patch.object(sensor_logs, 'database_available', return_value=False):
            result = self.handler().POST('0')
        self.assertEqual(result, (self.sensor, 'database'))
        self.assertEqual(self.sensor.log_storage, sensor_logs.STORAGE_JSON)

    def test_invalid_log_selection_preserves_saved_modes(self):
        with mock.patch.object(
                webpages.web,
                'input',
                return_value={'log_storage': 'bad', 'log_source': '99'},
        ), mock.patch.object(webpages, 'sensors', self.collection), \
                mock.patch.object(sensor_logs, 'database_available') as available:
            result = self.handler().POST('0')
        self.assertEqual(result, (self.sensor, 'logsettings'))
        available.assert_not_called()
        self.assertEqual(self.sensor.log_storage, sensor_logs.STORAGE_DATABASE)
        self.assertEqual(self.sensor.log_source, sensor_logs.SOURCE_DATABASE)

    def test_missing_connector_does_not_reset_saved_modes(self):
        with mock.patch.object(webpages.web, 'input', return_value={}), \
                mock.patch.object(webpages, 'sensors', self.collection), \
                mock.patch.object(sensor_logs, 'database_available') as available, \
                mock.patch.object(webpages.logEV, 'save_events_log'):
            with self.assertRaises(web.seeother):
                self.handler().POST('0')
        available.assert_not_called()
        self.assertEqual(self.sensor.log_storage, sensor_logs.STORAGE_DATABASE)
        self.assertEqual(self.sensor.log_source, sensor_logs.SOURCE_DATABASE)

    def test_clear_route_reports_queue_failure(self):
        with mock.patch.object(
                webpages.web, 'input', return_value={'action': 'clear'}
        ), mock.patch.object(webpages, 'sensors', self.collection), \
                mock.patch.object(sensor_logs, 'clear_records', return_value=False) as clear:
            result = self.handler().POST('0')
        clear.assert_called_once_with(self.sensor)
        self.assertEqual(result[0], '/sensors')
        self.assertTrue(result[1])

    def test_delete_all_reports_tombstone_queue_failures(self):
        sensor = SimpleNamespace(
            name='Failed sensor', soil_program=['-1'] * 16
        )

        class Collection(object):
            def __init__(self):
                self.items = [sensor]

            def get(self, index=None):
                return self.items if index is None else self.items[index]

            def count(self):
                return len(self.items)

            def remove_sensors(self, index):
                del self.items[index]

        collection = Collection()
        handler = object.__new__(webpages.sensors_page)
        handler.core_render = SimpleNamespace(
            notice=lambda path, message: (path, message),
            sensors_search=lambda: None,
        )
        with mock.patch.object(webpages.web, 'input', return_value={'action': 'delete_all'}), \
                mock.patch.object(webpages, 'sensors', collection), \
                mock.patch.object(webpages.programs, 'get', return_value=[]), \
                mock.patch.object(webpages.sensors_timer, 'stop_status'), \
                mock.patch.object(sensor_logs, 'queue_delete_records', return_value=False), \
                mock.patch.object(shutil, 'rmtree'):
            result = handler.POST()
        self.assertEqual(result[0], '/sensors')
        self.assertTrue(result[1])
        self.assertEqual(collection.count(), 1)


class SensorLogServerLifecycleTests(unittest.TestCase):
    def test_database_worker_is_a_core_worker(self):
        self.assertIn(sensor_logs.database_worker, server._core_workers())


if __name__ == '__main__':
    unittest.main()
