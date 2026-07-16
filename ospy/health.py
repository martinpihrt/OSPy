#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Small in-memory health registry for long-running OSPy components."""

import threading
import time


_lock = threading.RLock()
_components = {}


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
