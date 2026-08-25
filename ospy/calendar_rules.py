#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Calendar constraints shared by OSPy irrigation programs.

Stored values use stable machine codes.  User-facing labels and errors are
translated by the web/API layers through the normal OSPy gettext catalogue.
"""

import datetime
import logging
import uuid

from ospy.options import options


DAY_PARITIES = ("all", "odd", "even")
SUN_REFERENCES = ("sunrise", "sunset")
SUN_WINDOW_POLICIES = ("clamp", "skip")
_HOLIDAY_CACHE = {}


def _iso_date(value):
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value))


def parse_excluded_periods(value):
    """Parse one date or date range per line into persistent program data."""
    dates = []
    ranges = []
    for raw_line in str(value or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("..")]
        if len(parts) == 1:
            day = _iso_date(parts[0])
            dates.append(day.isoformat())
            continue
        if len(parts) != 2:
            raise ValueError("invalid_excluded_period")
        annual = all(len(part) == 5 for part in parts)
        if annual:
            for part in parts:
                month, month_day = [int(item) for item in part.split("-")]
                datetime.date(2000, month, month_day)
            start, end = parts
        else:
            start = _iso_date(parts[0]).isoformat()
            end = _iso_date(parts[1]).isoformat()
            if end < start:
                raise ValueError("invalid_excluded_range")
        ranges.append({"start": start, "end": end, "annual": annual})
    return sorted(set(dates)), ranges


def excluded_periods_text(program):
    lines = [str(item) for item in getattr(program, "excluded_dates", []) or []]
    for item in getattr(program, "excluded_ranges", []) or []:
        if isinstance(item, dict) and item.get("start") and item.get("end"):
            lines.append("{}..{}".format(item["start"], item["end"]))
    return "\n".join(lines)


def normalized_months(value):
    if not isinstance(value, (list, tuple, set)):
        return list(range(1, 13))
    result = []
    for item in value:
        if isinstance(item, bool):
            continue
        try:
            item = int(item)
        except (TypeError, ValueError):
            continue
        if 1 <= item <= 12:
            result.append(item)
    result = sorted(set(result))
    return result or list(range(1, 13))


def normalized_month_days(value):
    if not isinstance(value, (list, tuple, set)):
        return []
    result = []
    for item in value:
        if isinstance(item, bool):
            continue
        try:
            item = int(item)
        except (TypeError, ValueError):
            continue
        if 1 <= item <= 31:
            result.append(item)
    return sorted(set(result))


def date_is_eligible(program, day):
    """Return whether a recurring candidate satisfies calendar selectors."""
    day = _iso_date(day)
    if day.month not in normalized_months(
            getattr(program, "allowed_months", None)):
        return False
    parity = str(getattr(program, "day_parity", "all") or "all")
    if parity == "odd" and day.day % 2 == 0:
        return False
    if parity == "even" and day.day % 2 != 0:
        return False
    selected_days = normalized_month_days(
        getattr(program, "month_days", None))
    if selected_days and day.day not in selected_days:
        return False
    return True


def _annual_range_contains(day, start_value, end_value):
    start_month, start_day = [int(item) for item in start_value.split("-")]
    end_month, end_day = [int(item) for item in end_value.split("-")]
    current = (day.month, day.day)
    start = (start_month, start_day)
    end = (end_month, end_day)
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


def excluded_date_reason(program, day):
    """Return a stable reason code for a program-level date exclusion."""
    day = _iso_date(day)
    exact_dates = getattr(program, "excluded_dates", []) or []
    if day.isoformat() in set(str(item) for item in exact_dates):
        return "calendar_excluded"
    for item in getattr(program, "excluded_ranges", []) or []:
        if not isinstance(item, dict):
            continue
        try:
            if item.get("annual"):
                if _annual_range_contains(
                        day, str(item.get("start", "")),
                        str(item.get("end", ""))):
                    return "calendar_excluded"
            else:
                start = _iso_date(item.get("start"))
                end = _iso_date(item.get("end"))
                if start <= day <= end:
                    return "calendar_excluded"
        except (TypeError, ValueError):
            continue
    if bool(getattr(program, "exclude_holidays", False)):
        if not holiday_calendar_available(day):
            return "holiday_calendar_unavailable"
        if is_public_holiday(day):
            return "public_holiday"
    return False


def holiday_country_code():
    override = str(getattr(options, "holiday_country_override", "") or "").strip()
    detected = str(getattr(options, "weather_country_code", "") or "").strip()
    value = override or detected
    return value.upper() if len(value) == 2 and value.isalpha() else ""


def holidays_available():
    try:
        import holidays  # noqa: F401
        return True
    except ImportError:
        return False


def _holiday_calendar(day):
    day = _iso_date(day)
    country = holiday_country_code()
    if not country:
        return None
    key = (country, day.year)
    if key not in _HOLIDAY_CACHE:
        try:
            import holidays
            country_factory = getattr(holidays, "country_holidays", None)
            if callable(country_factory):
                calendar = country_factory(country, years=[day.year])
            else:
                country_factory = getattr(holidays, "CountryHoliday", None)
                if not callable(country_factory):
                    raise AttributeError(
                        _('Public holiday support is not installed.'))
                calendar = country_factory(country, years=[day.year])
            _HOLIDAY_CACHE[key] = calendar
        except Exception as error:
            _HOLIDAY_CACHE[key] = None
            logging.warning(
                _('Public holiday support is not installed.') +
                ' {}: {}'.format(country, error))
    return _HOLIDAY_CACHE.get(key)


def holiday_calendar_available(day=None):
    return _holiday_calendar(day or datetime.date.today()) is not None


def is_public_holiday(day):
    calendar = _holiday_calendar(day)
    return calendar is not None and _iso_date(day) in calendar


def holiday_name(day):
    calendar = _holiday_calendar(day)
    return str(calendar.get(_iso_date(day), "") or "") if calendar is not None else ""


def service_outage_reason(program, start, end, station=None):
    """Return a stable reason code when an automatic interval overlaps outage."""
    for item in getattr(options, "calendar_service_outages", []) or []:
        if not isinstance(item, dict):
            continue
        try:
            outage_start = datetime.datetime.fromisoformat(str(item.get("start", "")))
            outage_end = datetime.datetime.fromisoformat(str(item.get("end", "")))
        except (TypeError, ValueError):
            continue
        if end <= outage_start or start >= outage_end:
            continue
        try:
            scope = str(item.get("scope", "all") or "all")
            if (scope == "program" and
                    int(item.get("program", -1)) != program.index):
                continue
            if (scope == "group" and
                    str(item.get("group", "")) != str(program.group_id)):
                continue
            if scope == "station" and station not in [
                    int(value) for value in (item.get("stations", []) or [])
                    if str(value).lstrip("-").isdigit()]:
                continue
        except (AttributeError, TypeError, ValueError):
            continue
        return "service_outage"
    return False


def _service_outage_item(name, start, end, scope="all", target=None,
                         outage_id=None):
    if not isinstance(start, datetime.datetime) or not isinstance(end, datetime.datetime):
        raise ValueError("invalid_datetime")
    if end <= start:
        raise ValueError("invalid_range")
    if scope not in ("all", "program", "group", "station"):
        raise ValueError("invalid_scope")
    item = {
        "id": str(outage_id or uuid.uuid4().hex),
        "name": str(name or "").strip(),
        "start": start.isoformat(timespec="minutes"),
        "end": end.isoformat(timespec="minutes"),
        "scope": scope,
    }
    if scope == "program":
        item["program"] = int(target)
    elif scope == "group":
        item["group"] = str(target)
    elif scope == "station":
        item["stations"] = sorted(set(int(value) for value in (target or [])))
    return item


def add_service_outage(name, start, end, scope="all", target=None):
    item = _service_outage_item(name, start, end, scope, target)
    outages = list(getattr(options, "calendar_service_outages", []) or [])
    outages.append(item)
    options.calendar_service_outages = outages
    return item


def update_service_outage(outage_id, name, start, end, scope=None,
                          target=None):
    outages = list(getattr(options, "calendar_service_outages", []) or [])
    for index, current in enumerate(outages):
        if not isinstance(current, dict) or current.get("id") != str(outage_id):
            continue
        selected_scope = str(scope or current.get("scope", "all") or "all")
        if scope is None:
            if selected_scope == "program":
                target = current.get("program")
            elif selected_scope == "group":
                target = current.get("group")
            elif selected_scope == "station":
                target = current.get("stations", [])
        item = _service_outage_item(
            name, start, end, selected_scope, target, outage_id=outage_id)
        outages[index] = item
        options.calendar_service_outages = outages
        return item
    return None


def remove_service_outage(outage_id):
    outages = list(getattr(options, "calendar_service_outages", []) or [])
    remaining = [
        item for item in outages
        if not isinstance(item, dict) or item.get("id") != str(outage_id)
    ]
    if len(remaining) == len(outages):
        return False
    options.calendar_service_outages = remaining
    return True


def solar_provider_status():
    """Return machine-readable availability without importing disabled code."""
    try:
        import plugins
        if "sunrise_and_sunset" not in plugins.running():
            return {"available": False, "reason": "plugin_not_running"}
        provider = plugins.get("sunrise_and_sunset")
        if not callable(getattr(provider, "program_sun_times", None)):
            return {"available": False, "reason": "provider_incompatible"}
        available = getattr(provider, "program_sun_times_available", None)
        if callable(available) and not available():
            return {"available": False, "reason": "provider_not_configured"}
        return {"available": True, "reason": ""}
    except Exception:
        return {"available": False, "reason": "provider_error"}


def solar_time(day, reference):
    if reference not in SUN_REFERENCES:
        return None
    if not solar_provider_status()["available"]:
        return None
    try:
        import plugins
        values = plugins.get("sunrise_and_sunset").program_sun_times(_iso_date(day))
        value = values.get(reference) if isinstance(values, dict) else None
        if isinstance(value, datetime.datetime):
            return value.replace(tzinfo=None)
    except Exception:
        return None
    return None
