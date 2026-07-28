"""Bearer authentication and scope enforcement for API v1."""

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from functools import wraps

import web

from ospy import server, twofactor
from ospy.helpers import bruteforce_blocked, test_password
from ospy.log import logEV
from ospy.options import options

from .responses import APIError
from .store import mobile_store


ACCESS_LIFETIME = 15 * 60
ROLE_SCOPES = {
    "public": ["read"],
    "user": ["read", "control"],
    "admin": [
        "read", "control", "configuration", "plugins",
        "backup", "update", "system",
    ],
}


def _b64encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value):
    raw = str(value).encode("ascii")
    return base64.urlsafe_b64decode(raw + b"=" * ((4 - len(raw) % 4) % 4))


def _sign(value):
    return hmac.new(
        mobile_store.signing_secret().encode("utf-8"),
        value.encode("ascii"),
        hashlib.sha256,
    ).digest()


def issue_access_token(username, role, scopes, device_id, token_id):
    now = int(time.time())
    payload = {
        "iss": mobile_store.instance_id(),
        "sub": username,
        "role": role,
        "scopes": sorted(set(scopes)),
        "device_id": device_id,
        "sid": token_id,
        "iat": now,
        "exp": now + ACCESS_LIFETIME,
        "jti": uuid.uuid4().hex,
    }
    header = _b64encode(json.dumps(
        {"alg": "HS256", "typ": "OSPY-AT", "v": 1},
        separators=(",", ":"),
    ).encode("utf-8"))
    body = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = header + "." + body
    return signing_input + "." + _b64encode(_sign(signing_input))


def verify_access_token(token):
    try:
        header, body, signature = str(token).split(".", 2)
        signing_input = header + "." + body
        if not hmac.compare_digest(_sign(signing_input), _b64decode(signature)):
            raise ValueError("signature")
        metadata = json.loads(_b64decode(header).decode("utf-8"))
        payload = json.loads(_b64decode(body).decode("utf-8"))
        if metadata.get("typ") != "OSPY-AT" or metadata.get("v") != 1:
            raise ValueError("type")
        if payload.get("iss") != mobile_store.instance_id():
            raise ValueError("issuer")
        if int(payload.get("exp", 0)) <= int(time.time()):
            raise ValueError("expired")
        session = mobile_store.active_token_session(
            payload.get("sid"), payload.get("device_id")
        )
        if not session:
            raise ValueError("revoked")
        if (
            session["username"] != payload.get("sub") or
            session["role"] != payload.get("role")
        ):
            raise ValueError("identity")
        payload["scopes"] = sorted(
            set(payload.get("scopes", ())).intersection(session["scopes"])
        )
        return payload
    except Exception:
        raise APIError(401, "invalid_token", "The access token is invalid or expired.")


def current_identity():
    authorization = web.ctx.env.get("HTTP_AUTHORIZATION", "")
    if not authorization.startswith("Bearer "):
        raise APIError(401, "missing_token", "A Bearer access token is required.")
    identity = verify_access_token(authorization[7:].strip())
    web.ctx.api_v1_identity = identity
    return identity


def require_scope(scope):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            identity = current_identity()
            if scope not in identity.get("scopes", ()):
                raise APIError(
                    403, "insufficient_scope",
                    "The access token does not permit this operation.",
                    {"required_scope": scope},
                )
            return function(*args, **kwargs)
        return wrapper
    return decorator


def _validate_password(username, password):
    if getattr(options, "no_password", False):
        raise APIError(
            403, "password_required",
            "Configure an OSPy administrator password before pairing a mobile device.",
        )
    previous_category = server.session.get("category", "public")
    previous_visitor = server.session.get("visitor", "Unknown")
    try:
        if not test_password(str(password or ""), str(username or "")):
            code = "authentication_blocked" if bruteforce_blocked(username) else "invalid_credentials"
            status = 429 if code == "authentication_blocked" else 401
            raise APIError(status, code, "The username or password is not valid.")
        return server.session.get("category", "public")
    finally:
        server.session["category"] = previous_category
        server.session["visitor"] = previous_visitor


def _verify_second_factor(username, role, payload):
    if username != getattr(options, "admin_user", "admin") or role != "admin":
        return
    method = str(getattr(options, "two_factor_method", "none") or "none")
    if method == twofactor.METHOD_NONE:
        return
    code = str(payload.get("two_factor_code", "") or "").strip()
    if method == twofactor.METHOD_TOTP:
        if twofactor.verify_totp(options.two_factor_secret, code):
            return
        valid, remaining = twofactor.consume_backup_code(
            code, options.two_factor_backup_codes
        )
        if valid:
            options.two_factor_backup_codes = remaining
            return
        raise APIError(
            401, "two_factor_required",
            "A valid TOTP or one-time backup code is required.",
            {"method": "totp"},
        )
    if method == twofactor.METHOD_EMAIL:
        challenge_id = str(payload.get("challenge_id", "") or "")
        if challenge_id and code:
            challenge = mobile_store.login_challenge(challenge_id, username)
            if challenge and twofactor.verify_email_code(
                    code, challenge["nonce"], challenge["code_hash"], challenge["expires"]):
                mobile_store.consume_login_challenge(challenge_id)
                return
            raise APIError(
                401, "invalid_two_factor_code",
                "The e-mail verification code is invalid or expired.",
                {"method": "email", "challenge_id": challenge_id},
            )
        generated, nonce, code_hash, expires = twofactor.new_email_challenge()
        try:
            twofactor.send_email_code(generated)
        except Exception as error:
            raise APIError(
                503, "two_factor_delivery_failed",
                "The e-mail verification code could not be delivered.",
                {"reason": str(error)},
            )
        challenge_id = mobile_store.create_login_challenge(
            username, nonce, code_hash, expires
        )
        raise APIError(
            401, "two_factor_required",
            "Enter the verification code sent by e-mail.",
            {
                "method": "email",
                "challenge_id": challenge_id,
                "expires_in": max(0, int(expires - time.time())),
                "recipient": twofactor.masked_email_recipient(),
            },
        )


def login(payload):
    username = str(payload.get("username", "") or "").strip()
    password = payload.get("password", "")
    if not username or password is None:
        raise APIError(422, "missing_credentials", "Username and password are required.")
    role = _validate_password(username, password)
    if role == "sensor":
        raise APIError(403, "role_not_supported", "Sensor accounts cannot pair mobile devices.")
    _verify_second_factor(username, role, payload)
    requested = payload.get("scopes")
    allowed = ROLE_SCOPES.get(role, ["read"])
    if isinstance(requested, list):
        scopes = sorted(set(str(item) for item in requested).intersection(allowed))
    else:
        scopes = allowed
    device = payload.get("device") if isinstance(payload.get("device"), dict) else {}
    refresh = mobile_store.issue_refresh_token(
        username, role, scopes, device.get("id"), device.get("name", "Android"),
        device.get("app_version", ""),
    )
    access = issue_access_token(
        username, role, scopes, refresh["device_id"], refresh["id"]
    )
    logEV.save_events_log(
        "Mobile device paired",
        "User {} paired mobile device {} from IP {}.".format(
            username, device.get("name", "Android"), getattr(web.ctx, "ip", "-")
        ),
        id="Login", level="info", category="security",
    )
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": ACCESS_LIFETIME,
        "refresh_token": refresh["token"],
        "refresh_expires_in": max(0, int(refresh["expires"] - time.time())),
        "device_id": refresh["device_id"],
        "role": role,
        "scopes": scopes,
    }


def refresh(refresh_token):
    replacement = mobile_store.rotate_refresh_token(refresh_token)
    if replacement is None:
        raise APIError(401, "invalid_refresh_token", "The refresh token is invalid or expired.")
    access = issue_access_token(
        replacement["username"], replacement["role"], replacement["scopes"],
        replacement["device_id"], replacement["id"],
    )
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": ACCESS_LIFETIME,
        "refresh_token": replacement["token"],
        "refresh_expires_in": max(0, int(replacement["expires"] - time.time())),
        "device_id": replacement["device_id"],
        "role": replacement["role"],
        "scopes": replacement["scopes"],
    }
