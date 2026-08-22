import datetime
import json
import unittest
from unittest import mock

import plugins
from ospy import provider_contracts


def capabilities(provider_id='example_provider'):
    return {
        'contract': 'ospy.provider.v1',
        'provider_id': provider_id,
        'resource_types': ['tank'],
        'values': [{
            'id': 'fill_percent',
            'quantity': 'fill_ratio',
            'unit': '%',
            'value_type': 'number',
        }],
        'events': [{'code': 'tank.measurement'}],
        'alerts': [{'code': 'tank.sensor_error'}],
        'actions': [],
    }


def snapshot(provider_id='example_provider'):
    return {
        'contract': 'ospy.provider.v1',
        'provider_id': provider_id,
        'status': 'ok',
        'observed_at': '2026-08-21T12:00:00Z',
        'resources': [{
            'id': 'tank-1',
            'type': 'tank',
            'status': 'ok',
            'values': [{
                'id': 'fill_percent',
                'quantity': 'fill_ratio',
                'value': 72.5,
                'unit': '%',
                'value_type': 'number',
                'quality': 'measured',
                'observed_at': '2026-08-21T12:00:00Z',
            }],
            'alerts': [],
        }],
        'events': [],
        'alerts': [],
    }


class ProviderContractTests(unittest.TestCase):
    def test_manifest_provider_declaration_is_strict_and_normalized(self):
        base = {
            'schema_version': 1, 'id': 'example_provider',
            'name': 'Example', 'version': '1.0.0',
            'provider': {'contract': 'ospy.provider.v1', 'ignored': True},
        }
        normalized = plugins._normalize_plugin_manifest(base, 'example_provider')
        self.assertEqual(normalized['provider'], {'contract': 'ospy.provider.v1'})
        base['provider'] = []
        self.assertEqual(plugins._normalize_plugin_manifest(base, 'example_provider'), {})
        base['provider'] = {'contract': 'ospy.provider.v2'}
        self.assertEqual(plugins._normalize_plugin_manifest(base, 'example_provider'), {})

    def test_capabilities_and_snapshot_are_json_safe_and_detached(self):
        declaration = capabilities()
        reading = snapshot()
        normalized_declaration = provider_contracts.validate_capabilities(declaration)
        normalized_reading = provider_contracts.validate_snapshot(reading)

        declaration['values'][0]['unit'] = 'changed'
        reading['resources'][0]['values'][0]['value'] = 0
        self.assertEqual(normalized_declaration['values'][0]['unit'], '%')
        self.assertEqual(normalized_reading['resources'][0]['values'][0]['value'], 72.5)
        json.dumps(normalized_declaration, allow_nan=False)
        json.dumps(normalized_reading, allow_nan=False)

    def test_rejects_wrong_types_non_finite_values_and_provider_mismatch(self):
        invalid = snapshot()
        invalid['resources'][0]['values'][0]['value'] = float('nan')
        with self.assertRaises(provider_contracts.ProviderContractError):
            provider_contracts.validate_snapshot(invalid)
        invalid = snapshot()
        invalid['resources'][0]['values'][0]['value'] = True
        with self.assertRaises(provider_contracts.ProviderContractError):
            provider_contracts.validate_snapshot(invalid)
        with self.assertRaises(provider_contracts.ProviderContractError):
            provider_contracts.validate_snapshot(snapshot(), 'another_provider')

    def test_validates_event_alert_and_action_formats(self):
        reading = snapshot()
        reading['events'].append({
            'id': 'evt-1', 'code': 'tank.measurement', 'source': 'tank-1',
            'severity': 'info', 'occurred_at': '2026-08-21T12:00:00Z',
            'data': {'fill_percent': 72.5},
        })
        reading['alerts'].append({
            'id': 'tank-1.sensor', 'code': 'tank.sensor_error',
            'severity': 'error', 'state': 'active',
            'opened_at': '2026-08-21T12:00:00Z', 'context': {'resource_id': 'tank-1'},
        })
        declaration = capabilities()
        declaration['actions'].append({
            'id': 'refresh_cache', 'risk': 'read_only', 'parameters': {},
        })
        provider_contracts.validate_snapshot(reading)
        provider_contracts.validate_capabilities(declaration)

    def test_utc_timestamp_is_explicit_utc(self):
        timestamp = provider_contracts.utc_timestamp(0)
        self.assertEqual(timestamp, '1970-01-01T00:00:00Z')
        aware = datetime.datetime(2026, 8, 21, 14, 0,
                                  tzinfo=datetime.timezone(datetime.timedelta(hours=2)))
        self.assertEqual(provider_contracts.utc_timestamp(aware), '2026-08-21T12:00:00Z')

        invalid = snapshot()
        invalid['observed_at'] = '2026-08-21T12:00:00'
        with self.assertRaises(provider_contracts.ProviderContractError):
            provider_contracts.validate_snapshot(invalid)

    def test_plugin_registry_validates_and_isolates_provider_failures(self):
        valid = mock.Mock()
        valid.provider_capabilities.return_value = capabilities('valid_provider')
        valid.provider_snapshot.return_value = snapshot('valid_provider')
        broken = mock.Mock()
        broken.provider_capabilities.return_value = capabilities('broken_provider')
        broken.provider_snapshot.side_effect = IOError('sensor failed')
        modules = {'valid_provider': valid, 'broken_provider': broken}

        with mock.patch.object(plugins, 'running', return_value=list(modules)), \
                mock.patch.object(plugins, 'plugin_manifest', return_value={
                    'provider': {'contract': 'ospy.provider.v1'},
                }), \
                mock.patch.object(plugins, 'get', side_effect=lambda module: modules[module]):
            self.assertEqual(plugins.plugin_provider_modules(),
                             ['broken_provider', 'valid_provider'])
            collected = plugins.plugin_provider_snapshots()

        self.assertIn('valid_provider', collected['providers'])
        self.assertIn('broken_provider', collected['errors'])
        self.assertNotIn('broken_provider', collected['providers'])

    def test_provider_action_must_be_declared_and_returns_detached_json(self):
        provider = mock.Mock()
        declaration = capabilities('action_provider')
        declaration['actions'] = [{
            'id': 'close_valve', 'risk': 'safety',
            'parameters': {'force': 'boolean'},
        }]
        provider.provider_capabilities.return_value = declaration
        provider.provider_execute_action.return_value = {
            'status': 'ok', 'data': {'closed': True},
        }
        with mock.patch.object(plugins, 'running', return_value=['action_provider']), \
                mock.patch.object(plugins, 'plugin_manifest', return_value={
                    'provider': {'contract': 'ospy.provider.v1'},
                }), \
                mock.patch.object(plugins, 'get', return_value=provider):
            result = plugins.plugin_provider_execute_action(
                'action_provider', 'close_valve', 'tank-1', {'force': True})
            with self.assertRaises(RuntimeError):
                plugins.plugin_provider_execute_action(
                    'action_provider', 'undeclared', 'tank-1', {})

        self.assertEqual(result['status'], 'ok')
        provider.provider_execute_action.assert_called_once_with(
            'close_valve', resource_id='tank-1', parameters={'force': True})


if __name__ == '__main__':
    unittest.main()
