import io
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import threading
import unittest
from unittest import mock
import zipfile


TEST_DATA_DIR = tempfile.mkdtemp(prefix="ospy-tests-")
os.environ["OSPY_DATA_DIR"] = TEST_DATA_DIR
os.environ["OSPY_DISABLE_BACKGROUND_THREADS"] = "1"

from ospy import i18n  # Install the same gettext function used by a running OSPy.
import plugins
from ospy import options as options_module


ROOT = Path(__file__).resolve().parents[1]
CORE_PLUGIN_ROOT = ROOT / "plugins"


def _configured_official_plugin_roots():
    value = os.environ.get("OSPY_PLUGIN_ROOTS", "")
    if not value:
        return []
    return [
        Path(item).expanduser().resolve()
        for item in value.split(os.pathsep)
        if item.strip()
    ]


def _plugin_directories(plugin_root):
    if not plugin_root.is_dir():
        return []
    return sorted(
        directory
        for directory in plugin_root.iterdir()
        if directory.is_dir() and (directory / "__init__.py").is_file()
    )


def _plugin_archive(plugin_definitions):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zip_file:
        for plugin, manifest in plugin_definitions.items():
            base = "repository/plugins/{}".format(plugin)
            zip_file.writestr(
                base + "/__init__.py",
                "NAME = {!r}\nMENU = {!r}\n"
                "def start():\n    pass\n"
                "def stop():\n    pass\n".format(plugin, plugin),
            )
            zip_file.writestr(base + "/README.md", "# {}".format(plugin))
            if manifest is not None:
                if isinstance(manifest, bytes):
                    contents = manifest
                else:
                    contents = json.dumps(manifest).encode("utf-8")
                zip_file.writestr(base + "/plugin.json", contents)
    archive.seek(0)
    return archive


def _manifest(plugin, **changes):
    result = {
        "schema_version": 1,
        "id": plugin,
        "name": plugin,
        "version": "1.0.0",
        "ospy": {"min": "3.0.0"},
        "python": {"min": "3.8"},
        "requirements": [],
        "permissions": [],
    }
    result.update(changes)
    return result


class PluginManifestParserTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        options_module.options.__del__()
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)

    def test_tests_use_isolated_data_without_background_plugin_checker(self):
        self.assertTrue(
            os.path.realpath(options_module.OPTIONS_FILE).startswith(
                os.path.realpath(TEST_DATA_DIR) + os.sep
            )
        )
        self.assertFalse(plugins.checker.is_alive())

    def test_valid_manifest_is_normalized(self):
        manifest = {
            "schema_version": 1,
            "id": "example_plugin",
            "name": "Example Plugin",
            "version": "1.0.0",
            "homepage": "https://example.com/plugin",
            "ospy": {"min": "3.0.0"},
            "python": {"min": "3.8"},
            "requirements": [],
            "hardware": {},
            "permissions": ["network"],
            "conflicts": [],
        }
        normalized = plugins._manifest_from_bytes(
            json.dumps(manifest).encode("utf-8"), "example_plugin"
        )
        self.assertEqual(normalized["id"], "example_plugin")
        self.assertEqual(normalized["schema_version"], 1)
        self.assertEqual(normalized["name"], "Example Plugin")

    def test_invalid_manifests_are_rejected(self):
        invalid = (
            ({"schema_version": 0, "id": "example_plugin"}, "example_plugin"),
            ({"schema_version": True, "id": "example_plugin"}, "example_plugin"),
            ({"schema_version": 1, "id": "different_plugin"}, "example_plugin"),
            ({"schema_version": 1, "id": "Invalid ID"}, None),
            (
                {
                    "schema_version": 1,
                    "id": "example_plugin",
                    "homepage": "ftp://example.com",
                },
                "example_plugin",
            ),
            (
                {
                    "schema_version": 1,
                    "id": "example_plugin",
                    "requirements": "requests",
                },
                "example_plugin",
            ),
        )
        for manifest, module in invalid:
            with self.subTest(manifest=manifest, module=module):
                self.assertEqual(
                    plugins._manifest_from_bytes(
                        json.dumps(manifest).encode("utf-8"), module
                    ),
                    {},
                )


class PluginArchiveInstallationTests(unittest.TestCase):
    def test_unsafe_parent_path_is_rejected_before_any_write(self):
        archive = _plugin_archive({"safe_plugin": _manifest("safe_plugin")})
        with zipfile.ZipFile(archive, "a") as zip_file:
            zip_file.writestr(
                "repository/plugins/safe_plugin/../outside.py", "unsafe"
            )
        archive.seek(0)

        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ) as install_docs, mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            with self.assertRaises(ValueError):
                plugins.checker.install_custom_plugin(archive)

        install_docs.assert_not_called()
        install_plugin.assert_not_called()

    def test_duplicate_archive_path_is_rejected(self):
        archive = _plugin_archive({"duplicate_plugin": _manifest("duplicate_plugin")})
        with self.assertWarns(UserWarning):
            with zipfile.ZipFile(archive, "a") as zip_file:
                zip_file.writestr(
                    "repository/plugins/duplicate_plugin/README.md", "duplicate"
                )
        archive.seek(0)

        with self.assertRaises(ValueError):
            plugins.checker.install_custom_plugin(archive)

    def test_duplicate_plugin_identifier_is_rejected(self):
        archive = io.BytesIO()
        manifest = json.dumps(_manifest("duplicate_plugin"))
        with zipfile.ZipFile(archive, "w") as zip_file:
            for root in ("repository-one", "repository-two"):
                base = root + "/plugins/duplicate_plugin"
                zip_file.writestr(base + "/__init__.py", "NAME = 'Duplicate'\n")
                zip_file.writestr(base + "/plugin.json", manifest)
        archive.seek(0)

        with self.assertRaises(ValueError):
            plugins.checker.install_custom_plugin(archive)

    def test_symbolic_link_entry_is_rejected(self):
        archive = _plugin_archive({"link_plugin": _manifest("link_plugin")})
        link_info = zipfile.ZipInfo(
            "repository/plugins/link_plugin/linked-file"
        )
        link_info.create_system = 3
        link_info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(archive, "a") as zip_file:
            zip_file.writestr(link_info, "../../outside")
        archive.seek(0)

        with self.assertRaises(ValueError):
            plugins.checker.install_custom_plugin(archive)

    def test_archive_size_limit_is_enforced_before_installation(self):
        archive = _plugin_archive({"large_plugin": _manifest("large_plugin")})
        with zipfile.ZipFile(archive, "a") as zip_file:
            zip_file.writestr(
                "repository/plugins/large_plugin/large.bin", b"x" * 128
            )
        archive.seek(0)

        with mock.patch.object(
            plugins, "PLUGIN_ZIP_MAX_TOTAL_BYTES", 64
        ), mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            with self.assertRaises(ValueError):
                plugins.checker.install_custom_plugin(archive)

        install_plugin.assert_not_called()

    def test_archive_file_count_limit_is_enforced(self):
        archive = _plugin_archive({"many_files": _manifest("many_files")})
        with zipfile.ZipFile(archive, "a") as zip_file:
            zip_file.writestr("repository/plugins/many_files/extra.txt", "extra")
        archive.seek(0)

        with mock.patch.object(plugins, "PLUGIN_ZIP_MAX_FILES", 3):
            with self.assertRaises(ValueError):
                plugins.checker.install_custom_plugin(archive)

    def test_suspicious_compression_ratio_is_rejected(self):
        archive = _plugin_archive({"compressed_plugin": _manifest("compressed_plugin")})
        with zipfile.ZipFile(archive, "a", compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(
                "repository/plugins/compressed_plugin/repeated.bin",
                b"0" * 4096,
            )
        archive.seek(0)

        with mock.patch.object(plugins, "PLUGIN_ZIP_MAX_RATIO", 2):
            with self.assertRaises(ValueError):
                plugins.checker.install_custom_plugin(archive)

    def test_atomic_update_preserves_plugin_data(self):
        archive = _plugin_archive({"atomic_plugin": _manifest("atomic_plugin")})
        with tempfile.TemporaryDirectory(prefix="ospy-plugin-data-") as root:
            target_dir = os.path.join(root, "atomic_plugin")
            data_dir = os.path.join(target_dir, "data")
            os.makedirs(data_dir)
            with open(
                os.path.join(target_dir, "__init__.py"), "w", encoding="utf-8"
            ) as file_handle:
                file_handle.write("NAME = 'Old version'\n")
            with open(
                os.path.join(data_dir, "settings.json"), "w", encoding="utf-8"
            ) as file_handle:
                file_handle.write('{"preserved": true}')

            def test_plugin_dir(module=None):
                return os.path.join(root, module) if module else root

            with mock.patch.object(
                plugins, "plugin_dir", side_effect=test_plugin_dir
            ):
                plugins.checker._install_plugin(
                    archive,
                    "atomic_plugin",
                    "repository/plugins/atomic_plugin",
                )

            with open(
                os.path.join(target_dir, "data", "settings.json"),
                encoding="utf-8",
            ) as file_handle:
                self.assertEqual(file_handle.read(), '{"preserved": true}')
            with open(
                os.path.join(target_dir, "plugin.json"), encoding="utf-8"
            ) as file_handle:
                self.assertEqual(json.load(file_handle)["id"], "atomic_plugin")

    def test_failed_directory_swap_restores_previous_plugin(self):
        archive = _plugin_archive({"atomic_plugin": _manifest("atomic_plugin")})
        with tempfile.TemporaryDirectory(prefix="ospy-plugin-atomic-") as root:
            target_dir = os.path.join(root, "atomic_plugin")
            os.makedirs(target_dir)
            old_init = os.path.join(target_dir, "__init__.py")
            with open(old_init, "w", encoding="utf-8") as file_handle:
                file_handle.write("NAME = 'Old version'\n")

            real_replace = os.replace
            replace_calls = []

            def failing_replace(source, target):
                replace_calls.append((source, target))
                if len(replace_calls) == 2:
                    raise OSError("simulated swap failure")
                return real_replace(source, target)

            def test_plugin_dir(module=None):
                return os.path.join(root, module) if module else root

            with mock.patch.object(
                plugins, "plugin_dir", side_effect=test_plugin_dir
            ), mock.patch("os.replace", side_effect=failing_replace):
                with self.assertRaisesRegex(OSError, "simulated swap failure"):
                    plugins.checker._install_plugin(
                        archive,
                        "atomic_plugin",
                        "repository/plugins/atomic_plugin",
                    )

            with open(old_init, encoding="utf-8") as file_handle:
                self.assertEqual(file_handle.read(), "NAME = 'Old version'\n")
            self.assertFalse(
                any(name.startswith(".ospy-plugin-install-") for name in os.listdir(root))
            )

    def test_archive_reports_missing_and_invalid_manifests_as_incompatible(self):
        archive = _plugin_archive({
            "missing_manifest": None,
            "invalid_manifest": b"{not json",
        })
        contents = plugins.checker.zip_contents(archive, load_read_me=False)

        self.assertFalse(contents["missing_manifest"]["compatibility"]["compatible"])
        self.assertFalse(contents["missing_manifest"]["manifest_present"])
        self.assertTrue(
            contents["missing_manifest"]["compatibility"]["errors"]
        )
        self.assertFalse(contents["invalid_manifest"]["compatibility"]["compatible"])
        self.assertTrue(contents["invalid_manifest"]["manifest_present"])
        self.assertFalse(contents["invalid_manifest"]["manifest_valid"])
        self.assertTrue(
            contents["invalid_manifest"]["compatibility"]["errors"]
        )

    def test_incompatible_single_plugin_is_blocked_before_any_write(self):
        archive = _plugin_archive({
            "future_plugin": _manifest(
                "future_plugin", ospy={"min": "9999.0"}
            ),
        })

        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ) as install_docs, mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            with self.assertRaises(ValueError):
                plugins.checker.install_custom_plugin(
                    archive, "future_plugin"
                )

        install_docs.assert_not_called()
        install_plugin.assert_not_called()

    def test_bulk_install_skips_incompatible_and_installs_compatible_plugins(self):
        archive = _plugin_archive({
            "compatible_plugin": _manifest("compatible_plugin"),
            "future_plugin": _manifest(
                "future_plugin", ospy={"min": "9999.0"}
            ),
        })

        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ) as install_docs, mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            result = plugins.checker.install_custom_plugin(archive)

        self.assertEqual(result["installed"], ["compatible_plugin"])
        self.assertIn("future_plugin", result["blocked"])
        install_docs.assert_called_once()
        self.assertEqual(install_plugin.call_count, 1)
        self.assertEqual(install_plugin.call_args.args[1], "compatible_plugin")

    def test_compatibility_warning_does_not_block_installation(self):
        archive = _plugin_archive({
            "warning_plugin": _manifest(
                "warning_plugin", permissions=["unknown-permission"]
            ),
        })

        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ), mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            result = plugins.checker.install_custom_plugin(
                archive, "warning_plugin"
            )

        self.assertEqual(result["installed"], ["warning_plugin"])
        self.assertIn("warning_plugin", result["warnings"])
        install_plugin.assert_called_once()

    def test_automatic_update_skips_incompatible_available_version(self):
        checker = object.__new__(plugins._PluginChecker)
        checker._lock = threading.RLock()
        checker._repo_data = {}
        checker._repo_contents = {}
        checker._changes_cache = {}
        update = {
            "repo": "test-repository",
            "hash": "new-hash",
            "compatibility": {
                "compatible": False,
                "errors": ["Unsupported OSPy version."],
            },
        }

        with mock.patch.object(plugins, "REPOS", ["test-repository"]), \
                mock.patch.object(checker, "_download_zip", return_value=io.BytesIO()), \
                mock.patch.object(checker, "zip_contents", return_value={}), \
                mock.patch.object(plugins, "available", return_value=["future_plugin"]), \
                mock.patch.object(checker, "available_version", return_value=update), \
                mock.patch.object(checker, "sync_installed_status", return_value=False), \
                mock.patch.object(checker, "install_repo_plugin") as install_plugin:
            with self.assertLogs(level="WARNING") as captured:
                checker.refresh(install_updates=True)

        install_plugin.assert_not_called()
        self.assertTrue(
            any("future_plugin" in message for message in captured.output)
        )


class PluginDiagnosticsCollectionTests(unittest.TestCase):
    def setUp(self):
        setattr(plugins, "__plugin_diagnostics_cache", {"time": 0, "data": None})

    def test_simultaneous_diagnostics_requests_reuse_short_cache(self):
        result = [{"module": "cached_plugin"}]
        with mock.patch.object(
            plugins, "_plugin_diagnostics_uncached", return_value=result
        ) as collect:
            first = plugins.plugin_diagnostics()
            second = plugins.plugin_diagnostics()

        self.assertIs(first, result)
        self.assertIs(second, result)
        collect.assert_called_once_with()

    def test_forced_diagnostics_refresh_bypasses_cache(self):
        with mock.patch.object(
            plugins,
            "_plugin_diagnostics_uncached",
            side_effect=([{"sample": 1}], [{"sample": 2}]),
        ) as collect:
            first = plugins.plugin_diagnostics()
            second = plugins.plugin_diagnostics(force=True)

        self.assertEqual(first, [{"sample": 1}])
        self.assertEqual(second, [{"sample": 2}])
        self.assertEqual(collect.call_count, 2)


class PluginManifestRepositoryTests(unittest.TestCase):
    def _validate_manifest(self, plugin_dir):
        manifest_path = plugin_dir / plugins.PLUGIN_MANIFEST_FILE
        self.assertLessEqual(
            manifest_path.stat().st_size,
            plugins.PLUGIN_MANIFEST_MAX_BYTES,
            "{} exceeds the manifest size limit.".format(manifest_path),
        )
        normalized = plugins._manifest_from_bytes(
            manifest_path.read_bytes(), plugin_dir.name
        )
        self.assertTrue(normalized, "{} is invalid.".format(manifest_path))
        self.assertEqual(normalized.get("id"), plugin_dir.name)
        self.assertEqual(
            normalized.get("schema_version"), plugins.PLUGIN_MANIFEST_SCHEMA_VERSION
        )
        self.assertTrue(normalized.get("name"), "{} has no name.".format(manifest_path))
        self.assertTrue(
            normalized.get("version"), "{} has no version.".format(manifest_path)
        )

    def test_installed_plugin_manifests_are_valid(self):
        for plugin_dir in _plugin_directories(CORE_PLUGIN_ROOT):
            manifest_path = plugin_dir / plugins.PLUGIN_MANIFEST_FILE
            if manifest_path.is_file():
                with self.subTest(plugin=plugin_dir.name):
                    self._validate_manifest(plugin_dir)

    def test_official_plugin_roots_have_valid_manifests_for_every_plugin(self):
        for plugin_root in _configured_official_plugin_roots():
            with self.subTest(plugin_root=str(plugin_root)):
                self.assertTrue(
                    plugin_root.is_dir(),
                    "Configured plug-in root does not exist: {}".format(plugin_root),
                )
                plugin_dirs = _plugin_directories(plugin_root)
                self.assertTrue(
                    plugin_dirs,
                    "No plug-ins were found in {}".format(plugin_root),
                )
                missing = [
                    plugin_dir.name
                    for plugin_dir in plugin_dirs
                    if not (plugin_dir / plugins.PLUGIN_MANIFEST_FILE).is_file()
                ]
                self.assertFalse(
                    missing,
                    "Plug-ins without plugin.json in {}:\n{}".format(
                        plugin_root, "\n".join(missing)
                    ),
                )
                for plugin_dir in plugin_dirs:
                    with self.subTest(
                        plugin_root=str(plugin_root), plugin=plugin_dir.name
                    ):
                        self._validate_manifest(plugin_dir)


if __name__ == "__main__":
    unittest.main()
