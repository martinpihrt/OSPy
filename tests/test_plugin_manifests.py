import io
import json
import os
from pathlib import Path
import threading
import unittest
from unittest import mock
import zipfile

from ospy import i18n  # Install the same gettext function used by a running OSPy.
import plugins


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
