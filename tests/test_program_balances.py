import datetime
import unittest
from types import SimpleNamespace
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import programs as programs_module
from ospy import scheduler


class ProgramBalanceTests(unittest.TestCase):
    def test_enabled_weather_does_not_require_legacy_darksky_key(self):
        today = datetime.date.today()
        station = SimpleNamespace(
            balance={},
            eto_factor=-1.0,
            ignore_rain=False,
            index=0,
            precipitation=10.0,
            capacity=100.0,
        )
        manager = programs_module._Programs.__new__(programs_module._Programs)
        options = SimpleNamespace(use_weather=True)
        stations = SimpleNamespace(get=mock.Mock(return_value=[station]))
        weather = SimpleNamespace(
            get_eto=mock.Mock(return_value=3.0),
            get_rain=mock.Mock(return_value=2.5),
        )
        run_log = SimpleNamespace(
            finished_runs=mock.Mock(return_value=[]),
            active_runs=mock.Mock(return_value=[]),
        )

        with mock.patch.object(programs_module, "options", options), \
                mock.patch.object(programs_module, "stations", stations), \
                mock.patch.object(programs_module, "weather", weather), \
                mock.patch.object(programs_module, "log", run_log), \
                mock.patch.object(scheduler, "predicted_schedule", return_value=[]):
            manager.calculate_balances()

        self.assertEqual(station.balance[today]["eto"], -3.0)
        self.assertEqual(station.balance[today]["rain"], 2.5)
        self.assertTrue(station.balance[today]["valid"])
        weather.get_eto.assert_called()
        weather.get_rain.assert_called()


if __name__ == "__main__":
    unittest.main()
