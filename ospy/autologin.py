#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import hmac
import json
import os
import time
from email.utils import formatdate
from threading import Lock

import web

from ospy.log import log


TOKEN_FILE = os.path.join('ospy', 'data', 'auto_login_tokens.json')
COOKIE_NAME = 'ospy_auto_login'
TOKEN_TTL = 90 * 24 * 60 * 60
LOGIN_EVENT_WINDOW = 10
_LOCK = Lock()
_recent_logins = {}


def _now():
    return int(time.time())


def _hash_token(secret):
    return hashlib.sha256(secret.encode('utf-8')).hexdigest()


def _load_tokens():
    try:
        if not os.path.isfile(TOKEN_FILE):
            return {}
        with open(TOKEN_FILE, 'r') as token_file:
            data = json.load(token_file)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        log.error('autologin.py', _('Could not load auto-login tokens: {}').format(e))
        return {}


def _save_tokens(tokens):
    token_dir = os.path.dirname(TOKEN_FILE)
    if not os.path.isdir(token_dir):
        os.makedirs(token_dir)

    tmp_file = TOKEN_FILE + '.tmp'
    with open(tmp_file, 'w') as token_file:
        json.dump(tokens, token_file, sort_keys=True)
    try:
        os.chmod(tmp_file, 0o600)
    except Exception:
        pass
    os.replace(tmp_file, TOKEN_FILE)


def _cleanup(tokens):
    now_ts = _now()
    return {
        selector: token
        for selector, token in tokens.items()
        if int(token.get('expires', 0)) > now_ts
    }


def _cookie_secure():
    try:
        return bool(web.config.session_parameters.secure)
    except Exception:
        return False


def _set_cookie(token_value, expires_ts):
    web.setcookie(
        COOKIE_NAME,
        token_value,
        expires=formatdate(expires_ts, usegmt=True),
        httponly=True,
        secure=_cookie_secure(),
        path='/',
        samesite='Lax',
    )


def clear_cookie():
    try:
        web.setcookie(
            COOKIE_NAME,
            '',
            expires=-1,
            httponly=True,
            secure=_cookie_secure(),
            path='/',
            samesite='Lax',
        )
    except Exception:
        pass


def _request_info():
    env = getattr(web.ctx, 'env', {})
    return {
        'ip': env.get('REMOTE_ADDR', ''),
        'user_agent': env.get('HTTP_USER_AGENT', '')[:200],
    }


def issue(username, category):
    selector = os.urandom(16).hex()
    secret = os.urandom(32).hex()
    expires_ts = _now() + TOKEN_TTL
    info = _request_info()

    with _LOCK:
        tokens = _cleanup(_load_tokens())
        tokens[selector] = {
            'secret_hash': _hash_token(secret),
            'username': username,
            'category': category,
            'created': _now(),
            'last_used': _now(),
            'expires': expires_ts,
            'ip': info['ip'],
            'user_agent': info['user_agent'],
        }
        _save_tokens(tokens)

    _set_cookie('{}:{}'.format(selector, secret), expires_ts)


def _split_cookie(value):
    if not value or ':' not in value:
        return None, None
    selector, secret = value.split(':', 1)
    if not selector or not secret:
        return None, None
    return selector, secret


def _current_user_category(username):
    from ospy.options import options
    from ospy.users import users

    if username == options.admin_user:
        return 'admin'

    categories = {
        '0': 'public',
        '1': 'user',
        '2': 'admin',
        '3': 'sensor',
    }
    for user in users.get():
        if user.name == username:
            return categories.get(user.category)
    return None


def validate_cookie():
    selector, secret = _split_cookie(web.cookies().get(COOKIE_NAME))
    if not selector:
        return None

    with _LOCK:
        tokens = _cleanup(_load_tokens())
        token = tokens.get(selector)
        if not token:
            _save_tokens(tokens)
            clear_cookie()
            return None

        if not hmac.compare_digest(token.get('secret_hash', ''), _hash_token(secret)):
            clear_cookie()
            return None

        category = _current_user_category(token.get('username', ''))
        if not category:
            tokens.pop(selector, None)
            _save_tokens(tokens)
            clear_cookie()
            return None

        token['category'] = category
        token['last_used'] = _now()
        tokens[selector] = token
        _save_tokens(tokens)

    return {
        'username': token.get('username', ''),
        'category': category,
        'selector': selector,
    }


def should_log_login(selector):
    """Return True once for concurrent uses of the same remembered login.

    A browser can request several protected resources at the same time after
    its web session has expired.  They all arrive at /login with the same
    remember-me token and must not be reported as separate user logins.
    """
    now_ts = time.time()
    with _LOCK:
        expired = [
            key for key, timestamp in _recent_logins.items()
            if now_ts - timestamp >= LOGIN_EVENT_WINDOW
        ]
        for key in expired:
            _recent_logins.pop(key, None)

        if selector in _recent_logins:
            return False
        _recent_logins[selector] = now_ts
        return True


def revoke_cookie_token():
    selector, secret = _split_cookie(web.cookies().get(COOKIE_NAME))
    if selector:
        with _LOCK:
            tokens = _load_tokens()
            if selector in tokens:
                tokens.pop(selector, None)
                _save_tokens(tokens)
    clear_cookie()


def revoke_all():
    with _LOCK:
        _save_tokens({})
    clear_cookie()


def count():
    with _LOCK:
        tokens = _cleanup(_load_tokens())
        _save_tokens(tokens)
    return len(tokens)
