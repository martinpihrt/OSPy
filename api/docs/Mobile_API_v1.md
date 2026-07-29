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
| Home | `GET /overview`, `GET/PUT /irrigation` |
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

Clients should refresh this lightweight resource periodically while Home is
visible (the official Android client uses ten seconds), immediately after a
control action, and after an irrigation SSE event. The response's `updated`
value is the server-side snapshot time and should be shown as the last
successful refresh.

### Global irrigation controls

`GET /irrigation` returns `scheduler_enabled`, `manual_mode`, `rain_block`,
`rain_block_seconds`, `rain_delay` and the current `active_stations`.

`PUT /irrigation` requires the `control` scope and accepts one or more fields:

```json
{"scheduler_enabled":true}
```

```json
{"manual_mode":false,"rain_delay_hours":24}
```

The two mode fields must be JSON booleans. `rain_delay_hours` is clamped to
`0..8760`; zero clears all active rain-delay blocks, matching the web Home
control. A positive delay immediately applies the normal OSPy rain safety
rules. The response is the updated irrigation object. Unknown fields return
HTTP `422`. A client can therefore offer any duration in that range and use
`rain_block_seconds` from `GET /irrigation` or `GET /overview` for a live
countdown until the delay expires.

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
sensor type. They retain legacy raw fields and also provide a stable `display`
object containing one relevant typed reading, its unit, connection state,
formatted firmware, communication code and IP address. Mobile clients should
render `display` and reserve raw fields for advanced diagnostics.
`/sensors/{id}/history?offset=0&limit=100` returns bounded history
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

## Current v1 wire contracts and examples

This section documents the fields sent by the current API implementation
(`api_version` `1.0.0`). Examples omit fields that are not important to the
particular operation. Additive fields may be returned at any time, so clients
must ignore fields they do not recognize.

### Discovery response

Request:

```http
GET /api/v1/server
```

Response:

```json
{
  "data": {
    "instance_id": "8b32011d-d345-4af2-817d-c6150ed5c5ad",
    "name": "Home",
    "ospy_version": "3.0.312-beta",
    "release_date": "2026-07-29",
    "api_version": "1.0.0",
    "time": "2026-07-29T11:30:00+02:00",
    "authentication": {
      "type": "bearer",
      "access_token_seconds": 900,
      "two_factor_supported": true
    }
  },
  "meta": {"request_id": "req-..."}
}
```

The application should store `instance_id` as the server identity. The name,
address and OSPy version can change without creating a new installation.

### Login response

A successful `POST /auth/login` returns HTTP `201`:

```json
{
  "data": {
    "access_token": "short-lived-token",
    "expires_in": 900,
    "refresh_token": "rotating-long-lived-token",
    "refresh_expires_in": 2592000,
    "token_type": "Bearer",
    "role": "admin",
    "scopes": ["read", "control", "configuration", "plugins",
               "backup", "update", "system"],
    "device_id": "device-..."
  },
  "meta": {"request_id": "req-..."}
}
```

When another factor is required, HTTP `401` uses the stable error code
`two_factor_required`. For e-mail 2FA, `error.details.challenge_id` must be
included with the code in the repeated login request. Never persist the access
token as a password substitute; persist only the rotating refresh token in
protected storage.

### Home snapshot

Request:

```http
GET /api/v1/overview
Authorization: Bearer ACCESS_TOKEN
```

Response shape:

```json
{
  "data": {
    "instance": {
      "id": "8b32011d-d345-4af2-817d-c6150ed5c5ad",
      "name": "Home",
      "version": "3.0.312-beta"
    },
    "irrigation": {
      "scheduler_enabled": true,
      "manual_mode": false,
      "rain_block": false,
      "rain_block_seconds": 0,
      "rain_delay": null,
      "level_adjustment": 0.85,
      "active_stations": []
    },
    "weather": {
      "available": true,
      "cards": [],
      "provider": "CHMI ALADIN via Open-Meteo",
      "updated": "2026-07-29 11:01"
    },
    "notifications": {"unread": 0},
    "warnings": [],
    "updated": "2026-07-29T11:30:00+02:00"
  },
  "meta": {"request_id": "req-..."}
}
```

`rain_block` means that rain protection is currently blocking irrigation. It
does not mean merely that a rain-delay value or rain sensor exists.
`rain_block_seconds` is the non-negative time until the active block expires.
Each `active_stations` item has the same contract as an item from `/stations`.

### Station object and actions

```json
{
  "id": "station-0",
  "legacy_index": 0,
  "number": 1,
  "name": "Front lawn",
  "enabled": true,
  "running": true,
  "remaining_seconds": 275,
  "is_master": false,
  "is_master_two": false,
  "is_program_master": false,
  "activates_master": true,
  "activates_master_two": false,
  "ignore_rain": false,
  "usage": 12.5,
  "precipitation": 10.0,
  "capacity": 100.0,
  "eto_factor": 1.0
}
```

`remaining_seconds` is:

- `0` for a stopped station;
- a positive countdown for a scheduled/program run;
- `-1` when the output is running without a known end, for example after a
  direct manual API start.

Start or stop a station with an empty JSON body:

```http
POST /api/v1/stations/station-0/actions/start
Authorization: Bearer ACCESS_TOKEN
Content-Type: application/json

{}
```

The response is the updated station object. Start may return HTTP `409` with
`station_unavailable` for a disabled or master output. Stop All accepts `{}` at
`POST /stations/actions/stop-all` and returns
`{"data":{"stopped":true},"meta":{...}}`.

### Program and run-once responses

Program objects include:

| Field | Type | Meaning |
| --- | --- | --- |
| `id`, `legacy_index`, `number` | string/integer | Stable API ID and legacy/visible indices |
| `name`, `enabled` | string/boolean | User name and enabled state |
| `stations` | integer array | Zero-based station indices used by OSPy |
| `type`, `type_data` | integer/array | Native OSPy scheduling model |
| `manual`, `start`, `schedule` | mixed | Complete scheduling definition |
| `summary` | string | Human-readable summary; never use it for control logic |

`POST /programs/{id}/actions/run` and `/stop` accept `{}` and return:

```json
{"data":{"id":"program-0","action":"run","accepted":true},"meta":{...}}
```

`PUT /run-once` sends a mapping of typed station IDs to seconds. Values are
clamped to `0..86400`. The separate start call returns HTTP `202`.

### Sensor object, partial fields and history

The sensor list is a passive finite snapshot; reading it never starts a new
measurement. A typical object is:

```json
{
  "id": "sensor-0",
  "legacy_index": 0,
  "number": 1,
  "name": "Tank temperature",
  "enabled": true,
  "sens_type": 5,
  "com_type": 1,
  "last_read_value": 19.4,
  "last_response_datetime": "2026-07-29T11:28:31",
  "last_battery": 12.7,
  "rssi": 44,
  "fw": "1.19",
  "sample_rate": 60
}
```

For multi-value sensors, `last_read_value` remains the original sensor array.
The same response therefore includes a normalized block such as:

```json
{
  "display": {
    "type": "multi",
    "subtype": "ultrasonic",
    "communication": "wifi_lan",
    "reading": {"status":"ok","value":73,"unit":"cm"},
    "connected": true,
    "firmware": "1.19",
    "battery_unit": "V",
    "signal_unit": "%",
    "ip_address": "192.168.1.25"
  }
}
```

`display.reading.status` is `ok`, `pending`, `probe_error` or `unavailable`.
Binary readings additionally contain a stable `state`: `open`, `closed`,
`motion` or `no_motion`. Type and subtype codes include
`temperature_ds1` through `temperature_ds4`, `dry_contact`, `leak_detector`,
`moisture`, `motion`, `ultrasonic` and `soil_moisture`. Communication is
`wifi_lan`, `radio` or `unknown`. These are untranslated machine values; the
client provides localized labels.

Sensor types have different properties. Missing optional attributes may be
absent or `null`. `field_errors` is omitted when every available property was
read successfully. If reading one property fails, it contains:

```json
{
  "field": "battery",
  "code": "sensor_field_unavailable",
  "message": "TypeError: ..."
}
```

The remaining sensor and other sensors are still valid. A client must not retry
the complete list in a tight loop because of one `field_errors` entry.

History request and metadata:

```http
GET /api/v1/sensors/sensor-0/history?offset=0&limit=100
```

```json
{
  "data": [],
  "meta": {
    "offset": 0,
    "limit": 100,
    "total": 0,
    "has_more": false,
    "request_id": "req-..."
  }
}
```

### Weather, logs and diagnostics

`GET /weather/forecast` returns the cached Home forecast object, including
`available`, `cards`, `provider`, `provider_url` and `updated`. Card fields
currently include `time`, `temperature`, `precipitation`, `icon` and
`description`. Values intended for display can already contain units.
`GET /weather/forecast?date=2026-07-29` instead returns cached hourly provider
data for that date. Neither request downloads weather data synchronously.

Log entries preserve the OSPy log fields. Event entries normally contain
`date`, `time`, `subject`, `status`, `id`, `level` and `category`. `level` and
`category` are stable machine values; `subject` and `status` are display text
and may follow the selected OSPy language.

Diagnostic summary responses contain a stable top-level `status` and an
`items` array. Each item commonly supplies `id`, `title`, `status`, `summary`,
`details`, `solution`, `updated`, `link`, `confirmation_required`, `alert` and
`affects_summary`. Use only `status` (`ok`, `warning`, `error`, `critical` or
an explicitly documented additive value) for colours and decisions. Titles,
summaries, details and solutions are localized display text.

### Plug-in response

```json
{
  "id": "wind_monitor",
  "name": "Wind Speed Monitor",
  "version": "1.1.2",
  "enabled": true,
  "running": true,
  "health": {"status": "ok", "summary": "Wind monitoring is active."},
  "mobile": {
    "api_version": 1,
    "available": false,
    "methods": {
      "status": false,
      "cards": false,
      "settings_schema": false,
      "settings": false,
      "action": false
    },
    "actions": []
  }
}
```

The list shows installed plug-in packages only. Files and runtime data below
the plug-in root are not resources. A stopped plug-in can still be listed, but
calling one of its mobile functions returns an error. Mobile actions require
both a manifest declaration and the `plugins` scope.

### Notification and change cursors

`GET /notifications` returns an array in `data`. Metadata contains `unread`,
`next_cursor`, `has_more` and `request_id`. Pass the last `next_cursor` on the
next request. Acknowledgement changes server-side unread state; disabling
Android display notifications is a separate client preference and does not
acknowledge server notifications.

`GET /changes?after=42` returns all currently retained events after ID 42 and
sets `meta.last_event_id`. SSE delivers the same event objects. Event data is a
hint to refresh the affected resource, not a replacement for the authoritative
resource response.

### Asynchronous operation response

Backup creation, restore and update actions return HTTP `202`:

```json
{
  "data": {
    "id": "4a6a28f33c364a7cb5f458fe729d7964",
    "kind": "backup",
    "status": "pending",
    "progress": 0,
    "result": {},
    "error": "",
    "created": "2026-07-29T11:30:00+02:00",
    "updated": "2026-07-29T11:30:00+02:00"
  },
  "meta": {"request_id": "req-..."}
}
```

Poll the returned `id` as `operation_id` in
`GET /operations/{operation_id}`. Current states are `pending`, `running`, `completed` and
`failed`; clients should also tolerate additive intermediate states. A failed
operation keeps the polling HTTP request itself successful and reports its
reason in `data.error`.

### Validation error example

```json
{
  "error": {
    "code": "read_only_field",
    "message": "The station field cannot be changed through the mobile API.",
    "details": {"field": "running"},
    "request_id": "req-..."
  }
}
```

Client logic must branch on `error.code`, not on the English `message`. Show
the message to the user and include `request_id` in a support report.

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
