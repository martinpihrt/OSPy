import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import helpers


class FakeThread(object):
    instances = []

    def __init__(self, target, name):
        self.target = target
        self.name = name
        self.daemon = False
        self.started = False
        self.__class__.instances.append(self)

    def start(self):
        self.started = True


class ExternalIpTests(unittest.TestCase):
    def setUp(self):
        FakeThread.instances = []

    def test_stale_external_ip_returns_cached_value_and_starts_one_refresh(self):
        with mock.patch.object(helpers, "Thread", FakeThread), \
                mock.patch.object(helpers, "now", return_value=100), \
                mock.patch.object(helpers, "last_ip_check_time", 0), \
                mock.patch.object(
                    helpers, "external_ip_address", "198.51.100.20"
                ), mock.patch.object(
                    helpers, "external_ip_refresh_thread", None
                ):
            first = helpers.get_external_ip()
            second = helpers.get_external_ip()
            pending = helpers.external_ip_refresh_pending()

        self.assertEqual(first, "198.51.100.20")
        self.assertEqual(second, "198.51.100.20")
        self.assertTrue(pending)
        self.assertEqual(len(FakeThread.instances), 1)
        self.assertTrue(FakeThread.instances[0].started)
        self.assertEqual(FakeThread.instances[0].name, "ExternalIPRefresh")

    def test_background_refresh_updates_external_ip_cache(self):
        with mock.patch.object(helpers, "net_connect", return_value=True), \
                mock.patch.object(
                    helpers.subprocess,
                    "check_output",
                    return_value=b"203.0.113.25\n",
                ) as check_output, mock.patch.object(
                    helpers, "now", return_value=250
                ), mock.patch.object(helpers, "last_ip_check_time", 0), \
                mock.patch.object(helpers, "external_ip_address", "-"), \
                mock.patch.object(
                    helpers, "external_ip_refresh_thread", object()
                ):
            helpers._refresh_external_ip()
            address = helpers.external_ip_address
            checked_at = helpers.last_ip_check_time
            worker = helpers.external_ip_refresh_thread

        self.assertEqual(address, "203.0.113.25")
        self.assertEqual(checked_at, 250)
        self.assertIsNone(worker)
        self.assertIn("--max-time", check_output.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
