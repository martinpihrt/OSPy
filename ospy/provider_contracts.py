"""Versioned, JSON-safe contracts for plug-in data providers.

The provider contract deliberately contains stable machine identifiers only.
User-facing labels and translations belong to the consuming interface.
"""

import datetime
import json
import math
import re


CONTRACT_VERSION = 'ospy.provider.v1'
PROVIDER_STATUSES = frozenset(('ok', 'unavailable', 'stale', 'error', 'disabled'))
RESOURCE_STATUSES = PROVIDER_STATUSES
VALUE_QUALITIES = frozenset(('measured', 'derived', 'estimated', 'unknown'))
VALUE_TYPES = frozenset(('number', 'integer', 'boolean', 'string'))
ALERT_SEVERITIES = frozenset(('info', 'warning', 'error', 'critical'))
ALERT_STATES = frozenset(('active', 'acknowledged', 'cleared'))
ACTION_RISKS = frozenset(('read_only', 'control', 'safety'))
_IDENTIFIER = re.compile(r'^[a-z][a-z0-9_.-]{0,127}$')


class ProviderContractError(ValueError):
    """Raised when a provider returns data outside the public contract."""


def utc_timestamp(value=None):
    """Convert an epoch or datetime value to a UTC ISO-8601 timestamp."""
    if value is None:
        value = datetime.datetime.now(datetime.timezone.utc)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        value = datetime.datetime.fromtimestamp(value, datetime.timezone.utc)
    if not isinstance(value, datetime.datetime):
        raise ProviderContractError('Timestamp value is not a datetime or epoch.')
    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)
    return value.astimezone(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')


def _error(path, message):
    raise ProviderContractError('{}: {}'.format(path, message))


def _identifier(value, path):
    if not isinstance(value, str) or not _IDENTIFIER.match(value):
        _error(path, 'invalid stable identifier')


def _timestamp(value, path, required=False):
    if value in (None, ''):
        if required:
            _error(path, 'timestamp is required')
        return
    if not isinstance(value, str):
        _error(path, 'timestamp must be an ISO-8601 string')
    try:
        parsed = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (TypeError, ValueError):
        _error(path, 'invalid ISO-8601 timestamp')
    if parsed.tzinfo is None or parsed.utcoffset() != datetime.timedelta(0):
        _error(path, 'timestamp must include the UTC offset')


def _json_copy(value, path):
    try:
        encoded = json.dumps(value, allow_nan=False, sort_keys=True)
        return json.loads(encoded)
    except (TypeError, ValueError) as error:
        _error(path, 'not JSON-safe ({})'.format(error))


def _list(value, path):
    if not isinstance(value, list):
        _error(path, 'must be a list')
    return value


def _validate_value(item, path):
    if not isinstance(item, dict):
        _error(path, 'must be an object')
    for key in ('id', 'quantity'):
        _identifier(item.get(key), '{}.{}'.format(path, key))
    value_type = item.get('value_type')
    if value_type not in VALUE_TYPES:
        _error(path + '.value_type', 'unsupported value type')
    quality = item.get('quality')
    if quality not in VALUE_QUALITIES:
        _error(path + '.quality', 'unsupported quality')
    unit = item.get('unit')
    if not isinstance(unit, str) or len(unit) > 32:
        _error(path + '.unit', 'unit must be a short string')
    value = item.get('value')
    if value is not None:
        valid = {
            'number': isinstance(value, (int, float)) and not isinstance(value, bool),
            'integer': isinstance(value, int) and not isinstance(value, bool),
            'boolean': isinstance(value, bool),
            'string': isinstance(value, str),
        }[value_type]
        if not valid or (isinstance(value, float) and not math.isfinite(value)):
            _error(path + '.value', 'does not match value_type')
    _timestamp(item.get('observed_at'), path + '.observed_at')


def _validate_alert(item, path):
    if not isinstance(item, dict):
        _error(path, 'must be an object')
    for key in ('id', 'code'):
        _identifier(item.get(key), '{}.{}'.format(path, key))
    if item.get('severity') not in ALERT_SEVERITIES:
        _error(path + '.severity', 'unsupported severity')
    if item.get('state') not in ALERT_STATES:
        _error(path + '.state', 'unsupported state')
    _timestamp(item.get('opened_at'), path + '.opened_at', required=True)
    _timestamp(item.get('updated_at'), path + '.updated_at')
    if 'context' in item and not isinstance(item['context'], dict):
        _error(path + '.context', 'must be an object')


def _validate_event(item, path):
    if not isinstance(item, dict):
        _error(path, 'must be an object')
    for key in ('id', 'code', 'source'):
        _identifier(item.get(key), '{}.{}'.format(path, key))
    if item.get('severity') not in ALERT_SEVERITIES:
        _error(path + '.severity', 'unsupported severity')
    _timestamp(item.get('occurred_at'), path + '.occurred_at', required=True)
    if 'data' in item and not isinstance(item['data'], dict):
        _error(path + '.data', 'must be an object')


def _validate_action(item, path):
    if not isinstance(item, dict):
        _error(path, 'must be an object')
    _identifier(item.get('id'), path + '.id')
    if item.get('risk') not in ACTION_RISKS:
        _error(path + '.risk', 'unsupported risk')
    if not isinstance(item.get('parameters', {}), dict):
        _error(path + '.parameters', 'must be an object')


def validate_capabilities(data, expected_provider_id=None):
    """Validate and detach one provider capability declaration."""
    result = _json_copy(data, 'capabilities')
    if not isinstance(result, dict) or result.get('contract') != CONTRACT_VERSION:
        _error('capabilities.contract', 'unsupported provider contract')
    _identifier(result.get('provider_id'), 'capabilities.provider_id')
    if expected_provider_id and result['provider_id'] != expected_provider_id:
        _error('capabilities.provider_id', 'does not match the plug-in id')
    types = _list(result.get('resource_types'), 'capabilities.resource_types')
    if not types:
        _error('capabilities.resource_types', 'must not be empty')
    for index, resource_type in enumerate(types):
        _identifier(resource_type, 'capabilities.resource_types[{}]'.format(index))
    for key, validator in (('values', _validate_value), ('events', _validate_event),
                           ('alerts', _validate_alert), ('actions', _validate_action)):
        entries = _list(result.get(key, []), 'capabilities.' + key)
        # Capability entries describe fields and therefore omit live-only data.
        if key == 'values':
            for index, entry in enumerate(entries):
                probe = dict(entry)
                probe.setdefault('value', None)
                probe.setdefault('quality', 'unknown')
                validator(probe, 'capabilities.{}[{}]'.format(key, index))
        elif key == 'actions':
            for index, entry in enumerate(entries):
                validator(entry, 'capabilities.{}[{}]'.format(key, index))
        else:
            for index, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    _error('capabilities.{}[{}]'.format(key, index), 'must be an object')
                _identifier(entry.get('code'), 'capabilities.{}[{}].code'.format(key, index))
    return result


def validate_snapshot(data, expected_provider_id=None):
    """Validate and detach a current provider snapshot."""
    result = _json_copy(data, 'snapshot')
    if not isinstance(result, dict) or result.get('contract') != CONTRACT_VERSION:
        _error('snapshot.contract', 'unsupported provider contract')
    _identifier(result.get('provider_id'), 'snapshot.provider_id')
    if expected_provider_id and result['provider_id'] != expected_provider_id:
        _error('snapshot.provider_id', 'does not match the plug-in id')
    if result.get('status') not in PROVIDER_STATUSES:
        _error('snapshot.status', 'unsupported provider status')
    _timestamp(result.get('observed_at'), 'snapshot.observed_at')
    resources = _list(result.get('resources'), 'snapshot.resources')
    for r_index, resource in enumerate(resources):
        path = 'snapshot.resources[{}]'.format(r_index)
        if not isinstance(resource, dict):
            _error(path, 'must be an object')
        _identifier(resource.get('id'), path + '.id')
        _identifier(resource.get('type'), path + '.type')
        if resource.get('status') not in RESOURCE_STATUSES:
            _error(path + '.status', 'unsupported resource status')
        for v_index, value in enumerate(_list(resource.get('values'), path + '.values')):
            _validate_value(value, '{}.values[{}]'.format(path, v_index))
        for a_index, alert in enumerate(_list(resource.get('alerts', []), path + '.alerts')):
            _validate_alert(alert, '{}.alerts[{}]'.format(path, a_index))
    for index, event in enumerate(_list(result.get('events', []), 'snapshot.events')):
        _validate_event(event, 'snapshot.events[{}]'.format(index))
    for index, alert in enumerate(_list(result.get('alerts', []), 'snapshot.alerts')):
        _validate_alert(alert, 'snapshot.alerts[{}]'.format(index))
    return result
