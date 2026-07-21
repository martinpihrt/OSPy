import builtins
import datetime
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import settings_storage


class SettingsStorageTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
