import importlib.util
from contextlib import ExitStack
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import json
import time
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
                return "a" * 40
            if command == ["git", "rev-parse", "--verify", "origin/beta"]:
                return "b" * 40
            return "b" * 40

        watchdog_supported = hasattr(self.module, "arm_update_watchdog")
        with ExitStack() as stack:
            create = stack.enter_context(mock.patch(
                "ospy.backup.create_system_backup", return_value="safety.zip"
            ))
            stack.enter_context(mock.patch.object(
                self.module, "run_required_command", side_effect=record
            ))
            stack.enter_context(mock.patch.object(
                self.module, "git_output", side_effect=git_value
            ))
            arm = None
            if watchdog_supported:
                arm = stack.enter_context(mock.patch.object(
                    self.module, "arm_update_watchdog", return_value={"token": "token"}
                ))
            stack.enter_context(mock.patch.object(self.module, "Thread", _NoStartThread))
            stack.enter_context(mock.patch.object(self.module, "open", mock.mock_open()))
            save_now = stack.enter_context(mock.patch.object(type(core_options), "save_now"))
            result = self.module.perform_update()

        save_now.assert_called_once_with()
        create.assert_called_once_with(reason="before system update")
        if watchdog_supported:
            arm.assert_called_once_with("a" * 40, "b" * 40)
        self.assertLess(
            required.index(["git", "fetch", "--prune", "origin"]),
            required.index(["git", "checkout", "-B", "beta", "origin/beta"]),
        )
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

    def test_failed_update_restores_previous_commit_and_cancels_watchdog(self):
        if not hasattr(self.module, "arm_update_watchdog"):
            self.skipTest("System Update plug-in does not provide the external watchdog")
        previous = "a" * 40
        target = "b" * 40
        commands = []

        def required(command, timeout=60):
            commands.append(command)
            if command[:3] == ["git", "checkout", "-B"]:
                raise RuntimeError("checkout failed")
            return ""

        def git_value(command, timeout=30):
            if command == ["git", "rev-parse", "HEAD"]:
                return previous
            if command == ["git", "rev-parse", "--verify", "origin/master"]:
                return target
            return target

        watchdog = {"token": "secret"}
        with mock.patch("ospy.backup.create_system_backup", return_value="safety.zip"), \
                mock.patch.object(self.module, "run_required_command", side_effect=required), \
                mock.patch.object(self.module, "git_output", side_effect=git_value), \
                mock.patch.object(self.module, "arm_update_watchdog", return_value=watchdog), \
                mock.patch.object(self.module, "cancel_update_watchdog") as cancel, \
                mock.patch.object(self.module.log, "error"), \
                mock.patch.object(self.module, "open", mock.mock_open()), \
                mock.patch.object(type(core_options), "save_now"):
            result = self.module.perform_update()

        self.assertIsInstance(result, str)
        self.assertTrue(result)
        self.assertIn(["git", "reset", "--hard", previous], commands)
        cancel.assert_called_once_with(watchdog, status="update_failed")

    def test_watchdog_is_ready_before_repository_changes_are_allowed(self):
        if not hasattr(self.module, "WATCHDOG_READY_FILE"):
            self.skipTest("System Update plug-in does not provide a readiness handshake")
        state = {
            "token": "secret",
            "unit": "ospy-update-watchdog-test",
        }

        def executable(name):
            return {
                "systemd-run": "/bin/systemd-run",
                "systemctl": "/bin/systemctl",
                "sh": "/bin/sh",
            }.get(name)

        with mock.patch.object(self.module, "_watchdog_state", return_value=state), \
                mock.patch.object(self.module.shutil, "which", side_effect=executable), \
                mock.patch.object(self.module.os.path, "isdir", return_value=True), \
                mock.patch.object(self.module.os.path, "isfile", return_value=True), \
                mock.patch.object(self.module, "run_required_command", return_value="") as run, \
                mock.patch.object(
                    self.module, "_read_json", return_value={"token": "secret"}
                ), \
                mock.patch.object(self.module, "_write_json") as write:
            armed = self.module.arm_update_watchdog("a" * 40, "b" * 40)

        self.assertEqual(armed["mode"], "systemd")
        command = run.call_args.args[0]
        self.assertIn(self.module.WATCHDOG_SUPERVISOR, command)
        self.assertIn(self.module.WATCHDOG_SCRIPT, command)
        write.assert_called_once_with(self.module.WATCHDOG_STATE_FILE, armed)

    def test_watchdog_start_without_ready_signal_is_rejected(self):
        if not hasattr(self.module, "WATCHDOG_READY_FILE"):
            self.skipTest("System Update plug-in does not provide a readiness handshake")
        state = {
            "token": "secret",
            "unit": "ospy-update-watchdog-test",
        }
        self.module.WATCHDOG_START_TIMEOUT = 0
        with mock.patch.object(self.module, "_watchdog_state", return_value=state), \
                mock.patch.object(self.module.shutil, "which", return_value="/bin/tool"), \
                mock.patch.object(self.module.os.path, "isdir", return_value=True), \
                mock.patch.object(self.module.os.path, "isfile", return_value=True), \
                mock.patch.object(self.module, "run_required_command", return_value=""), \
                mock.patch.object(self.module, "run_command") as stop, \
                mock.patch.object(self.module, "_read_json", return_value={}), \
                mock.patch.object(self.module.os, "remove"):
            with self.assertRaises(RuntimeError):
                self.module.arm_update_watchdog("a" * 40, "b" * 40)

        self.assertEqual(
            stop.call_args.args[0],
            ["/bin/tool", "stop", "ospy-update-watchdog-test"],
        )

    def test_new_process_confirms_only_after_fresh_scheduler_heartbeat(self):
        if not hasattr(self.module, "acknowledge_update_watchdog"):
            self.skipTest("System Update plug-in does not provide watchdog acknowledgement")
        target = "b" * 40
        created = time.time() - 5
        state = {
            "token": "secret",
            "target_commit": target,
            "created": created,
        }
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            ack_path = Path(directory) / "ack.json"
            self.module.WATCHDOG_STATE_FILE = str(state_path)
            self.module.WATCHDOG_ACK_FILE = str(ack_path)
            self.module.WATCHDOG_RESULT_FILE = str(Path(directory) / "result.json")
            state_path.write_text(json.dumps(state), encoding="utf-8")
            with mock.patch.object(self.module, "git_output", return_value=target), \
                    mock.patch("ospy.health.component", return_value={"last_success": created - 1}):
                self.assertFalse(self.module.acknowledge_update_watchdog())
            self.assertFalse(ack_path.exists())

            with mock.patch.object(self.module, "git_output", return_value=target), \
                    mock.patch("ospy.health.component", return_value={"last_success": created + 1}), \
                    mock.patch.object(
                        self.module.socket, "create_connection", side_effect=OSError("not listening")
                    ):
                self.assertFalse(self.module.acknowledge_update_watchdog())
            self.assertFalse(ack_path.exists())

            with mock.patch.object(self.module, "git_output", return_value=target), \
                    mock.patch("ospy.health.component", return_value={"last_success": created + 1}), \
                    mock.patch.object(self.module.socket, "create_connection") as connect:
                self.assertTrue(self.module.acknowledge_update_watchdog())
            connect.return_value.close.assert_called_once_with()
            acknowledgement = json.loads(ack_path.read_text(encoding="utf-8"))
            self.assertEqual(acknowledgement["token"], "secret")
            self.assertEqual(acknowledgement["commit"], target)
            self.assertFalse(state_path.exists())
            result = json.loads(
                Path(self.module.WATCHDOG_RESULT_FILE).read_text(encoding="utf-8")
            )
            self.assertEqual(result["status"], "confirmed")

            # Simulate delayed external cleanup: a matching acknowledgement
            # must still override a stale pending marker in Diagnostics.
            state_path.write_text(json.dumps(state), encoding="utf-8")

            fake_checker = mock.Mock()
            fake_checker.is_alive.return_value = True
            fake_checker.status = {"can_update": False, "checking": False}
            with mock.patch.object(self.module, "checker", fake_checker), \
                    mock.patch.dict(self.module.plugin_options, {"use_update": True}):
                health = self.module.health()
            self.assertEqual(health["status"], "ok")


class SystemUpdateWatchdogProcessTests(unittest.TestCase):
    def setUp(self):
        plugin = _system_update_path()
        if plugin is None:
            raise unittest.SkipTest("System Update plug-in source is not available")
        helper_path = plugin.parent / "update_watchdog.py"
        if not helper_path.is_file():
            raise unittest.SkipTest("System Update watchdog helper is not available")
        spec = importlib.util.spec_from_file_location("_ospy_test_update_watchdog", str(helper_path))
        self.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.helper)

    def _write_state(self, directory, deadline):
        state_path = Path(directory) / "state.json"
        ack_path = Path(directory) / "ack.json"
        result_path = Path(directory) / "result.json"
        repository = Path(directory) / "repository"
        (repository / ".git").mkdir(parents=True)
        state = {
            "token": "secret",
            "repository": str(repository),
            "previous_commit": "a" * 40,
            "previous_branch": "beta",
            "target_commit": "b" * 40,
            "deadline": deadline,
            "acknowledgement": str(ack_path),
            "result": str(result_path),
            "ready": str(Path(directory) / "ready.json"),
        }
        state_path.write_text(json.dumps(state), encoding="utf-8")
        return state_path, ack_path, result_path, state

    def test_acknowledgement_prevents_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path, ack_path, result_path, state = self._write_state(
                directory, time.time() + 10
            )
            ack_path.write_text(
                json.dumps({"token": "secret", "status": "confirmed"}),
                encoding="utf-8",
            )
            with mock.patch.object(self.helper.subprocess, "run") as run:
                result = self.helper.monitor(str(state_path), "secret")

            self.assertEqual(result, 0)
            run.assert_not_called()
            self.assertFalse(state_path.exists())
            self.assertFalse(Path(state["ready"]).exists())
            saved = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "confirmed")

    def test_timeout_rolls_back_and_restarts_service(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path, _ack_path, result_path, state = self._write_state(
                directory, time.time() - 1
            )
            completed = mock.Mock(returncode=0)
            with mock.patch.object(self.helper.subprocess, "run", return_value=completed) as run, \
                    mock.patch.object(self.helper, "_restart_ospy") as restart:
                result = self.helper.monitor(str(state_path), "secret")

            self.assertEqual(result, 0)
            self.assertEqual(
                run.call_args_list[0].args[0],
                ["git", "-C", state["repository"], "reset", "--hard", "a" * 40],
            )
            self.assertEqual(
                run.call_args_list[1].args[0],
                ["git", "-C", state["repository"], "checkout", "-B", "beta", "a" * 40],
            )
            restart.assert_called_once_with(state)
            saved = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "rolled_back")
            self.assertFalse(state_path.exists())
            self.assertFalse(Path(state["ready"]).exists())

    def test_wrong_token_is_rejected_without_git_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path, _ack_path, _result_path, _state = self._write_state(
                directory, time.time() - 1
            )
            with mock.patch.object(self.helper.subprocess, "run") as run:
                result = self.helper.monitor(str(state_path), "wrong")
            self.assertEqual(result, 2)
            run.assert_not_called()


class SystemUpdateLegacyServiceTests(unittest.TestCase):
    def test_sysv_stop_does_not_match_every_python_process(self):
        service = (ROOT / "service" / "ospy.sh").read_text(encoding="utf-8")
        stop_body = service.split("do_stop()", 1)[1].split("do_reload()", 1)[0]
        commands = [
            line.strip() for line in stop_body.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertFalse(any("--exec $DAEMON" in line for line in commands))

    @unittest.skipUnless(os.name == "posix" and shutil.which("sh"), "POSIX shell required")
    def test_shell_supervisor_relaunches_a_signalled_python_helper(self):
        plugin = _system_update_path()
        if plugin is None:
            raise unittest.SkipTest("System Update plug-in source is not available")
        supervisor = plugin.parent / "update_watchdog_supervisor.sh"
        if not supervisor.is_file():
            raise unittest.SkipTest("System Update watchdog supervisor is not available")

        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state = directory / "state.json"
            count = directory / "count"
            fake_python = directory / "fake-python"
            state.write_text("{}", encoding="utf-8")
            fake_python.write_text(
                "#!/bin/sh\n"
                "COUNT=0\n"
                "[ ! -f \"$WATCHDOG_TEST_COUNT\" ] || COUNT=$(cat \"$WATCHDOG_TEST_COUNT\")\n"
                "COUNT=$((COUNT + 1))\n"
                "printf '%s' \"$COUNT\" > \"$WATCHDOG_TEST_COUNT\"\n"
                "[ \"$COUNT\" -ne 1 ] || exit 137\n"
                "exit 0\n",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            environment = dict(os.environ)
            environment["WATCHDOG_TEST_COUNT"] = str(count)
            completed = subprocess.run(
                [
                    shutil.which("sh"), str(supervisor), str(fake_python), "ignored",
                    "--state", str(state), "--token", "secret",
                ],
                check=False,
                timeout=5,
                env=environment,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(count.read_text(encoding="utf-8"), "2")


if __name__ == "__main__":
    unittest.main()
