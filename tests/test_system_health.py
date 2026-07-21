import unittest
from types import SimpleNamespace
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import health, webpages
from ospy.webpages import (
    _health_item, _incident_history_data, _plugin_health_groups,
    _runtime_health_items, _sqlite_mirror_details, _sqlite_readiness_details,
    _security_health_data,
)


class SystemHealthTests(unittest.TestCase):
    def test_sqlite_readiness_is_passive_and_keeps_shelve_visible(self):
        available = _sqlite_readiness_details({
            "available": True, "version": "3.46.1", "error": "",
        })
        unavailable = _sqlite_readiness_details({
            "available": False, "version": "", "error": "missing module",
        })

        self.assertIn("shelve/DBM", available)
        self.assertIn("3.46.1", available)
        self.assertIn("shelve/DBM", unavailable)
        self.assertIn("missing module", unavailable)

    def test_sqlite_mirror_details_keep_shelve_authoritative_on_failure(self):
        synchronized = _sqlite_mirror_details({
            "state": "synchronized", "count": 25,
            "last_save": 123.0, "error": "",
        })
        failed = _sqlite_mirror_details({
            "state": "error", "count": 0,
            "last_save": 0, "error": "disk full",
        })

        self.assertIn("25", synchronized)
        self.assertIn("disk full", failed)
        self.assertIn("Shelve", failed)

        diverged = _sqlite_mirror_details({
            "state": "diverged", "differences": ["changed: name"],
            "difference_count": 1, "error": "",
        })
        self.assertIn("changed: name", diverged)
        self.assertIn("Shelve", diverged)

        read_test = _sqlite_mirror_details({
            "state": "verified", "count": 25, "last_save": 123.0,
            "checked": 124.0, "read_test": "passed", "error": "",
        })
        self.assertIn("25", read_test)
        self.assertGreater(len(read_test), len(synchronized))

        recovery = _sqlite_mirror_details({
            "state": "verified", "count": 25, "last_save": 123.0,
            "checked": 124.0, "read_test": "passed",
            "recovery_test": "passed", "recovery_count": 25,
            "backup_recovery_test": "failed",
            "backup_recovery_error": "damaged backup", "error": "",
            "restore_rehearsal": "passed",
            "restore_rehearsal_source": "current",
            "restore_rehearsal_count": 25,
            "emergency_selection": "ready",
            "emergency_selection_source": "current",
            "emergency_selection_count": 25,
            "emergency_recovery_enabled": True,
            "emergency_recovery_used": "",
            "emergency_recovery_error": "",
            "preferred_read": "used",
            "preferred_read_count": 25,
            "preferred_read_error": "",
        })
        self.assertIn("25", recovery)
        self.assertIn("damaged backup", recovery)

        rehearsal_failure = _sqlite_mirror_details({
            "state": "verified", "count": 25, "last_save": 123.0,
            "restore_rehearsal": "failed",
            "restore_rehearsal_error": "temporary restore mismatch",
            "error": "",
        })
        self.assertIn("temporary restore mismatch", rehearsal_failure)

        emergency_failure = _sqlite_mirror_details({
            "state": "error", "count": 0, "last_save": 0,
            "emergency_selection": "failed",
            "emergency_selection_error": "no verified candidate",
            "error": "damaged current shadow",
        })
        self.assertIn("no verified candidate", emergency_failure)

        emergency_used = _sqlite_mirror_details({
            "state": "verified", "count": 25, "last_save": 123.0,
            "emergency_recovery_enabled": True,
            "emergency_recovery_used": "backup",
            "emergency_recovery_error": "",
            "error": "",
        })
        without_recovery = _sqlite_mirror_details({
            "state": "verified", "count": 25, "last_save": 123.0,
            "error": "",
        })
        self.assertGreater(len(emergency_used), len(without_recovery))

        preferred_fallback = _sqlite_mirror_details({
            "state": "error", "count": 0, "last_save": 0,
            "preferred_read": "fallback",
            "preferred_read_count": 0,
            "preferred_read_error": "checksum mismatch",
            "error": "checksum mismatch",
        })
        self.assertIn("checksum mismatch", preferred_fallback)

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

    def test_runtime_issue_registry_tracks_recurrence_and_resolution(self):
        issue_id = "test_runtime_issue"
        health.resolve_issue(issue_id)
        self.addCleanup(health.resolve_issue, issue_id)

        health.report_issue(
            issue_id, "Test component", "Operation failed",
            "ValueError: invalid value", "Correct the value", "/options",
            severity="warning",
        )
        health.report_issue(
            issue_id, "Test component", "Operation failed again",
            "ValueError: invalid value", "Correct the value", "/options",
            severity="error",
        )

        issue = next(
            item for item in health.active_issues()
            if item["id"] == issue_id
        )
        self.assertEqual(issue["count"], 2)
        self.assertEqual(issue["severity"], "error")
        self.assertEqual(issue["summary"], "Operation failed again")
        self.assertTrue(issue["first_seen"] <= issue["last_seen"])
        self.assertTrue(health.resolve_issue(issue_id))
        self.assertNotIn(
            issue_id, [item["id"] for item in health.active_issues()]
        )

    def test_health_item_exposes_specific_solution(self):
        item = _health_item(
            "runtime:test", "Runtime", "error", "Problem",
            solution="Specific recovery step",
        )

        self.assertEqual(item["solution"], "Specific recovery step")

    def test_runtime_issue_is_rendered_as_actionable_health_row(self):
        issue = {
            "id": "callback:example",
            "title": "Settings change handler",
            "summary": "A component could not apply a changed setting.",
            "details": "example.callback: ValueError: invalid",
            "solution": "Verify the changed setting.",
            "link": "/options",
            "severity": "error",
            "last_seen": 1,
            "count": 3,
        }
        with mock.patch.object(health, "active_issues", return_value=[issue]):
            rows = _runtime_health_items()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "runtime:callback:example")
        self.assertEqual(rows[0]["status"], "error")
        self.assertIn("3", rows[0]["details"])
        self.assertEqual(rows[0]["solution"], issue["solution"])
        self.assertEqual(rows[0]["link"], "/options")

    def test_incident_history_data_formats_dates_and_counts_states(self):
        incidents = [{
            "incident_id": "incident-1",
            "issue_id": "callback:example",
            "title": "Callback",
            "summary": "Failed",
            "details": "ValueError",
            "solution": "Correct settings",
            "link": "/options",
            "severity": "error",
            "status": "resolved",
            "opened": 1,
            "last_seen": 2,
            "resolved": 3,
            "count": 2,
        }]
        with mock.patch.object(
                health, "incident_history", return_value=incidents):
            data = _incident_history_data()

        self.assertEqual(data["counts"]["all"], 1)
        self.assertEqual(data["counts"]["resolved"], 1)
        self.assertEqual(data["incidents"][0]["count"], 2)
        self.assertTrue(data["incidents"][0]["resolved"])

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
