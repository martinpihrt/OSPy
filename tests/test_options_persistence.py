import datetime
import os
import shelve
import sqlite3
import tempfile
import threading
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import health, options as options_module


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

    def test_failed_settings_callback_reports_and_then_resolves_issue(self):
        instance = options_module._Options.__new__(options_module._Options)
        instance._lock = threading.RLock()
        instance._values = {"example": "old"}
        instance._callbacks = {}
        instance._write_timer = None

        state = {"fail": True}

        def callback(key, old, new):
            if state["fail"]:
                raise ValueError("callback rejected value")

        callback_name = "{}.{}".format(
            callback.__module__, callback.__qualname__
        )
        issue_id = "options_callback:" + callback_name
        health.resolve_issue(issue_id)
        self.addCleanup(health.resolve_issue, issue_id)
        instance._callbacks["example"] = {
            "functions": [callback],
            "last_value": "old",
        }

        with self.assertLogs(level="ERROR"), \
                mock.patch.object(options_module, "Timer") as timer:
            instance.example = "broken"
            timer.assert_called_once()

        issue_ids = [item["id"] for item in health.active_issues()]
        self.assertIn(issue_id, issue_ids)

        state["fail"] = False
        with mock.patch.object(options_module, "Timer"):
            instance.example = "fixed"

        self.assertNotIn(
            issue_id, [item["id"] for item in health.active_issues()]
        )

    def test_failed_settings_write_reports_active_issue(self):
        issue_id = "options_save"
        health.resolve_issue(issue_id)
        self.addCleanup(health.resolve_issue, issue_id)

        with tempfile.TemporaryDirectory(prefix="ospy-options-write-error-") as root:
            instance = self._new_options(root)
            previous_last_save = instance.last_save
            instance.name = "Changed"
            with self.assertLogs(level="WARNING"), mock.patch.object(
                options_module.shutil, "move",
                side_effect=OSError("simulated write failure")
            ):
                instance.save_now()

            self.assertEqual(instance.last_save, previous_last_save)

        issue = next(
            item for item in health.active_issues()
            if item["id"] == issue_id
        )
        self.assertIn("simulated write failure", issue["details"])
        self.assertEqual(issue["link"], "/options")

    def test_failed_sqlite_mirror_does_not_block_shelve_save_or_reload(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-mirror-error-") as root:
            instance = self._new_options(root)
            instance.name = "Saved despite mirror failure"
            with mock.patch.object(
                    options_module, "sqlite_capability",
                    return_value={"available": True, "version": "3", "error": ""}), \
                    mock.patch.object(
                        options_module.sqlite_mirror_store, "write",
                        side_effect=OSError("simulated mirror failure")), \
                    self.assertLogs(level="WARNING") as captured:
                instance.save_now()

            instance.__del__()

            reloaded = options_module._Options()
            reloaded.__del__()
            self.addCleanup(reloaded.__del__)

            self.assertEqual(reloaded.name, "Saved despite mirror failure")
            self.assertTrue(any(
                "simulated mirror failure" in message
                for message in captured.output
            ))

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
            first.plugin_update_channel = "beta"
            first.save_now()
            mirror_path = options_module.sqlite_mirror_store.path_for(
                options_module.OPTIONS_FILE
            )
            self.assertTrue(os.path.isfile(mirror_path))
            mirror_values = options_module.sqlite_mirror_store.read(mirror_path)
            self.assertEqual(mirror_values["name"], "Test garden")
            self.assertEqual(mirror_values["rain_block"], rain_until)
            self.assertEqual(first.last_save, mirror_values["last_save"])
            first.__del__()

            second = options_module._Options()
            second.__del__()
            self.addCleanup(second.__del__)

            self.assertEqual(second.name, "Test garden")
            self.assertEqual(second.rain_block, rain_until)
            self.assertEqual(second.plugin_status["example"]["date"], status_date)
            self.assertEqual(second.plugin_status["example"]["hash"], "abc123")
            self.assertEqual(second.plugin_update_channel, "beta")
            self.assertEqual(second.last_save, mirror_values["last_save"])
            self.assertEqual(
                second._sqlite_mirror_verification["state"], "verified"
            )
            self.assertEqual(
                second._sqlite_mirror_verification["read_test"], "passed"
            )
            self.assertEqual(
                second._sqlite_mirror_verification["decoded_count"],
                len(mirror_values),
            )

    def test_shadow_divergence_never_changes_authoritative_loaded_settings(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-divergence-") as root:
            first = self._new_options(root)
            first.name = "Authoritative shelve garden"
            first.save_now()
            mirror_path = options_module.sqlite_mirror_store.path_for(
                options_module.OPTIONS_FILE
            )

            connection = sqlite3.connect(mirror_path)
            try:
                connection.execute(
                    "UPDATE settings SET checksum = ? WHERE key = ?",
                    ("0" * 64, "name"),
                )
                connection.commit()
            finally:
                connection.close()
            first.__del__()

            with self.assertLogs(level="WARNING"):
                second = options_module._Options()
            second.__del__()
            self.addCleanup(second.__del__)

            self.assertEqual(second.name, "Authoritative shelve garden")
            self.assertEqual(
                second._sqlite_mirror_verification["state"], "error"
            )

    def test_shadow_read_test_failure_never_replaces_shelve_settings(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-read-test-") as root:
            first = self._new_options(root)
            first.name = "Shelve remains active"
            first.save_now()
            first.__del__()

            with mock.patch.object(
                    options_module.sqlite_mirror_store, "read_verified",
                    side_effect=ValueError("simulated decode rejection")), \
                    self.assertLogs(level="WARNING"):
                second = options_module._Options()
            second.__del__()
            self.addCleanup(second.__del__)

            self.assertEqual(second.name, "Shelve remains active")
            self.assertEqual(
                second._sqlite_mirror_verification["state"],
                "read_test_failed",
            )
            self.assertIn(
                "simulated decode rejection",
                second._sqlite_mirror_verification["error"],
            )

    def test_legacy_database_keeps_values_and_adds_new_defaults(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-migration-") as root:
            default, unused_tmp, unused_backup = self._paths(root)
            os.makedirs(os.path.dirname(default), exist_ok=True)
            with shelve.open(default) as database:
                database["name"] = "Legacy garden"
                database["weather_lat"] = 50.1234
                database["weather_lon"] = 14.5678
                database["stormglass_key"] = "legacy-weather-key"
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
            self.assertEqual(instance.plugin_update_channel, "master")
            self.assertEqual(instance.weather_provider, "stormglass")
            self.assertEqual(
                instance._values["legacy_extension_value"], {"enabled": True}
            )
            self.assertNotIn("auto_login_key", instance._values)

    def test_legacy_weather_without_stormglass_key_uses_open_meteo(self):
        with tempfile.TemporaryDirectory(prefix="ospy-weather-provider-migration-") as root:
            default, unused_tmp, unused_backup = self._paths(root)
            os.makedirs(os.path.dirname(default), exist_ok=True)
            with shelve.open(default) as database:
                database["name"] = "Key-free legacy garden"
                database["use_weather"] = True

            instance = self._new_options(root)

            self.assertEqual(instance.weather_provider, "open_meteo")

    def test_invalid_stored_weather_provider_fails_safe(self):
        with tempfile.TemporaryDirectory(prefix="ospy-weather-provider-invalid-") as root:
            default, unused_tmp, unused_backup = self._paths(root)
            os.makedirs(os.path.dirname(default), exist_ok=True)
            with shelve.open(default) as database:
                database["weather_provider"] = "untrusted-provider"

            instance = self._new_options(root)

            self.assertEqual(instance.weather_provider, "open_meteo")

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

            with self.assertLogs(level="WARNING"):
                instance = self._new_options(root)

            self.assertEqual(instance.name, "Recovered settings")

    def test_invalid_primary_value_falls_back_to_valid_backup(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-invalid-") as root:
            default, unused_tmp, backup = self._paths(root)
            os.makedirs(os.path.dirname(default), exist_ok=True)
            os.makedirs(os.path.dirname(backup), exist_ok=True)
            with shelve.open(default) as database:
                database["name"] = "Damaged settings"
                database["output_count"] = "many"
            with shelve.open(backup) as database:
                database["name"] = "Last valid settings"
                database["last_save"] = 1.0

            with self.assertLogs(level="WARNING") as captured:
                instance = self._new_options(root)

            self.assertEqual(instance.name, "Last valid settings")
            self.assertTrue(any(
                "output_count" in message for message in captured.output
            ))

    def test_invalid_stored_object_fields_keep_safe_defaults(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-object-") as root:
            instance = self._new_options(root)

            class StoredObject(object):
                def __init__(self):
                    self.count = 3
                    self.labels = ["safe"]

            stored = StoredObject()
            storage_key = instance.cls_name(stored, 0)
            instance._values[storage_key] = {
                "count": "invalid",
                "labels": {"invalid": True},
                "unknown_field": "ignored",
            }

            with self.assertLogs(level="WARNING"):
                instance.load(stored, 0)

            self.assertEqual(stored.count, 3)
            self.assertEqual(stored.labels, ["safe"])
            self.assertFalse(hasattr(stored, "unknown_field"))
            self.assertNotIn(storage_key, instance._block)

    def test_legitimate_program_and_sensor_runtime_types_are_restored(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-runtime-") as root:
            instance = self._new_options(root)

            class StoredRuntimeValues(object):
                def __init__(self):
                    self.enabled = 0
                    self.fixed = 0
                    self.fw = 0
                    self.last_battery = ""
                    self.last_response = 0
                    self.prev_read_value = -127
                    self.rssi = ""

            stored = StoredRuntimeValues()
            storage_key = instance.cls_name(stored, 0)
            instance._values[storage_key] = {
                "enabled": True,
                "fixed": True,
                "fw": "119",
                "last_battery": 3.31,
                "last_response": 1234.5,
                "prev_read_value": 21.75,
                "rssi": -63,
            }

            with mock.patch.object(options_module.logging, "warning") as warning:
                instance.load(stored, 0)

            warning.assert_not_called()
            self.assertIs(stored.enabled, True)
            self.assertIs(stored.fixed, True)
            self.assertEqual(stored.fw, "119")
            self.assertEqual(stored.last_battery, 3.31)
            self.assertEqual(stored.last_response, 1234.5)
            self.assertEqual(stored.prev_read_value, 21.75)
            self.assertEqual(stored.rssi, -63)

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
