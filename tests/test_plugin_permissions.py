import io
import json
import threading
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

from tests.test_support import TEST_DATA_DIR

from ospy import i18n  # Install the gettext function used by a running OSPy.
from ospy import options as options_module
import plugins


def _manifest(plugin, permissions=None, version="1.0.0"):
    return {
        "schema_version": 1,
        "id": plugin,
        "name": plugin,
        "version": version,
        "ospy": {"min": "3.0.0"},
        "python": {"min": "3.8"},
        "requirements": [],
        "permissions": list(permissions or []),
    }


def _plugin_archive(plugin, permissions=None, version="1.0.0"):
    archive = io.BytesIO()
    base = "repository/plugins/{}".format(plugin)
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr(
            base + "/__init__.py",
            "NAME = {!r}\nMENU = {!r}\n"
            "def start():\n    pass\n"
            "def stop():\n    pass\n".format(plugin, plugin),
        )
        zip_file.writestr(
            base + "/plugin.json",
            json.dumps(_manifest(plugin, permissions, version)),
        )
    archive.seek(0)
    return archive


class _PermissionOptions(SimpleNamespace):
    def __init__(self, initialized=True, approvals=None, plugin_status=None):
        super().__init__(
            _fallback=options_module.options,
            plugin_permission_approval_initialized=initialized,
            plugin_permission_approvals=dict(approvals or {}),
            plugin_status=dict(plugin_status or {}),
            enabled_plugins=[],
        )
        self.save_calls = 0
        self.save_result = True

    def __getattr__(self, name):
        return getattr(self._fallback, name)

    def save_now(self):
        self.save_calls += 1
        return self.save_result


class PluginPermissionApprovalTests(unittest.TestCase):
    def test_upgrade_migration_grandfathers_every_installed_plugin_once(self):
        option_values = _PermissionOptions(initialized=False)
        manifests = {
            "enabled_plugin": _manifest("enabled_plugin", ["network"]),
            "disabled_plugin": _manifest("disabled_plugin", ["files"]),
        }
        with mock.patch.object(options_module, "options", option_values), \
                mock.patch.object(
                    plugins, "available", return_value=list(manifests)
                ), mock.patch.object(
                    plugins, "plugin_manifest",
                    side_effect=lambda module: manifests[module],
                ):
            self.assertTrue(plugins.initialize_plugin_permission_approvals())
            self.assertFalse(plugins.initialize_plugin_permission_approvals())

        self.assertTrue(option_values.plugin_permission_approval_initialized)
        self.assertEqual(option_values.save_calls, 1)
        self.assertEqual(
            option_values.plugin_permission_approvals["enabled_plugin"]["permissions"],
            ["network"],
        )
        self.assertEqual(
            option_values.plugin_permission_approvals["disabled_plugin"]["source"],
            "existing-installation",
        )

    def test_added_permission_requires_a_new_approval(self):
        option_values = _PermissionOptions(approvals={
            "example": {"permissions": ["network"]},
        })
        expanded = _manifest("example", ["network", "files"], version="1.1.0")
        with mock.patch.object(options_module, "options", option_values):
            status = plugins.plugin_permission_approval("example", expanded)
            self.assertFalse(status["approved"])
            self.assertEqual(status["missing"], ["files"])

            approved = plugins.approve_plugin_permissions(
                "example", expanded, approved_by="admin", source="test"
            )

        self.assertTrue(approved["approved"])
        self.assertEqual(option_values.save_calls, 1)
        self.assertEqual(
            option_values.plugin_permission_approvals["example"]["permissions"],
            ["files", "network"],
        )

    def test_upgrade_migration_keeps_runtime_approval_if_disk_save_fails(self):
        option_values = _PermissionOptions(initialized=False)
        option_values.save_result = False
        manifest = _manifest("existing", ["network"])
        with mock.patch.object(options_module, "options", option_values), \
                mock.patch.object(plugins, "available", return_value=["existing"]), \
                mock.patch.object(plugins, "plugin_manifest", return_value=manifest):
            with self.assertLogs(level="WARNING"):
                self.assertTrue(
                    plugins.initialize_plugin_permission_approvals()
                )
            self.assertTrue(
                plugins.plugin_permission_approval("existing", manifest)["approved"]
            )

        self.assertTrue(option_values.plugin_permission_approval_initialized)

    def test_installation_is_blocked_until_permissions_are_approved(self):
        option_values = _PermissionOptions()
        archive = _plugin_archive("network_plugin", ["network"])
        with mock.patch.object(options_module, "options", option_values), \
                mock.patch.object(plugins, "available", return_value=[]), \
                mock.patch.object(plugins.checker, "_install_repo_docs"), \
                mock.patch.object(plugins.checker, "_install_plugin") as install:
            with self.assertRaises(ValueError) as blocked:
                plugins.checker.install_custom_plugin(
                    archive, "network_plugin"
                )
            install.assert_not_called()
            self.assertIn("network", str(blocked.exception))

            archive.seek(0)
            result = plugins.checker.install_custom_plugin(
                archive, "network_plugin", approve_permissions=True,
                approved_by="admin",
            )

        self.assertEqual(result["installed"], ["network_plugin"])
        self.assertEqual(result["permissions_approved"], ["network_plugin"])
        install.assert_called_once()
        self.assertEqual(
            option_values.plugin_permission_approvals["network_plugin"]["permissions"],
            ["network"],
        )

    def test_failed_installation_restores_previous_approval(self):
        old_entry = {"permissions": ["network"], "source": "old"}
        option_values = _PermissionOptions(approvals={"example": old_entry})
        archive = _plugin_archive("example", ["network", "files"], version="2.0.0")
        with mock.patch.object(options_module, "options", option_values), \
                mock.patch.object(plugins, "available", return_value=["example"]), \
                mock.patch.object(plugins.checker, "_install_repo_docs"), \
                mock.patch.object(
                    plugins.checker, "_install_plugin",
                    side_effect=OSError("simulated install failure"),
                ):
            with self.assertRaisesRegex(OSError, "simulated install failure"):
                plugins.checker.install_custom_plugin(
                    archive, "example", approve_permissions=True,
                    approved_by="admin",
                )

        self.assertEqual(
            option_values.plugin_permission_approvals["example"], old_entry
        )
        self.assertEqual(option_values.save_calls, 2)

    def test_automatic_update_skips_new_permissions(self):
        option_values = _PermissionOptions(
            approvals={"example": {"permissions": ["network"]}},
            plugin_status={"example": {"hash": "old-hash"}},
        )
        checker = object.__new__(plugins._PluginChecker)
        checker._lock = threading.RLock()
        checker._repo_data = {}
        checker._repo_contents = {}
        checker._changes_cache = {}
        update = {
            "repo": "test-repository",
            "hash": "new-hash",
            "manifest": _manifest("example", ["network", "files"], "2.0.0"),
            "compatibility": {"compatible": True, "errors": []},
        }

        with mock.patch.object(options_module, "options", option_values), \
                mock.patch.object(plugins, "REPOS", ["test-repository"]), \
                mock.patch.object(checker, "_download_zip", return_value=io.BytesIO()), \
                mock.patch.object(checker, "zip_contents", return_value={}), \
                mock.patch.object(plugins, "available", return_value=["example"]), \
                mock.patch.object(checker, "available_version", return_value=update), \
                mock.patch.object(checker, "sync_installed_status", return_value=False), \
                mock.patch.object(checker, "install_repo_plugin") as install:
            with self.assertLogs(level="WARNING") as captured:
                checker.refresh(install_updates=True)

        install.assert_not_called()
        self.assertTrue(any("example" in line for line in captured.output))

    def test_approval_save_failure_is_fail_closed(self):
        option_values = _PermissionOptions()
        option_values.save_result = False
        manifest = _manifest("example", ["network"])
        with mock.patch.object(options_module, "options", option_values):
            with self.assertRaises(RuntimeError):
                plugins.approve_plugin_permissions("example", manifest)

        self.assertNotIn("example", option_values.plugin_permission_approvals)

    def test_unapproved_plugin_is_stopped_before_its_code_is_imported(self):
        option_values = _PermissionOptions()
        option_values.enabled_plugins = ["example"]
        manifest = _manifest("example", ["network"])
        with mock.patch.object(options_module, "options", option_values), \
                mock.patch.object(plugins, "plugin_manifest", return_value=manifest), \
                mock.patch.object(plugins.importlib, "import_module") as import_module, \
                mock.patch.object(plugins, "_protect"), \
                mock.patch.object(plugins, "_clear_plugin_caches"), \
                mock.patch.object(plugins, "_unload_plugin_modules"):
            self.assertFalse(plugins.start_plugin("example"))

        import_module.assert_not_called()
        self.assertNotIn("example", option_values.enabled_plugins)


if __name__ == "__main__":
    unittest.main()
