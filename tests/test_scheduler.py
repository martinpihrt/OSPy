import copy
import datetime
from types import SimpleNamespace
import threading
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import programs as programs_module
from ospy import scheduler


class _Stations(object):
    master = None
    master_two = None

    def __init__(self, station_list):
        self._stations = station_list

    def __getitem__(self, index):
        return self._stations[index]

    def get(self, index):
        return self._stations[index]

    def count(self):
        return len(self._stations)

    def enabled_stations(self):
        return [station for station in self._stations if station.enabled]


class _Programs(object):
    run_now_program = None

    def __init__(self, program_list):
        self._programs = program_list

    def get(self):
        return self._programs

    @staticmethod
    def apply_group_postponements(intervals, start, end):
        return intervals


class _RunOnce(object):
    def __init__(self, intervals=None):
        self.intervals = intervals or {}

    def active_intervals(self, start, end, station):
        return copy.deepcopy(self.intervals.get(station, []))


class SchedulerPredictionTests(unittest.TestCase):
    def _station(self, index, ignore_rain=False, enabled=True):
        return SimpleNamespace(
            index=index,
            enabled=enabled,
            usage=1.0,
            ignore_rain=ignore_rain,
        )

    def _program(self, index, stations, start, end, manual=False):
        program = SimpleNamespace(
            index=index,
            name="Program {}".format(index + 1),
            stations=set(stations),
            enabled=True,
            fixed=True,
            cut_off=0,
            control_master=0,
            manual=manual,
        )
        program.active_intervals = mock.Mock(
            return_value=[{"start": start, "end": end}]
        )
        return program

    def _predict(
            self, station_list, program_list, start, end,
            run_once=None, scheduler_enabled=True, rain_end=None,
            station_delay=0, max_usage=0):
        options = SimpleNamespace(
            max_usage=max_usage,
            station_delay=station_delay,
            scheduler_enabled=scheduler_enabled,
            min_runtime=0,
        )
        rain_end = rain_end or datetime.datetime.min
        with mock.patch.multiple(
            scheduler,
            options=options,
            stations=_Stations(station_list),
            programs=_Programs(program_list),
            run_once=run_once or _RunOnce(),
            rain_blocks=SimpleNamespace(block_end=lambda: rain_end),
            inputs=SimpleNamespace(rain_sensed=lambda: False),
            log=SimpleNamespace(finished_runs=lambda: [], active_runs=lambda: []),
            level_adjustments=SimpleNamespace(total_adjustment=lambda: 1.0),
            program_level_adjustments={},
        ):
            return scheduler.predicted_schedule(start, end)

    def test_regular_program_is_blocked_by_rain_delay(self):
        now = datetime.datetime.now()
        run_start = now + datetime.timedelta(minutes=1)
        run_end = run_start + datetime.timedelta(minutes=5)
        result = self._predict(
            [self._station(0)],
            [self._program(0, [0], run_start, run_end)],
            now,
            now + datetime.timedelta(hours=1),
            rain_end=now + datetime.timedelta(hours=2),
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["blocked"], "rain delay")

    def test_manual_run_once_bypasses_scheduler_and_rain_blocks(self):
        now = datetime.datetime.now()
        run_start = now + datetime.timedelta(minutes=1)
        run_end = run_start + datetime.timedelta(minutes=2)
        result = self._predict(
            [self._station(0)],
            [],
            now,
            now + datetime.timedelta(hours=1),
            run_once=_RunOnce({0: [{"start": run_start, "end": run_end}]}),
            scheduler_enabled=False,
            rain_end=now + datetime.timedelta(hours=2),
        )

        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["manual"])
        self.assertFalse(result[0]["blocked"])

    def test_usage_limit_preserves_order_and_applies_station_delay(self):
        now = datetime.datetime.now()
        run_start = now + datetime.timedelta(minutes=1)
        run_end = run_start + datetime.timedelta(minutes=5)
        result = self._predict(
            [self._station(0), self._station(1)],
            [
                self._program(0, [0], run_start, run_end),
                self._program(1, [1], run_start, run_end),
            ],
            now,
            now + datetime.timedelta(hours=1),
            station_delay=30,
            max_usage=1.0,
        )

        self.assertEqual([item["station"] for item in result], [0, 1])
        self.assertEqual(result[0]["start"], run_start)
        self.assertEqual(
            result[1]["start"], run_end + datetime.timedelta(seconds=30)
        )

    def test_unlimited_usage_allows_parallel_station_runs(self):
        now = datetime.datetime.now()
        run_start = now + datetime.timedelta(minutes=1)
        run_end = run_start + datetime.timedelta(minutes=5)

        result = self._predict(
            [self._station(0), self._station(1)],
            [
                self._program(0, [0], run_start, run_end),
                self._program(1, [1], run_start, run_end),
            ],
            now,
            now + datetime.timedelta(hours=1),
            max_usage=0,
        )

        self.assertEqual([item["start"] for item in result], [run_start, run_start])

    def test_disabled_station_is_excluded_from_schedule(self):
        now = datetime.datetime.now()
        run_start = now + datetime.timedelta(minutes=1)
        run_end = run_start + datetime.timedelta(minutes=5)

        result = self._predict(
            [self._station(0, enabled=False)],
            [self._program(0, [0], run_start, run_end)],
            now,
            now + datetime.timedelta(hours=1),
        )

        self.assertEqual(result, [])


class ProgramGroupPostponementTests(unittest.TestCase):
    def setUp(self):
        self.source_start = datetime.datetime(2030, 1, 2, 8, 0)
        self.source_end = self.source_start + datetime.timedelta(minutes=10)
        self.target_start = datetime.datetime(2030, 1, 3, 9, 0)
        self.program = SimpleNamespace(
            enabled=True,
            group_id="garden",
            stations={0},
            schedule=[[480, 490]],
        )
        self.manager = programs_module._Programs.__new__(programs_module._Programs)
        self.manager._programs = [self.program]
        self.manager._postponement_lock = threading.RLock()
        self.source = {
            "uid": "source-run",
            "station": 0,
            "program": 0,
            "start": self.source_start,
            "end": self.source_end,
        }
        shift = self.target_start - self.source_start
        self.item = {
            "id": "postponement-1",
            "group_id": "garden",
            "created": self.source_start - datetime.timedelta(days=1),
            "source_start": self.source_start,
            "source_end": self.source_end,
            "target_start": self.target_start,
            "target_end": self.source_end + shift,
            "shift_seconds": shift.total_seconds(),
            "runs": [{
                "source_uid": "source-run",
                "station": 0,
                "program": 0,
                "program_name": "Morning",
                "control_master": 0,
                "usage": 1.0,
                "program_group_id": "garden",
                "program_stations": [0],
                "program_schedule": [[480, 490]],
                "start": self.source_start,
                "end": self.source_end,
            }],
        }
        self.options = SimpleNamespace(
            program_groups=[{"id": "garden", "name": "Garden"}],
            program_group_postponements=[copy.deepcopy(self.item)],
        )

    def test_postponement_replaces_only_source_occurrence(self):
        with mock.patch.object(programs_module, "options", self.options):
            result = self.manager.apply_group_postponements(
                [copy.deepcopy(self.source)],
                self.source_start - datetime.timedelta(hours=1),
                self.target_start + datetime.timedelta(hours=1),
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["start"], self.target_start)
        self.assertEqual(result[0]["postponement_id"], "postponement-1")
        self.assertNotEqual(result[0]["uid"], self.source["uid"])

    def test_cancelling_before_source_time_restores_regular_run(self):
        with mock.patch.object(programs_module, "options", self.options):
            removed = self.manager.cancel_group_postponement(
                "garden",
                "postponement-1",
                now=self.source_start - datetime.timedelta(minutes=1),
            )
            result = self.manager.apply_group_postponements(
                [copy.deepcopy(self.source)],
                self.source_start - datetime.timedelta(hours=1),
                self.target_start + datetime.timedelta(hours=1),
            )

        self.assertIsNotNone(removed)
        self.assertEqual(result, [self.source])


if __name__ == "__main__":
    unittest.main()
