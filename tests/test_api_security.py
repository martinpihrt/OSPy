import base64
from types import SimpleNamespace
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import helpers
import web
from api import api as api_module
from api import utils
from api.errors import API_Unauthorized


def _basic_header(username, password):
    value = "{}:{}".format(username, password).encode("ascii")
    return "Basic " + base64.b64encode(value).decode("ascii")


def _undecorated(function):
    while hasattr(function, "__wrapped__"):
        function = function.__wrapped__
    return function


class ApiSecurityTests(unittest.TestCase):
    def setUp(self):
        web.ctx.clear()
        web.ctx.env = {
            "REMOTE_ADDR": "192.0.2.10",
            "HTTP_AUTHORIZATION": _basic_header("admin", "secret"),
            "QUERY_STRING": "",
        }
        web.ctx.method = "GET"
        web.ctx.headers = []
        utils._API_AUTH_EVENT_TIMES.clear()

    def test_valid_basic_authentication_is_accepted(self):
        with mock.patch.object(utils, "test_password", return_value=True), \
                mock.patch.object(utils, "print_report"):
            self.assertTrue(utils.authenticate_basic())

    def test_failed_authentication_is_logged_once_per_minute(self):
        with mock.patch.object(utils, "test_password", return_value=False), \
                mock.patch.object(utils, "bruteforce_blocked", return_value=False), \
                mock.patch.object(utils.logEV, "save_events_log") as save_event, \
                mock.patch.object(utils, "print_report"):
            for unused in range(2):
                with self.assertRaises(API_Unauthorized):
                    utils.authenticate_basic()

        save_event.assert_called_once()
        self.assertEqual(save_event.call_args.kwargs["category"], "security")
        self.assertEqual(save_event.call_args.kwargs["level"], "warning")

    def test_bruteforce_block_is_logged_as_error(self):
        with mock.patch.object(utils, "test_password", return_value=False), \
                mock.patch.object(utils, "bruteforce_blocked", return_value=True), \
                mock.patch.object(utils.logEV, "save_events_log") as save_event, \
                mock.patch.object(utils, "print_report"):
            with self.assertRaises(API_Unauthorized):
                utils.authenticate_basic()

        self.assertEqual(save_event.call_args.kwargs["level"], "error")

    def test_repeated_failures_lock_and_success_clears_login_key(self):
        helpers.BRUTEFORCE_ATTEMPTS.clear()
        with mock.patch.object(helpers, "_request_ip", return_value="192.0.2.10"):
            for unused in range(helpers.BRUTEFORCE_LOCK_AFTER):
                helpers._bruteforce_failure("admin")
            self.assertTrue(helpers.bruteforce_blocked("admin"))
            helpers._bruteforce_success("admin")
            self.assertFalse(helpers.bruteforce_blocked("admin"))

    def test_state_changing_request_requires_csrf_when_enabled(self):
        web.ctx.method = "PUT"
        original_no_password = utils.options.no_password
        original_csrf_required = utils.options.api_csrf_required
        utils.options._values["no_password"] = False
        utils.options._values["api_csrf_required"] = True

        @utils.auth
        def change_state():
            return "changed"

        try:
            with mock.patch.object(utils, "authenticate_basic") as authenticate, \
                    mock.patch.object(utils, "verify_csrf") as verify:
                self.assertEqual(change_state(), "changed")
            authenticate.assert_called_once_with()
            verify.assert_called_once_with()
        finally:
            utils.options._values["no_password"] = original_no_password
            utils.options._values["api_csrf_required"] = original_csrf_required

    def test_read_only_request_does_not_require_csrf(self):
        web.ctx.method = "GET"
        original_no_password = utils.options.no_password
        original_csrf_required = utils.options.api_csrf_required
        utils.options._values["no_password"] = False
        utils.options._values["api_csrf_required"] = True

        @utils.auth
        def read_state():
            return "read"

        try:
            with mock.patch.object(utils, "authenticate_basic"), \
                    mock.patch.object(utils, "verify_csrf") as verify:
                self.assertEqual(read_state(), "read")
            verify.assert_not_called()
        finally:
            utils.options._values["no_password"] = original_no_password
            utils.options._values["api_csrf_required"] = original_csrf_required

    def test_public_session_is_denied_but_admin_is_allowed(self):
        original_no_password = utils.options.no_password
        utils.options._values["no_password"] = False

        @utils.permission
        def protected_action():
            return "allowed"

        try:
            with mock.patch.object(utils.server, "session", {
                    "category": "public", "visitor": "guest"
            }, create=True), mock.patch.object(
                    utils.logEV, "save_events_log"
            ), mock.patch.object(utils, "print_report"):
                with self.assertRaises(API_Unauthorized):
                    protected_action()

            with mock.patch.object(utils.server, "session", {
                    "category": "admin", "visitor": "admin"
            }, create=True):
                self.assertEqual(protected_action(), "allowed")
        finally:
            utils.options._values["no_password"] = original_no_password


class ApiStateOperationTests(unittest.TestCase):
    def setUp(self):
        web.ctx.clear()
        web.ctx.env = {"REMOTE_ADDR": "192.0.2.20"}
        web.ctx.method = "POST"
        self.station = SimpleNamespace(
            index=0,
            name="Front lawn",
            enabled=True,
            ignore_rain=False,
            is_master=False,
            is_master_two=False,
            is_master_by_program=False,
            activate_master=False,
            activate_master_two=False,
            activate_master_by_program=False,
            remaining_seconds=0,
            active=False,
            usage=1.0,
            precipitation=0.0,
            capacity=0.0,
            eto_factor=1.0,
            balance={},
        )

    def test_station_start_calls_controller_and_writes_audit_event(self):
        stations = mock.MagicMock()
        stations.__getitem__.return_value = self.station
        handler = _undecorated(api_module.Stations.POST)
        with mock.patch.object(api_module, "stations", stations), \
                mock.patch.object(api_module.web, "input", return_value={"do": "start"}), \
                mock.patch.object(api_module.logEV, "save_events_log") as save_event, \
                mock.patch.object(api_module.server, "session", {
                    "visitor": "admin"
                }, create=True):
            result = handler(api_module.Stations(), "0")

        stations.activate.assert_called_once_with(0)
        self.assertEqual(result["name"], "Front lawn")
        self.assertEqual(save_event.call_args.kwargs["category"], "irrigation")

    def test_run_once_sets_only_selected_enabled_station(self):
        second = SimpleNamespace(index=1, name="Back lawn")
        stations = mock.MagicMock()
        stations.enabled_stations.return_value = [self.station, second]
        stations.__getitem__.return_value = self.station
        handler = _undecorated(api_module.Runonce.POST)
        with mock.patch.object(api_module, "stations", stations), \
                mock.patch.object(api_module.web, "input", return_value={"time": "45"}), \
                mock.patch.object(api_module.run_once, "set") as set_run_once, \
                mock.patch.object(api_module.logEV, "save_events_log") as save_event, \
                mock.patch.object(api_module.server, "session", {
                    "visitor": "admin"
                }, create=True):
            result = handler(api_module.Runonce(), "0")

        self.assertEqual(result, "OK")
        set_run_once.assert_called_once_with({0: 45, 1: 0})
        self.assertEqual(save_event.call_args.kwargs["category"], "irrigation")


if __name__ == "__main__":
    unittest.main()
