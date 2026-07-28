import datetime
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.parse import parse_qs, urlparse

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import weather as weather_module


class WeatherProviderTests(unittest.TestCase):
    def instance(self):
        instance = weather_module._Weather.__new__(weather_module._Weather)
        instance._lat = 50.0
        instance._lon = 14.0
        instance._elevation = 0.0
        instance._tz_offset = 0
        instance._result_cache = {}
        instance._forecast_snapshot = []
        instance._forecast_updated = 0
        instance._lock = threading.Lock()
        return instance

    def options(self, provider="open_meteo", **updates):
        values = {
            "location": "Prague",
            "weather_location_mode": "coordinates",
            "weather_lat": "50.0",
            "weather_lon": "14.0",
            "weather_provider": provider,
            "weather_cache": {},
            "stormglass_key": "test-key",
            "temp_unit": "C",
            "time_format": True,
        }
        values.update(updates)
        return SimpleNamespace(**values)

    @staticmethod
    def payload(day, include_probability=False):
        times = ["{}T{:02d}:00".format(day.isoformat(), hour) for hour in range(24)]
        hourly = {
            "time": times,
            "temperature_2m": [10.0 + hour for hour in range(24)],
            "pressure_msl": [1012.0] * 24,
            "cloud_cover": [20.0] * 24,
            "relative_humidity_2m": [60.0] * 24,
            "precipitation": [0.4] * 24,
            "wind_speed_10m": [2.5] * 24,
            "weather_code": [2] * 24,
            "is_day": [1] * 24,
            "et0_fao_evapotranspiration": [0.1] * 24,
        }
        if include_probability:
            hourly["precipitation_probability"] = [35.0] * 24
        return {
            "elevation": 250.0,
            "utc_offset_seconds": 7200,
            "hourly": hourly,
        }

    def test_chmi_provider_uses_verified_aladin_model_and_normalizes_data(self):
        instance = self.instance()
        today = datetime.date.today()
        options = self.options("chmi")
        payload = self.payload(today)

        with mock.patch.object(weather_module, "options", options), \
                mock.patch.object(
                    instance, "_get_open_meteo_json", return_value=payload
                ) as download:
            result = instance.get_hourly_data(today)

        query = parse_qs(urlparse(download.call_args.args[0]).query)
        self.assertEqual(query["models"], ["chmi_aladin_seamless"])
        self.assertEqual(len(result), 24)
        self.assertEqual(result[0]["provider"], "chmi")
        self.assertEqual(result[0]["temperature"], 10.0)
        self.assertEqual(result[0]["humidity"], 0.6)
        self.assertEqual(result[0]["windSpeed"], 2.5)
        self.assertEqual(result[0]["weatherCode"], 2)
        self.assertEqual(result[0]["eto"], 0.1)
        self.assertEqual(instance._elevation, 250.0)

    def test_automatic_provider_requests_precipitation_probability_without_model(self):
        instance = self.instance()
        today = datetime.date.today()
        options = self.options("open_meteo")

        with mock.patch.object(weather_module, "options", options), \
                mock.patch.object(
                    instance,
                    "_get_open_meteo_json",
                    return_value=self.payload(today, include_probability=True),
                ) as download:
            result = instance.get_hourly_data(today)

        query = parse_qs(urlparse(download.call_args.args[0]).query)
        self.assertNotIn("models", query)
        self.assertIn("precipitation_probability", query["hourly"][0])
        self.assertEqual(result[0]["precipitationProbability"], 35.0)

    def test_provider_dispatch_keeps_stormglass_compatibility(self):
        instance = self.instance()
        today = datetime.date.today()
        with mock.patch.object(
                weather_module, "options", self.options("stormglass")), \
                mock.patch.object(
                    instance, "_get_stormglass_data", return_value=[{"provider": "stormglass"}]
                ) as stormglass, mock.patch.object(instance, "_get_open_meteo_data") as open_meteo:
            result = instance.get_hourly_data(today)

        self.assertEqual(result[0]["provider"], "stormglass")
        stormglass.assert_called_once_with(today)
        open_meteo.assert_not_called()

    def test_invalid_provider_fails_safe_to_open_meteo(self):
        with mock.patch.object(
                weather_module, "options", self.options("unsupported")):
            self.assertEqual(weather_module.selected_provider(), "open_meteo")

    def test_home_forecast_returns_now_plus_three_and_six_hours_from_cache(self):
        instance = self.instance()
        now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        instance._forecast_snapshot = [
            {
                "time": int((now + datetime.timedelta(hours=offset)).timestamp()),
                "temperature": 20.0 + offset,
                "precipitation": float(offset) / 10,
                "precipitationProbability": 40.0,
                "weatherCode": code,
                "isDay": offset != 0,
            }
            for offset, code in ((0, 0), (3, 61), (6, 95))
        ]
        instance._forecast_updated = now.timestamp()

        with mock.patch.object(
                weather_module, "options", self.options("open_meteo")):
            forecast = instance.get_home_forecast()

        self.assertEqual(len(forecast["cards"]), 3)
        self.assertEqual(
            [card["icon"] for card in forecast["cards"]],
            ["clear-night", "rain", "storm"],
        )
        self.assertTrue(forecast["provider"])
        self.assertEqual(forecast["provider_url"], "https://open-meteo.com/")
        self.assertIn("40%", forecast["cards"][0]["precipitation"])

    def test_all_wmo_weather_codes_have_specific_icons(self):
        expected = {
            0: "clear",
            1: "mainly-clear",
            2: "partly-cloudy",
            3: "cloudy",
            45: "fog",
            48: "fog",
            51: "drizzle",
            53: "drizzle",
            55: "drizzle",
            56: "freezing-drizzle",
            57: "freezing-drizzle",
            61: "rain",
            63: "rain",
            65: "rain",
            66: "freezing-rain",
            67: "freezing-rain",
            71: "snow",
            73: "snow",
            75: "snow",
            77: "snow-grains",
            80: "showers",
            81: "showers",
            82: "showers",
            85: "snow-showers",
            86: "snow-showers",
            95: "storm",
            96: "storm-hail",
            99: "storm-hail",
        }
        for code, icon in expected.items():
            with self.subTest(code=code):
                self.assertEqual(
                    weather_module._Weather._forecast_icon(code, True), icon
                )
        icon_root = (
            Path(weather_module.__file__).resolve().parents[1] /
            "static" / "images" / "weather"
        )
        expected_icons = set(expected.values()) | {
            "clear-night", "mainly-clear-night", "partly-cloudy-night"
        }
        for icon in expected_icons:
            with self.subTest(asset=icon):
                self.assertTrue((icon_root / (icon + ".svg")).is_file())

    def test_clear_and_cloudy_night_codes_use_night_icons(self):
        self.assertEqual(
            weather_module._Weather._forecast_icon(0, False), "clear-night"
        )
        self.assertEqual(
            weather_module._Weather._forecast_icon(1, False),
            "mainly-clear-night",
        )
        self.assertEqual(
            weather_module._Weather._forecast_icon(2, False),
            "partly-cloudy-night",
        )

    def test_stormglass_daylight_uses_location_instead_of_fixed_hours(self):
        instance = self.instance()
        instance._tz_offset = 2
        midnight = datetime.datetime(2026, 7, 15, 3, 0).timestamp()
        noon = datetime.datetime(2026, 7, 15, 12, 0).timestamp()

        self.assertFalse(instance._is_daylight(midnight))
        self.assertTrue(instance._is_daylight(noon))

    def test_provider_eto_is_used_and_pressure_reads_pressure_field(self):
        instance = self.instance()
        instance.get_hourly_data = mock.Mock(return_value=[
            {"eto": 0.2, "pressure": 1000.0, "windSpeed": 1.0},
            {"eto": 0.3, "pressure": 1020.0, "windSpeed": 9.0},
        ])
        with mock.patch.object(
                weather_module, "options", self.options("open_meteo")):
            self.assertAlmostEqual(instance.get_eto(datetime.date.today()), 0.5)
        self.assertAlmostEqual(
            instance._mean_pressure_kpa([
                {"pressure": 1000.0, "windSpeed": 1.0},
                {"pressure": 1020.0, "windSpeed": 9.0},
            ]),
            101.0,
        )


if __name__ == "__main__":
    unittest.main()
