import datetime
import os
import shelve
import tempfile
import threading
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import options as options_module


class OptionsPersistenceTests(unittest.TestCase):
    def _paths(self, root):
        return (
            os.path.join(root, "default", "options.db"),
            os.path.join(root, "tmp", "options.db"),
            os.path.join(root, "backup", "options.db"),
        )

    def _new_options(self, root):
        options_module.options.__del__()
        default, temporary, backup = self._paths(root)
        os.makedirs(os.path.dirname(default), exist_ok=True)
        patches = (
            mock.patch.object(options_module, "OPTIONS_FILE", default),
            mock.patch.object(options_module, "OPTIONS_TMP", temporary),
            mock.patch.object(options_module, "OPTIONS_BACKUP", backup),
        )
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        instance = options_module._Options()
        instance.__del__()
        self.addCleanup(instance.__del__)
        return instance

    def test_values_and_nested_dates_survive_save_and_reload(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-roundtrip-") as root:
            first = self._new_options(root)
            rain_until = datetime.datetime(2030, 6, 1, 12, 30)
            status_date = datetime.datetime(2030, 5, 31, 9, 15)
            first.name = "Test garden"
            first.rain_block = rain_until
            first.plugin_status = {
                "example": {"date": status_date, "hash": "abc123"}
            }
            first.save_now()
            first.__del__()

            second = options_module._Options()
            second.__del__()
            self.addCleanup(second.__del__)

            self.assertEqual(second.name, "Test garden")
            self.assertEqual(second.rain_block, rain_until)
            self.assertEqual(second.plugin_status["example"]["date"], status_date)
            self.assertEqual(second.plugin_status["example"]["hash"], "abc123")

    def test_legacy_database_keeps_values_and_adds_new_defaults(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-migration-") as root:
            default, unused_tmp, unused_backup = self._paths(root)
            os.makedirs(os.path.dirname(default), exist_ok=True)
            with shelve.open(default) as database:
                database["name"] = "Legacy garden"
                database["weather_lat"] = 50.1234
                database["weather_lon"] = 14.5678
                database["rain_block"] = "DATETIME:2031-02-03 04:05:06"
                database["legacy_extension_value"] = {"enabled": True}
                database["auto_login_key"] = "obsolete-secret"

            instance = self._new_options(root)

            self.assertEqual(instance.name, "Legacy garden")
            self.assertEqual(instance.weather_lat, "50.1234")
            self.assertEqual(instance.weather_lon, "14.5678")
            self.assertEqual(
                instance.rain_block, datetime.datetime(2031, 2, 3, 4, 5, 6)
            )
            self.assertTrue(instance.show_diagnostics_modal_home)
            self.assertEqual(
                instance._values["legacy_extension_value"], {"enabled": True}
            )
            self.assertNotIn("auto_login_key", instance._values)

    def test_empty_primary_database_falls_back_to_valid_backup(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-fallback-") as root:
            default, unused_tmp, backup = self._paths(root)
            os.makedirs(os.path.dirname(default), exist_ok=True)
            os.makedirs(os.path.dirname(backup), exist_ok=True)
            with shelve.open(default):
                pass
            with shelve.open(backup) as database:
                database["name"] = "Recovered settings"
                database["last_save"] = 1.0

            instance = self._new_options(root)

            self.assertEqual(instance.name, "Recovered settings")

    def test_option_mutation_waits_for_active_database_write(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-lock-") as root:
            instance = self._new_options(root)
            started = threading.Event()
            finished = threading.Event()

            def update_option():
                started.set()
                instance.name = "Serialized update"
                finished.set()

            with instance._lock:
                worker = threading.Thread(target=update_option)
                worker.start()
                self.assertTrue(started.wait(1.0))
                self.assertFalse(finished.wait(0.05))

            worker.join(1.0)
            self.assertFalse(worker.is_alive())
            self.assertTrue(finished.is_set())
            self.assertEqual(instance.name, "Serialized update")
            instance.__del__()


if __name__ == "__main__":
    unittest.main()
