import json
import os
import tempfile
import unittest
from unittest import mock


class MobileAPIV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from api.v1.api import get_app
        cls.app = get_app()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_data_dir = os.environ.get("OSPY_DATA_DIR")
        os.environ["OSPY_DATA_DIR"] = self.temp.name

    def tearDown(self):
        if self.previous_data_dir is None:
            os.environ.pop("OSPY_DATA_DIR", None)
        else:
            os.environ["OSPY_DATA_DIR"] = self.previous_data_dir
        self.temp.cleanup()

    @staticmethod
    def _json(response):
        return json.loads(response.data.decode("utf-8"))

    def _token(self, scopes=("read",), role="admin"):
        from api.v1.security import issue_access_token
        from api.v1.store import mobile_store
        refresh = mobile_store.issue_refresh_token(
            "mobile-test", role, scopes, "test-device", "Unit test"
        )
        return issue_access_token(
            "mobile-test", role, scopes, refresh["device_id"], refresh["id"]
        ), refresh

    def _request(self, path, token=None, method="GET", data=None):
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + token
        if data is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(data)
        return self.app.request(path, method=method, headers=headers, data=data)

    def test_public_discovery_and_openapi(self):
        response = self._request("/server")
        self.assertEqual(response.status, "200 OK")
        data = self._json(response)["data"]
        self.assertEqual(data["api_version"], "1.0.0")
        self.assertTrue(data["instance_id"])

        response = self._request("/openapi.json")
        document = self._json(response)
        self.assertEqual(document["openapi"], "3.0.3")
        self.assertIn("/stations", document["paths"])
        self.assertIn("put", document["paths"]["/stations/{station_id}"])
        self.assertIn("post", document["paths"]["/programs"])
        self.assertIn("delete", document["paths"]["/programs/{program_id}"])
        self.assertIn("delete", document["paths"]["/auth/devices/{device_id}"])

    def test_protected_endpoint_requires_bearer_token(self):
        response = self._request("/stations")
        self.assertEqual(response.status, "401 Unauthorized")
        self.assertEqual(self._json(response)["error"]["code"], "missing_token")

    def test_read_token_lists_stations_but_cannot_control(self):
        token, unused_refresh = self._token(("read",), role="user")
        response = self._request("/stations", token)
        self.assertEqual(response.status, "200 OK")
        stations = self._json(response)["data"]
        self.assertTrue(stations)
        self.assertTrue(stations[0]["id"].startswith("station-"))

        response = self._request(
            "/stations/station-0/actions/start", token, method="POST", data={}
        )
        self.assertEqual(response.status, "403 Forbidden")
        self.assertEqual(
            self._json(response)["error"]["code"], "insufficient_scope"
        )

    def test_control_token_uses_station_control_path(self):
        token, unused_refresh = self._token(("read", "control"), role="user")
        with mock.patch("api.v1.api.stations.activate", return_value=[0]) as activate:
            response = self._request(
                "/stations/station-0/actions/start", token,
                method="POST", data={},
            )
        self.assertEqual(response.status, "200 OK")
        activate.assert_called_once_with(0)

    def test_refresh_token_is_rotated_and_old_token_is_rejected(self):
        from api.v1.security import refresh
        token, original = self._token(("read",), role="user")
        replacement = refresh(original["token"])
        self.assertNotEqual(replacement["refresh_token"], original["token"])
        with self.assertRaises(Exception) as context:
            refresh(original["token"])
        self.assertEqual(getattr(context.exception, "code", ""), "invalid_refresh_token")

    def test_pairing_same_device_revokes_previous_session(self):
        from api.v1.security import issue_access_token, verify_access_token
        from api.v1.store import mobile_store
        first = mobile_store.issue_refresh_token(
            "mobile-test", "user", ("read",), "same-device", "Phone"
        )
        first_access = issue_access_token(
            "mobile-test", "user", ("read",), first["device_id"], first["id"]
        )
        second = mobile_store.issue_refresh_token(
            "mobile-test", "user", ("read",), "same-device", "Phone"
        )
        self.assertNotEqual(first["id"], second["id"])
        with self.assertRaises(Exception) as context:
            verify_access_token(first_access)
        self.assertEqual(getattr(context.exception, "code", ""), "invalid_token")

    def test_device_id_cannot_take_over_another_users_pairing(self):
        from api.v1.store import mobile_store
        first = mobile_store.issue_refresh_token(
            "alice", "user", ("read",), "shared-device-id", "Alice phone"
        )
        second = mobile_store.issue_refresh_token(
            "bob", "user", ("read",), "shared-device-id", "Bob phone"
        )
        self.assertEqual(first["device_id"], "shared-device-id")
        self.assertNotEqual(second["device_id"], "shared-device-id")
        devices = {item["id"]: item for item in mobile_store.devices()}
        self.assertEqual(devices["shared-device-id"]["username"], "alice")

    def test_notification_pagination_and_acknowledgement(self):
        from api.v1.store import mobile_store
        mobile_store.add_notification(
            "diagnostics", "warning", "test", "Test warning", "Details"
        )
        token, unused_refresh = self._token(("read",), role="user")
        response = self._request("/notifications?unread=1", token)
        payload = self._json(response)
        self.assertEqual(len(payload["data"]), 1)
        self.assertEqual(payload["meta"]["unread"], 1)
        self.assertIn("T", payload["data"][0]["created"])
        self.assertIsNone(payload["data"][0]["acknowledged"])

        notification_id = payload["data"][0]["id"]
        response = self._request(
            "/notifications/{}/ack".format(notification_id),
            token, method="POST", data={},
        )
        self.assertEqual(self._json(response)["data"]["unread"], 0)

    def test_operations_are_persistent(self):
        from api.v1.store import mobile_store
        operation_id = mobile_store.create_operation("test")
        mobile_store.update_operation(
            operation_id, status="completed", progress=100, result={"ok": True}
        )
        token, unused_refresh = self._token(("read",), role="user")
        response = self._request("/operations/" + operation_id, token)
        operation = self._json(response)["data"]
        self.assertEqual(operation["status"], "completed")
        self.assertEqual(operation["result"], {"ok": True})
        self.assertIn("T", operation["created"])

    def test_declared_plugin_action_uses_safe_action_capability(self):
        token, unused_refresh = self._token(("read", "plugins"), role="admin")
        with mock.patch(
                "api.v1.api.plugins.plugin_mobile_call",
                return_value={"accepted": True}) as mobile_call:
            response = self._request(
                "/plugins/example/actions/refresh", token,
                method="POST", data={"value": 1},
            )
        self.assertEqual(response.status, "200 OK")
        self.assertTrue(self._json(response)["data"]["accepted"])
        mobile_call.assert_called_once_with(
            "example", "action", "refresh", {"value": 1}
        )


class MobilePluginContractTests(unittest.TestCase):
    def test_unknown_mobile_capability_is_rejected(self):
        import plugins
        with self.assertRaises(ValueError):
            plugins.plugin_mobile_call("missing", "arbitrary")

    def test_mobile_capabilities_are_json_safe_for_legacy_plugin(self):
        import plugins
        with mock.patch.object(plugins, "plugin_manifest", return_value={}):
            result = plugins.plugin_mobile_capabilities("legacy")
        json.dumps(result)
        self.assertEqual(result["api_version"], 1)
        self.assertFalse(result["available"])



class MobileAPIDocumentationTests(unittest.TestCase):
    def test_mobile_api_reference_is_listed_in_help(self):
        from ospy.helpers import get_help_files
        filenames = [
            item[2].replace("\\", "/")
            for item in get_help_files() if len(item) > 2
        ]
        self.assertIn("api/docs/Mobile_API_v1.md", filenames)

    def test_all_language_guides_reference_versioned_mobile_api(self):
        import glob
        guides = glob.glob("ospy/docs/Web Interface Guide - *.md")
        self.assertEqual(len(guides), 7)
        for filename in guides:
            with open(filename, encoding="utf-8") as source:
                text = source.read()
            self.assertIn("../../api/docs/Mobile_API_v1.md", text, filename)
