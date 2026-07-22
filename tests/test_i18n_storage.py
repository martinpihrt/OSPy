import glob
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n


class I18nStorageBootstrapTests(unittest.TestCase):
    def _settings_path(self, root):
        return os.path.join(root, "default", "options.db")

    def _write_pair(self, root, language="cs_CZ", preferred=True):
        path = self._settings_path(root)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        values = {
            "lang": language,
            "sqlite_preferred_reads": preferred,
        }
        saved_at = i18n.settings_store.write(path, values, saved_at=123.0)
        i18n.sqlite_mirror_store.write(
            i18n.sqlite_mirror_store.path_for(path), values, saved_at
        )
        return path

    def test_missing_language_database_is_not_created(self):
        with tempfile.TemporaryDirectory(prefix="ospy-i18n-missing-") as root:
            path = self._settings_path(root)
            with mock.patch.object(i18n, "OPTIONS_FILES", [path]):
                language = i18n.load_saved_language()

            self.assertEqual(language, "default")
            self.assertEqual(glob.glob(path + "*"), [])

    def test_verified_sqlite_language_is_used_only_after_shelve_match(self):
        with tempfile.TemporaryDirectory(prefix="ospy-i18n-verified-") as root:
            path = self._write_pair(root)
            with mock.patch.object(i18n, "OPTIONS_FILES", [path]), \
                    mock.patch.object(
                        i18n, "sqlite_capability",
                        return_value={"available": True, "version": "3", "error": ""}
                    ), \
                    mock.patch.object(
                        i18n.sqlite_mirror_store, "read_verified_value",
                        wraps=i18n.sqlite_mirror_store.read_verified_value,
                    ) as verified_read:
                language = i18n.load_saved_language()

            self.assertEqual(language, "cs_CZ")
            verified_read.assert_called_once()

    def test_damaged_sqlite_language_falls_back_to_shelve(self):
        with tempfile.TemporaryDirectory(prefix="ospy-i18n-fallback-") as root:
            path = self._write_pair(root)
            mirror_path = i18n.sqlite_mirror_store.path_for(path)
            connection = sqlite3.connect(mirror_path)
            try:
                connection.execute(
                    "UPDATE settings SET checksum = ? WHERE key = ?",
                    ("0" * 64, "lang"),
                )
                connection.commit()
            finally:
                connection.close()

            with mock.patch.object(i18n, "OPTIONS_FILES", [path]), \
                    mock.patch.object(
                        i18n, "sqlite_capability",
                        return_value={"available": True, "version": "3", "error": ""}
                    ):
                language = i18n.load_saved_language()

            self.assertEqual(language, "cs_CZ")

    def test_disabled_verified_reads_never_open_sqlite(self):
        with tempfile.TemporaryDirectory(prefix="ospy-i18n-disabled-") as root:
            path = self._write_pair(root, language="sk_SK", preferred=False)
            with mock.patch.object(i18n, "OPTIONS_FILES", [path]), \
                    mock.patch.object(
                        i18n.sqlite_mirror_store, "compare"
                    ) as comparison:
                language = i18n.load_saved_language()

            self.assertEqual(language, "sk_SK")
            comparison.assert_not_called()

    def test_sqlite_primary_marker_loads_language_without_shelve_comparison(self):
        with tempfile.TemporaryDirectory(prefix="ospy-i18n-primary-") as root:
            path = self._settings_path(root)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            values = {
                "lang": "de_DE",
                "settings_storage_mode": "sqlite_primary",
                "sqlite_emergency_recovery": True,
                "sqlite_preferred_reads": True,
                "sqlite_strict_dual_write": True,
            }
            i18n.sqlite_mirror_store.write(
                i18n.sqlite_mirror_store.path_for(path), values, 123.0
            )
            marker = os.path.join(root, "sqlite_primary.enabled")
            with open(marker, "w", encoding="ascii") as target:
                target.write("enabled-v1\n")

            with mock.patch.object(i18n, "OPTIONS_FILES", [path]), \
                    mock.patch.object(i18n, "SQLITE_PRIMARY_MARKER", marker), \
                    mock.patch.object(
                        i18n, "sqlite_capability",
                        return_value={"available": True, "version": "3", "error": ""}
                    ), \
                    mock.patch.object(
                        i18n.settings_store, "read"
                    ) as shelve_read:
                language = i18n.load_saved_language()

            self.assertEqual(language, "de_DE")
            shelve_read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
