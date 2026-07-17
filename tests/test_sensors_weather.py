import datetime
import json
from threading import Thread
from types import SimpleNamespace
import unittest
from unittest import mock

import web

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from api import api as api_module
from ospy import helpers
from ospy import sensors as sensors_module
from ospy import weather as weather_module
from ospy import webpages


def undecorated(function):
    while hasattr(function, "__wrapped__"):
        function = function.__wrapped__
    return function


class SensorStateTests(unittest.TestCase):
    def setUp(self):
        web.ctx.clear()
        web.ctx.env = {"REMOTE_ADDR": "192.0.2.50"}
        web.ctx.method = "POST"
        web.ctx.headers = []

    def test_sensor_timeout_marks_device_offline(self):
        sensor = SimpleNamespace(
            enabled=True,
            response=1,
            last_response=100,
            manufacturer=0,
            sens_type=0,
            show_in_footer=False,
            last_read_value=[12.5] + [-127] * 8,
        )
        sensor_collection = SimpleNamespace(get=lambda: [sensor])
        timer = sensors_module._Sensors_Timer.__new__(
            sensors_module._Sensors_Timer
        )

        with mock.patch.object(sensors_module, "sensors", sensor_collection), \
                mock.patch.object(sensors_module, "now", return_value=221):
            timer.check_sensors()

        self.assertEqual(sensor.response, 0)
        self.assertEqual(sensor.last_read_value[0], 12.5)

    def test_valid_sensor_packet_recovers_offline_sensor(self):
        sensor = SimpleNamespace(
            index=0,
            ip_address=("192", "0", "2", "50"),
            mac_address="AA:BB:CC:DD:EE:FF",
            cpu_core=0,
            rssi=0,
            last_battery=0,
            last_read_value=[-127] * 9,
            soil_last_read_value=[-127] * 16,
            last_response=100,
            last_response_datetime="old",
            response=0,
            fw=100,
        )
        sensor_collection = SimpleNamespace(get=lambda: [sensor])
        payload = {
            "name": "Temperature sensor",
            "ip": "192.0.2.50",
            "mac": "AA:BB:CC:DD:EE:FF",
            "stype": 5,
            "scom": 0,
            "fw": 101,
            "cpu": 0,
            "temp": 215,
            "rssi": 80,
            "batt": 123,
        }
        handler = undecorated(api_module.Sensor.POST)

        with mock.patch.object(api_module, "sensors", sensor_collection), \
                mock.patch.object(
                    api_module,
                    "options",
                    SimpleNamespace(
                        api_sensor_auth_required=False,
                        no_password=True,
                        temp_unit="C",
                    ),
                ), mock.patch.object(
                    api_module.web, "input",
                    return_value={"do": json.dumps(payload)},
                ), mock.patch.object(helpers, "now", return_value=500), \
                mock.patch.object(
                    api_module, "datetime_string", return_value="2030-01-01 12:00:00"
                ), mock.patch.object(webpages, "sensorSearch", []):
            handler(api_module.Sensor())

        self.assertEqual(sensor.response, 1)
        self.assertEqual(sensor.last_response, 500)
        self.assertEqual(sensor.last_response_datetime, "2030-01-01 12:00:00")
        self.assertEqual(sensor.last_read_value[0], 21.5)
        self.assertEqual(sensor.fw, 101)

    def test_malformed_sensor_packet_preserves_last_valid_state(self):
        sensor = SimpleNamespace(
            response=1,
            last_response=500,
            last_response_datetime="2030-01-01 12:00:00",
            last_read_value=[21.5] + [-127] * 8,
        )
        sensor_collection = SimpleNamespace(get=lambda: [sensor])
        handler = undecorated(api_module.Sensor.POST)

        with mock.patch.object(api_module, "sensors", sensor_collection), \
                mock.patch.object(
                    api_module,
                    "options",
                    SimpleNamespace(api_sensor_auth_required=False, no_password=True),
                ), mock.patch.object(
                    api_module.web, "input", return_value={"do": "not-json"}
                ), mock.patch.object(api_module.log, "error"), \
                mock.patch.object(webpages, "sensorSearch", []):
            handler(api_module.Sensor())

        self.assertEqual(sensor.response, 1)
        self.assertEqual(sensor.last_response, 500)
        self.assertEqual(sensor.last_read_value[0], 21.5)

    def test_incomplete_sensor_packet_is_ignored(self):
        sensor = SimpleNamespace(
            response=1,
            last_response=500,
            last_read_value=[21.5] + [-127] * 8,
        )
        sensor_collection = SimpleNamespace(get=lambda: [sensor])
        handler = undecorated(api_module.Sensor.POST)

        with mock.patch.object(api_module, "sensors", sensor_collection), \
                mock.patch.object(
                    api_module,
                    "options",
                    SimpleNamespace(api_sensor_auth_required=False, no_password=True),
                ), mock.patch.object(
                    api_module.web, "input",
                    return_value={"do": json.dumps({"mac": "AA:BB"})},
                ), mock.patch.object(webpages, "sensorSearch", []):
            handler(api_module.Sensor())

        self.assertEqual(sensor.response, 1)
        self.assertEqual(sensor.last_response, 500)
        self.assertEqual(sensor.last_read_value[0], 21.5)

    def test_legacy_regulation_output_is_normalized_to_integer(self):
        collection = SimpleNamespace(get=lambda: [])
        options_type = type(sensors_module.options)
        with mock.patch.object(options_type, "load"), \
                mock.patch.object(options_type, "save"):
            sensor = sensors_module._Sensor(collection, 0)
            sensor.reg_output = "2"

        self.assertEqual(sensor.reg_output, 2)
        self.assertIsInstance(sensor.reg_output, int)
        self.assertEqual(sensors_module._normalize_reg_output("invalid", 8), 0)
        self.assertEqual(sensors_module._normalize_reg_output("99", 8), 0)

    def test_numeric_legacy_regulation_output_is_accepted_for_migration(self):
        compatible = sensors_module.options._compatible_value

        self.assertTrue(compatible(0, "2", "reg_output"))
        self.assertTrue(compatible(0, 2, "reg_output"))
        self.assertFalse(compatible(0, "invalid", "reg_output"))


class Response(object):
    def __init__(self, value):
        self.value = value

    def read(self):
        return json.dumps(self.value).encode("utf-8")

    def info(self):
        return self

    def get_content_charset(self, default):
        return default


class WeatherRecoveryTests(unittest.TestCase):
    def weather(self):
        instance = weather_module._Weather.__new__(weather_module._Weather)
        instance._lat = 50.0
        instance._lon = 14.0
        instance._elevation = 0.0
        instance._determine_location = True
        instance._callbacks = []
        instance._result_cache = {}
        return instance

    def options(self, **updates):
        values = {
            "location": "Prague",
            "weather_location_mode": "search",
            "weather_lat": "50.0",
            "weather_lon": "14.0",
            "weather_status": 1,
            "weather_cache": {},
            "stormglass_key": "test-key",
            "use_weather": True,
            "name": "Test OSPy",
        }
        values.update(updates)
        return SimpleNamespace(**values)

    def test_location_timeout_keeps_last_valid_coordinates(self):
        instance = self.weather()
        options = self.options()

        with mock.patch.object(weather_module, "options", options), \
                mock.patch.object(
                    weather_module, "urlopen", side_effect=TimeoutError("timeout")
                ) as urlopen:
            with self.assertRaises(TimeoutError):
                instance._find_location()

        self.assertEqual((instance._lat, instance._lon), (50.0, 14.0))
        self.assertEqual(options.weather_status, 2)
        self.assertEqual(
            urlopen.call_args.kwargs["timeout"],
            weather_module.WEATHER_HTTP_TIMEOUT,
        )

    def test_location_updates_only_after_valid_response(self):
        instance = self.weather()
        options = self.options()
        response = Response([{"lat": "49.8175", "lon": "15.4730"}])

        with mock.patch.object(weather_module, "options", options), \
                mock.patch.object(weather_module, "urlopen", return_value=response):
            instance._find_location()

        self.assertEqual((instance._lat, instance._lon), (49.8175, 15.473))
        self.assertEqual(options.weather_status, 1)

    def test_stormglass_rejects_error_payload_and_uses_timeout(self):
        options = self.options()
        with mock.patch.object(weather_module, "options", options), \
                mock.patch.object(
                    weather_module, "urlopen",
                    return_value=Response({"errors": {"key": "invalid"}}),
                ) as urlopen:
            with self.assertRaises(ValueError):
                weather_module._Weather._get_stormglass_json("https://example.test")

        self.assertEqual(
            urlopen.call_args.kwargs["timeout"],
            weather_module.WEATHER_HTTP_TIMEOUT,
        )

    def test_weather_cache_keeps_last_value_after_refresh_failure(self):
        options = self.options()

        class CachedWeather(object):
            def __init__(self):
                self._result_cache = {}
                self.fail = False

            @weather_module._cache("sample")
            def read(self, check_date):
                if self.fail:
                    raise TimeoutError("timeout")
                return {"temperature": 21.5}

        instance = CachedWeather()
        today = datetime.date.today()
        with mock.patch.object(weather_module, "options", options):
            first = instance.read(today)
            instance.fail = True
            second = instance.read(today)

        self.assertEqual(first, {"temperature": 21.5})
        self.assertEqual(second, first)

    def test_weather_thread_retries_location_after_failure(self):
        class StopLoop(BaseException):
            pass

        instance = self.weather()
        Thread.__init__(instance)
        instance._stop_event = mock.Mock()
        instance._stop_event.is_set.return_value = False
        instance._stop_event.wait.return_value = False
        options = self.options()
        instance._sleep = mock.Mock(side_effect=[None, StopLoop()])

        with mock.patch.object(weather_module, "options", options), \
                mock.patch.object(weather_module.time, "sleep"), \
                mock.patch.object(
                    instance,
                    "_find_location",
                    side_effect=[TimeoutError("timeout"), None],
                ) as find_location, mock.patch.object(weather_module, "heartbeat"), \
                mock.patch.object(weather_module, "update_details"), \
                mock.patch.object(weather_module.logging, "warning"):
            with self.assertRaises(StopLoop):
                instance.run()

        self.assertEqual(find_location.call_count, 2)
        self.assertFalse(instance._determine_location)


if __name__ == "__main__":
    unittest.main()
