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
        self.assertIn("put", document["paths"]["/irrigation"])
        self.assertIn("put", document["paths"]["/plugins/{plugin_id}"])

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

    def test_overview_keeps_working_when_weather_provider_fails(self):
        token, unused_refresh = self._token(("read",), role="user")
        with mock.patch(
                "api.v1.api.weather.get_home_forecast",
                side_effect=RuntimeError("provider timeout")):
            response = self._request("/overview", token)
        self.assertEqual(response.status, "200 OK")
        data = self._json(response)["data"]
        self.assertFalse(data["weather"]["available"])
        self.assertEqual(data["weather"]["cards"], [])
        self.assertIn(
            "weather_unavailable",
            [item["code"] for item in data["warnings"]],
        )
        self.assertIn("irrigation", data)

    def test_sensors_keep_working_when_optional_field_fails(self):
        class BrokenSensor(object):
            index = 7
            name = "Test sensor"
            enabled = 1

            @property
            def last_read_value(self):
                raise RuntimeError("temporary sensor failure")

        token, unused_refresh = self._token(("read",), role="user")
        with mock.patch("api.v1.api.sensors", [BrokenSensor()]):
            response = self._request("/sensors", token)
        self.assertEqual(response.status, "200 OK")
        data = self._json(response)["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Test sensor")
        self.assertIsNone(data[0]["last_read_value"])
        self.assertEqual(
            data[0]["field_errors"][0]["code"],
            "sensor_field_unavailable",
        )

    def test_sensors_use_finite_snapshot_instead_of_legacy_iteration(self):
        class Sensor(object):
            index = 0
            name = "Passive sensor"
            enabled = True

        class LegacySensors(object):
            def get(self):
                return [Sensor()]

            def __getitem__(self, index):
                raise AssertionError("The API must not iterate this collection")

        token, unused_refresh = self._token(("read",), role="user")
        with mock.patch("api.v1.api.sensors", LegacySensors()):
            response = self._request("/sensors", token)
        self.assertEqual(response.status, "200 OK")
        data = self._json(response)["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Passive sensor")

    def test_sensor_display_exposes_one_typed_reading(self):
        class Sensor(object):
            index = 0
            name = "Tank level"
            enabled = 1
            manufacturer = 0
            sens_type = 6
            multi_type = 8
            com_type = 0
            last_read_value = [23.6, -127, -127, -127, 1, 0, 0, 0, 73]
            response = True
            fw = 119
            ip_address = ("192", "168", "1", "25")

        token, unused_refresh = self._token(("read",), role="user")
        with mock.patch("api.v1.api.sensors", [Sensor()]):
            response = self._request("/sensors", token)
        display = self._json(response)["data"][0]["display"]
        self.assertTrue(self._json(response)["data"][0]["enabled"])
        self.assertEqual(display["type"], "multi")
        self.assertEqual(display["subtype"], "ultrasonic")
        self.assertEqual(display["reading"]["value"], 73)
        self.assertEqual(display["reading"]["unit"], "cm")
        self.assertEqual(display["firmware"], "1.19")
        self.assertEqual(display["ip_address"], "192.168.1.25")

    def test_irrigation_control_requires_control_scope(self):
        token, unused_refresh = self._token(("read",), role="user")
        response = self._request(
            "/irrigation", token, method="PUT",
            data={"scheduler_enabled": True},
        )
        self.assertEqual(response.status, "403 Forbidden")

    def test_irrigation_control_updates_scheduler_and_manual_mode(self):
        from api.v1 import api

        token, unused_refresh = self._token(
            ("read", "control"), role="user"
        )
        scheduler_before = api.options.scheduler_enabled
        manual_before = api.options.manual_mode
        try:
            with mock.patch(
                    "api.v1.api.logEV.save_events_log"), mock.patch(
                    "api.v1.api.event_stream.publish"):
                response = self._request(
                    "/irrigation", token, method="PUT",
                    data={
                        "scheduler_enabled": True,
                        "manual_mode": True,
                    },
                )
            self.assertEqual(response.status, "200 OK")
            data = self._json(response)["data"]
            self.assertTrue(data["scheduler_enabled"])
            self.assertTrue(data["manual_mode"])
        finally:
            api.options.scheduler_enabled = scheduler_before
            api.options.manual_mode = manual_before

    def test_irrigation_control_sets_configurable_rain_delay(self):
        from api.v1 import api

        token, unused_refresh = self._token(
            ("read", "control"), role="user"
        )
        rain_block_before = api.options.rain_block
        try:
            with mock.patch(
                    "api.v1.api.helpers.stop_onrain") as stop_onrain, mock.patch(
                    "api.v1.api.rain_blocks.seconds_left",
                    return_value=5400), mock.patch(
                    "api.v1.api.logEV.save_events_log"), mock.patch(
                    "api.v1.api.event_stream.publish"):
                response = self._request(
                    "/irrigation", token, method="PUT",
                    data={"rain_delay_hours": 1.5},
                )
            self.assertEqual(response.status, "200 OK")
            data = self._json(response)["data"]
            self.assertTrue(data["rain_block"])
            self.assertEqual(data["rain_block_seconds"], 5400)
            stop_onrain.assert_called_once_with()
        finally:
            api.options.rain_block = rain_block_before

    def test_overview_reports_only_an_active_rain_block(self):
        token, unused_refresh = self._token(("read",), role="user")
        with mock.patch(
                "api.v1.api.rain_blocks.seconds_left",
                return_value=0):
            response = self._request("/overview", token)
        irrigation = self._json(response)["data"]["irrigation"]
        self.assertFalse(irrigation["rain_block"])
        self.assertEqual(irrigation["rain_block_seconds"], 0)

    def test_directly_active_station_has_unknown_remaining_time(self):
        from api.v1 import api

        station = mock.Mock()
        station.index = 0
        station.name = "Manual output"
        station.enabled = True
        station.active = True
        station.remaining_seconds = 0
        station.is_master = False
        station.is_master_two = False
        station.is_master_by_program = False
        station.ignore_rain = False
        station.usage = 0
        station.precipitation = 0
        station.capacity = 0
        station.eto_factor = 1

        result = api._station_data(station)
        self.assertTrue(result["running"])
        self.assertEqual(result["remaining_seconds"], -1)

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

    def test_plugin_enable_uses_normal_lifecycle(self):
        from api.v1 import api

        token, unused_refresh = self._token(
            ("read", "plugins"), role="admin"
        )
        previous = list(api.options.enabled_plugins)
        try:
            api.options.enabled_plugins = []
            with mock.patch(
                    "api.v1.api.plugins.plugin_names",
                    return_value=["example"]), mock.patch(
                    "api.v1.api.plugins.plugin_permission_approval",
                    return_value={"approved": True, "missing": []}), mock.patch(
                    "api.v1.api.plugins.plugin_compatibility",
                    return_value={"compatible": True, "errors": []}), mock.patch(
                    "api.v1.api.plugins.start_enabled_plugins"), mock.patch(
                    "api.v1.api.plugins.running",
                    return_value=["example"]), mock.patch(
                    "api.v1.api.plugins.plugin_manifest",
                    return_value={"name": "Example", "version": "1.0.0"}), mock.patch(
                    "api.v1.api.plugins.plugin_diagnostics",
                    return_value=[]), mock.patch(
                    "api.v1.api.plugins.plugin_mobile_capabilities",
                    return_value={}), mock.patch(
                    "api.v1.api.logEV.save_events_log"), mock.patch(
                    "api.v1.api.event_stream.publish"):
                response = self._request(
                    "/plugins/example", token,
                    method="PUT", data={"enabled": True},
                )
            self.assertEqual(response.status, "200 OK")
            self.assertTrue(self._json(response)["data"]["enabled"])
            self.assertIn("example", api.options.enabled_plugins)
        finally:
            api.options.enabled_plugins = previous

    def test_plugin_enable_never_approves_permissions(self):
        token, unused_refresh = self._token(
            ("read", "plugins"), role="admin"
        )
        with mock.patch(
                "api.v1.api.plugins.plugin_names",
                return_value=["example"]), mock.patch(
                "api.v1.api.plugins.plugin_permission_approval",
                return_value={"approved": False, "missing": ["network"]}):
            response = self._request(
                "/plugins/example", token,
                method="PUT", data={"enabled": True},
            )
        self.assertEqual(response.status, "409 Conflict")
        self.assertEqual(
            self._json(response)["error"]["code"],
            "plugin_permission_approval_required",
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

    def test_mobile_api_reference_documents_current_wire_contracts(self):
        with open("api/docs/Mobile_API_v1.md", encoding="utf-8") as source:
            text = source.read()
        for required_term in (
                "rain_block_seconds",
                "rain_delay_hours",
                "remaining_seconds",
                '"display"',
                "activates_master",
                "sensor_field_unavailable",
                "two_factor_required",
                "refresh_expires_in",
                "next_cursor",
                "operation_id"):
            self.assertIn(required_term, text)
        self.assertIn('PUT /plugins/{id}', text)
