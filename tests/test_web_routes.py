import json
import os
import unittest
from unittest import mock

import web

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import helpers
from ospy import server
from ospy import webpages
from ospy.helpers import template_globals
from ospy.urls import urls


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_ROOT = os.path.join(ROOT, "ospy", "templates")


class FakeSession(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(name) from error

    def __setattr__(self, name, value):
        self[name] = value

    def regenerate_id(self):
        return None

    def kill(self):
        self.clear()


class WebRouteIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_session = server.session
        cls.original_base_render = webpages.WebPage.base_render
        cls.original_core_render = webpages.WebPage.core_render
        cls.session = FakeSession()
        server.session = cls.session

        render_globals = template_globals()
        render_globals.update({
            "get_cpu_temp": lambda unused_unit=None: 42,
            "get_cpu_usage": lambda: 5,
            "get_external_ip": lambda: "198.51.100.10",
            "get_ip": lambda: "192.0.2.10",
            "uptime": lambda: "1 day",
        })
        base_render = web.template.render(
            TEMPLATE_ROOT, globals=render_globals, cache=False
        ).base
        webpages.WebPage.base_render = base_render
        webpages.WebPage.core_render = web.template.render(
            TEMPLATE_ROOT, globals=render_globals, cache=False, base=base_render
        )
        cls.app = web.application(urls, {})

    @classmethod
    def tearDownClass(cls):
        webpages.WebPage.base_render = cls.original_base_render
        webpages.WebPage.core_render = cls.original_core_render
        server.session = cls.original_session

    def setUp(self):
        self.session.clear()
        self.session.update({
            "validated": True,
            "pages": [],
            "category": "admin",
            "visitor": "Test administrator",
            "ip": "192.0.2.10",
            "csrf_token": "test-csrf-token",
        })

    def test_main_admin_pages_render_through_routes(self):
        paths_and_markers = {
            "/": b"<!doctype html>",
            "/programs": b"<!doctype html>",
            "/runonce": b"<!doctype html>",
            "/log": b"<!doctype html>",
            "/options": b"<!doctype html>",
            "/stations": b"<!doctype html>",
            "/help": b"<!doctype html>",
            "/diagnostics": b"<!doctype html>",
        }

        for path, marker in paths_and_markers.items():
            with self.subTest(path=path):
                response = self.app.request(path)
                self.assertEqual(response.status, "200 OK")
                self.assertIn(marker, response.data)

    def test_anonymous_user_is_redirected_to_login(self):
        self.session["validated"] = False
        self.session["category"] = "public"

        response = self.app.request("/diagnostics")

        self.assertEqual(response.status, "303 See Other")
        self.assertTrue(response.headers["Location"].endswith("/login"))

    def test_login_page_renders_for_anonymous_user(self):
        self.session["validated"] = False
        self.session["category"] = "public"

        with mock.patch.object(webpages.autologin, "validate_cookie", return_value=None):
            response = self.app.request("/login")

        self.assertEqual(response.status, "200 OK")
        self.assertIn(b'id="password"', response.data)

    def test_non_admin_cannot_read_diagnostics_api(self):
        self.session["category"] = "user"

        response = self.app.request("/system_health.json")

        self.assertEqual(response.status, "403 Forbidden")

    def test_admin_can_read_diagnostics_api(self):
        payload = {"ok": True, "items": []}
        with mock.patch.object(webpages, "_system_health_data", return_value=payload):
            response = self.app.request("/system_health.json")

        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertIn(b'"ok": true', response.data)

    def test_diagnostics_api_errors_stay_json_responses(self):
        endpoints = (
            ("/diagnostics.json", "_diagnostics_data"),
            ("/system_health.json", "_system_health_data"),
        )

        for path, collector in endpoints:
            with self.subTest(path=path), \
                    mock.patch.object(webpages, collector, side_effect=RuntimeError("test")), \
                    mock.patch.object(webpages.log, "error"):
                response = self.app.request(path)

            payload = json.loads(response.data.decode("utf-8"))
            self.assertEqual(response.status, "200 OK")
            self.assertEqual(response.headers["Content-Type"], "application/json")
            self.assertIn("no-store", response.headers["Cache-Control"])
            self.assertFalse(payload["ok"])
            self.assertTrue(payload["error"])

    def test_unknown_plugin_history_returns_empty_json_history(self):
        response = self.app.request(
            "/diagnostics_history.json?plugin=missing_plugin&range=invalid"
        )

        payload = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response.status, "200 OK")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertEqual(payload["plugin"], "missing_plugin")
        self.assertEqual(payload["history"], [])

    def test_plugin_management_and_install_pages_render_without_network(self):
        repository_plugin = {
            "name": "Test plug-in",
            "version": "1.0.0",
            "read_me": "",
            "compatibility": {
                "compatible": True,
                "status": "ok",
                "summary": "Compatible.",
                "errors": [],
                "warnings": [],
                "permissions": [],
            },
        }
        with mock.patch.object(webpages.plugins, "available", return_value=[]), \
                mock.patch.object(webpages.plugins, "REPOS", ["test-repository"]), \
                mock.patch.object(webpages.plugins.checker, "sync_installed_statuses"), \
                mock.patch.object(webpages.plugins.checker, "update"), \
                mock.patch.object(
                    webpages.plugins.checker,
                    "get_repo_contents",
                    return_value={"test_plugin": repository_plugin},
                ):
            manage_response = self.app.request("/plugins_manage")
            install_response = self.app.request("/plugins_install")

        self.assertEqual(manage_response.status, "200 OK")
        self.assertIn(b"plugin-refresh-form", manage_response.data)
        self.assertEqual(install_response.status, "200 OK")
        self.assertIn(b"test_plugin", install_response.data)

    def test_admin_post_without_csrf_is_rejected_before_handler(self):
        with mock.patch.object(helpers, "print_report"):
            response = self.app.request(
                "/diagnostics", method="POST", data={"action": "restart"}
            )

        self.assertEqual(response.status, "403 Forbidden")

    def test_admin_post_with_csrf_reaches_handler(self):
        response = self.app.request(
            "/diagnostics",
            method="POST",
            data={
                "action": "restart",
                "plugin": "missing_plugin",
                "csrf": self.session["csrf_token"],
            },
        )

        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertIn(b'"ok": false', response.data)

    def test_non_admin_cannot_restart_plugin(self):
        self.session["category"] = "user"

        with mock.patch.object(webpages.plugins, "reload_plugin") as reload_plugin:
            response = self.app.request(
                "/diagnostics",
                method="POST",
                data={
                    "action": "restart",
                    "plugin": "test_plugin",
                    "csrf": self.session["csrf_token"],
                },
            )

        self.assertEqual(response.status, "403 Forbidden")
        reload_plugin.assert_not_called()


if __name__ == "__main__":
    unittest.main()
