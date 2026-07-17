import importlib.util
import os
from pathlib import Path
import sys
from threading import Event
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext used by plug-ins
from ospy.options import options as core_options


ROOT = Path(__file__).resolve().parents[1]


def _system_update_path():
    candidates = [
        ROOT / "plugins" / "system_update" / "__init__.py",
        ROOT.parent / "OSPy-plugins" / "plugins" / "system_update" / "__init__.py",
    ]
    for configured in os.environ.get("OSPY_PLUGIN_ROOTS", "").split(os.pathsep):
        if configured:
            candidates.append(Path(configured) / "system_update" / "__init__.py")
    return next((path for path in candidates if path.is_file()), None)


def _load_system_update():
    path = _system_update_path()
    if path is None:
        raise unittest.SkipTest("System Update plug-in source is not available")
    name = "_ospy_test_system_update"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    runtime = mock.Mock()
    runtime.stop_event = Event()
    try:
        with mock.patch("plugins.get_runtime", return_value=runtime):
            spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = old
    return module, path.parent


class _NoStartThread:
    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        pass


class SystemUpdateChannelTests(unittest.TestCase):
    def setUp(self):
        self.module, self.plugin_dir = _load_system_update()
        self.previous = self.module.plugin_options.get("update_channel", "stable")

    def tearDown(self):
        self.module.plugin_options["update_channel"] = self.previous

    def test_master_is_default_and_invalid_values_fail_closed_to_stable(self):
        self.assertEqual(self.module.UPDATE_CHANNELS["stable"], "master")
        self.module.plugin_options["update_channel"] = "stable"
        self.assertEqual(self.module.selected_channel(), "stable")
        self.assertEqual(self.module.selected_remote_branch(), "origin/master")
        self.module.plugin_options["update_channel"] = "arbitrary-branch"
        self.assertEqual(self.module.selected_channel(), "stable")
        self.assertEqual(self.module.selected_remote_branch(), "origin/master")

    def test_beta_selects_only_the_fixed_beta_branch(self):
        self.module.plugin_options["update_channel"] = "beta"
        self.assertEqual(self.module.selected_channel(), "beta")
        self.assertEqual(self.module.selected_branch(), "beta")
        self.assertEqual(self.module.selected_remote_branch(), "origin/beta")

    def test_repository_check_reads_the_selected_remote_branch(self):
        self.module.plugin_options["update_channel"] = "beta"
        checker = object.__new__(self.module.StatusChecker)
        checker.status = {
            "checking": False,
            "can_update": False,
            "can_error": False,
            "commits": [],
            "local_hash": "",
        }
        checker.started = Event()
        commands = []

        def git_value(command, timeout=30):
            commands.append(command)
            if command == ["git", "config", "--get", "remote.origin.url"]:
                return "https://github.com/martinpihrt/OSPy.git"
            if command == ["git", "rev-list", "HEAD", "--count"]:
                return "100"
            if command == ["git", "rev-list", "origin/beta", "--count"]:
                return "101"
            if command == ["git", "rev-parse", "HEAD"]:
                return "local-hash"
            if command == ["git", "rev-parse", "origin/beta"]:
                return "beta-hash"
            if command[:3] == ["git", "log", "-1"]:
                return "2026-07-17"
            if command == ["git", "rev-list", "origin/beta", "--count", "--first-parent"]:
                return "101"
            if command == ["git", "log", "HEAD..origin/beta", "--oneline"]:
                return "abc beta change"
            if command[:3] == ["git", "log", "-n"]:
                return "abc|2026-07-17|beta change"
            return "beta-hash"

        with mock.patch.object(self.module, "run_required_command", return_value=""), \
                mock.patch.object(self.module, "git_output", side_effect=git_value), \
                mock.patch.object(self.module.log, "error"):
            checker._update_rev_data()

        self.assertEqual(checker.status["channel"], "beta")
        self.assertEqual(checker.status["remote_branch"], "origin/beta")
        self.assertTrue(checker.status["can_update"])
        self.assertFalse(any("origin/master" in command for command in commands))

    def test_missing_beta_branch_is_reported_without_offering_an_update(self):
        self.module.plugin_options["update_channel"] = "beta"
        checker = object.__new__(self.module.StatusChecker)
        checker.status = {
            "checking": False,
            "can_update": True,
            "can_error": False,
            "commits": [],
            "local_hash": "",
        }
        checker.started = Event()

        def git_value(command, timeout=30):
            if command == ["git", "config", "--get", "remote.origin.url"]:
                return "https://github.com/martinpihrt/OSPy.git"
            raise RuntimeError("missing branch")

        with mock.patch.object(self.module, "run_required_command", return_value=""), \
                mock.patch.object(self.module, "git_output", side_effect=git_value), \
                mock.patch.object(self.module.log, "error"):
            checker._update_rev_data()

        self.assertFalse(checker.status["can_update"])
        self.assertTrue(checker.status["can_error"])
        self.assertFalse(checker.status["can_ownership_error"])
        self.assertIn("origin/beta", checker.status["error_message"])

    def test_update_uses_selected_branch_after_creating_safety_backup(self):
        self.module.plugin_options["update_channel"] = "beta"
        required = []

        def record(command, timeout=60):
            required.append(command)
            return ""

        def git_value(command, timeout=30):
            if command == ["git", "rev-parse", "HEAD"]:
                return "local-hash"
            return "remote-hash"

        with mock.patch("ospy.backup.create_system_backup", return_value="safety.zip") as create, \
                mock.patch.object(self.module, "run_required_command", side_effect=record), \
                mock.patch.object(self.module, "git_output", side_effect=git_value), \
                mock.patch.object(self.module, "Thread", _NoStartThread), \
                mock.patch.object(self.module, "open", mock.mock_open()), \
                mock.patch.object(type(core_options), "save_now") as save_now:
            result = self.module.perform_update()

        save_now.assert_called_once_with()
        create.assert_called_once_with(reason="before system update")
        self.assertIn(["git", "checkout", "-B", "beta", "origin/beta"], required)
        self.assertIn(["git", "reset", "--hard", "origin/beta"], required)
        self.assertTrue(result)

    def test_interface_explains_both_named_channels(self):
        template = (self.plugin_dir / "templates" / "system_update.html").read_text(encoding="utf-8")
        self.assertIn('value="stable"', template)
        self.assertIn('(master)', template)
        self.assertIn('value="beta"', template)
        self.assertIn('(beta)', template)
        self.assertIn("default", template)


if __name__ == "__main__":
    unittest.main()
