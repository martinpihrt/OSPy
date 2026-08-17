import datetime
import unittest
from types import SimpleNamespace
from unittest import mock

from ospy import calendar_rules
from ospy.programs import ProgramType, _Program, _Programs


class _DetachedPrograms(object):
    def __init__(self):
        self.items = []

    def get(self):
        return self.items[:]


def detached_program():
    manager = _DetachedPrograms()
    program = _Program(manager, -1)
    program.set_days_simple(6 * 60, 30, 0, 0, list(range(7)))
    manager.items.append(program)
    program.__dict__["_stations"] = [0]
    program.update_station_schedule()
    return program


class ProgramCalendarTests(unittest.TestCase):
    def test_month_parity_and_selected_month_days_are_combined(self):
        program = SimpleNamespace(
            allowed_months=[4, "invalid"], day_parity="odd",
            month_days=[1, 15, 31, "invalid"],
        )
        self.assertTrue(calendar_rules.date_is_eligible(
            program, datetime.date(2027, 4, 15)))
        self.assertFalse(calendar_rules.date_is_eligible(
            program, datetime.date(2027, 4, 16)))
        self.assertFalse(calendar_rules.date_is_eligible(
            program, datetime.date(2027, 5, 15)))

    def test_excluded_period_parser_supports_exact_and_annual_ranges(self):
        dates, ranges = calendar_rules.parse_excluded_periods(
            "2027-05-01\n2027-08-01..2027-08-14\n12-20..01-10")
        self.assertEqual(["2027-05-01"], dates)
        self.assertEqual(2, len(ranges))
        self.assertFalse(ranges[0]["annual"])
        self.assertTrue(ranges[1]["annual"])

    def test_excluded_run_remains_visible_with_reason(self):
        program = detached_program()
        day = datetime.date.today() + datetime.timedelta(days=1)
        program.__dict__["excluded_dates"] = [day.isoformat()]
        start = datetime.datetime.combine(day, datetime.time.min)
        intervals = program.active_intervals(
            start, start + datetime.timedelta(days=1), 0)
        self.assertEqual(1, len(intervals))
        self.assertEqual("calendar_excluded", intervals[0]["calendar_blocked"])

    def test_manual_solar_run_builds_schedule_without_provider(self):
        program = detached_program()
        program.set_solar(ProgramType.SUNRISE, 10, 5, 2, list(range(7)))
        program.start_now()
        self.assertTrue(program.manual)
        self.assertEqual([[0, 10], [15, 25], [30, 40]], program.schedule)

    def test_copy_keeps_native_solar_type_and_calendar(self):
        manager = _Programs.__new__(_Programs)
        manager._programs = []
        source = _Program(manager, -1)
        source.set_solar(ProgramType.SUNSET, 12, 3, 1, [1, 4])
        source.__dict__["allowed_months"] = [4, 5, 6]
        manager._programs.append(source)
        with mock.patch("ospy.programs.options.save"):
            copied_index = manager.copy_program(0)
        copied = manager._programs[copied_index]
        self.assertEqual(ProgramType.SUNSET, copied.type)
        self.assertEqual([12, 3, 1, [1, 4]], copied.type_data)
        self.assertEqual([4, 5, 6], copied.allowed_months)
        self.assertEqual([], copied.schedule)

    def test_solar_offset_is_clamped_to_allowed_window(self):
        program = detached_program()
        program.set_solar(ProgramType.SUNRISE, 20, 0, 0, list(range(7)))
        program.__dict__["sun_offset_minutes"] = -120
        program.__dict__["sun_earliest_minute"] = 5 * 60
        program.__dict__["sun_latest_minute"] = 8 * 60
        program.__dict__["sun_window_policy"] = "clamp"
        day = datetime.date.today() + datetime.timedelta(days=1)
        start = datetime.datetime.combine(day, datetime.time.min)
        with mock.patch.object(
                calendar_rules, "solar_time",
                return_value=start.replace(hour=6)):
            intervals = program.active_intervals(
                start, start + datetime.timedelta(days=1), 0)
        self.assertEqual(start.replace(hour=5), intervals[0]["start"])

    def test_service_outage_overlap_uses_scope_and_half_open_range(self):
        program = SimpleNamespace(index=2, group_id="garden")
        start = datetime.datetime(2027, 6, 1, 8, 0)
        fake_options = SimpleNamespace(calendar_service_outages=[{
            "start": "2027-06-01T08:30",
            "end": "2027-06-01T09:30",
            "scope": "program",
            "program": 2,
        }])
        with mock.patch.object(calendar_rules, "options", fake_options):
            self.assertEqual(
                "service_outage",
                calendar_rules.service_outage_reason(
                    program, start, start + datetime.timedelta(hours=1), 0),
            )
            self.assertFalse(calendar_rules.service_outage_reason(
                program, start - datetime.timedelta(hours=1), start, 0))

    def test_missing_holiday_dependency_blocks_only_opted_in_program(self):
        program = SimpleNamespace(
            excluded_dates=[], excluded_ranges=[], exclude_holidays=True,
        )
        with mock.patch.object(
                calendar_rules, "holidays_available", return_value=False):
            self.assertEqual(
                "holiday_calendar_unavailable",
                calendar_rules.excluded_date_reason(
                    program, datetime.date(2027, 1, 1)),
            )
        program.exclude_holidays = False
        self.assertFalse(calendar_rules.excluded_date_reason(
            program, datetime.date(2027, 1, 1)))


if __name__ == "__main__":
    unittest.main()
