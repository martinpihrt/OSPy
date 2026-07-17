import unittest

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy.webpages import _health_item, _plugin_health_groups


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


if __name__ == "__main__":
    unittest.main()
