# OSPy Mobile API v1

The stable mobile API is available below `/api/v1`. It is intended for native
applications and integrations that must not parse OSPy HTML. The older `/api`
continues to work unchanged.

## Conventions and discovery

- Base URL example: `https://ospy.example:8080/api/v1`.
- JSON and text use UTF-8. Send `Content-Type: application/json` with bodies.
- Protected calls send `Authorization: Bearer ACCESS_TOKEN`.
- Dates use ISO 8601. IDs such as `station-0` are opaque and must not be
  calculated from the visible number.
- Clients must ignore unknown response fields and use `/capabilities` instead
  of parsing the OSPy version.
- Every JSON response disables caching and includes `X-Request-ID`.

Public endpoints are `GET /`, `/server`, `/capabilities` and `/openapi.json`.
`/server` provides the permanent installation UUID so the application can
distinguish installations with the same visible name.

## Pairing and security

1. Read `GET /api/v1/server` and verify the displayed OSPy installation.
2. Send the administrator or user name, password and a device description to
   `POST /api/v1/auth/login`.
3. When administrator two-factor authentication is enabled, include a TOTP or
   backup code. E-mail 2FA returns a challenge identifier and sends a code; send
   both in the repeated login request.
4. Store the returned refresh token only in protected operating-system storage,
   such as Android Keystore. Access tokens are short-lived and belong in memory.
5. Rotate the refresh token with `POST /api/v1/auth/refresh`. Reuse of an old
   rotated token is rejected. `POST /auth/logout` or deleting a paired device
   revokes access.

Pairing is deliberately unavailable while OSPy has no administrator password.
Tokens contain scopes. Read-only clients cannot operate stations; system,
backup, update and plug-in administration require their separate administrator
scopes.

The v1 API does not use the browser session cookie and does not accept a CSRF
token as authentication. A browser origin is not granted CORS access by
default. Native clients authenticate only with the Bearer token. Login uses the
same brute-force protection and audit log as the web login. Passwords, 2FA
codes and refresh tokens must never be placed in a URL.

### Login, refresh and device revocation

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "secret",
  "two_factor_code": "123456",
  "challenge_id": "only-for-email-2fa",
  "device": {
    "id": "optional-existing-device-id",
    "name": "Pixel 9",
    "app_version": "1.0.0"
  }
}
```

Omit the second-factor fields when 2FA is disabled. With e-mail 2FA, the first
request returns `two_factor_required`, sends a code and supplies
`challenge_id`; repeat the login with the challenge and code.

The result contains the access and refresh tokens, expiry times, role, scopes
and device ID. Refresh through `POST /auth/refresh` with
`{"refresh_token":"..."}`. Persist the replacement before deleting the old
token. `POST /auth/logout` revokes the current token session.
`GET /auth/devices` lists paired devices and
`DELETE /auth/devices/{device_id}` revokes one.

### Scopes

| Scope | Permission |
| --- | --- |
| `read` | Status, resources, logs, diagnostics, notifications and operations |
| `control` | Stations, programs, run-once and Stop All |
| `configuration` | Station, program and common sensor configuration |
| `plugins` | Manifest-declared mobile plug-in actions |
| `backup` | Create, download and restore system backups |
| `update` | Check, install and roll back updates |
| `system` | Restart OSPy, reboot Linux or power off |

The user role may receive `read` and `control`; the administrator may receive
every scope. Sensor accounts cannot pair a mobile device.

When a device pairs again with its existing device ID, its former refresh-token
session is revoked. Refresh is one-time rotation: after a successful refresh,
the old refresh token and access token no longer authorize requests. A client
must persist the returned replacement refresh token before continuing.

## Response format

Successful JSON responses use:

```json
{"data": {}, "meta": {"request_id": "req-..."}}
```

Errors use:

```json
{"error": {"code": "invalid_token", "message": "...", "details": {}, "request_id": "req-..."}}
```

Dates use ISO 8601. Station, program and sensor identifiers are typed strings
such as `station-0`; `legacy_index` is also returned where useful. A client
should discover supported functionality from `/capabilities`, not from the
OSPy version text.

Common statuses are `200`, `201`, `202`, `400`, `401`, `403`, `404`, `409`,
`413`, `422`, `429`, `500` and `503`. Stable error codes include
`missing_token`, `invalid_token`, `insufficient_scope`, `invalid_json`,
`not_found`, `station_unavailable`, `empty_run_once`, `two_factor_required`
and `update_plugin_unavailable`.

`X-Request-ID` may be supplied by the client (maximum 100 characters) and is
returned in the response header and error body. Include it when reporting a
failed request. JSON bodies are limited to 1 MiB. Pagination limits are bounded
by the server even if a larger value is requested.

### Complete endpoint index

| Area | Endpoints |
| --- | --- |
| Discovery | `GET /`, `/server`, `/capabilities`, `/openapi.json` |
| Authentication | `POST /auth/login`, `/auth/refresh`, `/auth/logout` |
| Devices | `GET /auth/devices`, `DELETE /auth/devices/{id}` |
| Home | `GET /overview` |
| Stations | `GET/PUT /stations`, `GET/PUT /stations/{id}`, `POST /stations/{id}/actions/start|stop`, `POST /stations/actions/stop-all` |
| Programs | `GET/POST /programs`, `GET/PUT/DELETE /programs/{id}`, `POST /programs/{id}/actions/run|stop` |
| Run-once | `GET/PUT /run-once`, `POST /run-once/actions/start` |
| Sensors | `GET /sensors`, `GET/PUT /sensors/{id}`, `GET /sensors/{id}/history` |
| Weather | `GET /weather/current`, `/weather/forecast`, `/weather/status` |
| Logs | `GET /logs/runs|events|emails` |
| Diagnostics | `GET /diagnostics/summary|components|incidents|security|translations` |
| Notifications | `GET /notifications`, `POST /notifications/{id}/ack` |
| Changes | `GET /stream`, `/changes` |
| Plug-ins | `GET /plugins`, `/plugins/{id}`, `/plugins/{id}/mobile`, `POST /plugins/{id}/actions/{action}` |
| Backups | `GET/POST /backups`, `GET /backups/{id}/download`, `POST /backups/{id}/restore` |
| Updates | `GET /updates`, `POST /updates/actions/check|apply|rollback` |
| System | `POST /system/actions/restart-ospy|reboot|poweroff` |
| Operations | `GET /operations/{id}` |

## Main resources

- `/overview` — one lightweight Home-screen snapshot.
- `/stations` — stations, master roles, live state and remaining time.
- `/stations/{id}/actions/start|stop` and `/stations/actions/stop-all`.
- `/programs`, `/programs/{id}/actions/run|stop`.
- `/run-once` and `/run-once/actions/start`.
- `/sensors`, `/sensors/{id}`, `/sensors/{id}/history`.
- `/weather/current`, `/weather/forecast`, `/weather/status`.
- `/logs/runs`, `/logs/events`, `/logs/emails`, with `offset` and `limit`.
- `/diagnostics/summary|components|incidents|security|translations`.
- `/notifications`, acknowledgement of one item or `all`.
- `/plugins`, plug-in health and optional mobile contributions.
- `/backups`, `/updates`, `/system/actions/*` and `/operations/{id}`.

State-changing calls use `POST` or `PUT` with a JSON object. OSPy applies the
same station and scheduler safety rules as the web interface. Stop All also
ends run-now and run-once scheduling and switches off the master relay.

## Detailed resource reference

### Overview

`GET /overview` is the first request after login or a long disconnection. It
returns the installation identity and version, scheduler/manual/rain state,
water-level adjustment, active stations and remaining time, cached Home weather
cards and the unread-notification count. It does not perform network weather
downloads. Optional subsystem failures do not discard the complete Home
snapshot: the affected value is empty or unavailable and `warnings` contains
stable `code`, `component` and diagnostic `message` fields. Clients should show
the warning without hiding the still-valid irrigation controls and state.

### Stations and master

| Method | Path | Scope |
| --- | --- | --- |
| GET | `/stations`, `/stations/{id}` | `read` |
| PUT | `/stations`, `/stations/{id}` | `configuration` |
| POST | `/stations/{id}/actions/start` or `stop` | `control` |
| POST | `/stations/actions/stop-all` | `control` |

Station JSON includes `id`, `legacy_index`, visible number, name, enabled and
running state, remaining seconds, master roles, rain behaviour, usage,
precipitation, capacity and ETo factor. Live state, number and identifiers are
read-only. Direct start is rejected for disabled or master outputs.

Stop All follows the web safety sequence: disable scheduler processing, clear
run-now and run-once state, finish the run log, clear physical outputs and
switch off the additional relay output. The action is audited.

Single-station configuration sends only fields that should change:

```json
{"name":"Front lawn","enabled":true,"ignore_rain":false,"usage":12.5}
```

Bulk configuration uses `{"stations":[{"id":"station-0",...}]}`. Unknown or
live-state fields are rejected instead of being silently stored.

### Programs

`GET /programs` and `/programs/{id}` return the OSPy type, `type_data`,
stations, calculated schedule and summary. `POST /programs` creates a program;
`PUT /programs/{id}` updates it and `DELETE` removes it. Creation requires
`name`, `stations`, `type` and `type_data`. To preserve every scheduling
variant, read a program of the intended type and send the same shape after
editing. `/programs/{id}/actions/run|stop` requires `control`.

Program creation example:

```json
{
  "name": "Morning lawn",
  "enabled": true,
  "stations": [0, 1],
  "type": 0,
  "type_data": [360, 30, 0, 0, [0, 1, 2, 3, 4]]
}
```

Program types and `type_data` are deliberately the same scheduling model as
OSPy. For custom programs, `start` may be an ISO 8601 date-time and `schedule`
contains the explicit schedule. Invalid station indices are discarded and an
invalid program shape returns `invalid_program`.

### Run-once

`GET /run-once` reads durations. `PUT /run-once` accepts seconds:

```json
{"stations":{"station-0":300,"station-1":600}}
```

Values are bounded to 24 hours. `POST /run-once/actions/start` rejects an empty
plan. Stop All cancels it.

### Sensors and graphs

`GET /sensors` and `/sensors/{id}` return the common identity, communication,
value, response, battery, RSSI, firmware and logging fields supplied by the
sensor type. `/sensors/{id}/history?offset=0&limit=100` returns bounded history
where available. If a legacy or temporarily unavailable sensor property raises
an error, the sensor and its remaining properties are still returned. That
property is `null` and `field_errors` identifies the field, stable error code
and diagnostic message. `PUT /sensors/{id}` changes only common safe fields: name,
enabled state, sample rate and log/e-mail/Home switches. Type-specific
calibration remains in the web interface.

History returns an array plus `offset`, `limit`, `total` and `has_more`
metadata. OSPy reads the existing bounded sensor graph data; the endpoint does
not start a fresh sensor measurement.

### Weather

- `/weather/current` — cached current provider data.
- `/weather/forecast` — cached Home forecast cards.
- `/weather/forecast?date=YYYY-MM-DD` — cached hourly provider data.
- `/weather/status` — provider, update time and configured location without
  credentials.

### Logs

`/logs/runs`, `/logs/events` and `/logs/emails` accept `offset` and `limit`
(`1..500`). Results are newest first. Metadata contains `total`, `has_more`,
`offset` and `limit`. Reads never clear a log.

### Diagnostics

`/diagnostics/summary`, `/components`, `/incidents`, `/security` and
`/translations` reuse the calculations shown by the OSPy Diagnostics page.
Clients must use status fields, not translated summary text, when choosing
colours or alerts.

### Notifications

`GET /notifications?unread=1&limit=100&cursor=ID` returns persistent
newest-first notifications. Acknowledge one with
`POST /notifications/{id}/ack` or all with `/notifications/all/ack`. The
bounded notification database is separate from authoritative OSPy settings.
Initial events include active rain protection and a stopped irrigation station.
Diagnostics errors are converted to notifications only after at least one
mobile device has been paired. The health calculation runs outside the
scheduler signal so notification work cannot delay irrigation.

## Live changes

`GET /api/v1/stream` is a Server-Sent Events endpoint. Clients reconnect using
`Last-Event-ID`. If SSE is unavailable, use `/changes?after={event_id}`. The
stream is replayable within a bounded in-memory window; the client should
refresh `/overview` after a long disconnect.

Events have `id`, `event`, `data` and `time`. The in-memory replay window is
bounded; after an event gap, reload the affected resource. Typical event names
are `stations.changed`, `station.start`, `station.stop`,
`conditions.changed`, `notification`, `plugin.action`,
`operation.completed` and `operation.failed`.

SSE frames follow the standard form:

```text
id: 42
event: stations.changed
data: {"sender":0,"details":{}}
```

If no event arrives during the wait, the server returns an SSE keep-alive.
Polling clients use the `meta.last_event_id` returned by `/changes`.

## Plug-ins

Every installed plug-in appears in `/plugins` with state, diagnostics and
`health()`. A plug-in may optionally declare `mobile.api_version` and action
names in `plugin.json`, then implement JSON-only functions:

```python
mobile_status()
mobile_cards()
mobile_settings_schema()
mobile_settings()
mobile_action(action, payload)
```

Only declared actions can be called. Arbitrary plug-in functions and HTML are
never exposed. Legacy plug-ins remain visible but simply report that no native
mobile contribution is available.

The manifest fragment is:

```json
{
  "mobile": {
    "api_version": 1,
    "actions": ["refresh", "reset-counter"]
  }
}
```

`GET /plugins` lists all installed plug-ins, run/enable state, compatibility,
health and mobile capabilities. `/plugins/{id}/mobile` returns only available
JSON contributions. `POST /plugins/{id}/actions/{declared_action}` rejects
actions absent from the manifest. Plug-ins cannot inject mobile HTML or call
arbitrary methods through the API.

## Backups, updates and system actions

These administrator operations return an operation identifier. Follow
`/operations/{id}` until it is completed or failed. Backup downloads are ZIP
files and retain the existing OSPy validation and restore protections. Update
actions require the running System Update plug-in. Restart, reboot and poweroff
are intentionally separate actions and require the `system` scope.

### Backup endpoints

- `GET /backups` lists retained archives.
- `POST /backups` starts creation.
- `GET /backups/{filename}/download` returns `application/zip`.
- `POST /backups/{filename}/restore` validates, stages and restores it, then
  schedules restart.

Existing ZIP path, checksum, size, schema and SQLite/shelve validation remains
authoritative. The mobile API does not weaken restore checks.

### Update and system endpoints

`GET /updates` returns System Update health. `/updates/actions/check|apply|
rollback` requires the running System Update plug-in. System actions are
`/system/actions/restart-ospy`, `/reboot` and `/poweroff`.

Long operations return HTTP `202` with an operation object. Poll
`GET /operations/{id}` until `status` is `completed` or `failed`; fields include
`kind`, `progress`, `result`, `error`, `created` and `updated`.

Creating a backup, restoring one and update actions execute on daemon workers,
so the HTTP handler does not block the scheduler. A completed operation does
not imply that a requested OSPy restart has already finished; after restart,
reconnect through `/server` and `/overview`.

## Client implementation checklist

1. Let the user verify `/server` before sending a password.
2. Require HTTPS for Internet-facing installations and clearly warn about HTTP.
3. Keep access tokens in memory and refresh tokens in OS-protected storage.
4. Support e-mail and TOTP 2FA challenges.
5. Request only necessary scopes and handle `403 insufficient_scope`.
6. Make dangerous actions explicit and confirm reboot, poweroff and restore.
7. Reconnect SSE with `Last-Event-ID`, then refresh Overview after a gap.
8. Never parse OSPy HTML or translated status sentences.
9. Do not log tokens, passwords, backup contents or provider credentials.
10. Revoke the paired device when an installation is removed from the app.

## API description and compatibility

The machine-readable description is `/api/v1/openapi.json`. Additive fields and
new endpoints may appear in API v1; existing meanings are not changed. A future
incompatible design will use `/api/v2`. Clients must ignore unknown JSON fields.

The OpenAPI document is discovery-oriented and does not replace the validation
rules in this reference. Additive resources, fields and event types may appear
in v1. Removing a field, changing its meaning or changing authentication
semantics requires a new major API path.
