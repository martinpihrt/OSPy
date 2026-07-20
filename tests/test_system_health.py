import unittest
from types import SimpleNamespace
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import webpages
from ospy.webpages import (
    _health_item, _plugin_health_groups, _security_health_data,
)


class SystemHealthTests(unittest.TestCase):
    def test_plugin_health_error_requires_confirmation(self):
        plugin = {
            "enabled": True,
            "running": True,
            "last_error": "",
            "health": {"status": "error"},
            "compatibility": {"status": "ok"},
            "preflight": {"status": "ok"},
        }

        immediate, health, warnings = _plugin_health_groups([plugin])

        self.assertEqual(immediate, [])
        self.assertEqual(health, [plugin])
        self.assertEqual(warnings, [])

    def test_start_and_validation_failures_are_immediate(self):
        stopped = {
            "enabled": True,
            "running": False,
            "health": {"status": "error"},
            "compatibility": {"status": "ok"},
            "preflight": {"status": "ok"},
        }
        incompatible = {
            "enabled": True,
            "running": True,
            "health": {"status": "ok"},
            "compatibility": {"status": "error"},
            "preflight": {"status": "ok"},
        }

        immediate, health, warnings = _plugin_health_groups(
            [stopped, incompatible]
        )

        self.assertEqual(immediate, [stopped, incompatible])
        self.assertEqual(health, [])
        self.assertEqual(warnings, [])

    def test_health_item_exposes_confirmation_flag(self):
        item = _health_item(
            "plugins", "Plug-ins", "error", "Problem",
            confirmation_required=True,
        )

        self.assertTrue(item["confirmation_required"])

    def test_security_profiles_make_internet_requirements_stricter(self):
        insecure_options = SimpleNamespace(
            use_ssl=False,
            use_own_ssl=False,
            no_password=False,
            two_factor_method="none",
            api_sensor_auth_required=False,
            api_csrf_required=False,
            api_cors_allowed_origin="*",
            sensor_fw_passwd="fg4s5b.s,trr7sw8sgyvrDfg",
        )
        with mock.patch.object(webpages, "options", insecure_options), \
                mock.patch.object(
                    webpages.web.config.session_parameters, "secure", False
                ):
            data = _security_health_data()

        items = {item["id"]: item for item in data["items"]}
        self.assertEqual(items["https"]["status"]["home"], "warning")
        self.assertEqual(items["https"]["status"]["internet"], "error")
        self.assertEqual(items["two_factor"]["status"]["internet"], "error")
        self.assertEqual(items["sensor_api_auth"]["status"]["internet"], "error")
        self.assertEqual(items["api_csrf"]["status"]["internet"], "error")
        self.assertEqual(items["cors"]["status"]["internet"], "error")
        self.assertEqual(items["sensor_password"]["status"]["home"], "error")
        self.assertNotIn(
            insecure_options.sensor_fw_passwd,
            str(items["sensor_password"]),
        )

    def test_hardened_security_settings_pass_configuration_checks(self):
        hardened_options = SimpleNamespace(
            use_ssl=True,
            use_own_ssl=False,
            no_password=False,
            two_factor_method="totp",
            api_sensor_auth_required=True,
            api_csrf_required=True,
            api_cors_allowed_origin="https://controller.example",
            sensor_fw_passwd="Unique-Sensor-Password-2026",
        )
        with mock.patch.object(webpages, "options", hardened_options), \
                mock.patch.object(
                    webpages.web.config.session_parameters, "secure", True
                ):
            data = _security_health_data()

        items = {item["id"]: item for item in data["items"]}
        for item_id in (
                "https", "anonymous", "two_factor", "sensor_api_auth",
                "api_csrf", "cors", "sensor_password"):
            self.assertEqual(items[item_id]["status"]["internet"], "ok")
        self.assertEqual(items["http_headers"]["status"]["internet"], "error")


if __name__ == "__main__":
    unittest.main()
