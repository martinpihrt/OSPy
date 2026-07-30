"""Consistent request parsing, JSON responses and API errors."""

import json
import traceback
import uuid
from functools import wraps

import web

from ospy.log import log


STATUS_TEXT = {
    200: "200 OK",
    201: "201 Created",
    202: "202 Accepted",
    204: "204 No Content",
    400: "400 Bad Request",
    401: "401 Unauthorized",
    403: "403 Forbidden",
    404: "404 Not Found",
    409: "409 Conflict",
    413: "413 Payload Too Large",
    422: "422 Unprocessable Entity",
    429: "429 Too Many Requests",
    500: "500 Internal Server Error",
    503: "503 Service Unavailable",
}
MAX_JSON_BODY = 1024 * 1024


class APIError(Exception):
    def __init__(self, status, code, message, details=None):
        super(APIError, self).__init__(message)
        self.status = int(status)
        self.code = str(code)
        self.message = str(message)
        self.details = details or {}


def request_id():
    existing = getattr(web.ctx, "api_v1_request_id", None)
    if existing:
        return existing
    value = web.ctx.env.get("HTTP_X_REQUEST_ID", "") if hasattr(web.ctx, "env") else ""
    value = value.strip()[:100] if value else "req-" + uuid.uuid4().hex
    web.ctx.api_v1_request_id = value
    return value


def _headers():
    web.header("Content-Type", "application/json; charset=utf-8")
    web.header("Cache-Control", "no-store")
    web.header("X-Content-Type-Options", "nosniff")
    web.header("X-Request-ID", request_id())


def respond(data=None, status=200, meta=None):
    _headers()
    web.ctx.status = STATUS_TEXT.get(status, str(status))
    if status == 204:
        return ""
    payload = {
        "data": data,
        "meta": dict(meta or {}),
    }
    payload["meta"]["request_id"] = request_id()
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def error_response(error):
    _headers()
    web.ctx.status = STATUS_TEXT.get(error.status, str(error.status))
    return json.dumps(
        {
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
                "request_id": request_id(),
            }
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def endpoint(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        request_id()
        try:
            return function(*args, **kwargs)
        except APIError as error:
            return error_response(error)
        except Exception:
            log.error("api/v1", traceback.format_exc())
            return error_response(APIError(
                500, "internal_error", "The API request could not be completed."
            ))
    return wrapper


def json_body(required=True):
    raw = web.data() or b""
    if len(raw) > MAX_JSON_BODY:
        raise APIError(413, "payload_too_large", "The JSON request is too large.")
    if not raw:
        if required:
            raise APIError(400, "missing_json", "A JSON request body is required.")
        return {}
    try:
        value = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
    except (UnicodeDecodeError, ValueError):
        raise APIError(400, "invalid_json", "The request body is not valid JSON.")
    if not isinstance(value, dict):
        raise APIError(422, "invalid_json_type", "The JSON request must be an object.")
    return value


def query_bool(name, default=False):
    value = web.input().get(name)
    if value is None:
        return default
    return str(value).lower() in ("1", "true", "yes", "on")
