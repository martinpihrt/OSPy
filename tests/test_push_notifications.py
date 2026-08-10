import hashlib
import hmac
import json
import os
import tempfile
import unittest
from unittest import mock


class _Response(object):
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class PushNotificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_data_dir = os.environ.get("OSPY_DATA_DIR")
        os.environ["OSPY_DATA_DIR"] = self.temp.name

        from api.v1.store import mobile_store
        self.store = mobile_store
        refresh = self.store.issue_refresh_token(
            "push-test", "admin", ["read"], "push-device", "Test phone"
        )
        self.device_id = refresh["device_id"]
        self.secret = "secret-value-" * 4
        self.store.save_push_subscription(
            self.device_id, "subscription-identifier-12345", self.secret,
            categories=["rain", "other"],
        )
        self.store.set_push_config(True, "https://relay.example")

    def tearDown(self):
        if self.previous_data_dir is None:
            os.environ.pop("OSPY_DATA_DIR", None)
        else:
            os.environ["OSPY_DATA_DIR"] = self.previous_data_dir
        self.temp.cleanup()

    def test_delivery_is_signed_and_does_not_expose_secret_in_payload(self):
        from api.v1.push import PushDispatcher

        dispatcher = PushDispatcher()
        subscription = self.store.push_subscription(
            self.device_id, include_secret=True
        )
        notification = {
            "id": 7,
            "event_type": "rain",
            "severity": "warning",
            "code": "rain_active",
            "title": "Rain",
            "message": "Rain detected",
            "data": {"active": True},
        }
        with mock.patch("api.v1.push.urlopen", return_value=_Response()) as send:
            dispatcher._deliver(subscription, notification)

        request = send.call_args.args[0]
        body = request.data
        self.assertNotIn(self.secret.encode("utf-8"), body)
        timestamp = request.get_header("X-ospy-timestamp")
        expected = hmac.new(
            self.secret.encode("utf-8"),
            timestamp.encode("ascii") + b"\n" + body,
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(request.get_header("X-ospy-signature"), expected)
        self.assertEqual(json.loads(body.decode("utf-8"))["code"], "rain_active")

    def test_revoking_device_also_removes_push_subscription(self):
        self.store.revoke_device(self.device_id)
        self.assertIsNone(self.store.push_subscription(self.device_id))

    def test_category_mapping_keeps_station_events_separate(self):
        from api.v1.push import notification_category

        self.assertEqual(
            notification_category("irrigation", "station_started"),
            "station_started",
        )
        self.assertEqual(
            notification_category("irrigation", "station_stopped"),
            "station_stopped",
        )
        self.assertEqual(notification_category("rain", "rain_active"), "rain")


if __name__ == "__main__":
    unittest.main()
