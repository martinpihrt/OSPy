"""Stable versioned JSON API used by native OSPy clients."""

import datetime
import json
import os
import threading
import time

import web

import plugins
from ospy import helpers, server, version
from ospy.backup import (
    apply_staged_restore, create_system_backup, list_system_backups,
    stage_restore, system_backup_path,
)
from ospy.log import log, logEM, logEV
from ospy.options import level_adjustments, options, rain_blocks
from ospy.programs import ProgramType, programs
from ospy.runonce import run_once
from ospy.sensors import sensors
from ospy.stations import stations
from ospy.weather import weather

from . import openapi
from .responses import (
    APIError, endpoint, json_body, query_bool, request_id, respond,
)
from .security import (
    current_identity, login, refresh, require_scope, verify_access_token,
)
from .store import mobile_store
from .stream import event_stream


API_VERSION = "1.0.0"
API_FEATURES = [
    "overview", "irrigation_control", "stations", "master", "programs",
    "schedule", "run_once", "sensors",
    "weather", "logs", "diagnostics", "notifications", "plugins",
    "backup", "update", "system", "sse",
]
_hooks_lock = threading.Lock()
_hooks_ready = False
_health_monitor_lock = threading.Lock()
_health_monitor_active = False
_health_problem_codes = set()


def _identity():
    return getattr(web.ctx, "api_v1_identity", None) or current_identity()


def _actor():
    identity = _identity()
    return identity.get("sub", "mobile")


def _remote_ip():
    return getattr(web.ctx, "ip", "-")


def _iso(value):
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    return value


def _safe_value(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe_value(item) for item in value]
    return str(value)


def _safe_attribute(value, key, default=None):
    try:
        return getattr(value, key)
    except Exception:
        return default


def _warning(code, component, message):
    return {
        "code": code,
        "component": component,
        "message": message,
    }


def _station_id(index):
    return "station-{}".format(index)


def _parse_id(value, prefix, count):
    text = str(value)
    if text.startswith(prefix + "-"):
        text = text[len(prefix) + 1:]
    try:
        index = int(text)
    except (TypeError, ValueError):
        raise APIError(404, "not_found", "The requested object does not exist.")
    if index < 0 or index >= count:
        raise APIError(404, "not_found", "The requested object does not exist.")
    return index


def _station_data(station):
    running = bool(station.active)
    remaining = int(station.remaining_seconds or 0)
    if running and remaining == 0:
        remaining = -1
    return {
        "id": _station_id(station.index),
        "legacy_index": station.index,
        "number": station.index + 1,
        "name": station.name,
        "enabled": bool(station.enabled),
        "running": running,
        "remaining_seconds": remaining,
        "is_master": bool(station.is_master),
        "is_master_two": bool(station.is_master_two),
        "is_program_master": bool(station.is_master_by_program),
        "activates_master": bool(station.activate_master),
        "activates_master_two": bool(station.activate_master_two),
        "ignore_rain": bool(station.ignore_rain),
        "usage": float(station.usage),
        "precipitation": float(station.precipitation),
        "capacity": float(station.capacity),
        "eto_factor": float(station.eto_factor),
    }


def _program_data(program):
    result = {
        "id": "program-{}".format(program.index),
        "legacy_index": program.index,
        "number": program.index + 1,
        "name": program.name,
        "enabled": bool(program.enabled),
        "stations": list(program.stations),
        "station_ids": [_station_id(index) for index in program.stations],
        "type": int(program.type),
        "type_name": ProgramType.NAMES.get(program.type, ""),
        "type_data": _safe_value(program.type_data),
        "summary": program.summary(),
        "schedule": _safe_value(program.schedule),
        "manual": bool(program.manual),
        "start": _iso(program.start),
    }
    result["station_details"] = [
        {
            "id": _station_id(index),
            "legacy_index": index,
            "number": index + 1,
            "name": stations[index].name,
        }
        for index in program.stations
        if 0 <= index < stations.count()
    ]
    result["editor"] = _program_editor(program)
    return result


def _program_editor(program):
    """Return a stable, labelled view of the native OSPy scheduling fields."""
    data = _safe_value(program.type_data)
    editor = {
        "schema_version": 1,
        "type": int(program.type),
        "type_name": ProgramType.NAMES.get(program.type, ""),
        "fields": {},
    }
    try:
        if program.type in (ProgramType.DAYS_SIMPLE, ProgramType.REPEAT_SIMPLE):
            editor["fields"] = {
                "start_minute": int(data[0]),
                "duration_minutes": int(data[1]),
                "pause_minutes": int(data[2]),
                "repeat_count": int(data[3]),
            }
            if program.type == ProgramType.DAYS_SIMPLE:
                editor["fields"]["days"] = [int(item) for item in data[4]]
            else:
                editor["fields"]["repeat_days"] = int(data[4])
                editor["fields"]["start_date"] = _iso(data[5])
        elif program.type == ProgramType.DAYS_ADVANCED:
            editor["fields"] = {
                "intervals": data[0],
                "days": [int(item) for item in data[1]],
            }
        elif program.type == ProgramType.REPEAT_ADVANCED:
            editor["fields"] = {
                "intervals": data[0],
                "repeat_days": int(data[1]),
                "start_date": _iso(data[2]),
            }
        elif program.type == ProgramType.WEEKLY_ADVANCED:
            editor["fields"] = {"intervals": data[0]}
        elif program.type == ProgramType.WEEKLY_WEATHER:
            editor["fields"] = {
                "irrigation_min": int(data[0]),
                "irrigation_max": int(data[1]),
                "run_max": int(data[2]),
                "pause_minutes": int(data[3]),
                "priority_intervals": data[4],
            }
        else:
            editor["fields"] = {
                "start": _iso(program.start),
                "modulo": int(getattr(program, "modulo", 0)),
                "manual": bool(program.manual),
                "intervals": _safe_value(program.schedule),
            }
    except (IndexError, TypeError, ValueError):
        editor["valid"] = False
        editor["fields"] = {}
    else:
        editor["valid"] = True
    return editor


def _timeline_item(interval, now):
    station_index = int(interval.get("station", -1))
    start = interval.get("start")
    end = interval.get("end")
    active = interval.get("active")
    blocked = interval.get("blocked", False)
    if blocked:
        state = "blocked"
    elif active is True:
        state = "running"
    elif isinstance(end, datetime.datetime) and end <= now:
        state = "completed"
    else:
        state = "upcoming"
    duration = 0
    remaining = 0
    progress = 0.0
    if isinstance(start, datetime.datetime) and isinstance(end, datetime.datetime):
        duration = max(0, int((end - start).total_seconds()))
        if state == "running":
            remaining = max(0, int((end - now).total_seconds()))
            if duration:
                progress = min(
                    1.0, max(0.0, (now - start).total_seconds() / duration)
                )
    station = stations[station_index] if 0 <= station_index < stations.count() else None
    return {
        "id": str(interval.get("uid", "")),
        "state": state,
        "start": _iso(start),
        "end": _iso(end),
        "original_start": _iso(interval.get("original_start")),
        "duration_seconds": duration,
        "remaining_seconds": remaining,
        "progress": round(progress, 4),
        "blocked": bool(blocked),
        "blocked_reason": str(blocked) if blocked not in (True, False) else "",
        "manual": bool(interval.get("manual", False)),
        "program_id": (
            "program-{}".format(interval.get("program"))
            if isinstance(interval.get("program"), int) and interval.get("program") >= 0
            else None
        ),
        "program_name": str(interval.get("program_name", "")),
        "station_id": _station_id(station_index) if station is not None else None,
        "station_number": station_index + 1 if station is not None else None,
        "station_name": station.name if station is not None else "",
        "is_master": bool(station and (station.is_master or station.is_master_two)),
    }


def _sensor_data(sensor):
    keys = (
        "name", "enabled", "manufacturer", "sens_type", "multi_type",
        "com_type", "last_read_value",
        "last_response", "last_response_datetime", "last_battery", "rssi",
        "response", "fw", "sample_rate", "log_samples", "log_event",
        "send_email", "show_in_footer", "ip_address", "mac_address",
        "last_voltage",
    )
    result = {
        "id": "sensor-{}".format(_safe_attribute(sensor, "index", 0)),
        "legacy_index": _safe_attribute(sensor, "index", 0),
        "number": _safe_attribute(sensor, "index", 0) + 1,
    }
    field_errors = []
    for key in keys:
        try:
            result[key] = _safe_value(getattr(sensor, key))
        except AttributeError:
            continue
        except Exception as error:
            result[key] = None
            field_errors.append({
                "field": key,
                "code": "sensor_field_unavailable",
                "message": "{}: {}".format(type(error).__name__, error),
            })
    result["enabled"] = bool(result.get("enabled"))
    result["response"] = bool(result.get("response"))
    if field_errors:
        result["field_errors"] = field_errors
    result["display"] = _sensor_display_data(result)
    return result


_SENSOR_TYPES = (
    "none", "dry_contact", "leak_detector", "moisture", "motion",
    "temperature", "multi", "multi_contact",
)
_MULTI_SENSOR_TYPES = (
    "temperature_ds1", "temperature_ds2", "temperature_ds3",
    "temperature_ds4", "dry_contact", "leak_detector", "moisture",
    "motion", "ultrasonic", "soil_moisture",
)
_SENSOR_COMMUNICATION = ("wifi_lan", "radio")


def _sensor_firmware_version(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    digits = str(number).zfill(3)
    return "{}.{}".format(digits[0], digits[1:])


def _sensor_reading(result):
    values = result.get("last_read_value")
    sensor_type = result.get("sens_type")
    multi_type = result.get("multi_type")
    unit = ""
    state = ""
    index = None

    if sensor_type == 1:
        index, state = 4, "contact"
    elif sensor_type == 2:
        index, unit = 5, "l/s"
    elif sensor_type == 3:
        index, unit = 6, "%"
    elif sensor_type == 4:
        index, state = 7, "motion"
    elif sensor_type == 5:
        index, unit = 0, str(_safe_attribute(options, "temp_unit", "C"))
    elif sensor_type == 6 and isinstance(multi_type, int):
        if 0 <= multi_type <= 3:
            index, unit = multi_type, str(
                _safe_attribute(options, "temp_unit", "C")
            )
        elif multi_type == 4:
            index, state = 4, "contact"
        elif multi_type == 5:
            index, unit = 5, "l/s"
        elif multi_type == 6:
            index, unit = 6, "%"
        elif multi_type == 7:
            index, state = 7, "motion"
        elif multi_type == 8:
            index, unit = 8, "cm"

    if not isinstance(values, list) or index is None or index >= len(values):
        return {"status": "unavailable", "value": None, "unit": unit}
    value = values[index]
    if value == "":
        return {"status": "pending", "value": None, "unit": unit}
    if value == -127 or value == -127.0:
        return {"status": "probe_error", "value": value, "unit": unit}
    reading = {"status": "ok", "value": _safe_value(value), "unit": unit}
    try:
        numeric_state = int(value)
    except (TypeError, ValueError):
        numeric_state = None
    if state == "contact" and numeric_state is not None:
        reading["state"] = "closed" if numeric_state == 1 else "open"
    elif state == "motion" and numeric_state is not None:
        reading["state"] = "motion" if numeric_state == 1 else "no_motion"
    return reading


def _sensor_display_data(result):
    sensor_type = result.get("sens_type")
    multi_type = result.get("multi_type")
    communication = result.get("com_type")
    type_code = (
        _SENSOR_TYPES[sensor_type]
        if isinstance(sensor_type, int) and
        0 <= sensor_type < len(_SENSOR_TYPES)
        else "unknown"
    )
    subtype_code = (
        _MULTI_SENSOR_TYPES[multi_type]
        if type_code == "multi" and isinstance(multi_type, int) and
        0 <= multi_type < len(_MULTI_SENSOR_TYPES)
        else ""
    )
    communication_code = (
        _SENSOR_COMMUNICATION[communication]
        if isinstance(communication, int) and
        0 <= communication < len(_SENSOR_COMMUNICATION)
        else "unknown"
    )
    address = result.get("ip_address")
    return {
        "type": type_code,
        "subtype": subtype_code,
        "communication": communication_code,
        "reading": _sensor_reading(result),
        "connected": bool(result.get("response")),
        "firmware": _sensor_firmware_version(result.get("fw")),
        "battery_unit": "V",
        "signal_unit": "%" if result.get("manufacturer") == 0 else "dBm",
        "ip_address": (
            ".".join(str(part) for part in address)
            if isinstance(address, list) and len(address) == 4 else ""
        ),
    }


def _sensor_snapshot():
    """Return a finite, passive snapshot of the configured sensors.

    The legacy sensor collection implements ``__getitem__`` but returns
    ``None`` instead of raising ``IndexError`` after its last item.  Iterating
    over that object directly therefore never terminates.
    """
    getter = getattr(sensors, "get", None)
    if callable(getter):
        return list(getter() or [])
    return list(sensors)


def _paginate(items):
    query = web.input()
    try:
        limit = max(1, min(500, int(query.get("limit", 100))))
        offset = max(0, int(query.get("offset", 0)))
    except ValueError:
        raise APIError(422, "invalid_pagination", "Pagination values must be integers.")
    total = len(items)
    return items[offset:offset + limit], {
        "offset": offset,
        "limit": limit,
        "total": total,
        "has_more": offset + limit < total,
    }


def _stop_all():
    from ospy import outputs
    options.scheduler_enabled = False
    programs.run_now_program = None
    run_once.clear()
    log.finish_run(None)
    stations.clear()
    outputs.relay_output = False
    event_stream.publish("irrigation.stop_all", {"actor": _actor()})
    logEV.save_events_log(
        _("Irrigation stopped through mobile API"),
        _("API user {} stopped all stations and active programs from IP {}.").format(
            _actor(), _remote_ip()
        ),
        level="warning", category="irrigation",
    )


def _irrigation_data():
    try:
        rain_block_seconds = max(0, int(rain_blocks.seconds_left()))
    except Exception:
        rain_block_seconds = 0
    active = []
    for station in stations:
        try:
            if station.active:
                active.append(_station_data(station))
        except Exception:
            continue
    return {
        "scheduler_enabled": bool(_safe_attribute(
            options, "scheduler_enabled", False
        )),
        "manual_mode": bool(_safe_attribute(options, "manual_mode", False)),
        "rain_block": rain_block_seconds > 0,
        "rain_block_seconds": rain_block_seconds,
        "rain_delay": _safe_value(_safe_attribute(options, "rain_delay", None)),
        "active_stations": active,
    }


def _required_boolean(payload, key):
    value = payload.get(key)
    if not isinstance(value, bool):
        raise APIError(
            422, "invalid_irrigation_setting",
            "{} must be a JSON boolean.".format(key),
        )
    return value


def _notification(event_type, severity, code, title, message, data=None):
    notification_id = mobile_store.add_notification(
        event_type, severity, code, title, message, data or {}
    )
    event_stream.publish("notification", {
        "id": notification_id,
        "type": event_type,
        "severity": severity,
        "code": code,
        "title": title,
        "message": message,
        "data": data or {},
    })


def _start_operation(kind, worker):
    operation_id = mobile_store.create_operation(kind)

    def run():
        mobile_store.update_operation(operation_id, "running", 5)
        try:
            result = worker()
            mobile_store.update_operation(
                operation_id, "completed", 100, _safe_value(result or {})
            )
            event_stream.publish("operation.completed", {
                "id": operation_id, "kind": kind,
            })
        except Exception as error:
            mobile_store.update_operation(
                operation_id, "failed", 100, error=str(error)
            )
            event_stream.publish("operation.failed", {
                "id": operation_id, "kind": kind, "error": str(error),
            })

    thread = threading.Thread(
        target=run, name="OSPy API operation {}".format(kind)
    )
    thread.daemon = True
    thread.start()
    return mobile_store.operation(operation_id)


def _connect_hooks():
    global _hooks_ready
    with _hooks_lock:
        if _hooks_ready:
            return
        from ospy.stations import (
            master_one_off, master_one_on, master_two_off, master_two_on,
            station_clear, station_off, station_on, zone_change,
        )
        from ospy.scheduler import (
            core_30_sec_tick,
            internet_available, internet_not_available, rain_active,
            rain_delay_remove, rain_delay_set, rain_not_active,
        )

        def publish_station(sender=None, **kwargs):
            event_stream.publish("stations.changed", {
                "sender": _safe_value(sender),
                "details": _safe_value(kwargs),
            })

        for signal in (
                zone_change, master_one_on, master_one_off, master_two_on,
                master_two_off, station_on, station_off, station_clear):
            signal.connect(publish_station, weak=False)

        def publish_condition(sender=None, **kwargs):
            name = getattr(sender, "name", None) or str(sender or "")
            event_stream.publish("conditions.changed", {
                "sender": name, "details": _safe_value(kwargs),
            })

        for signal in (
                rain_active, rain_not_active, rain_delay_set,
                rain_delay_remove, internet_available, internet_not_available):
            signal.connect(publish_condition, weak=False)

        def notify_rain(sender=None, **kwargs):
            _notification(
                "rain", "warning", "rain_active", _("Rain is active"),
                _("OSPy is applying the configured rain protection."),
                {"details": _safe_value(kwargs)},
            )

        rain_active.connect(notify_rain, weak=False)

        def notify_station_finished(sender=None, **kwargs):
            try:
                station = stations[int(sender)]
                if station.is_master or station.is_master_two:
                    return
                title = _("Irrigation completed")
                message = _("Station {} has stopped.").format(station.name)
                data = {"station": _station_data(station)}
            except Exception:
                title = _("Irrigation state changed")
                message = _("An irrigation output has stopped.")
                data = {"sender": _safe_value(sender)}
            _notification(
                "irrigation", "info", "station_stopped", title, message, data
            )

        station_off.connect(notify_station_finished, weak=False)

        def schedule_health_check(sender=None, **kwargs):
            global _health_monitor_active
            with _health_monitor_lock:
                if _health_monitor_active:
                    return
                _health_monitor_active = True

            def check():
                global _health_monitor_active, _health_problem_codes
                try:
                    if not any(
                            item.get("revoked") is None
                            for item in mobile_store.devices()):
                        return
                    from ospy.webpages import _system_health_data
                    health = _system_health_data()
                    current = set()
                    for item in health.get("items", []):
                        if item.get("status") != "error" or not item.get("alert", True):
                            continue
                        code = str(item.get("id", "diagnostics"))
                        current.add(code)
                        if code not in _health_problem_codes:
                            _notification(
                                "diagnostics", "error", code,
                                str(item.get("title", _("OSPy diagnostics"))),
                                str(item.get(
                                    "summary",
                                    _("A system problem was detected."),
                                )),
                                {
                                    "details": _safe_value(item.get("details", "")),
                                    "solution": _safe_value(item.get("solution", "")),
                                    "link": item.get("link", "/diagnostics"),
                                },
                            )
                    _health_problem_codes = current
                finally:
                    with _health_monitor_lock:
                        _health_monitor_active = False

            worker = threading.Thread(
                target=check, name="OSPy API health notification"
            )
            worker.daemon = True
            worker.start()

        core_30_sec_tick.connect(schedule_health_check, weak=False)
        _hooks_ready = True


class Root(object):
    @endpoint
    def GET(self):
        return respond({
            "name": "OSPy Mobile API",
            "version": API_VERSION,
            "documentation": "/help#mobile-api",
            "openapi": "/api/v1/openapi.json",
        })


class ServerInfo(object):
    @endpoint
    def GET(self):
        return respond({
            "instance_id": mobile_store.instance_id(),
            "name": getattr(options, "name", "OSPy"),
            "ospy_version": version.ver_str,
            "release_date": version.ver_date,
            "api_version": API_VERSION,
            "time": datetime.datetime.now().astimezone().isoformat(),
            "authentication": {
                "type": "bearer",
                "access_token_seconds": 900,
                "two_factor_supported": True,
            },
        })


class Capabilities(object):
    @endpoint
    def GET(self):
        return respond({
            "api_version": API_VERSION,
            "features": API_FEATURES,
            "stream": {"sse": "/api/v1/stream", "polling": "/api/v1/changes"},
            "roles": ["public", "user", "admin"],
            "plugin_mobile_api": 1,
        })


class OpenAPI(object):
    @endpoint
    def GET(self):
        web.header("Content-Type", "application/json; charset=utf-8")
        web.header("Cache-Control", "no-store")
        web.header("X-Content-Type-Options", "nosniff")
        web.header("X-Request-ID", request_id())
        return json.dumps(
            openapi.document(), ensure_ascii=False, separators=(",", ":")
        )


class Login(object):
    @endpoint
    def POST(self):
        return respond(login(json_body()), status=201)


class Refresh(object):
    @endpoint
    def POST(self):
        payload = json_body()
        return respond(refresh(payload.get("refresh_token", "")))


class Logout(object):
    @endpoint
    @require_scope("read")
    def POST(self):
        identity = _identity()
        mobile_store.revoke_refresh_token(identity["sid"])
        return respond({"revoked": True})


class Devices(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        identity = _identity()
        return respond(mobile_store.devices(
            None if identity["role"] == "admin" else identity["sub"]
        ))


class Device(object):
    @endpoint
    @require_scope("read")
    def DELETE(self, device_id):
        identity = _identity()
        allowed = {
            item["id"] for item in mobile_store.devices(
                None if identity["role"] == "admin" else identity["sub"]
            )
        }
        if device_id not in allowed:
            raise APIError(404, "not_found", "The paired device does not exist.")
        mobile_store.revoke_device(device_id)
        return respond({"revoked": True, "device_id": device_id})


class Overview(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        warnings = []
        active = []
        try:
            rain_block_seconds = max(0, int(rain_blocks.seconds_left()))
        except Exception as error:
            rain_block_seconds = 0
            warnings.append(_warning(
                "rain_status_unavailable",
                "irrigation",
                "{}: {}".format(type(error).__name__, error),
            ))
        for item in stations:
            try:
                if item.active:
                    active.append(_station_data(item))
            except Exception as error:
                warnings.append(_warning(
                    "station_status_unavailable",
                    "stations",
                    "{}: {}".format(type(error).__name__, error),
                ))
        try:
            forecast = weather.get_home_forecast()
        except Exception as error:
            forecast = {
                "available": False,
                "cards": [],
                "provider": "",
                "updated": None,
            }
            warnings.append(_warning(
                "weather_unavailable",
                "weather",
                "{}: {}".format(type(error).__name__, error),
            ))
        try:
            adjustment = level_adjustments.total_adjustment()
        except Exception as error:
            adjustment = None
            warnings.append(_warning(
                "level_adjustment_unavailable",
                "irrigation",
                "{}: {}".format(type(error).__name__, error),
            ))
        return respond({
            "instance": {
                "id": mobile_store.instance_id(),
                "name": _safe_attribute(options, "name", "OSPy"),
                "version": version.ver_str,
            },
            "irrigation": {
                "scheduler_enabled": bool(_safe_attribute(
                    options, "scheduler_enabled", False
                )),
                "manual_mode": bool(_safe_attribute(
                    options, "manual_mode", False
                )),
                "rain_block": rain_block_seconds > 0,
                "rain_block_seconds": rain_block_seconds,
                "rain_delay": _safe_value(_safe_attribute(
                    options, "rain_delay", None
                )),
                "level_adjustment": adjustment,
                "active_stations": active,
            },
            "weather": forecast,
            "notifications": {
                "unread": mobile_store.unread_notification_count(),
            },
            "warnings": warnings,
            "updated": datetime.datetime.now().astimezone().isoformat(),
        })


class Irrigation(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        return respond(_irrigation_data())

    @endpoint
    @require_scope("control")
    def PUT(self):
        payload = json_body()
        allowed = {
            "scheduler_enabled", "manual_mode", "rain_delay_hours",
        }
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise APIError(
                422, "unknown_irrigation_setting",
                "The irrigation setting is not supported.",
                {"fields": unknown},
            )
        if not payload:
            raise APIError(
                422, "empty_irrigation_settings",
                "At least one irrigation setting is required.",
            )

        changed = {}
        if "scheduler_enabled" in payload:
            value = _required_boolean(payload, "scheduler_enabled")
            options.scheduler_enabled = value
            changed["scheduler_enabled"] = value
        if "manual_mode" in payload:
            value = _required_boolean(payload, "manual_mode")
            options.manual_mode = value
            changed["manual_mode"] = value
        if "rain_delay_hours" in payload:
            hours = payload["rain_delay_hours"]
            if isinstance(hours, bool) or not isinstance(hours, (int, float)):
                raise APIError(
                    422, "invalid_rain_delay",
                    "rain_delay_hours must be a number.",
                )
            hours = max(0.0, min(24.0 * 365.0, float(hours)))
            if hours == 0:
                rain_blocks.clear()
            options.rain_block = (
                datetime.datetime.now() + datetime.timedelta(hours=hours)
            )
            helpers.stop_onrain()
            changed["rain_delay_hours"] = hours

        event_stream.publish("irrigation.settings_changed", changed)
        logEV.save_events_log(
            _("Irrigation settings changed through mobile API"),
            _("API user {} changed irrigation settings from IP {}: {}.").format(
                _actor(), _remote_ip(), ", ".join(sorted(changed))
            ),
            level="info", category="irrigation",
        )
        return respond(_irrigation_data())


class Stations(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        return respond([_station_data(item) for item in stations])

    @endpoint
    @require_scope("configuration")
    def PUT(self):
        payload = json_body()
        updates = payload.get("stations")
        if not isinstance(updates, list):
            raise APIError(422, "invalid_stations", "Stations must be an array.")
        changed = []
        for item in updates:
            if not isinstance(item, dict) or "id" not in item:
                raise APIError(422, "invalid_station", "Each station requires an id.")
            index = _parse_id(item["id"], "station", stations.count())
            _update_station(stations[index], item)
            changed.append(_station_data(stations[index]))
        return respond(changed)


class Station(object):
    @endpoint
    @require_scope("read")
    def GET(self, station_id):
        index = _parse_id(station_id, "station", stations.count())
        return respond(_station_data(stations[index]))

    @endpoint
    @require_scope("configuration")
    def PUT(self, station_id):
        index = _parse_id(station_id, "station", stations.count())
        _update_station(stations[index], json_body())
        event_stream.publish("station.configured", _station_data(stations[index]))
        return respond(_station_data(stations[index]))


class StationAction(object):
    @endpoint
    @require_scope("control")
    def POST(self, station_id, action):
        index = _parse_id(station_id, "station", stations.count())
        station = stations[index]
        if action == "start":
            if not station.enabled or station.is_master or station.is_master_two:
                raise APIError(409, "station_unavailable", "This station cannot be started directly.")
            stations.activate(index)
        elif action == "stop":
            stations.deactivate(index)
        else:
            raise APIError(404, "unknown_action", "The station action is not supported.")
        event_stream.publish("station." + action, _station_data(station))
        if action == "start":
            event_title = _("Station start through mobile API")
            event_status = _(
                "API user {} requested start for station {} from IP {}."
            ).format(_actor(), station.name, _remote_ip())
        else:
            event_title = _("Station stop through mobile API")
            event_status = _(
                "API user {} requested stop for station {} from IP {}."
            ).format(_actor(), station.name, _remote_ip())
        logEV.save_events_log(
            event_title,
            event_status,
            level="info", category="irrigation",
        )
        return respond(_station_data(station))


class StopAll(object):
    @endpoint
    @require_scope("control")
    def POST(self):
        _stop_all()
        return respond({"stopped": True})


class Programs(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        return respond([_program_data(item) for item in programs])

    @endpoint
    @require_scope("configuration")
    def POST(self):
        payload = json_body()
        program = programs.create_program()
        _update_program(program, payload, require_schedule=True)
        programs.add_program(program)
        event_stream.publish("program.created", _program_data(program))
        return respond(_program_data(program), status=201)


class Program(object):
    @endpoint
    @require_scope("read")
    def GET(self, program_id):
        index = _parse_id(program_id, "program", programs.count())
        return respond(_program_data(programs[index]))

    @endpoint
    @require_scope("configuration")
    def PUT(self, program_id):
        index = _parse_id(program_id, "program", programs.count())
        _update_program(programs[index], json_body(), require_schedule=False)
        event_stream.publish("program.configured", _program_data(programs[index]))
        return respond(_program_data(programs[index]))

    @endpoint
    @require_scope("configuration")
    def DELETE(self, program_id):
        index = _parse_id(program_id, "program", programs.count())
        removed = _program_data(programs[index])
        programs.remove_program(index)
        event_stream.publish("program.deleted", removed)
        return respond({"deleted": removed["id"]})


class ProgramAction(object):
    @endpoint
    @require_scope("control")
    def POST(self, program_id, action):
        index = _parse_id(program_id, "program", programs.count())
        if action == "run":
            programs.run_now(index)
        elif action == "stop":
            programs.run_now_program = None
            log.finish_run(None)
            stations.clear()
        else:
            raise APIError(404, "unknown_action", "The program action is not supported.")
        event_stream.publish("program." + action, {"id": "program-{}".format(index)})
        return respond({"id": "program-{}".format(index), "action": action, "accepted": True})


class RunOnce(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        values = getattr(run_once, "_station_seconds", {})
        return respond({
            "stations": {
                _station_id(index): int(seconds)
                for index, seconds in values.items()
            }
        })

    @endpoint
    @require_scope("control")
    def PUT(self):
        values = json_body().get("stations", {})
        if not isinstance(values, dict):
            raise APIError(422, "invalid_stations", "Stations must be an object.")
        parsed = {}
        for key, value in values.items():
            index = _parse_id(key, "station", stations.count())
            try:
                seconds = int(value)
            except (TypeError, ValueError):
                raise APIError(422, "invalid_duration", "Station durations must be seconds.")
            parsed[index] = max(0, min(24 * 60 * 60, seconds))
        run_once.set(parsed)
        return respond({"stations": {_station_id(k): v for k, v in parsed.items()}})


class RunOnceStart(object):
    @endpoint
    @require_scope("control")
    def POST(self):
        values = getattr(run_once, "_station_seconds", {})
        if not any(value > 0 for value in values.values()):
            raise APIError(409, "empty_run_once", "No run-once duration is configured.")
        options.scheduler_enabled = True
        event_stream.publish("run_once.started", {
            "stations": {_station_id(k): v for k, v in values.items()}
        })
        return respond({"accepted": True}, status=202)


class Sensors(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        return respond([_sensor_data(item) for item in _sensor_snapshot()])


class Sensor(object):
    @endpoint
    @require_scope("read")
    def GET(self, sensor_id):
        index = _parse_id(sensor_id, "sensor", sensors.count())
        return respond(_sensor_data(sensors[index]))

    @endpoint
    @require_scope("configuration")
    def PUT(self, sensor_id):
        index = _parse_id(sensor_id, "sensor", sensors.count())
        payload = json_body()
        allowed = {
            "name", "enabled", "sample_rate", "log_samples", "log_event",
            "send_email", "show_in_footer",
        }
        for key, value in payload.items():
            if key not in allowed:
                raise APIError(
                    422, "read_only_field",
                    "The sensor field cannot be changed through the mobile API.",
                    {"field": key},
                )
            setattr(sensors[index], key, value)
        event_stream.publish("sensor.configured", _sensor_data(sensors[index]))
        return respond(_sensor_data(sensors[index]))


class SensorHistory(object):
    @endpoint
    @require_scope("read")
    def GET(self, sensor_id):
        index = _parse_id(sensor_id, "sensor", sensors.count())
        sensor = sensors[index]
        values = []
        data_root = os.path.abspath(os.environ.get(
            "OSPY_DATA_DIR", os.path.join("ospy", "data")
        ))
        graph_path = os.path.join(
            data_root, "sensors", str(index), "logs", "graph", "graph.json"
        )
        if (
                os.path.isfile(graph_path) and
                os.path.getsize(graph_path) <= 32 * 1024 * 1024):
            try:
                with open(graph_path, "r", encoding="utf-8") as source:
                    candidate = json.load(source)
                if isinstance(candidate, list):
                    values = [_safe_value(item) for item in candidate]
            except (OSError, ValueError):
                values = []
        for name in ("log", "samples", "history", "sensor_log"):
            if values:
                break
            candidate = getattr(sensor, name, None)
            if isinstance(candidate, list):
                values = [_safe_value(item) for item in candidate]
                break
        page, meta = _paginate(values)
        return respond(page, meta=meta)


class WeatherCurrent(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        return respond(_safe_value(weather.get_current_data()))


class WeatherForecast(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        query = web.input()
        if query.get("date"):
            try:
                day = datetime.datetime.strptime(query.date, "%Y-%m-%d")
            except ValueError:
                raise APIError(422, "invalid_date", "Use an ISO date in YYYY-MM-DD form.")
            return respond(_safe_value(weather.get_hourly_data(day)))
        return respond(_safe_value(weather.get_home_forecast()))


class WeatherStatus(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        home = weather.get_home_forecast()
        return respond({
            "provider": home.get("provider", ""),
            "provider_url": home.get("provider_url", ""),
            "updated": home.get("updated", ""),
            "location": {
                "name": getattr(options, "location", ""),
                "latitude": getattr(options, "latitude", None),
                "longitude": getattr(options, "longitude", None),
            },
        })


class Logs(object):
    @endpoint
    @require_scope("read")
    def GET(self, kind):
        if kind == "runs":
            items = log.finished_runs()
            now = datetime.datetime.now()
            normalized = [
                _timeline_item(item, now)
                for item in reversed(items)
                if isinstance(item, dict)
            ]
        elif kind == "events":
            items = logEV.finished_events()
            normalized = [_safe_value(item) for item in reversed(items)]
        elif kind == "emails":
            items = logEM.finished_email()
            normalized = [_safe_value(item) for item in reversed(items)]
        else:
            raise APIError(404, "unknown_log", "The requested log does not exist.")
        page, meta = _paginate(normalized)
        return respond(page, meta=meta)


class Schedule(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        from ospy.scheduler import combined_schedule

        values = web.input(date=None, hours=None)
        now = datetime.datetime.now()
        if values.date:
            try:
                selected = (
                    now.date()
                    if str(values.date).lower() == "today"
                    else datetime.date.fromisoformat(str(values.date))
                )
            except ValueError:
                raise APIError(
                    422, "invalid_date", "The schedule date is not valid."
                )
            start = datetime.datetime.combine(selected, datetime.time.min)
            end = start + datetime.timedelta(days=1)
        else:
            try:
                hours = int(values.hours or 24)
            except (TypeError, ValueError):
                raise APIError(
                    422, "invalid_hours", "The schedule range is not valid."
                )
            hours = max(1, min(168, hours))
            start = now
            end = start + datetime.timedelta(hours=hours)
        # ``combined_schedule`` also contains the complete finished-run log
        # while the requested range crosses the current time.  Filter every
        # returned interval here so the mobile API can never leak old history
        # into a current/day timeline.
        intervals = []
        for interval in combined_schedule(start, end):
            if not isinstance(interval, dict):
                continue
            interval_start = interval.get("start")
            interval_end = interval.get("end")
            if not isinstance(interval_start, datetime.datetime):
                continue
            if not isinstance(interval_end, datetime.datetime):
                interval_end = interval_start
            if interval_start < end and interval_end > start:
                intervals.append(interval)
        items = [_timeline_item(interval, now) for interval in intervals]
        items.sort(key=lambda item: item.get("start") or "")
        return respond({
            "from": _iso(start),
            "to": _iso(end),
            "updated": _iso(now),
            "items": items,
        })


class Diagnostics(object):
    @endpoint
    @require_scope("read")
    def GET(self, section):
        from ospy import webpages
        providers = {
            "summary": webpages._diagnostics_data,
            "components": webpages._system_health_data,
            "incidents": webpages._incident_history_data,
            "security": webpages._security_health_data,
        }
        if section == "translations":
            provider = getattr(webpages, "_translation_health_data", None)
            if provider:
                return respond(_safe_value(provider()))
            return respond([])
        if section not in providers:
            raise APIError(404, "unknown_diagnostics_section", "The diagnostics section does not exist.")
        return respond(_safe_value(providers[section]()))


class Notifications(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        query = web.input()
        try:
            cursor = int(query.get("cursor", 0) or 0)
            limit = max(1, min(200, int(query.get("limit", 100))))
        except ValueError:
            raise APIError(422, "invalid_pagination", "Pagination values must be integers.")
        page = mobile_store.notifications(
            cursor=cursor or None, limit=limit,
            unread=query_bool("unread", False),
        )
        return respond(page["items"], meta={
            "unread": mobile_store.unread_notification_count(),
            "next_cursor": page["next_cursor"],
            "has_more": page["has_more"],
        })


class NotificationAck(object):
    @endpoint
    @require_scope("read")
    def POST(self, notification_id):
        if notification_id == "all":
            mobile_store.acknowledge_notification()
        else:
            try:
                mobile_store.acknowledge_notification(int(notification_id))
            except ValueError:
                raise APIError(404, "not_found", "The notification does not exist.")
        return respond({
            "acknowledged": True,
            "unread": mobile_store.unread_notification_count(),
        })


class Changes(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        try:
            after = int(web.input().get("after", 0) or 0)
        except ValueError:
            raise APIError(422, "invalid_cursor", "The event cursor must be an integer.")
        events = event_stream.after(after)
        return respond(events, meta={
            "last_event_id": events[-1]["id"] if events else after,
        })


class Stream(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        try:
            after = int(
                web.ctx.env.get("HTTP_LAST_EVENT_ID", "") or
                web.input().get("after", 0) or 0
            )
        except ValueError:
            raise APIError(422, "invalid_cursor", "The event cursor must be an integer.")
        events = event_stream.wait_after(after, timeout=15)
        web.header("Content-Type", "text/event-stream; charset=utf-8")
        web.header("Cache-Control", "no-cache")
        web.header("X-Accel-Buffering", "no")
        if not events:
            return ": keep-alive\n\n"
        return "".join(event_stream.encode_sse(item) for item in events)


class Plugins(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        diagnostics = {
            item.get("module"): item for item in plugins.plugin_diagnostics()
        }
        installed = []
        for module in plugins.plugin_names():
            manifest = plugins.plugin_manifest(module)
            installed.append({
                "id": module,
                "name": manifest.get("name", module),
                "version": manifest.get("version", ""),
                "enabled": module in options.enabled_plugins,
                "running": module in plugins.running(),
                "health": _safe_value(diagnostics.get(module, {})),
                "mobile": plugins.plugin_mobile_capabilities(module),
            })
        return respond(installed)


class Plugin(object):
    @endpoint
    @require_scope("read")
    def GET(self, plugin_id):
        if plugin_id not in plugins.plugin_names():
            raise APIError(404, "not_found", "The plug-in is not installed.")
        manifest = plugins.plugin_manifest(plugin_id)
        diagnostics = next((
            item for item in plugins.plugin_diagnostics()
            if item.get("module") == plugin_id
        ), {})
        return respond({
            "id": plugin_id,
            "manifest": _safe_value(manifest),
            "enabled": plugin_id in options.enabled_plugins,
            "running": plugin_id in plugins.running(),
            "health": _safe_value(diagnostics),
            "mobile": plugins.plugin_mobile_capabilities(plugin_id),
        })

    @endpoint
    @require_scope("plugins")
    def PUT(self, plugin_id):
        if plugin_id not in plugins.plugin_names():
            raise APIError(404, "not_found", "The plug-in is not installed.")
        payload = json_body()
        if set(payload) != {"enabled"} or not isinstance(payload["enabled"], bool):
            raise APIError(
                422, "invalid_plugin_configuration",
                "The plug-in request must contain one boolean enabled field.",
            )

        enabled = payload["enabled"]
        enabled_plugins = list(options.enabled_plugins)
        if enabled:
            approval = plugins.plugin_permission_approval(plugin_id)
            if not approval["approved"]:
                raise APIError(
                    409, "plugin_permission_approval_required",
                    "The plug-in permissions must be approved in the OSPy web interface.",
                    {"missing": approval["missing"]},
                )
            compatibility = plugins.plugin_compatibility(
                plugin_id, enabled_plugins + [plugin_id]
            )
            if not compatibility["compatible"]:
                raise APIError(
                    409, "incompatible_plugin",
                    "The plug-in is not compatible with this OSPy installation.",
                    {"errors": compatibility["errors"]},
                )
            if plugin_id not in enabled_plugins:
                enabled_plugins.append(plugin_id)
        elif plugin_id in enabled_plugins:
            enabled_plugins.remove(plugin_id)

        options.enabled_plugins = enabled_plugins
        plugins.start_enabled_plugins()
        running = plugin_id in plugins.running()
        if enabled and not running:
            raise APIError(
                409, "plugin_start_failed",
                "The plug-in could not be started. Open OSPy Diagnostics for details.",
            )

        logEV.save_events_log(
            _('Plug-in enabled') if enabled else _('Plug-in disabled'),
            (
                _('User {} enabled plug-in {}.') if enabled else
                _('User {} disabled plug-in {}.')
            ).format(_actor(), plugin_id),
            level='info' if enabled else 'warning',
            category='system',
        )
        result = self.GET.__wrapped__(self, plugin_id)
        event_stream.publish(
            "plugin.configured",
            {"plugin": plugin_id, "enabled": enabled, "running": running},
        )
        return result


class PluginMobile(object):
    @endpoint
    @require_scope("read")
    def GET(self, plugin_id):
        query = web.input()
        from_time = query.get("from") or None
        to_time = query.get("to") or None
        try:
            max_points = int(query.get("max_points", 400))
        except (TypeError, ValueError):
            raise APIError(
                422, "invalid_history_range",
                "max_points must be an integer between 20 and 2000.",
            )
        if max_points < 20 or max_points > 2000:
            raise APIError(
                422, "invalid_history_range",
                "max_points must be an integer between 20 and 2000.",
            )

        def parse_boundary(value):
            if not value:
                return None
            try:
                return datetime.datetime.fromisoformat(
                    value[:-1] + "+00:00" if value.endswith("Z") else value
                )
            except (TypeError, ValueError):
                raise APIError(
                    422, "invalid_history_range",
                    "History boundaries must use ISO 8601 date-time values.",
                )

        parsed_from = parse_boundary(from_time)
        parsed_to = parse_boundary(to_time)
        if parsed_from is not None and parsed_to is not None:
            try:
                invalid_order = parsed_from >= parsed_to
            except TypeError:
                raise APIError(
                    422, "invalid_history_range",
                    "History boundaries must use the same timezone form.",
                )
            if invalid_order:
                raise APIError(
                    422, "invalid_history_range",
                    "The history start must be earlier than its end.",
                )

        result = {"capabilities": plugins.plugin_mobile_capabilities(plugin_id)}
        for capability, key in (
                ("status", "status"), ("cards", "cards"),
                ("settings_schema", "settings_schema"),
                ("settings", "settings")):
            try:
                result[key] = plugins.plugin_mobile_call(
                    plugin_id, capability,
                    from_time=from_time, to_time=to_time,
                    max_points=max_points,
                )
            except Exception:
                result[key] = None
        return respond(_safe_value(result))


class PluginAction(object):
    @endpoint
    @require_scope("plugins")
    def POST(self, plugin_id, action):
        result = plugins.plugin_mobile_call(
            plugin_id, "action", action, json_body(required=False)
        )
        event_stream.publish("plugin.action", {"plugin": plugin_id, "action": action})
        return respond(_safe_value(result))


class Backups(object):
    @endpoint
    @require_scope("backup")
    def GET(self):
        return respond(_safe_value(list_system_backups()))

    @endpoint
    @require_scope("backup")
    def POST(self):
        def create():
            path = create_system_backup()
            return {"filename": os.path.basename(path)}
        return respond(_start_operation("backup", create), status=202)


class BackupDownload(object):
    @endpoint
    @require_scope("backup")
    def GET(self, backup_id):
        path = system_backup_path(backup_id)
        if not path or not os.path.isfile(path):
            raise APIError(404, "not_found", "The backup does not exist.")
        web.header("Content-Type", "application/zip")
        web.header("Content-Disposition", 'attachment; filename="{}"'.format(os.path.basename(path)))
        with open(path, "rb") as source:
            return source.read()


class BackupRestore(object):
    @endpoint
    @require_scope("backup")
    def POST(self, backup_id):
        path = system_backup_path(backup_id)
        if not path or not os.path.isfile(path):
            raise APIError(404, "not_found", "The backup does not exist.")
        def restore():
            staged, unused_manifest = stage_restore(path)
            apply_staged_restore(staged)
            helpers.restart(wait=2)
            return {"restart_required": True}
        return respond(_start_operation("restore", restore), status=202)


class Updates(object):
    @endpoint
    @require_scope("read")
    def GET(self):
        result = {"ospy": None, "plugins": []}
        try:
            if "system_update" in plugins.running():
                module = plugins.get("system_update")
                if hasattr(module, "health"):
                    result["ospy"] = _safe_value(module.health())
        except Exception as error:
            result["ospy"] = {"status": "error", "message": str(error)}
        return respond(result)


class UpdateAction(object):
    @endpoint
    @require_scope("update")
    def POST(self, action):
        if "system_update" not in plugins.running():
            raise APIError(409, "update_plugin_unavailable", "System Update is not running.")
        module = plugins.get("system_update")
        def update():
            if action == "apply" and hasattr(module, "perform_update"):
                return module.perform_update()
            elif action == "rollback" and hasattr(module, "perform_rollback_selected"):
                return module.perform_rollback_selected()
            elif action == "check":
                checker = getattr(module, "checker", None)
                if checker and hasattr(checker, "update"):
                    return checker.update()
                return {}
            raise RuntimeError("The update action is not supported.")
        if action not in ("apply", "rollback", "check"):
            raise APIError(404, "unknown_action", "The update action is not supported.")
        return respond(_start_operation("update." + action, update), status=202)


class SystemAction(object):
    @endpoint
    @require_scope("system")
    def POST(self, action):
        actions = {
            "restart-ospy": helpers.restart,
            "reboot": helpers.reboot,
            "poweroff": helpers.poweroff,
        }
        if action not in actions:
            raise APIError(404, "unknown_action", "The system action is not supported.")
        operation_id = mobile_store.create_operation("system." + action)
        mobile_store.update_operation(
            operation_id, "accepted", 10, {"action": action}
        )
        actions[action](wait=2)
        return respond(mobile_store.operation(operation_id), status=202)


class Operation(object):
    @endpoint
    @require_scope("read")
    def GET(self, operation_id):
        operation = mobile_store.operation(operation_id)
        if operation is None:
            raise APIError(404, "not_found", "The operation does not exist.")
        return respond(operation)


def _update_station(station, payload):
    allowed = {
        "name", "enabled", "ignore_rain", "activate_master",
        "activate_master_two", "activate_master_by_program", "usage",
        "precipitation", "capacity", "eto_factor",
    }
    for key, value in payload.items():
        if key in ("id", "legacy_index", "number"):
            continue
        if key not in allowed:
            raise APIError(
                422, "read_only_field",
                "The station field cannot be changed through the mobile API.",
                {"field": key},
            )
        setattr(station, key, value)


def _update_program(program, payload, require_schedule):
    from api.api import Programs as LegacyPrograms
    if not isinstance(payload, dict):
        raise APIError(422, "invalid_program", "The program must be an object.")
    if require_schedule:
        required = {"name", "stations", "type", "type_data"}
        missing = sorted(required.difference(payload))
        if missing:
            raise APIError(
                422, "missing_program_fields",
                "The program definition is incomplete.", {"missing": missing},
            )
    base = _program_data(program)
    merged = {
        "name": payload.get("name", base["name"]),
        "stations": payload.get("stations", base["stations"]),
        "enabled": payload.get("enabled", base["enabled"]),
        "type": payload.get("type", base["type"]),
        "type_data": payload.get("type_data", base["type_data"]),
        "modulo": payload.get("modulo", getattr(program, "modulo", 1)),
        "manual": payload.get("manual", base["manual"]),
        "start": payload.get("start", base["start"]),
        "schedule": payload.get("schedule", base["schedule"]),
    }
    try:
        merged["type"] = int(merged["type"])
        if merged["type"] == ProgramType.CUSTOM:
            start = merged.get("start")
            if isinstance(start, str):
                normalized = start.strip()
                if normalized.endswith("Z"):
                    normalized = normalized[:-1] + "+00:00"
                parsed = datetime.datetime.fromisoformat(normalized)
                if parsed.tzinfo is not None:
                    parsed = parsed.astimezone().replace(tzinfo=None)
                merged["start"] = parsed.timestamp()
            elif isinstance(start, datetime.datetime):
                parsed = start
                if parsed.tzinfo is not None:
                    parsed = parsed.astimezone().replace(tzinfo=None)
                merged["start"] = parsed.timestamp()
        program.type = merged["type"]
        LegacyPrograms()._dict_to_program(program, merged)
        program.name = str(merged["name"])
        program.enabled = bool(merged["enabled"])
        program.stations = [
            int(item) for item in merged["stations"]
            if 0 <= int(item) < stations.count()
        ]
    except Exception as error:
        raise APIError(
            422, "invalid_program", "The program definition is not valid.",
            {"reason": str(error)},
        )


URLS = (
    "/", Root,
    "/server", ServerInfo,
    "/capabilities", Capabilities,
    "/openapi.json", OpenAPI,
    "/auth/login", Login,
    "/auth/refresh", Refresh,
    "/auth/logout", Logout,
    "/auth/devices", Devices,
    "/auth/devices/(.+)", Device,
    "/overview", Overview,
    "/irrigation", Irrigation,
    "/stations", Stations,
    "/stations/actions/stop-all", StopAll,
    "/stations/([^/]+)", Station,
    "/stations/([^/]+)/actions/([^/]+)", StationAction,
    "/programs", Programs,
    "/programs/([^/]+)", Program,
    "/programs/([^/]+)/actions/([^/]+)", ProgramAction,
    "/run-once", RunOnce,
    "/run-once/actions/start", RunOnceStart,
    "/sensors", Sensors,
    "/sensors/([^/]+)", Sensor,
    "/sensors/([^/]+)/history", SensorHistory,
    "/weather/current", WeatherCurrent,
    "/weather/forecast", WeatherForecast,
    "/weather/status", WeatherStatus,
    "/schedule", Schedule,
    "/logs/([^/]+)", Logs,
    "/diagnostics/([^/]+)", Diagnostics,
    "/notifications", Notifications,
    "/notifications/([^/]+)/ack", NotificationAck,
    "/changes", Changes,
    "/stream", Stream,
    "/plugins", Plugins,
    "/plugins/([^/]+)", Plugin,
    "/plugins/([^/]+)/mobile", PluginMobile,
    "/plugins/([^/]+)/actions/([^/]+)", PluginAction,
    "/backups", Backups,
    "/backups/([^/]+)/download", BackupDownload,
    "/backups/([^/]+)/restore", BackupRestore,
    "/updates", Updates,
    "/updates/actions/([^/]+)", UpdateAction,
    "/system/actions/([^/]+)", SystemAction,
    "/operations/([^/]+)", Operation,
)


def get_app():
    _connect_hooks()
    return web.application(URLS, globals())
