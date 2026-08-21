# OSPy plug-in provider contract v1

`ospy.provider.v1` is the internal, read-only data contract shared by monitoring
plug-ins, Automation Rules and Irrigation Safety. It is additive: a plug-in can
continue to expose its existing pages, health diagnostics and Mobile API cards.

Provider plug-ins declare the contract in `plugin.json`:

```json
"provider": {"contract": "ospy.provider.v1"}
```

They implement `provider_capabilities()` and `provider_snapshot()`. Both return
JSON-safe dictionaries. A snapshot must use cached state and must not perform a
hardware read, start a worker, change settings or execute a control action.

## Stable identifiers and time

Identifiers and codes use lowercase ASCII letters, numbers, dots, hyphens and
underscores. They are never translated. User interfaces translate labels derived
from those identifiers. Timestamps are ISO-8601 UTC strings such as
`2026-08-21T12:00:00Z`; an unknown timestamp is `null`.

Provider and resource status is one of `ok`, `unavailable`, `stale`, `error` or
`disabled`. One failing provider cannot prevent snapshots from other providers.

## Capabilities

```json
{
  "contract": "ospy.provider.v1",
  "provider_id": "tank_monitor",
  "resource_types": ["tank"],
  "values": [
    {"id": "fill_percent", "quantity": "fill_ratio", "unit": "%", "value_type": "number"}
  ],
  "events": [{"code": "tank_monitor.measurement"}],
  "alerts": [{"code": "tank_monitor.sensor_error"}],
  "actions": []
}
```

A value descriptor fixes the `id`, physical `quantity`, canonical `unit` and
`value_type`. Value types are `number`, `integer`, `boolean` and `string`.
Actions are descriptors with a stable `id`, `risk` (`read_only`, `control` or
`safety`) and a JSON object named `parameters`. Stage 1 providers expose no
control actions.

## Snapshot

```json
{
  "contract": "ospy.provider.v1",
  "provider_id": "tank_monitor",
  "status": "ok",
  "observed_at": "2026-08-21T12:00:00Z",
  "resources": [{
    "id": "tank-1",
    "type": "tank",
    "status": "ok",
    "values": [{
      "id": "fill_percent",
      "quantity": "fill_ratio",
      "value": 72.5,
      "unit": "%",
      "value_type": "number",
      "quality": "measured",
      "observed_at": "2026-08-21T12:00:00Z"
    }],
    "alerts": []
  }],
  "events": [],
  "alerts": []
}
```

`value` may be `null` when no reading exists. Quality is `measured`, `derived`,
`estimated` or `unknown`. A provider may expose multiple resources, as Current
Loop Tanks Monitor does for its enabled channels.

Events contain `id`, `code`, `source`, `severity`, `occurred_at` and optional
JSON `data`. Alerts contain `id`, `code`, `severity`, `state`, `opened_at`, an
optional `updated_at` and optional JSON `context`. Severity is `info`, `warning`,
`error` or `critical`; alert state is `active`, `acknowledged` or `cleared`.

The core validates and detaches every response before returning it. Invalid or
non-finite values, wrong types, invalid timestamps and mismatched provider IDs
are rejected. `plugin_provider_snapshots()` isolates errors by provider.

## Stage 1 providers

- Water Meter: cached flow and accumulated volumes.
- Pressure Monitor: cached binary pressure presence and master state; it does
  not invent a pressure in bar or kPa.
- Water Tank Monitor: one ultrasonic tank with level, fill and volume.
- Current Loop Tanks Monitor: up to four enabled 4–20 mA tank channels.

