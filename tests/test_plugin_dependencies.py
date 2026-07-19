import json
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
import plugins
from ospy.options import options


class PluginDependencyTests(unittest.TestCase):
    def setUp(self):
        self.original_enabled = list(options.enabled_plugins)
        self.test_modules = {
            "dependency_provider",
            "dependency_consumer",
            "dependency_cycle_a",
            "dependency_cycle_b",
        }

    def tearDown(self):
        options.enabled_plugins = self.original_enabled
        for module in self.test_modules:
            plugins.__dict__["__plugin_runtime"].pop(module, None)

    @staticmethod
    def _manifest(module, dependencies=None):
        return {
            "schema_version": 1,
            "id": module,
            "name": module,
            "version": "1.0.0",
            "dependencies": dependencies or [],
        }

    def test_manifest_normalizes_required_and_optional_dependencies(self):
        manifest = self._manifest(
            "dependency_consumer",
            [
                "dependency_provider",
                {"plugin": "optional_provider", "required": False},
            ],
        )
        normalized = plugins._manifest_from_bytes(
            json.dumps(manifest).encode("utf-8"),
            "dependency_consumer",
        )
        self.assertEqual(
            normalized["dependencies"],
            [
                {"id": "dependency_provider", "required": True},
                {"id": "optional_provider", "required": False},
            ],
        )

    def test_invalid_dependency_declarations_reject_manifest(self):
        invalid_dependencies = (
            "dependency_provider",
            [{"id": "Invalid ID"}],
            [{"id": "dependency_provider", "required": "yes"}],
            ["dependency_provider", "dependency_provider"],
        )
        for dependencies in invalid_dependencies:
            with self.subTest(dependencies=dependencies):
                manifest = self._manifest("dependency_consumer", dependencies)
                self.assertEqual(
                    plugins._manifest_from_bytes(
                        json.dumps(manifest).encode("utf-8"),
                        "dependency_consumer",
                    ),
                    {},
                )

    def test_required_dependency_must_be_installed_and_enabled(self):
        manifest = self._manifest(
            "dependency_consumer",
            [{"id": "dependency_provider", "required": True}],
        )
        missing = plugins.plugin_manifest_compatibility(
            "dependency_consumer",
            manifest,
            enabled_modules=["dependency_consumer"],
            available_modules=["dependency_consumer"],
        )
        self.assertFalse(missing["compatible"])
        self.assertTrue(any("dependency_provider" in item for item in missing["errors"]))

        disabled = plugins.plugin_manifest_compatibility(
            "dependency_consumer",
            manifest,
            enabled_modules=["dependency_consumer"],
            available_modules=["dependency_consumer", "dependency_provider"],
        )
        self.assertFalse(disabled["compatible"])
        self.assertTrue(any("dependency_provider" in item for item in disabled["errors"]))

        enabled = plugins.plugin_manifest_compatibility(
            "dependency_consumer",
            manifest,
            enabled_modules=["dependency_consumer", "dependency_provider"],
            available_modules=["dependency_consumer", "dependency_provider"],
        )
        self.assertTrue(enabled["compatible"])

    def test_optional_enabled_dependency_starts_first(self):
        manifests = {
            "dependency_provider": self._manifest("dependency_provider"),
            "dependency_consumer": self._manifest(
                "dependency_consumer",
                [{"id": "dependency_provider", "required": False}],
            ),
        }
        options.enabled_plugins = ["dependency_consumer", "dependency_provider"]
        started = []
        with mock.patch.object(plugins, "available", return_value=[
                "dependency_consumer", "dependency_provider"]), \
                mock.patch.object(
                    plugins, "plugin_manifest", side_effect=lambda module: manifests[module]
                ), \
                mock.patch.object(
                    plugins, "start_plugin", side_effect=lambda module: started.append(module) or True
                ):
            plugins.start_enabled_plugins()

        self.assertEqual(started, ["dependency_provider", "dependency_consumer"])

    def test_shutdown_stops_consumers_before_providers(self):
        manifests = {
            "dependency_provider": self._manifest("dependency_provider"),
            "dependency_consumer": self._manifest(
                "dependency_consumer",
                [{"id": "dependency_provider", "required": False}],
            ),
        }
        stopped = []
        with mock.patch.object(
                plugins, "running", return_value=[
                    "dependency_provider", "dependency_consumer"]
                ), \
                mock.patch.object(
                    plugins, "plugin_manifest", side_effect=lambda module: manifests[module]
                ), \
                mock.patch.object(
                    plugins, "_runtime_entry", return_value={"runtime": None}
                ), \
                mock.patch.object(
                    plugins, "stop_plugin", side_effect=lambda module, timeout: stopped.append(module) or True
                ):
            self.assertEqual(plugins.stop_all_plugins(), [])

        self.assertEqual(stopped, ["dependency_consumer", "dependency_provider"])

    def test_dependency_cycle_is_not_started(self):
        manifests = {
            "dependency_cycle_a": self._manifest(
                "dependency_cycle_a",
                [{"id": "dependency_cycle_b", "required": True}],
            ),
            "dependency_cycle_b": self._manifest(
                "dependency_cycle_b",
                [{"id": "dependency_cycle_a", "required": True}],
            ),
        }
        options.enabled_plugins = ["dependency_cycle_a", "dependency_cycle_b"]
        with mock.patch.object(
                plugins, "available", return_value=[
                    "dependency_cycle_a", "dependency_cycle_b"]
                ), \
                mock.patch.object(
                    plugins, "plugin_manifest", side_effect=lambda module: manifests[module]
                ), \
                mock.patch.object(plugins, "start_plugin") as start:
            with self.assertLogs(level="ERROR"):
                plugins.start_enabled_plugins()

        start.assert_not_called()
        error = plugins._runtime_entry("dependency_cycle_a")["last_error"]
        self.assertIn("dependency_cycle_a", error)
        self.assertIn("dependency_cycle_b", error)


if __name__ == "__main__":
    unittest.main()
