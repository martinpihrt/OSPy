import builtins
import datetime
import hashlib
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import settings_storage


class SettingsStorageTests(unittest.TestCase):
    def test_sqlite_primary_readiness_requires_checks_and_evidence(self):
        status = {
            "settings_storage_mode": "verification",
            "state": "verified",
            "read_test": "passed",
            "recovery_test": "passed",
            "backup_recovery_test": "passed",
            "restore_rehearsal": "passed",
            "emergency_selection": "ready",
            "emergency_recovery_enabled": True,
            "preferred_read": "used",
            "strict_dual_write_enabled": True,
            "migration_evidence": {
                "verified_start_streak": 5,
                "strict_write_streak": 20,
            },
        }

        ready = settings_storage.sqlite_primary_readiness(status)
        self.assertEqual(ready["state"], "ready")
        self.assertEqual(ready["blockers"], [])
        self.assertEqual(ready["collecting"], [])

        status["settings_storage_mode"] = "sqlite_primary"
        self.assertEqual(
            settings_storage.sqlite_primary_readiness(status)["state"],
            "ready",
        )
        status["settings_storage_mode"] = "verification"

        status["migration_evidence"]["verified_start_streak"] = 4
        collecting = settings_storage.sqlite_primary_readiness(status)
        self.assertEqual(collecting["state"], "collecting")
        self.assertEqual(collecting["collecting"], ["verified_starts"])

        status["backup_recovery_test"] = "failed"
        blocked = settings_storage.sqlite_primary_readiness(status)
        self.assertEqual(blocked["state"], "blocked")
        self.assertIn("backup_recovery", blocked["blockers"])

    def test_migration_evidence_counts_successes_and_resets_failed_path(self):
        with tempfile.TemporaryDirectory(prefix="ospy-storage-evidence-") as root:
            path = os.path.join(root, "sqlite_migration_evidence.json")
            evidence = settings_storage.SQLiteMigrationEvidence()

            first = evidence.record(path, "verified_start", True)
            second = evidence.record(path, "verified_start", True)
            written = evidence.record(path, "strict_write", True)
            failed = evidence.record(
                path, "strict_write", False, "simulated disk failure"
            )

            self.assertEqual(first["verified_start_streak"], 1)
            self.assertEqual(second["verified_start_streak"], 2)
            self.assertEqual(written["strict_write_streak"], 1)
            self.assertEqual(failed["verified_start_streak"], 2)
            self.assertEqual(failed["strict_write_streak"], 0)
            self.assertEqual(failed["last_failure_event"], "strict_write")
            self.assertEqual(failed["last_error"], "simulated disk failure")
            self.assertFalse(os.path.exists(path + ".new"))

    def test_invalid_migration_evidence_is_non_authoritative(self):
        with tempfile.TemporaryDirectory(prefix="ospy-storage-evidence-bad-") as root:
            path = os.path.join(root, "sqlite_migration_evidence.json")
            with open(path, "w", encoding="utf-8") as target:
                target.write("not-json")

            status = settings_storage.SQLiteMigrationEvidence().read(path)

            self.assertEqual(status["verified_start_streak"], 0)
            self.assertEqual(status["strict_write_streak"], 0)
            self.assertEqual(status["last_error"], "")

    def test_shelve_store_round_trip_preserves_existing_value_types(self):
        with tempfile.TemporaryDirectory(prefix="ospy-storage-") as root:
            path = os.path.join(root, "options.db")
            stored = {
                "name": "Garden",
                "date": datetime.date(2030, 5, 6),
                "nested": {"enabled": True, "values": [1, 2, 3]},
            }
            store = settings_storage.ShelveSettingsStore()

            saved_at = store.write(path, stored, saved_at=123.5)
            loaded = store.read(path)

            self.assertEqual(saved_at, 123.5)
            self.assertEqual(loaded["name"], stored["name"])
            self.assertEqual(loaded["date"], stored["date"])
            self.assertEqual(loaded["nested"], stored["nested"])
            self.assertEqual(loaded["last_save"], 123.5)
            self.assertEqual(store.last_save(path), 123.5)
            self.assertTrue(store.backend(path))

    def test_active_settings_backend_remains_shelve(self):
        self.assertIsInstance(
            settings_storage.settings_store,
            settings_storage.ShelveSettingsStore,
        )
        self.assertEqual(settings_storage.settings_store.name, "shelve")

    def test_sqlite_probe_uses_memory_and_creates_no_file(self):
        with tempfile.TemporaryDirectory(prefix="ospy-sqlite-probe-") as root:
            before = os.listdir(root)
            with mock.patch.object(
                    sqlite3, "connect", wraps=sqlite3.connect) as connect:
                result = settings_storage.sqlite_capability(refresh=True)
            after = os.listdir(root)

        self.assertTrue(result["available"], result["error"])
        self.assertTrue(result["version"])
        connect.assert_called_once_with(":memory:")
        self.assertEqual(before, after)

    def test_missing_sqlite_is_reported_without_breaking_storage(self):
        original_import = builtins.__import__

        def import_without_sqlite(name, *args, **kwargs):
            if name == "sqlite3":
                raise ModuleNotFoundError("simulated missing sqlite3")
            return original_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=import_without_sqlite):
            result = settings_storage.sqlite_capability(refresh=True)

        self.assertFalse(result["available"])
        self.assertIn("simulated missing sqlite3", result["error"])
        self.assertIsInstance(
            settings_storage.settings_store,
            settings_storage.ShelveSettingsStore,
        )

        settings_storage.sqlite_capability(refresh=True)

    def test_sqlite_mirror_round_trip_and_status(self):
        with tempfile.TemporaryDirectory(prefix="ospy-sqlite-mirror-") as root:
            path = os.path.join(root, "options.sqlite3")
            values = {
                "name": "Mirror garden",
                "date": datetime.date(2031, 7, 8),
                "nested": {"values": [1, 2], "enabled": True},
            }

            written = settings_storage.sqlite_mirror_store.write(
                path, values, saved_at=456.75
            )
            loaded = settings_storage.sqlite_mirror_store.read(path)
            status = settings_storage.sqlite_mirror_store.status(path)

            self.assertEqual(written["state"], "synchronized")
            self.assertEqual(loaded["name"], values["name"])
            self.assertEqual(loaded["date"], values["date"])
            self.assertEqual(loaded["nested"], values["nested"])
            self.assertEqual(loaded["last_save"], 456.75)
            self.assertEqual(status["state"], "synchronized")
            self.assertEqual(status["count"], len(values) + 1)
            self.assertEqual(status["last_save"], 456.75)
            self.assertFalse(os.path.exists(path + ".new"))

            comparison = settings_storage.sqlite_mirror_store.compare(
                path, loaded
            )
            self.assertEqual(comparison["state"], "verified")
            self.assertEqual(comparison["difference_count"], 0)
            reconstructed = settings_storage.sqlite_mirror_store.read_verified(
                path, loaded
            )
            self.assertEqual(reconstructed, loaded)
            with mock.patch.object(
                    settings_storage.pickle, "loads",
                    wraps=settings_storage.pickle.loads) as decode:
                language_value = \
                    settings_storage.sqlite_mirror_store.read_verified_value(
                        path, "name", loaded
                    )
            self.assertEqual(language_value, loaded["name"])
            self.assertEqual(decode.call_count, 1)
            recovery = settings_storage.sqlite_mirror_store.read_recovery_candidate(
                path
            )
            self.assertEqual(recovery, loaded)

            changed = dict(loaded)
            changed["name"] = "Different garden"
            comparison = settings_storage.sqlite_mirror_store.compare(
                path, changed
            )
            self.assertEqual(comparison["state"], "diverged")
            self.assertIn("changed: name", comparison["differences"])

    def test_damaged_sqlite_mirror_is_reported_without_becoming_a_source(self):
        with tempfile.TemporaryDirectory(prefix="ospy-sqlite-damaged-") as root:
            path = os.path.join(root, "options.sqlite3")
            with open(path, "wb") as damaged:
                damaged.write(b"not a sqlite database")

            status = settings_storage.sqlite_mirror_store.status(path)

            self.assertEqual(status["state"], "error")
            self.assertTrue(status["error"])
            self.assertIsInstance(
                settings_storage.settings_store,
                settings_storage.ShelveSettingsStore,
            )

    def test_checksum_damage_is_detected_without_unpickling_mirror_values(self):
        with tempfile.TemporaryDirectory(prefix="ospy-sqlite-checksum-") as root:
            path = os.path.join(root, "options.sqlite3")
            settings_storage.sqlite_mirror_store.write(
                path, {"name": "Safe garden"}, saved_at=789.0
            )
            connection = sqlite3.connect(path)
            try:
                connection.execute(
                    "UPDATE settings SET checksum = ? WHERE key = ?",
                    ("0" * 64, "name"),
                )
                connection.commit()
            finally:
                connection.close()

            with mock.patch("pickle.loads") as unsafe_load:
                status = settings_storage.sqlite_mirror_store.status(path)
                with self.assertRaises(ValueError):
                    settings_storage.sqlite_mirror_store.read_verified(
                        path, {"name": "Safe garden", "last_save": 789.0}
                    )

            self.assertEqual(status["state"], "error")
            self.assertIn("checksum", status["error"].lower())
            unsafe_load.assert_not_called()

    def test_schema_one_shadow_waits_for_safe_replacement(self):
        with tempfile.TemporaryDirectory(prefix="ospy-sqlite-schema-one-") as root:
            path = os.path.join(root, "options.sqlite3")
            connection = sqlite3.connect(path)
            try:
                connection.execute(
                    "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
                )
                connection.execute(
                    "CREATE TABLE settings (key TEXT PRIMARY KEY, value BLOB NOT NULL)"
                )
                connection.executemany(
                    "INSERT INTO metadata (key, value) VALUES (?, ?)",
                    [("schema_version", "1"), ("last_save", "123.0")],
                )
                connection.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?)",
                    ("name", sqlite3.Binary(b"legacy")),
                )
                connection.commit()
            finally:
                connection.close()

            status = settings_storage.sqlite_mirror_store.status(path)

            self.assertEqual(status["state"], "upgrade_pending")
            self.assertEqual(status["schema_version"], 1)

    def test_schema_two_shadow_waits_for_safe_replacement(self):
        with tempfile.TemporaryDirectory(prefix="ospy-sqlite-schema-two-") as root:
            path = os.path.join(root, "options.sqlite3")
            value = b"schema-two-value"
            connection = sqlite3.connect(path)
            try:
                connection.execute(
                    "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
                )
                connection.execute(
                    "CREATE TABLE settings ("
                    "key TEXT PRIMARY KEY, value BLOB NOT NULL, checksum TEXT NOT NULL)"
                )
                connection.executemany(
                    "INSERT INTO metadata (key, value) VALUES (?, ?)",
                    [("schema_version", "2"), ("last_save", "234.0")],
                )
                connection.execute(
                    "INSERT INTO settings (key, value, checksum) VALUES (?, ?, ?)",
                    ("name", sqlite3.Binary(value), hashlib.sha256(value).hexdigest()),
                )
                connection.commit()
            finally:
                connection.close()

            status = settings_storage.sqlite_mirror_store.status(path)

            self.assertEqual(status["state"], "upgrade_pending")
            self.assertEqual(status["schema_version"], 2)

    def test_deleted_recovery_row_fails_manifest_before_unpickling(self):
        with tempfile.TemporaryDirectory(prefix="ospy-sqlite-deleted-row-") as root:
            path = os.path.join(root, "options.sqlite3")
            settings_storage.sqlite_mirror_store.write(
                path, {"name": "Complete garden", "enabled": True},
                saved_at=901.0,
            )
            connection = sqlite3.connect(path)
            try:
                connection.execute("DELETE FROM settings WHERE key = ?", ("name",))
                connection.commit()
            finally:
                connection.close()

            with mock.patch("pickle.loads") as unsafe_load:
                status = settings_storage.sqlite_mirror_store.status(path)
                with self.assertRaises(ValueError):
                    settings_storage.sqlite_mirror_store.read_recovery_candidate(
                        path
                    )

            self.assertEqual(status["state"], "error")
            self.assertTrue(
                "record" in status["error"].lower() or
                "snapshot" in status["error"].lower()
            )
            unsafe_load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
