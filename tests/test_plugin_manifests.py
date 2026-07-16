import json
import os
from pathlib import Path
import unittest

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
