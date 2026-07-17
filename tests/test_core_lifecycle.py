import threading
import time
import os
import tempfile
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
import plugins
from ospy import options as options_module
from ospy import scheduler as scheduler_module
from ospy import sensors as sensors_module
from ospy import server
from ospy import weather as weather_module


class CooperativeWorkerTests(unittest.TestCase):
    @staticmethod
    def _assert_sleep_is_interruptible(instance):
        worker = threading.Thread(target=instance._sleep, args=(60,))
        worker.start()
        time.sleep(0.02)
        instance.request_stop()
        worker.join(0.5)
        if worker.is_alive():
            raise AssertionError("worker sleep did not react to the stop event")

    def test_sensor_sleep_reacts_to_stop_event(self):
        instance = sensors_module._Sensors_Timer.__new__(
            sensors_module._Sensors_Timer
        )
        threading.Thread.__init__(instance)
        instance._sleep_time = 0
        instance._stop_event = threading.Event()
        self._assert_sleep_is_interruptible(instance)

    def test_scheduler_loop_stops_within_bound(self):
        instance = scheduler_module._Scheduler.__new__(
            scheduler_module._Scheduler
        )
        threading.Thread.__init__(instance)
        instance._stop_event = threading.Event()
        instance._reported_blocked = {}
        checked = threading.Event()

        def check_schedule():
            checked.set()

        with mock.patch.object(
                scheduler_module._Scheduler,
                "_check_schedule",
                side_effect=check_schedule,
        ), mock.patch.multiple(
                scheduler_module,
                options=mock.Mock(manual_mode=False, scheduler_enabled=True),
                log=mock.Mock(active_runs=lambda: []),
                rain_blocks=mock.Mock(
                    block_end=lambda: scheduler_module.datetime.datetime.min
                ),
                inputs=mock.Mock(rain_sensed=lambda: False),
                update_details=mock.DEFAULT,
                heartbeat=mock.DEFAULT,
        ):
            instance.start()
            self.assertTrue(checked.wait(0.5))
            instance.request_stop()
            self.assertTrue(instance.wait_stopped(0.5))

    def test_weather_sleep_reacts_to_stop_event(self):
        instance = weather_module._Weather.__new__(weather_module._Weather)
        threading.Thread.__init__(instance)
        instance._sleep_time = 0
        instance._stop_event = threading.Event()
        self._assert_sleep_is_interruptible(instance)

    def test_plugin_checker_sleep_reacts_to_stop_event(self):
        instance = plugins._PluginChecker.__new__(plugins._PluginChecker)
        threading.Thread.__init__(instance)
        instance._sleep_time = 0
        instance._stop_event = threading.Event()
        self._assert_sleep_is_interruptible(instance)


class OptionsShutdownTests(unittest.TestCase):
    def test_flush_cancels_pending_timer_and_writes_immediately(self):
        instance = options_module._Options.__new__(options_module._Options)
        instance._lock = threading.RLock()
        timer = mock.Mock()
        timer.is_alive.return_value = False
        instance._write_timer = timer
        instance._write = mock.Mock()

        instance.flush()

        timer.cancel.assert_called_once_with()
        self.assertIsNone(instance._write_timer)
        instance._write.assert_called_once_with()

    def test_cleanup_waits_for_an_already_running_writer(self):
        instance = options_module._Options.__new__(options_module._Options)
        instance._lock = threading.RLock()
        timer = mock.Mock()
        timer.is_alive.return_value = True
        instance._write_timer = timer

        instance.cancel_pending_write()

        timer.cancel.assert_called_once_with()
        timer.join.assert_called_once_with(
            options_module.OPTIONS_WRITE_STOP_TIMEOUT
        )
        self.assertIsNone(instance._write_timer)


class ServerShutdownTests(unittest.TestCase):
    def tearDown(self):
        server._stopping = False

    def test_safe_stop_clears_runs_stations_and_master_relay(self):
        programs = mock.Mock(run_now_program=object())
        run_once = mock.Mock()
        run_log = mock.Mock()
        stations = mock.Mock()
        outputs = mock.Mock(relay_output=True)

        with mock.patch("ospy.programs.programs", programs), \
                mock.patch("ospy.runonce.run_once", run_once), \
                mock.patch("ospy.log.log", run_log), \
                mock.patch("ospy.stations.stations", stations), \
                mock.patch("ospy.outputs.outputs", outputs):
            server._safe_stop_outputs()

        self.assertIsNone(programs.run_now_program)
        run_once.clear.assert_called_once_with()
        run_log.finish_run.assert_called_once_with(None)
        stations.clear.assert_called_once_with()
        self.assertFalse(outputs.relay_output)

    def test_server_stop_is_ordered_and_idempotent(self):
        calls = []
        web_server = mock.Mock()
        web_server.stop.side_effect = lambda: calls.append("web")
        server.__dict__["__server"] = web_server
        server._stopping = False

        with mock.patch.object(
                server, "_request_core_stop",
                side_effect=lambda: calls.append("request-core"),
        ), mock.patch.object(
                server, "_safe_stop_outputs",
                side_effect=lambda: calls.append("outputs"),
        ), mock.patch.object(
                server.plugins, "stop_all_plugins",
                side_effect=lambda timeout: calls.append("plugins") or [],
        ), mock.patch.object(
                server, "_wait_for_core_stop",
                side_effect=lambda timeout: calls.append("wait-core") or [],
        ), mock.patch.object(
                options_module._Options, "flush",
                side_effect=lambda: calls.append("flush"),
        ), mock.patch.object(
                server, "close_sessions",
                side_effect=lambda: calls.append("sessions"),
        ), mock.patch.object(server.logEV, "save_events_log"), \
                mock.patch("ospy.webpages.stop_diagnostics_history"):
            server.stop()
            server.stop()

        self.assertEqual(
            calls,
            [
                "web", "request-core", "outputs", "plugins", "outputs",
                "wait-core", "outputs", "flush", "sessions",
            ],
        )

    def test_damaged_session_database_is_recreated(self):
        with tempfile.TemporaryDirectory(prefix="ospy-sessions-damaged-") as root:
            session_file = os.path.join(root, "sessions.db")
            damaged_file = session_file + ".broken"
            with open(damaged_file, "wb") as file_handle:
                file_handle.write(b"damaged")
            replacement = mock.Mock()

            with mock.patch.object(
                    server.shelve, "open",
                    side_effect=[RuntimeError("damaged database"), replacement],
            ), mock.patch.object(server.log, "error") as error_log:
                opened = server._open_session_store(session_file)

            self.assertIs(opened, replacement)
            self.assertFalse(os.path.exists(damaged_file))
            self.assertTrue(error_log.called)


if __name__ == "__main__":
    unittest.main()
