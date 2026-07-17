import datetime
from contextlib import nullcontext
from threading import Thread
from types import SimpleNamespace
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import scheduler
from ospy import stations as stations_module


class MemoryIO(object):
    OUT = "out"
    HIGH = 1
    LOW = 0

    def __init__(self):
        self.writes = []

    def setup(self, pin, mode):
        return None

    def output(self, pin, value):
        self.writes.append((pin, value))


def memory_shift_stations(enabled=(True, True, True, True)):
    controller = stations_module._ShiftStations.__new__(
        stations_module._ShiftStations
    )
    controller._io = MemoryIO()
    controller._sr_dat = 1
    controller._sr_clk = 2
    controller._sr_noe = 3
    controller._sr_lat = 4
    controller._state = [False] * len(enabled)
    controller._stations = [
        SimpleNamespace(
            enabled=value,
            is_master=False,
            is_master_two=False,
            is_master_by_program=False,
        )
        for value in enabled
    ]
    return controller


class StationOutputSafetyTests(unittest.TestCase):
    def test_shift_driver_writes_activation_and_deactivation(self):
        controller = memory_shift_stations()

        controller.activate([0, 2])
        self.assertEqual(controller.active(), [True, False, True, False])
        self.assertTrue(controller._io.writes)

        controller.deactivate(0)
        self.assertEqual(controller.active(), [False, False, True, False])

    def test_invalid_indices_never_address_an_output(self):
        controller = memory_shift_stations()
        writes_before = list(controller._io.writes)

        controller.activate([-1, 99])
        controller.deactivate([-1, 99])

        self.assertEqual(controller.active(), [False, False, False, False])
        self.assertEqual(controller._io.writes, writes_before)
        self.assertFalse(controller.active(-1))
        self.assertFalse(controller.active(99))

    def test_disabled_station_is_not_activated(self):
        controller = memory_shift_stations(enabled=(True, False))
        writes_before = list(controller._io.writes)

        controller.activate(1)

        self.assertEqual(controller.active(), [False, False])
        self.assertEqual(controller._io.writes, writes_before)

    def test_disabled_master_output_can_still_be_controlled(self):
        controller = memory_shift_stations(enabled=(True, False))
        controller._stations[1].is_master = True

        controller.activate(1)

        self.assertEqual(controller.active(), [False, True])

    def test_clear_writes_all_outputs_off(self):
        controller = memory_shift_stations()
        controller.activate([0, 1, 2, 3])

        controller.clear()

        self.assertEqual(controller.active(), [False, False, False, False])
        data_writes = [
            value for pin, value in controller._io.writes
            if pin == controller._sr_dat
        ]
        self.assertEqual(data_writes[-4:], [MemoryIO.LOW] * 4)


class _Station(object):
    def __init__(self, manager, index):
        self.manager = manager
        self.index = index
        self.enabled = True
        self.ignore_rain = False
        self.activate_master = False
        self.activate_master_two = False
        self.activate_master_by_program = False

    @property
    def active(self):
        return self.manager.states[self.index]

    @active.setter
    def active(self, value):
        self.manager.states[self.index] = bool(value)


class _Stations(object):
    def __init__(self, count=4):
        self.states = [False] * count
        self.items = [_Station(self, index) for index in range(count)]
        self.master = 2
        self.master_two = 3

    def get(self, index):
        return self.items[index]

    def activate(self, index):
        self.states[index] = True

    def deactivate(self, index):
        self.states[index] = False


class SchedulerOutputTests(unittest.TestCase):
    def setUp(self):
        scheduler.pom_last_rain = False
        scheduler.pom_last_internet = False
        scheduler.pom_last_rain_delay = False
        scheduler.blocking_from_pressurizer = False

    def _check_schedule(self, active_runs, stations, outputs, now=None, **delays):
        options = SimpleNamespace(
            manual_mode=True,
            scheduler_enabled=True,
            master_relay=True,
            master_on_delay=delays.get("master_on_delay", 0),
            master_off_delay=delays.get("master_off_delay", 0),
            master_on_delay_two=delays.get("master_on_delay_two", 0),
            master_off_delay_two=delays.get("master_off_delay_two", 0),
        )
        log = SimpleNamespace(
            active_runs=lambda: list(active_runs),
            finished_runs=lambda: [],
            finish_run=mock.Mock(),
        )
        time_patch = nullcontext()
        if now is not None:
            class FixedDateTime(datetime.datetime):
                @classmethod
                def now(cls, tz=None):
                    return now
            time_patch = mock.patch.object(
                scheduler.datetime, "datetime", FixedDateTime
            )
        with time_patch, mock.patch.multiple(
                scheduler,
                options=options,
                stations=stations,
                outputs=outputs,
                log=log,
                programs=SimpleNamespace(cleanup_group_postponements=lambda unused: None),
                rain_blocks=SimpleNamespace(
                    block_end=lambda: datetime.datetime.min,
                    seconds_left=lambda: 0,
                ),
                inputs=SimpleNamespace(rain_sensed=lambda: False),
                get_external_ip=lambda: "-",
        ):
            scheduler._Scheduler._check_schedule()

    def test_primary_and_secondary_master_follow_active_station(self):
        now = datetime.datetime.now()
        stations = _Stations()
        stations.get(0).activate_master = True
        stations.get(0).activate_master_two = True
        outputs = SimpleNamespace(relay_output=False)
        entry = {
            "station": 0,
            "start": now - datetime.timedelta(seconds=5),
            "end": now + datetime.timedelta(seconds=30),
            "blocked": False,
            "manual": True,
            "control_master": 0,
        }

        self._check_schedule([entry], stations, outputs)

        self.assertTrue(stations.get(stations.master).active)
        self.assertTrue(stations.get(stations.master_two).active)
        self.assertTrue(outputs.relay_output)

        self._check_schedule([], stations, outputs)
        self.assertFalse(stations.get(stations.master).active)
        self.assertFalse(stations.get(stations.master_two).active)
        self.assertFalse(outputs.relay_output)

    def test_master_on_and_off_delays_are_respected(self):
        start = datetime.datetime(2030, 1, 1, 12, 0, 0)
        end = start + datetime.timedelta(minutes=1)
        stations = _Stations()
        stations.get(0).activate_master = True
        outputs = SimpleNamespace(relay_output=False)
        entry = {
            "station": 0,
            "start": start,
            "end": end,
            "blocked": False,
            "manual": True,
            "control_master": 0,
        }
        delays = {"master_on_delay": 10, "master_off_delay": 30}

        self._check_schedule(
            [entry], stations, outputs,
            now=start + datetime.timedelta(seconds=9), **delays
        )
        self.assertFalse(stations.get(stations.master).active)

        self._check_schedule(
            [entry], stations, outputs,
            now=start + datetime.timedelta(seconds=10), **delays
        )
        self.assertTrue(stations.get(stations.master).active)

        self._check_schedule(
            [entry], stations, outputs,
            now=end + datetime.timedelta(seconds=29), **delays
        )
        self.assertTrue(stations.get(stations.master).active)

        self._check_schedule(
            [entry], stations, outputs,
            now=end + datetime.timedelta(seconds=30), **delays
        )
        self.assertFalse(stations.get(stations.master).active)

    def test_scheduler_loop_continues_after_output_exception(self):
        class StopLoop(BaseException):
            pass

        instance = scheduler._Scheduler.__new__(scheduler._Scheduler)
        Thread.__init__(instance)
        instance._reported_blocked = {}
        options = SimpleNamespace(manual_mode=False, scheduler_enabled=True)
        with mock.patch.multiple(
                scheduler,
                options=options,
                log=SimpleNamespace(active_runs=lambda: []),
                rain_blocks=SimpleNamespace(block_end=lambda: datetime.datetime.min),
                inputs=SimpleNamespace(rain_sensed=lambda: False),
                update_details=mock.DEFAULT,
                heartbeat=mock.DEFAULT,
        ) as patched, mock.patch.object(
                scheduler._Scheduler,
                "_check_schedule",
                side_effect=[RuntimeError("output failed"), StopLoop()],
        ) as check_schedule, mock.patch.object(scheduler.time, "sleep"), \
                mock.patch.object(scheduler.logging, "warning"):
            with self.assertRaises(StopLoop):
                instance.run()

        self.assertEqual(check_schedule.call_count, 2)
        self.assertTrue(any(
            call.kwargs.get("ok") is False
            for call in patched["heartbeat"].call_args_list
        ))


if __name__ == "__main__":
    unittest.main()
