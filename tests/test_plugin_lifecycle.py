import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
import plugins
from ospy.options import options


PLUGIN = "lifecycle_test_plugin"
warnings.filterwarnings(
    "ignore", message="'cgi' is deprecated.*", category=DeprecationWarning
)


def _archive(version, fail_start=False):
    archive = io.BytesIO()
    manifest = {
        "schema_version": 1,
        "id": PLUGIN,
        "name": "Lifecycle Test Plugin",
        "version": version,
        "ospy": {"min": "3.0.0"},
        "python": {"min": "3.8"},
        "requirements": [],
        "permissions": [],
    }
    source = """
NAME = 'Lifecycle Test Plugin'
MENU = None
VERSION = {!r}
STARTED = False

def start():
    global STARTED
    {}
    STARTED = True

def stop():
    global STARTED
    STARTED = False

def health():
    return {{'status': 'ok' if STARTED else 'error', 'summary': VERSION}}
""".format(version, "raise RuntimeError('simulated start failure')" if fail_start else "pass")
    base = "repository/plugins/{}".format(PLUGIN)
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr(base + "/__init__.py", source)
        zip_file.writestr(base + "/plugin.json", json.dumps(manifest))
        zip_file.writestr(base + "/README.md", "# Lifecycle Test Plugin")
    archive.seek(0)
    return archive


class PluginLifecycleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ospy-plugin-lifecycle-")
        self.original_enabled = list(options.enabled_plugins)
        self.original_status = dict(options.plugin_status)
        plugins.__path__.append(self.root)
        self.addCleanup(self._cleanup)

        def test_plugin_dir(module=None):
            if module and module.startswith("plugins."):
                module = module[8:]
            return os.path.join(self.root, module) if module else self.root

        self.plugin_dir_patch = mock.patch.object(
            plugins, "plugin_dir", side_effect=test_plugin_dir
        )
        self.plugin_dir_patch.start()

    def _cleanup(self):
        enabled = list(options.enabled_plugins)
        if PLUGIN in enabled:
            enabled.remove(PLUGIN)
            options.enabled_plugins = enabled
        if PLUGIN in plugins.running():
            plugins.stop_plugin(PLUGIN)
        plugins._clear_plugin_caches(PLUGIN)
        plugins._unload_plugin_modules(PLUGIN)
        options.enabled_plugins = self.original_enabled
        options.plugin_status = self.original_status
        options.__del__()
        self.plugin_dir_patch.stop()
        if self.root in plugins.__path__:
            plugins.__path__.remove(self.root)
        sys.modules.pop("plugins." + PLUGIN, None)
        shutil.rmtree(self.root, ignore_errors=True)

    def _install(self, archive):
        plugins.checker._install_plugin(
            archive,
            PLUGIN,
            "repository/plugins/{}".format(PLUGIN),
        )

    def test_install_activate_restart_update_disable_and_rollback(self):
        self._install(_archive("1.0.0"))
        data_dir = os.path.join(self.root, PLUGIN, "data")
        os.makedirs(data_dir, exist_ok=True)
        settings_file = os.path.join(data_dir, "settings.json")
        with open(settings_file, "w", encoding="utf-8") as file_handle:
            file_handle.write('{"preserved": true}')

        options.enabled_plugins = list(options.enabled_plugins) + [PLUGIN]
        self.assertTrue(plugins.start_plugin(PLUGIN))
        self.assertIn(PLUGIN, plugins.running())
        self.assertEqual(plugins.get(PLUGIN).VERSION, "1.0.0")
        self.assertEqual(plugins.plugin_health(PLUGIN)["status"], "ok")

        self.assertTrue(plugins.reload_plugin(PLUGIN))
        self.assertEqual(plugins.get(PLUGIN).VERSION, "1.0.0")

        self._install(_archive("2.0.0"))
        self.assertIn(PLUGIN, plugins.running())
        self.assertEqual(plugins.get(PLUGIN).VERSION, "2.0.0")
        with open(settings_file, encoding="utf-8") as file_handle:
            self.assertEqual(file_handle.read(), '{"preserved": true}')

        with self.assertLogs(level="ERROR") as captured:
            with self.assertRaises(RuntimeError):
                self._install(_archive("3.0.0", fail_start=True))
        self.assertTrue(
            any("simulated start failure" in message for message in captured.output)
        )
        self.assertIn(PLUGIN, options.enabled_plugins)
        self.assertIn(PLUGIN, plugins.running())
        self.assertEqual(plugins.get(PLUGIN).VERSION, "2.0.0")
        with open(settings_file, encoding="utf-8") as file_handle:
            self.assertEqual(file_handle.read(), '{"preserved": true}')

        enabled = list(options.enabled_plugins)
        enabled.remove(PLUGIN)
        options.enabled_plugins = enabled
        plugins.stop_plugin(PLUGIN)
        self.assertNotIn(PLUGIN, plugins.running())


if __name__ == "__main__":
    unittest.main()
