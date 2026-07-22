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
    def test_system_selects_keep_internal_values_and_translate_labels(self):
        definitions = {
            item["key"]: item for item in options_module._Options.OPTIONS
        }
        self.assertEqual(definitions["theme"]["default"], "basic")
        self.assertIn("basic", definitions["theme"]["option_names"])
        self.assertEqual(
            definitions["station_image_source"]["default"],
            "Station images",
        )
        self.assertIn(
            "Station images",
            definitions["station_image_source"]["option_names"],
        )
        self.assertEqual(definitions["scroll_top_position"]["default"], "right")
        self.assertIn(
            "right", definitions["scroll_top_position"]["option_names"]
        )

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

    def test_sqlite_controls_have_a_dedicated_settings_category(self):
        definitions = {
            item["key"]: item for item in options_module._Options.OPTIONS
        }
        storage_category = definitions["sqlite_emergency_recovery"]["category"]
        self.assertEqual(
            definitions["sqlite_preferred_reads"]["category"],
            storage_category,
        )
        self.assertEqual(
            definitions["sqlite_strict_dual_write"]["category"],
            storage_category,
        )
        self.assertNotEqual(definitions["name"]["category"], storage_category)
        self.assertEqual(
            {
                item["key"] for item in options_module._Options.OPTIONS
                if item.get("category") == storage_category
            },
            {
                "settings_storage_mode",
                "sqlite_emergency_recovery",
                "sqlite_preferred_reads",
                "sqlite_strict_dual_write",
            },
        )

    def test_legacy_storage_controls_infer_summary_mode(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-storage-mode-") as root:
            default, unused_temporary, unused_backup = self._paths(root)
            os.makedirs(os.path.dirname(default), exist_ok=True)
            with shelve.open(default) as database:
                database["sqlite_emergency_recovery"] = True
                database["sqlite_preferred_reads"] = True
                database["sqlite_strict_dual_write"] = True

            instance = self._new_options(root)

            self.assertEqual(instance.settings_storage_mode, "verification")

    def test_storage_mode_applies_profiles_and_preserves_custom_controls(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-storage-profile-") as root:
            instance = self._new_options(root)

            instance.apply_settings_storage_mode("verification")
            self.assertEqual(instance.settings_storage_mode, "verification")
            self.assertTrue(all(
                instance._values[key]
                for key in instance.SETTINGS_STORAGE_CONTROL_KEYS
            ))

            instance.sqlite_preferred_reads = False
            instance.refresh_settings_storage_mode()
            self.assertEqual(instance.settings_storage_mode, "custom")
            self.assertTrue(instance.sqlite_emergency_recovery)
            self.assertFalse(instance.sqlite_preferred_reads)
            self.assertTrue(instance.sqlite_strict_dual_write)

            instance.apply_settings_storage_mode("compatible")
            self.assertEqual(instance.settings_storage_mode, "compatible")
            self.assertFalse(any(
                instance._values[key]
                for key in instance.SETTINGS_STORAGE_CONTROL_KEYS
            ))

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

    def test_strict_dual_write_rejects_save_when_sqlite_fails(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-strict-write-") as root:
            instance = self._new_options(root)
            instance.sqlite_strict_dual_write = True
            instance.name = "Last verified dual-write settings"
            instance.save_now()
            committed_last_save = instance.last_save

            instance.name = "Uncommitted settings"
            with mock.patch.object(
                    options_module.sqlite_mirror_store, "write",
                    side_effect=OSError("simulated strict SQLite failure")), \
                    self.assertLogs(level="WARNING"):
                instance.save_now()

            self.assertEqual(instance.last_save, committed_last_save)
            self.assertFalse(os.path.isdir(os.path.dirname(options_module.OPTIONS_TMP)))
            self.assertEqual(
                instance._sqlite_mirror_verification["migration_evidence"]
                ["strict_write_streak"],
                0,
            )
            self.assertIn(
                "simulated strict SQLite failure",
                instance._sqlite_mirror_verification["migration_evidence"]
                ["last_error"],
            )
            instance.__del__()

            reloaded = options_module._Options()
            reloaded.__del__()
            self.addCleanup(reloaded.__del__)
            self.assertEqual(reloaded.name, "Last verified dual-write settings")
            self.assertTrue(reloaded.sqlite_strict_dual_write)

    def test_strict_dual_write_supports_verified_sqlite_reads(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-strict-read-") as root:
            first = self._new_options(root)
            first.sqlite_strict_dual_write = True
            first.sqlite_preferred_reads = True
            first.name = "Strict dual-write round trip"
            first.save_now()
            first.__del__()

            second = options_module._Options()
            second.__del__()
            self.addCleanup(second.__del__)
            self.assertEqual(second.name, "Strict dual-write round trip")
            self.assertEqual(
                second._sqlite_mirror_verification["preferred_read"], "used"
            )
            self.assertTrue(
                second._sqlite_mirror_verification["strict_dual_write_enabled"]
            )
            evidence = second._sqlite_mirror_verification["migration_evidence"]
            self.assertGreaterEqual(evidence["verified_start_streak"], 1)
            self.assertGreaterEqual(evidence["strict_write_streak"], 1)

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
            self.assertEqual(first._sqlite_mirror_verification["state"], "verified")
            self.assertEqual(first._sqlite_mirror_verification["read_test"], "passed")
            self.assertEqual(first._sqlite_mirror_verification["recovery_test"], "passed")
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
            self.assertEqual(
                second._sqlite_mirror_verification["recovery_test"], "passed"
            )
            self.assertEqual(
                second._sqlite_mirror_verification["restore_rehearsal"],
                "passed",
            )
            self.assertEqual(
                second._sqlite_mirror_verification["restore_rehearsal_source"],
                "current",
            )
            self.assertEqual(
                second._sqlite_mirror_verification["restore_rehearsal_count"],
                len(mirror_values),
            )
            self.assertEqual(
                second._sqlite_mirror_verification["emergency_selection"],
                "ready",
            )
            self.assertEqual(
                second._sqlite_mirror_verification["preferred_read"],
                "disabled",
            )
            self.assertEqual(
                second._sqlite_mirror_verification["emergency_selection_source"],
                "current",
            )
            second.name = "Save after successful restore rehearsal"
            second.save_now()
            self.assertEqual(
                second._sqlite_mirror_verification["restore_rehearsal"],
                "passed",
            )
            self.assertEqual(
                second._sqlite_mirror_verification["restore_rehearsal_source"],
                "current",
            )
            self.assertEqual(
                second._sqlite_mirror_verification["emergency_selection"],
                "ready",
            )

    def test_opt_in_verified_sqlite_read_path_matches_shelve_and_is_retained(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-preferred-read-") as root:
            first = self._new_options(root)
            first.sqlite_preferred_reads = True
            first.name = "Verified SQLite read path"
            first.save_now()
            mirror_path = options_module.sqlite_mirror_store.path_for(
                options_module.OPTIONS_FILE
            )
            expected_count = len(
                options_module.sqlite_mirror_store.read(mirror_path)
            )
            first.__del__()

            second = options_module._Options()
            second.__del__()
            self.addCleanup(second.__del__)

            self.assertEqual(second.name, "Verified SQLite read path")
            self.assertEqual(
                second._sqlite_mirror_verification["preferred_read"], "used"
            )
            self.assertEqual(
                second._sqlite_mirror_verification["preferred_read_count"],
                expected_count,
            )
            second.name = "Preferred read status survives a normal save"
            second.save_now()
            self.assertEqual(
                second._sqlite_mirror_verification["preferred_read"], "used"
            )

    def test_current_and_backup_sqlite_recovery_candidates_are_validated(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-recovery-pair-") as root:
            instance = self._new_options(root)
            instance.name = "Previous recovery snapshot"
            instance.save_now()
            instance.name = "Current recovery snapshot"
            instance.save_now()

            verification = instance._sqlite_mirror_verification
            self.assertEqual(verification["recovery_test"], "passed")
            self.assertEqual(verification["backup_recovery_test"], "passed")
            self.assertGreater(verification["recovery_count"], 0)
            self.assertGreater(verification["backup_recovery_count"], 0)

            backup_values = options_module.sqlite_mirror_store.read_recovery_candidate(
                options_module.sqlite_mirror_store.path_for(
                    options_module.OPTIONS_BACKUP
                )
            )
            self.assertEqual(backup_values["name"], "Previous recovery snapshot")

    def test_restore_rehearsal_uses_backup_when_current_shadow_is_damaged(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-restore-backup-") as root:
            first = self._new_options(root)
            first.name = "Previous SQLite recovery snapshot"
            first.save_now()
            first.name = "Authoritative current shelve settings"
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

            self.assertEqual(
                second.name, "Authoritative current shelve settings"
            )
            self.assertEqual(
                second._sqlite_mirror_verification["restore_rehearsal"],
                "passed",
            )
            self.assertEqual(
                second._sqlite_mirror_verification["restore_rehearsal_source"],
                "backup",
            )
            self.assertEqual(
                second._sqlite_mirror_verification["emergency_selection_source"],
                "backup",
            )

    def test_invalid_shelve_candidates_only_simulate_sqlite_selection(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-emergency-dry-run-") as root:
            first = self._new_options(root)
            first.name = "SQLite data must remain unused"
            first.save_now()
            first.name = "Current SQLite data must remain unused"
            first.save_now()
            default, unused_temporary, backup = self._paths(root)
            first.__del__()

            for path in (default, backup):
                with shelve.open(path) as database:
                    database["output_count"] = "invalid"

            with self.assertLogs(level="WARNING"):
                second = options_module._Options()
            second.__del__()
            self.addCleanup(second.__del__)

            self.assertIsNone(second._load_source)
            self.assertNotEqual(
                second.name, "Current SQLite data must remain unused"
            )
            self.assertEqual(
                second._sqlite_mirror_verification["emergency_selection"],
                "ready",
            )
            self.assertEqual(
                second._sqlite_mirror_verification["emergency_selection_source"],
                "current",
            )
            self.assertGreater(
                second._sqlite_mirror_verification["emergency_selection_count"],
                0,
            )

    def test_emergency_recovery_marker_follows_verified_opt_in(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-recovery-marker-") as root:
            instance = self._new_options(root)
            marker = instance._sqlite_emergency_marker_path()
            self.assertFalse(os.path.exists(marker))

            instance.sqlite_emergency_recovery = True
            instance.save_now()
            self.assertTrue(os.path.isfile(marker))
            with open(marker, "r", encoding="ascii") as marker_file:
                self.assertEqual(marker_file.read().strip(), "enabled-v1")

            instance.sqlite_emergency_recovery = False
            instance.save_now()
            self.assertFalse(os.path.exists(marker))

    def test_marker_write_failure_never_activates_emergency_recovery(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-marker-failure-") as root:
            instance = self._new_options(root)
            instance.sqlite_emergency_recovery = True
            marker = instance._sqlite_emergency_marker_path()
            with mock.patch.object(
                    options_module._Options,
                    "_write_sqlite_emergency_marker",
                    side_effect=OSError("simulated marker write failure")), \
                    self.assertLogs(level="WARNING"):
                instance.save_now()

            self.assertFalse(os.path.exists(marker))
            self.assertTrue(instance.sqlite_emergency_recovery)
            with shelve.open(options_module.OPTIONS_FILE, flag="r") as database:
                self.assertTrue(database["sqlite_emergency_recovery"])

    def test_disabling_marker_fails_closed_before_settings_write(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-marker-disable-") as root:
            instance = self._new_options(root)
            instance.sqlite_emergency_recovery = True
            instance.save_now()
            marker = instance._sqlite_emergency_marker_path()
            self.assertTrue(os.path.isfile(marker))

            instance.sqlite_emergency_recovery = False
            with mock.patch.object(
                    options_module.settings_store, "write",
                    side_effect=OSError("simulated settings failure")), \
                    self.assertLogs(level="WARNING"):
                instance.save_now()

            self.assertFalse(os.path.exists(marker))

    def test_marker_alone_cannot_enable_emergency_recovery(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-recovery-marker-only-") as root:
            first = self._new_options(root)
            first.name = "SQLite copy has no recovery permission"
            first.save_now()
            marker = first._sqlite_emergency_marker_path()
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            with open(marker, "w", encoding="ascii") as marker_file:
                marker_file.write("enabled-v1\n")
            default, unused_temporary, backup = self._paths(root)
            first.__del__()
            for path in (default, backup):
                with shelve.open(path) as database:
                    database["output_count"] = "invalid"

            with self.assertLogs(level="WARNING"):
                second = options_module._Options()
            second.__del__()
            self.addCleanup(second.__del__)

            self.assertIsNone(second._load_source)
            self.assertNotEqual(
                second.name, "SQLite copy has no recovery permission"
            )
            self.assertIn(
                "does not contain recovery permission",
                second._sqlite_emergency_recovery_error,
            )

    def test_opt_in_recovers_from_current_sqlite_only_after_all_shelves_fail(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-recovery-current-") as root:
            first = self._new_options(root)
            first.sqlite_emergency_recovery = True
            first.name = "Verified current emergency settings"
            first.save_now()
            default, temporary, backup = self._paths(root)
            first.__del__()
            for path in (default, backup):
                with shelve.open(path) as database:
                    database["output_count"] = "invalid"

            with self.assertLogs(level="WARNING"):
                second = options_module._Options()
            second.__del__()
            self.addCleanup(second.__del__)

            self.assertEqual(second.name, "Verified current emergency settings")
            self.assertEqual(second._load_source, temporary)
            self.assertEqual(second._sqlite_emergency_recovered_from, "current")
            self.assertTrue(second.sqlite_emergency_recovery)
            self.assertTrue(os.path.isdir(os.path.dirname(temporary)))
            self.assertGreater(len(second.recovery_messages()), 0)

    def test_opt_in_falls_back_to_verified_backup_sqlite(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-recovery-backup-") as root:
            first = self._new_options(root)
            first.sqlite_emergency_recovery = True
            first.name = "Verified backup emergency settings"
            first.save_now()
            first.name = "Damaged current emergency settings"
            first.save_now()
            default, temporary, backup = self._paths(root)
            mirror_path = options_module.sqlite_mirror_store.path_for(default)
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
            for path in (default, backup):
                with shelve.open(path) as database:
                    database["output_count"] = "invalid"

            with self.assertLogs(level="WARNING"):
                second = options_module._Options()
            second.__del__()
            self.addCleanup(second.__del__)

            self.assertEqual(second.name, "Verified backup emergency settings")
            self.assertEqual(second._load_source, temporary)
            self.assertEqual(second._sqlite_emergency_recovered_from, "backup")

    def test_restore_rehearsal_failure_keeps_shelve_authoritative(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-restore-failure-") as root:
            first = self._new_options(root)
            first.name = "Shelve survives restore rehearsal"
            first.save_now()
            first.__del__()

            with mock.patch.object(
                    options_module._Options, "_sqlite_restore_rehearsal",
                    side_effect=ValueError("simulated disposable restore failure")), \
                    self.assertLogs(level="WARNING"):
                second = options_module._Options()
            second.__del__()
            self.addCleanup(second.__del__)

            self.assertEqual(second.name, "Shelve survives restore rehearsal")
            self.assertEqual(
                second._sqlite_mirror_verification["restore_rehearsal"],
                "failed",
            )
            self.assertIn(
                "simulated disposable restore failure",
                second._sqlite_mirror_verification["restore_rehearsal_error"],
            )

    def test_recovery_dry_run_failure_does_not_fail_primary_save(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-recovery-failure-") as root:
            instance = self._new_options(root)
            instance.name = "Shelve survives recovery test"
            with mock.patch.object(
                    options_module.sqlite_mirror_store,
                    "read_recovery_candidate",
                    side_effect=ValueError("simulated recovery rejection")), \
                    self.assertLogs(level="WARNING"):
                instance.save_now()

            self.assertEqual(
                instance._sqlite_mirror_verification["recovery_test"], "failed"
            )
            instance.__del__()

            reloaded = options_module._Options()
            reloaded.__del__()
            self.addCleanup(reloaded.__del__)
            self.assertEqual(reloaded.name, "Shelve survives recovery test")

    def test_shadow_divergence_never_changes_authoritative_loaded_settings(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-divergence-") as root:
            first = self._new_options(root)
            first.sqlite_preferred_reads = True
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
            self.assertEqual(
                second._sqlite_mirror_verification["preferred_read"],
                "fallback",
            )

    def test_shadow_read_test_failure_never_replaces_shelve_settings(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-read-test-") as root:
            first = self._new_options(root)
            first.sqlite_preferred_reads = True
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
            self.assertEqual(
                second._sqlite_mirror_verification["preferred_read"],
                "fallback",
            )

    def test_post_save_shadow_read_failure_does_not_fail_primary_save(self):
        with tempfile.TemporaryDirectory(prefix="ospy-options-save-read-test-") as root:
            instance = self._new_options(root)
            instance.name = "Primary save remains valid"
            with mock.patch.object(
                    options_module.sqlite_mirror_store, "read_verified",
                    side_effect=ValueError("simulated post-save rejection")), \
                    self.assertLogs(level="WARNING"):
                instance.save_now()

            self.assertEqual(instance.name, "Primary save remains valid")
            self.assertEqual(
                instance._sqlite_mirror_verification["state"],
                "read_test_failed",
            )
            instance.__del__()

            reloaded = options_module._Options()
            reloaded.__del__()
            self.addCleanup(reloaded.__del__)
            self.assertEqual(reloaded.name, "Primary save remains valid")

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
            self.assertFalse(instance.sqlite_emergency_recovery)
            self.assertFalse(instance.sqlite_preferred_reads)
            self.assertFalse(instance.sqlite_strict_dual_write)
            self.assertEqual(instance.settings_storage_mode, "compatible")
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
