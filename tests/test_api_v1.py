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
        self.assertIn("post", document["paths"]["/push"])
        self.assertIn("post", document["paths"]["/push/test"])
        self.assertIn("put", document["paths"]["/irrigation"])
        self.assertIn("/program-groups", document["paths"])
        self.assertIn(
            "post",
            document["paths"]["/program-groups/{group_id}/postponements"],
        )
        self.assertIn("put", document["paths"]["/plugins/{plugin_id}"])
        self.assertIn("/schedule", document["paths"])

    def test_protected_endpoint_requires_bearer_token(self):
        response = self._request("/stations")
        self.assertEqual(response.status, "401 Unauthorized")
        self.assertEqual(self._json(response)["error"]["code"], "missing_token")

    def test_device_can_register_update_and_remove_push_subscription(self):
        token, refresh = self._token(("read",), role="user")
        response = self._request(
            "/push", token, method="POST", data={
                "subscription_id": "subscription-identifier-12345",
                "send_secret": "s" * 48,
                "enabled": True,
                "categories": ["rain", "station_started"],
            },
        )
        self.assertEqual(response.status, "201 Created")
        subscription = self._json(response)["data"]
        self.assertEqual(subscription["device_id"], refresh["device_id"])
        self.assertNotIn("send_secret", subscription)

        response = self._request(
            "/push", token, method="PUT", data={
                "enabled": False,
                "categories": ["diagnostics"],
            },
        )
        self.assertEqual(response.status, "200 OK")
        self.assertFalse(self._json(response)["data"]["enabled"])

        response = self._request("/push", token, method="DELETE")
        self.assertEqual(response.status, "200 OK")
        self.assertTrue(self._json(response)["data"]["unregistered"])

    def test_push_registration_rejects_unknown_category(self):
        token, unused_refresh = self._token(("read",), role="user")
        response = self._request(
            "/push", token, method="POST", data={
                "subscription_id": "subscription-identifier-12345",
                "send_secret": "s" * 48,
                "categories": ["not-a-category"],
            },
        )
        self.assertEqual(response.status, "422 Unprocessable Entity")
        self.assertEqual(
            self._json(response)["error"]["code"], "invalid_push_categories"
        )

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
        from api.v1 import api

        token, unused_refresh = self._token(("read", "control"), role="user")
        manual_before = api.options.manual_mode
        try:
            api.options.manual_mode = True
            with mock.patch(
                    "api.v1.api.stations.activate", return_value=[0]) as activate, \
                    mock.patch("api.v1.api.log.start_run") as start_run:
                response = self._request(
                    "/stations/station-0/actions/start", token,
                    method="POST", data={},
                )
            self.assertEqual(response.status, "200 OK")
            activate.assert_called_once_with(0)
            interval = start_run.call_args.args[0]
            self.assertEqual(interval["station"], 0)
            self.assertTrue(interval["manual"])
            self.assertEqual(interval["program"], -1)
        finally:
            api.options.manual_mode = manual_before

    def test_station_start_requires_manual_mode(self):
        from api.v1 import api

        token, unused_refresh = self._token(("read", "control"), role="user")
        manual_before = api.options.manual_mode
        try:
            api.options.manual_mode = False
            with mock.patch("api.v1.api.stations.activate") as activate:
                response = self._request(
                    "/stations/station-0/actions/start", token,
                    method="POST", data={},
                )
            self.assertEqual(response.status, "409 Conflict")
            self.assertEqual(
                self._json(response)["error"]["code"],
                "manual_mode_required",
            )
            activate.assert_not_called()
        finally:
            api.options.manual_mode = manual_before

    def test_station_start_accepts_a_bounded_manual_duration(self):
        import datetime
        from api.v1 import api

        token, unused_refresh = self._token(("read", "control"), role="user")
        manual_before = api.options.manual_mode
        try:
            api.options.manual_mode = True
            with mock.patch(
                    "api.v1.api.stations.activate", return_value=[0]), \
                    mock.patch("api.v1.api.log.start_run") as start_run:
                response = self._request(
                    "/stations/station-0/actions/start", token,
                    method="POST", data={"duration_seconds": 125},
                )
            self.assertEqual(response.status, "200 OK")
            interval = start_run.call_args.args[0]
            self.assertEqual(
                interval["end"] - interval["start"],
                datetime.timedelta(seconds=125),
            )
        finally:
            api.options.manual_mode = manual_before

    def test_station_start_rejects_invalid_manual_duration(self):
        from api.v1 import api

        token, unused_refresh = self._token(("read", "control"), role="user")
        manual_before = api.options.manual_mode
        try:
            api.options.manual_mode = True
            for value in (0, 60000, True, "60"):
                response = self._request(
                    "/stations/station-0/actions/start", token,
                    method="POST", data={"duration_seconds": value},
                )
                self.assertEqual(response.status, "422 Unprocessable Entity")
                self.assertEqual(
                    self._json(response)["error"]["code"],
                    "invalid_station_duration",
                )
        finally:
            api.options.manual_mode = manual_before

    def test_station_stop_finishes_its_manual_run(self):
        token, unused_refresh = self._token(("read", "control"), role="user")
        other = {"station": 1}
        selected = {"station": 0}
        with mock.patch("api.v1.api.stations.deactivate") as deactivate, \
                mock.patch(
                    "api.v1.api.log.active_runs",
                    side_effect=[[other, selected], [], []],
                ), mock.patch("api.v1.api.log.finish_run") as finish_run:
            response = self._request(
                "/stations/station-0/actions/stop", token,
                method="POST", data={},
            )
        self.assertEqual(response.status, "200 OK")
        deactivate.assert_called_once_with(0)
        finish_run.assert_called_once_with(selected)

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

    def test_irrigation_control_sets_user_level_adjustment(self):
        from api.v1 import api

        token, unused_refresh = self._token(
            ("read", "control"), role="user"
        )
        level_before = api.options.level_adjustment
        try:
            with mock.patch(
                    "api.v1.api.level_adjustments.total_adjustment",
                    return_value=0.75), mock.patch(
                    "api.v1.api.logEV.save_events_log"), mock.patch(
                    "api.v1.api.event_stream.publish"):
                response = self._request(
                    "/irrigation", token, method="PUT",
                    data={"level_adjustment_percent": 75},
                )
            self.assertEqual(response.status, "200 OK")
            data = self._json(response)["data"]
            self.assertEqual(data["level_adjustment_percent"], 75.0)
            self.assertEqual(data["user_level_adjustment"], 0.75)
            self.assertEqual(data["level_adjustment"], 0.75)
            self.assertEqual(api.options.level_adjustment, 0.75)
        finally:
            api.options.level_adjustment = level_before

    def test_irrigation_control_rejects_invalid_level_atomically(self):
        from api.v1 import api

        token, unused_refresh = self._token(
            ("read", "control"), role="user"
        )
        level_before = api.options.level_adjustment
        response = self._request(
            "/irrigation", token, method="PUT",
            data={"level_adjustment_percent": -1},
        )
        self.assertEqual(response.status, "422 Unprocessable Entity")
        self.assertEqual(
            self._json(response)["error"]["code"],
            "invalid_level_adjustment",
        )
        self.assertEqual(api.options.level_adjustment, level_before)

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

    def test_schedule_returns_normalized_mobile_timeline(self):
        import datetime

        token, unused_refresh = self._token(("read",), role="user")
        now = datetime.datetime.now()
        interval = {
            "uid": "test-run",
            "station": 0,
            "program": 0,
            "program_name": "Morning",
            "start": now - datetime.timedelta(minutes=5),
            "original_start": now - datetime.timedelta(minutes=5),
            "end": now + datetime.timedelta(minutes=5),
            "active": True,
            "blocked": False,
            "manual": False,
        }
        with mock.patch(
                "ospy.scheduler.combined_schedule",
                return_value=[interval]):
            response = self._request("/schedule?hours=24", token)
        self.assertEqual(response.status, "200 OK")
        data = self._json(response)["data"]
        self.assertEqual(data["items"][0]["state"], "running")
        self.assertEqual(data["items"][0]["station_id"], "station-0")
        self.assertEqual(data["items"][0]["program_id"], "program-0")
        self.assertGreater(data["items"][0]["progress"], 0)

    def test_schedule_today_excludes_finished_runs_outside_today(self):
        import datetime

        token, unused_refresh = self._token(("read",), role="user")
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        old_interval = {
            "uid": "old-run",
            "station": 0,
            "program": 0,
            "program_name": "Old",
            "start": yesterday.replace(hour=8, minute=0),
            "original_start": yesterday.replace(hour=8, minute=0),
            "end": yesterday.replace(hour=8, minute=30),
            "active": False,
            "blocked": False,
            "manual": False,
        }
        current_interval = {
            "uid": "today-run",
            "station": 0,
            "program": 0,
            "program_name": "Today",
            "start": now - datetime.timedelta(minutes=5),
            "original_start": now - datetime.timedelta(minutes=5),
            "end": now + datetime.timedelta(minutes=5),
            "active": True,
            "blocked": False,
            "manual": False,
        }
        with mock.patch(
                "ospy.scheduler.combined_schedule",
                return_value=[old_interval, current_interval]):
            response = self._request("/schedule?date=today", token)
        self.assertEqual(response.status, "200 OK")
        items = self._json(response)["data"]["items"]
        self.assertEqual([item["id"] for item in items], ["today-run"])

    def test_run_log_date_returns_only_completed_history_for_that_day(self):
        import datetime
        from api.v1 import api

        token, unused_refresh = self._token(("read",), role="user")
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        yesterday_start = datetime.datetime.combine(
            yesterday, datetime.time(hour=8)
        )
        today_start = yesterday_start + datetime.timedelta(days=1)

        def run(uid, start):
            return {
                "uid": uid,
                "station": 0,
                "program": 0,
                "program_name": "Morning",
                "start": start,
                "original_start": start,
                "end": start + datetime.timedelta(minutes=30),
                "active": False,
                "blocked": False,
                "manual": False,
            }

        with mock.patch.object(
                api.log, "finished_runs",
                return_value=[run("yesterday-run", yesterday_start),
                              run("today-run", today_start)]):
            response = self._request(
                "/logs/runs?date={}&limit=500".format(yesterday.isoformat()),
                token,
            )

        self.assertEqual(response.status, "200 OK")
        payload = self._json(response)
        self.assertEqual(
            [item["id"] for item in payload["data"]],
            ["yesterday-run"],
        )
        self.assertEqual(payload["meta"]["total"], 1)

    def test_program_editor_describes_simple_schedule(self):
        from api.v1 import api
        from ospy.programs import ProgramType

        program = mock.Mock()
        program.type = ProgramType.DAYS_SIMPLE
        program.type_data = [360, 20, 5, 1, [0, 2, 4]]
        result = api._program_editor(program)
        self.assertTrue(result["valid"])
        self.assertEqual(result["kind"], "days_simple")
        self.assertEqual(result["fields"]["start_minute"], 360)
        self.assertEqual(result["fields"]["duration_minutes"], 20)
        self.assertEqual(result["fields"]["days"], [0, 2, 4])

    def test_program_enabled_partial_update_does_not_rebuild_schedule(self):
        from api.v1 import api

        class Program(object):
            enabled = False

        program = Program()
        with mock.patch(
                "api.api.Programs._dict_to_program",
                side_effect=AssertionError("schedule must not be rebuilt")):
            api._update_program(program, {"enabled": True}, require_schedule=False)
        self.assertTrue(program.enabled)

    def test_program_enabled_partial_update_rejects_non_boolean_atomically(self):
        from api.v1 import api

        class Program(object):
            enabled = False

        program = Program()
        with self.assertRaises(Exception) as context:
            api._update_program(
                program, {"enabled": "true"}, require_schedule=False
            )
        self.assertEqual(getattr(context.exception, "code", ""), "invalid_program")
        self.assertFalse(program.enabled)

    def test_program_full_update_is_committed_only_after_validation(self):
        from api.v1 import api
        from ospy.programs import programs, ProgramType

        program = programs.create_program()
        program.name = "Original"
        program.enabled = False
        program.set_weekly_advanced([[60, 90]])
        original = (program.name, program.enabled, program.type, program.type_data)
        with self.assertRaises(Exception) as context:
            api._update_program(program, {
                "name": "Partly changed",
                "enabled": True,
                "stations": [],
                "type": ProgramType.DAYS_SIMPLE,
                "type_data": [360, 10, 0, 0, []],
            }, require_schedule=False)
        self.assertEqual(getattr(context.exception, "code", ""), "invalid_program")
        self.assertEqual(
            (program.name, program.enabled, program.type, program.type_data),
            original,
        )

    def test_program_days_simple_definition_is_created_without_type_conversion(self):
        from api.v1 import api
        from ospy.programs import programs, ProgramType

        program = programs.create_program()
        groups_before = api.options.program_groups
        api.options.program_groups = groups_before + [{
            "id": "greenhouse", "name": "Greenhouse", "collapsed": False,
        }]
        program.group_id = "greenhouse"
        program.fixed = 1
        try:
            api._update_program(program, {
                "name": "Mobile program",
                "enabled": True,
                "stations": [],
                "type": ProgramType.DAYS_SIMPLE,
                "type_data": [360, 10, 0, 0, [0, 2, 4]],
            }, require_schedule=True)
            self.assertEqual(program.name, "Mobile program")
            self.assertEqual(program.type, ProgramType.DAYS_SIMPLE)
            self.assertEqual(program.type_data, [360, 10, 0, 0, [0, 2, 4]])
            self.assertTrue(program.schedule)
            self.assertEqual(program.group_id, "greenhouse")
            self.assertEqual(program.fixed, 1)
        finally:
            api.options.program_groups = groups_before

    def test_program_update_moves_program_to_existing_group_atomically(self):
        from api.v1 import api
        from ospy.programs import programs, ProgramType

        groups_before = api.options.program_groups
        api.options.program_groups = groups_before + [{
            "id": "orchard", "name": "Orchard", "collapsed": False,
        }]
        program = programs.create_program()
        program.name = "Morning"
        program.enabled = True
        program.set_days_simple(360, 10, 0, 0, [0])
        try:
            api._update_program(program, {
                "group_id": "orchard",
            }, require_schedule=False)
            self.assertEqual(program.group_id, "orchard")

            with self.assertRaises(Exception) as context:
                api._update_program(program, {
                    "name": "Must not commit",
                    "group_id": "missing-group",
                }, require_schedule=False)
            self.assertEqual(getattr(context.exception, "code", ""), "invalid_program")
            self.assertEqual(program.name, "Morning")
            self.assertEqual(program.group_id, "orchard")
            self.assertEqual(program.type, ProgramType.DAYS_SIMPLE)
        finally:
            api.options.program_groups = groups_before

    def test_program_groups_endpoint_exposes_membership_and_next_runs(self):
        import datetime
        from api.v1 import api

        token, unused_refresh = self._token(("read",), role="user")
        groups_before = api.options.program_groups
        api.options.program_groups = [{
            "id": "default", "name": "Default", "collapsed": False,
        }]
        occurrence = {
            "number": 1,
            "name": "Morning",
            "start": datetime.datetime(2026, 8, 14, 6, 0),
            "end": datetime.datetime(2026, 8, 14, 6, 10),
            "minutes": 10,
        }
        try:
            with mock.patch(
                    "api.v1.api.programs.programs_in_group",
                    return_value=[]), mock.patch(
                    "api.v1.api.helpers.program_group_run_sequence",
                    return_value=[occurrence]), mock.patch(
                    "api.v1.api.programs.group_postponement",
                    return_value=None):
                response = self._request("/program-groups", token)
            self.assertEqual(response.status, "200 OK")
            group = self._json(response)["data"][0]
            self.assertEqual(group["id"], "default")
            self.assertEqual(group["next_runs"][0]["program_id"], "program-0")
            self.assertEqual(group["next_runs"][0]["duration_minutes"], 10)
        finally:
            api.options.program_groups = groups_before

    def test_program_group_postponement_endpoints_use_control_scope(self):
        import datetime

        token, unused_refresh = self._token(
            ("read", "control"), role="user"
        )
        item = {
            "id": "postponement-1",
            "group_id": "default",
            "created": datetime.datetime(2026, 8, 13, 10, 0),
            "source_start": datetime.datetime(2026, 8, 14, 6, 0),
            "source_end": datetime.datetime(2026, 8, 14, 6, 10),
            "target_start": datetime.datetime(2026, 8, 14, 8, 0),
            "target_end": datetime.datetime(2026, 8, 14, 8, 10),
            "shift_seconds": 7200,
            "runs": [{"program": 0, "station": 0}],
        }
        with mock.patch(
                "api.v1.api.programs.create_group_postponement",
                return_value=item) as create, mock.patch(
                "api.v1.api.event_stream.publish"), mock.patch(
                "api.v1.api.logEV.save_events_log"), mock.patch(
                "api.v1.api.threading.Timer"):
            response = self._request(
                "/program-groups/default/postponements", token,
                method="POST", data={"target_start": "2026-08-14T08:00:00"},
            )
        self.assertEqual(response.status, "201 Created")
        self.assertEqual(
            self._json(response)["data"]["id"], "postponement-1"
        )
        create.assert_called_once_with(
            "default", datetime.datetime(2026, 8, 14, 8, 0)
        )

        with mock.patch(
                "api.v1.api.programs.cancel_group_postponement",
                return_value=item), mock.patch(
                "api.v1.api.event_stream.publish"), mock.patch(
                "api.v1.api.logEV.save_events_log"), mock.patch(
                "api.v1.api.threading.Timer"):
            response = self._request(
                "/program-groups/default/postponements/postponement-1",
                token, method="DELETE",
            )
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(
            self._json(response)["data"]["cancelled"], "postponement-1"
        )

    def test_program_definitions_preserve_every_supported_type(self):
        from api.v1 import api
        from ospy.programs import programs, ProgramType

        definitions = {
            ProgramType.DAYS_SIMPLE: [360, 10, 0, 0, [0, 2]],
            ProgramType.DAYS_ADVANCED: [[[60, 70]], [1, 3]],
            ProgramType.REPEAT_SIMPLE: [360, 10, 0, 0, 2, "2026-08-08"],
            ProgramType.REPEAT_ADVANCED: [[[60, 70]], 2, "2026-08-08"],
            ProgramType.WEEKLY_ADVANCED: [[[60, 70]]],
            ProgramType.CUSTOM: [[[60, 70]]],
            ProgramType.WEEKLY_WEATHER: [5, 10, 5, 0.5, [[360, 1]]],
        }
        for program_type, type_data in definitions.items():
            program = programs.create_program()
            definition = {
                "name": "Type {}".format(program_type),
                "enabled": False,
                "stations": [],
                "type": program_type,
                "type_data": type_data,
                "modulo": 1440,
                "manual": False,
                "start": "2026-08-08T00:00:00",
                "schedule": [[60, 70]],
            }
            api._apply_program_definition(program, definition)
            self.assertEqual(program.type, program_type)
            editor = api._program_editor(program)
            self.assertTrue(editor["valid"])
            self.assertNotEqual(editor["kind"], "unsupported")
            if program_type == ProgramType.WEEKLY_WEATHER:
                self.assertEqual(program.type_data[3], 0.5)
                self.assertEqual(editor["fields"]["pause_ratio"], 0.5)

    def test_refresh_token_rotation_allows_one_crash_recovery_retry(self):
        from api.v1.security import refresh
        token, original = self._token(("read",), role="user")
        replacement = refresh(original["token"])
        self.assertNotEqual(replacement["refresh_token"], original["token"])
        recovered = refresh(original["token"])
        self.assertNotEqual(recovered["refresh_token"], original["token"])
        self.assertNotEqual(
            recovered["refresh_token"], replacement["refresh_token"]
        )
        with self.assertRaises(Exception) as context:
            refresh(original["token"])
        self.assertEqual(getattr(context.exception, "code", ""), "invalid_refresh_token")

    def test_access_token_remains_valid_after_normal_refresh_rotation(self):
        from api.v1.security import refresh, verify_access_token

        access, original = self._token(("read",), role="user")
        refresh(original["token"])
        identity = verify_access_token(access)
        self.assertEqual(identity["device_id"], original["device_id"])

    def test_logout_still_invalidates_access_token(self):
        from api.v1.security import verify_access_token
        from api.v1.store import mobile_store

        access, original = self._token(("read",), role="user")
        mobile_store.revoke_refresh_token(original["id"])
        with self.assertRaises(Exception) as context:
            verify_access_token(access)
        self.assertEqual(getattr(context.exception, "code", ""), "invalid_token")

    def test_logout_invalidates_access_token_even_after_refresh_rotation(self):
        from api.v1.security import verify_access_token
        from api.v1.store import mobile_store

        access, original = self._token(("read",), role="user")
        replacement = mobile_store.rotate_refresh_token(original["token"])
        mobile_store.revoke_refresh_token(replacement["id"])
        with self.assertRaises(Exception) as context:
            verify_access_token(access)
        self.assertEqual(getattr(context.exception, "code", ""), "invalid_token")

    def test_refresh_token_recovery_retry_expires_with_grace_window(self):
        from api.v1.store import (
            DEFAULT_REFRESH_LIFETIME, REFRESH_RECOVERY_GRACE, mobile_store,
        )
        original = mobile_store.issue_refresh_token(
            "mobile-test", "user", ("read",), "grace-device", "Phone"
        )
        issued = original["expires"] - DEFAULT_REFRESH_LIFETIME
        with mock.patch("api.v1.store.time.time", return_value=issued + 1):
            self.assertIsNotNone(
                mobile_store.rotate_refresh_token(original["token"])
            )
        with mock.patch(
                "api.v1.store.time.time",
                return_value=issued + REFRESH_RECOVERY_GRACE + 2):
            self.assertIsNone(
                mobile_store.rotate_refresh_token(original["token"])
            )

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
        self.assertEqual(first["device_id"], second["device_id"])
        matching_devices = [
            item for item in mobile_store.devices()
            if item["id"] == "same-device"
        ]
        self.assertEqual(len(matching_devices), 1)
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

    def test_plugin_mobile_forwards_valid_history_range(self):
        token, unused_refresh = self._token(("read",), role="user")
        with mock.patch(
                "api.v1.api.plugins.plugin_mobile_capabilities",
                return_value={}), mock.patch(
                "api.v1.api.plugins.plugin_mobile_call",
                return_value=[]) as mobile_call:
            response = self._request(
                "/plugins/example/mobile?from=2026-08-05T00%3A00%3A00"
                "&to=2026-08-06T00%3A00%3A00&max_points=321",
                token,
            )
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(mobile_call.call_count, 4)
        mobile_call.assert_any_call(
            "example", "cards",
            from_time="2026-08-05T00:00:00",
            to_time="2026-08-06T00:00:00",
            max_points=321,
        )

    def test_plugin_mobile_rejects_invalid_history_range(self):
        token, unused_refresh = self._token(("read",), role="user")
        response = self._request(
            "/plugins/example/mobile?from=invalid&max_points=400", token
        )
        self.assertEqual(response.status, "422 Unprocessable Entity")
        self.assertEqual(
            self._json(response)["error"]["code"], "invalid_history_range"
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

    def test_optional_mobile_arguments_are_filtered_for_legacy_method(self):
        import plugins

        class LegacyPlugin(object):
            @staticmethod
            def mobile_cards():
                return [{"id": "legacy"}]

        with mock.patch.object(plugins, "running", return_value=["legacy"]), \
                mock.patch.object(plugins, "get", return_value=LegacyPlugin()):
            result = plugins.plugin_mobile_call(
                "legacy", "cards", from_time="2026-08-05T00:00:00",
                to_time="2026-08-06T00:00:00", max_points=400,
            )
        self.assertEqual(result, [{"id": "legacy"}])



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
                "operation_id",
                "station_details",
                "Scheduler timeline",
                "mobile_cards()"):
            self.assertIn(required_term, text)
        self.assertIn('PUT /plugins/{id}', text)
