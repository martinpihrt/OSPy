#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Two-factor authentication helpers for the main OSPy administrator."""

import base64
import hashlib
import hmac
import io
import secrets
import struct
import time


METHOD_NONE = 'none'
METHOD_TOTP = 'totp'
METHOD_EMAIL = 'email'
VALID_METHODS = (METHOD_NONE, METHOD_TOTP, METHOD_EMAIL)
TOTP_PERIOD = 30
EMAIL_CODE_LIFETIME = 300


def generate_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode('ascii').rstrip('=')


def _decode_secret(secret):
    secret = ''.join(str(secret or '').split()).upper()
    return base64.b32decode(secret + '=' * ((8 - len(secret) % 8) % 8), casefold=True)


def totp_code(secret, timestamp=None):
    timestamp = time.time() if timestamp is None else timestamp
    counter = int(timestamp // TOTP_PERIOD)
    digest = hmac.new(_decode_secret(secret), struct.pack('>Q', counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0f
    number = (struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7fffffff) % 1000000
    return '{:06d}'.format(number)


def verify_totp(secret, code, timestamp=None, window=1):
    code = str(code or '').strip().replace(' ', '')
    if len(code) != 6 or not code.isdigit() or not secret:
        return False
    timestamp = time.time() if timestamp is None else timestamp
    return any(hmac.compare_digest(totp_code(secret, timestamp + step * TOTP_PERIOD), code)
               for step in range(-window, window + 1))


def provisioning_uri(secret, username, issuer='OSPy'):
    from urllib.parse import quote
    label = '{}:{}'.format(issuer, username)
    return 'otpauth://totp/{}?secret={}&issuer={}&digits=6&period={}'.format(
        quote(label, safe=''), secret, quote(issuer, safe=''), TOTP_PERIOD)


def qr_png(data):
    try:
        import qrcode
    except ImportError:
        return None
    image = qrcode.make(data)
    output = io.BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()


def hash_email_code(code, nonce):
    return hashlib.sha256(('{}:{}'.format(nonce, code)).encode('utf-8')).hexdigest()


def new_email_challenge():
    code = '{:06d}'.format(secrets.randbelow(1000000))
    nonce = secrets.token_hex(16)
    return code, nonce, hash_email_code(code, nonce), time.time() + EMAIL_CODE_LIFETIME


def verify_email_code(code, nonce, expected_hash, expires_at):
    if time.time() > float(expires_at or 0):
        return False
    return hmac.compare_digest(hash_email_code(str(code or '').strip(), nonce), expected_hash or '')


def generate_backup_codes(count=8):
    return ['{}-{}'.format(secrets.token_hex(2).upper(), secrets.token_hex(2).upper())
            for _ in range(count)]


def hash_backup_code(code):
    normalized = str(code or '').strip().replace('-', '').upper()
    return hashlib.sha256(normalized.encode('ascii', 'ignore')).hexdigest()


def consume_backup_code(code, stored_hashes):
    candidate = hash_backup_code(code)
    remaining = list(stored_hashes or [])
    for index, stored in enumerate(remaining):
        if hmac.compare_digest(candidate, stored):
            del remaining[index]
            return True, remaining
    return False, remaining


def email_plugin_status():
    try:
        import plugins
        if 'email_notifications_ssl' not in plugins.running():
            return False, _('The E-mail Notifications SSL plug-in is not running.')
        module = plugins.get('email_notifications_ssl')
        if hasattr(module, 'is_configured'):
            if not module.is_configured():
                return False, _('The E-mail Notifications SSL plug-in is not properly configured.')
            return True, ''
        cfg = module.email_options
        required = ('emlserver', 'emlusr', 'emlpwd', 'emladr0')
        if not all(cfg.get(key) for key in required):
            return False, _('The E-mail Notifications SSL plug-in is not properly configured.')
        return True, ''
    except Exception:
        return False, _('The E-mail Notifications SSL plug-in is not available.')


def masked_email_recipient():
    try:
        import plugins
        address = str(plugins.get('email_notifications_ssl').email_options.get('emladr0', ''))
        local, domain = address.split('@', 1)
        return '{}***@{}'.format(local[:1], domain)
    except Exception:
        return ''


def send_email_code(code):
    available, message = email_plugin_status()
    if not available:
        raise RuntimeError(message)
    import plugins
    module = plugins.get('email_notifications_ssl')
    if hasattr(module, 'send_2fa_code'):
        module.send_2fa_code(code, 5)
        return
    text = _(
        'Your OSPy verification code is <b>{}</b>. The code expires in 5 minutes. '
        'If you did not try to sign in, change your password.'
    ).format(code)
    module.email(text, _('OSPy login verification code'))
