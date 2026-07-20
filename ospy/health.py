#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Small in-memory health registry for long-running OSPy components."""

import threading
import time


_lock = threading.RLock()
_components = {}
_issues = {}


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
        previous = _issues.get(issue_id, {})
        _issues[issue_id] = {
            'id': str(issue_id),
            'title': str(title),
            'summary': str(summary),
            'details': str(details or ''),
            'solution': str(solution or ''),
            'link': str(link or ''),
            'severity': severity,
            'first_seen': previous.get('first_seen', timestamp),
            'last_seen': timestamp,
            'count': previous.get('count', 0) + 1,
        }


def resolve_issue(issue_id):
    """Remove an active issue after the affected operation succeeds again."""
    with _lock:
        return _issues.pop(issue_id, None) is not None


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
