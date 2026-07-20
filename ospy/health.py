#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Small in-memory health registry for long-running OSPy components."""

import json
import logging
import os
import threading
import time
import uuid


_lock = threading.RLock()
_components = {}
_issues = {}
_incidents = []
_incident_history_loaded = False

_DATA_DIR = os.environ.get('OSPY_DATA_DIR', os.path.join('ospy', 'data'))
INCIDENT_HISTORY_FILE = os.path.join(_DATA_DIR, 'diagnostics_incidents.json')
INCIDENT_HISTORY_VERSION = 1
INCIDENT_HISTORY_LIMIT = 200
INCIDENT_HISTORY_MAX_BYTES = 512 * 1024


def _text(value, limit):
    return str(value or '')[:limit]


def _safe_incident(raw):
    """Validate and bound one persisted incident record."""
    if not isinstance(raw, dict) or not raw.get('incident_id'):
        return None
    try:
        opened = float(raw.get('opened', 0))
        last_seen = float(raw.get('last_seen', opened))
        resolved = float(raw.get('resolved', 0))
        count = max(1, int(raw.get('count', 1)))
    except (TypeError, ValueError):
        return None
    status = raw.get('status', 'resolved')
    if status not in ('open', 'resolved', 'interrupted'):
        status = 'resolved'
    severity = raw.get('severity', 'error')
    if severity not in ('warning', 'error'):
        severity = 'error'
    return {
        'incident_id': _text(raw.get('incident_id'), 80),
        'issue_id': _text(raw.get('issue_id'), 180),
        'title': _text(raw.get('title'), 240),
        'summary': _text(raw.get('summary'), 600),
        'details': _text(raw.get('details'), 1200),
        'solution': _text(raw.get('solution'), 1200),
        'link': _text(raw.get('link'), 400),
        'severity': severity,
        'status': status,
        'opened': opened,
        'last_seen': last_seen,
        'resolved': resolved,
        'count': count,
    }


def _persist_incidents_locked():
    directory = os.path.dirname(INCIDENT_HISTORY_FILE)
    temporary = INCIDENT_HISTORY_FILE + '.tmp'
    try:
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        payload = {
            'version': INCIDENT_HISTORY_VERSION,
            'incidents': _incidents[-INCIDENT_HISTORY_LIMIT:],
        }
        with open(temporary, 'w', encoding='utf-8') as history_file:
            json.dump(payload, history_file, ensure_ascii=False, sort_keys=True)
            history_file.flush()
            os.fsync(history_file.fileno())
        os.replace(temporary, INCIDENT_HISTORY_FILE)
    except Exception as err:
        logging.warning('Could not save diagnostics incident history: %s', err)
        try:
            if os.path.isfile(temporary):
                os.remove(temporary)
        except OSError:
            logging.debug('Could not remove temporary incident history file.')


def _load_incidents_locked():
    global _incident_history_loaded, _incidents
    if _incident_history_loaded:
        return
    _incident_history_loaded = True
    _incidents = []
    if not os.path.isfile(INCIDENT_HISTORY_FILE):
        return
    try:
        if os.path.getsize(INCIDENT_HISTORY_FILE) > INCIDENT_HISTORY_MAX_BYTES:
            raise ValueError('incident history file is too large')
        with open(INCIDENT_HISTORY_FILE, 'r', encoding='utf-8') as history_file:
            payload = json.load(history_file)
        if not isinstance(payload, dict) or payload.get('version') != INCIDENT_HISTORY_VERSION:
            raise ValueError('unsupported incident history format')
        records = payload.get('incidents', [])
        if not isinstance(records, list):
            raise ValueError('incident history is not a list')
        for raw in records[-INCIDENT_HISTORY_LIMIT:]:
            incident = _safe_incident(raw)
            if incident is not None:
                _incidents.append(incident)

        interrupted = False
        now = time.time()
        for incident in _incidents:
            if incident['status'] == 'open':
                incident['status'] = 'interrupted'
                incident['resolved'] = now
                interrupted = True
        if interrupted:
            _persist_incidents_locked()
    except Exception as err:
        _incidents = []
        logging.warning('Could not load diagnostics incident history: %s', err)


def heartbeat(component, ok=True, message='', **details):
    """Record that a component completed work or encountered an error."""
    timestamp = time.time()
    with _lock:
        entry = _components.setdefault(component, {
            'last_update': 0,
            'last_success': 0,
            'last_error': 0,
            'message': '',
            'error': '',
            'details': {},
        })
        entry['last_update'] = timestamp
        entry['details'].update(details)
        if ok:
            entry['last_success'] = timestamp
            entry['message'] = message or entry.get('message', '')
            entry['error'] = ''
        else:
            entry['last_error'] = timestamp
            entry['error'] = message


def update_details(component, **details):
    """Update component metadata without treating it as completed work."""
    with _lock:
        entry = _components.setdefault(component, {
            'last_update': 0,
            'last_success': 0,
            'last_error': 0,
            'message': '',
            'error': '',
            'details': {},
        })
        entry['details'].update(details)


def component(component_name):
    """Return a detached snapshot for one component."""
    with _lock:
        entry = _components.get(component_name, {})
        result = dict(entry)
        result['details'] = dict(entry.get('details', {}))
        return result


def snapshot():
    """Return a detached snapshot of all registered components."""
    with _lock:
        return {
            name: dict(entry, details=dict(entry.get('details', {})))
            for name, entry in _components.items()
        }


def report_issue(issue_id, title, summary, details='', solution='', link='',
                 severity='error'):
    """Record an active recoverable problem for administrator diagnostics."""
    if severity not in ('warning', 'error'):
        severity = 'error'
    timestamp = time.time()
    with _lock:
        _load_incidents_locked()
        previous = _issues.get(issue_id, {})
        incident_id = previous.get('incident_id')
        if not incident_id:
            incident_id = '{}-{}'.format(
                int(timestamp * 1000), uuid.uuid4().hex[:12]
            )
        issue = {
            'id': str(issue_id),
            'incident_id': incident_id,
            'title': _text(title, 240),
            'summary': _text(summary, 600),
            'details': _text(details, 1200),
            'solution': _text(solution, 1200),
            'link': _text(link, 400),
            'severity': severity,
            'first_seen': previous.get('first_seen', timestamp),
            'last_seen': timestamp,
            'count': previous.get('count', 0) + 1,
        }
        _issues[issue_id] = issue

        incident = next((
            item for item in _incidents
            if item.get('incident_id') == incident_id
        ), None)
        if incident is None:
            incident = {
                'incident_id': incident_id,
                'issue_id': _text(issue_id, 180),
                'status': 'open',
                'opened': issue['first_seen'],
                'resolved': 0,
            }
            _incidents.append(incident)
        incident.update({
            'title': issue['title'],
            'summary': issue['summary'],
            'details': issue['details'],
            'solution': issue['solution'],
            'link': issue['link'],
            'severity': issue['severity'],
            'last_seen': timestamp,
            'count': issue['count'],
        })
        del _incidents[:-INCIDENT_HISTORY_LIMIT]
        _persist_incidents_locked()


def resolve_issue(issue_id):
    """Remove an active issue after the affected operation succeeds again."""
    with _lock:
        _load_incidents_locked()
        issue = _issues.pop(issue_id, None)
        if issue is None:
            return False
        timestamp = time.time()
        for incident in _incidents:
            if incident.get('incident_id') == issue.get('incident_id'):
                incident['status'] = 'resolved'
                incident['resolved'] = timestamp
                incident['last_seen'] = max(
                    incident.get('last_seen', 0), issue.get('last_seen', 0)
                )
                break
        _persist_incidents_locked()
        return True


def active_issues():
    """Return detached active issues ordered by severity and latest occurrence."""
    with _lock:
        result = [dict(issue) for issue in _issues.values()]
    return sorted(
        result,
        key=lambda issue: (
            0 if issue.get('severity') == 'error' else 1,
            -issue.get('last_seen', 0),
            issue.get('id', ''),
        )
    )


def incident_history(status='all', limit=100):
    """Return bounded persisted incident history, newest occurrence first."""
    try:
        limit = max(1, min(INCIDENT_HISTORY_LIMIT, int(limit)))
    except (TypeError, ValueError):
        limit = 100
    if status not in ('all', 'open', 'resolved', 'interrupted'):
        status = 'all'
    with _lock:
        _load_incidents_locked()
        records = [dict(incident) for incident in _incidents]
    if status != 'all':
        records = [item for item in records if item.get('status') == status]
    records.sort(key=lambda item: item.get('last_seen', 0), reverse=True)
    return records[:limit]
