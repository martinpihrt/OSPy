#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Rimco'

# System imports
import logging
import traceback
from ospy.helpers import avg

from urllib.request import urlopen, Request
from urllib.parse import quote_plus, urlencode
from urllib.error import HTTPError, URLError

import json
import datetime
import time
import math
import os
from threading import Event, Thread, Lock, current_thread

from ospy.options import options
from ospy.health import heartbeat, update_details

from . import i18n


WEATHER_HTTP_TIMEOUT = 15
WEATHER_PROVIDERS = ('open_meteo', 'chmi', 'stormglass')
OPEN_METEO_URL = 'https://api.open-meteo.com/v1/forecast'
OPEN_METEO_HOURLY = (
    'temperature_2m', 'pressure_msl', 'cloud_cover',
    'relative_humidity_2m', 'precipitation', 'wind_speed_10m',
    'weather_code', 'is_day', 'et0_fao_evapotranspiration'
)


def selected_provider():
    """Return only a supported persisted provider identifier."""
    provider = getattr(options, 'weather_provider', 'open_meteo')
    return provider if provider in WEATHER_PROVIDERS else 'open_meteo'


def provider_name(provider=None):
    provider = provider or selected_provider()
    return {
        'open_meteo': _('Open-Meteo automatic model'),
        'chmi': _('CHMI ALADIN via Open-Meteo'),
        'stormglass': _('Stormglass'),
    }.get(provider, _('Open-Meteo automatic model'))


def provider_url(provider=None):
    return (
        'https://stormglass.io/'
        if (provider or selected_provider()) == 'stormglass'
        else 'https://open-meteo.com/'
    )


def _cache(cache_name):
    def cache_decorator(func):
        def func_wrapper(self, check_date):
            if isinstance(check_date, datetime.datetime):
                check_date = check_date.date()

            location_key = (
                options.location,
                options.weather_location_mode,
                options.weather_lat,
                options.weather_lon,
                selected_provider(),
            )
            if 'location' not in self._result_cache or location_key != self._result_cache['location']:
                self._result_cache.clear()
                self._result_cache['location'] = location_key

            if cache_name not in self._result_cache:
                self._result_cache[cache_name] = {}

            for key in list(self._result_cache[cache_name].keys()):
                if (datetime.date.today() - key).days > 30:
                    del self._result_cache[cache_name][key]

            if check_date not in self._result_cache[cache_name] or (datetime.date.today() - check_date).days <= 1:
                try:
                    self._result_cache[cache_name][check_date] = func(self, check_date)
                    options.weather_cache = self._result_cache
                except Exception:
                    if check_date not in self._result_cache[cache_name]:
                        raise

            return self._result_cache[cache_name][check_date]
        return func_wrapper
    return cache_decorator


class _Weather(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self._lock = Lock()
        self._callbacks = []

        self._requests = []
        self._lat = None
        self._lon = None
        self._elevation = 0.0
        self._tz_offset = 0
        self._determine_location = True
        self._result_cache = options.weather_cache
        self._forecast_snapshot = []
        self._forecast_updated = 0

        options.add_callback('location', self._option_cb)
        options.add_callback('weather_location_mode', self._option_cb)
        options.add_callback('weather_provider', self._option_cb)
        options.add_callback('stormglass_key', self._option_cb)
        options.add_callback('use_weather', self._option_cb)
        options.add_callback('weather_lat', self._option_cb)            # from home page weather status (latitude)
        options.add_callback('weather_lon', self._option_cb)            # from home page weather status (longtitude)

        self._sleep_time = 0
        self._stop_event = Event()
        if os.environ.get('OSPY_DISABLE_BACKGROUND_THREADS') != '1':
            self.start()

    def _option_cb(self, key, old, new):
        self._determine_location = True
        if key in ('weather_provider', 'stormglass_key'):
            with self._lock:
                self._result_cache.clear()
                self._forecast_snapshot = []
                self._forecast_updated = 0
                options.weather_cache = self._result_cache
        self.update()

    def add_callback(self, function):
        if function not in self._callbacks:
            self._callbacks.append(function)

    def remove_callback(self, function):
        if function in self._callbacks:
            self._callbacks.remove(function)

    def update(self):
        self._sleep_time = 0

    def request_stop(self):
        """Ask the weather worker to finish promptly."""
        self._stop_event.set()
        self.update()

    def wait_stopped(self, timeout=5.0):
        if self.is_alive() and self is not current_thread():
            self.join(max(0.0, float(timeout)))
        return not self.is_alive()

    def _sleep(self, secs):
        if not hasattr(self, '_stop_event'):
            self._stop_event = Event()
        self._sleep_time = secs
        while self._sleep_time > 0 and not self._stop_event.is_set():
            wait_time = min(1, self._sleep_time)
            if self._stop_event.wait(wait_time):
                break
            self._sleep_time -= wait_time
        return not self._stop_event.is_set()

    def run(self):
        if not hasattr(self, '_stop_event'):
            self._stop_event = Event()
        update_details('weather', thread_name=self.name or self.__class__.__name__)
        if self._stop_event.wait(5):  # Some delay to allow internet to initialize
            return
        while not self._stop_event.is_set():
            try:
                if self._determine_location:
                    self._find_location()
                    self._determine_location = False
                for function in self._callbacks:
                    function()
                if options.use_weather:
                    self._refresh_home_forecast()

                heartbeat(
                    'weather',
                    enabled=options.use_weather,
                    status=options.weather_status,
                    provider=selected_provider(),
                    latitude=self._lat,
                    longitude=self._lon
                )
                self._sleep(3600)
            except Exception:
                error = traceback.format_exc()
                heartbeat('weather', ok=False, message=error,
                          enabled=options.use_weather,
                          provider=selected_provider(),
                          status=options.weather_status)
                logging.warning(_('Weather error:') + ' ' + error)
                self._sleep(6*3600)

    def _find_location(self):
        if options.weather_location_mode == 'coordinates':
            try:
                latitude = float(options.weather_lat)
                longitude = float(options.weather_lon)
                if not -90.0 <= latitude <= 90.0 or not -180.0 <= longitude <= 180.0:
                    raise ValueError('Coordinates outside valid range')
                self._lat = latitude
                self._lon = longitude
                options.weather_status = 1
                if (selected_provider() == 'stormglass' and
                        options.stormglass_key and options.use_weather):
                    url = "https://api.stormglass.io/v2/elevation/point?lat=%s&lng=%s" % self.get_lat_lon()
                    try:
                        self._elevation = self._get_stormglass_json(url)['data']['elevation']
                    except Exception:
                        logging.debug(_('Elevation not downloaded from stormglass.'))
                        self._elevation = 0.0
                return
            except (TypeError, ValueError):
                options.weather_status = 2
                raise Exception(_('No location coordinates available!'))

        if options.location:
            options.weather_status = 2
            request = Request(
                "https://nominatim.openstreetmap.org/search?q=%s&format=json" % quote_plus(options.location),
                headers={'User-Agent': 'OSPy/{} contact: pihrt.com'.format(options.name)}
            )
            data = urlopen(request, timeout=WEATHER_HTTP_TIMEOUT)
            data = json.loads(data.read().decode(data.info().get_content_charset('utf-8')))
            if not data:
                self._lat = None
                self._lon = None
                options.weather_status = 0 # Weather - No location found!
                raise Exception(_('No location found:') + ' ' + options.location)
            else:
                self._lat = float(data[0]['lat'])
                self._lon = float(data[0]['lon'])
                options.weather_lat = str(float(data[0]['lat']))
                options.weather_lon = str(float(data[0]['lon']))
                options.weather_status = 1 # found
                if (selected_provider() == 'stormglass' and
                        options.stormglass_key and options.use_weather):
                    url = "https://api.stormglass.io/v2/elevation/point?lat=%s&lng=%s" % self.get_lat_lon()
                    try:
                        self._elevation = self._get_stormglass_json(url)['data']['elevation']
                        logging.debug(_('Location found: %s, %s at %.1fm above sea level'), self._lat, self._lon, self._elevation)
                    except:
                        logging.debug(_('Elevation not downloaded from stormglass.'))
                        self._elevation = 0.0
                else:
                    logging.debug(_('Location found: %s, %s; elevation will be supplied by the selected weather provider.'), self._lat, self._lon)
        else:
            self._lat = None
            self._lon = None
            options.weather_status = 0

    def get_lat_lon(self):
        if self._lat is None or self._lon is None:
            self._determine_location = True  # Let the weather thread try again when it wakes up
            options.weather_status = 2 # Weather - No location coordinates available!
            raise Exception(_('No location coordinates available!'))
        return self._lat, self._lon

    @staticmethod
    def _sg_time_to_timestamp(sg_time):
        return int(datetime.datetime.strptime(sg_time[:22] + sg_time[23:], '%Y-%m-%dT%H:%M:%S%z').timestamp())

    @staticmethod
    def _get_stormglass_json(url):
        logging.debug(url)
        request = Request(url)
        request.add_header('Authorization', options.stormglass_key)
        try:
            data = urlopen(request, timeout=WEATHER_HTTP_TIMEOUT)
            result = json.loads(data.read().decode(data.info().get_content_charset('utf-8')))
            if not isinstance(result, dict) or not result or result.get('errors'):
                raise ValueError('Invalid Stormglass response')
            return result
        except HTTPError as e:
            if e.code == 402:
                logging.warning(_('For the free API, it has a limit of 7 calls per day.'))
            else:
                logging.warning(_('HTTPError: {} - {}').format(e.code, e.reason)) 
            raise

    @_cache('stormglass_data')
    def _get_stormglass_data(self, check_date):
        if not options.stormglass_key:
            raise ValueError(_('Stormglass requires an API key.'))
        # Use 7 day intervals to limit API calls:
        start_dt = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)
        while start_dt > datetime.datetime.combine(check_date, datetime.time()):
            start_dt -= datetime.timedelta(days=7)
        start_timestamp = start_dt.timestamp()

        url = "https://api.stormglass.io/v2/weather/point?lat=%s&lng=%s&params=airTemperature,pressure,cloudCover,humidity,precipitation,windSpeed&start=%d" % (self.get_lat_lon() + (start_timestamp,))

        # Rate limit API calls to max 1 per 4 hours. This should work to get to max 10 API calls per day.
        if 'stormglass_json' not in self._result_cache:
            self._result_cache['stormglass_json'] = {}

        for key in list(self._result_cache['stormglass_json'].keys()):
            if datetime.datetime.now() - self._result_cache['stormglass_json'][key]['time'] > datetime.timedelta(hours=4):
                del self._result_cache['stormglass_json'][key]

        if url not in self._result_cache['stormglass_json']:
            self._result_cache['stormglass_json'][url] = {'time': datetime.datetime.now(),
                                                          'data': self._get_stormglass_json(url)}
            options.weather_cache = self._result_cache
        
        self._tz_offset = int(time.localtime().tm_gmtoff / 3600)
        result = []

        if 'hours' in self._result_cache['stormglass_json'][url]['data']:
            for hr_data in self._result_cache['stormglass_json'][url]['data']['hours']:
                hr_timestamp = self._sg_time_to_timestamp(hr_data['time'])
                if datetime.date.fromtimestamp(hr_timestamp) == check_date:
                    precipitation = hr_data['precipitation']['sg']
                    cloud_cover = hr_data['cloudCover']['sg'] / 100.0
                    if precipitation > 2.5:
                        weather_code = 63
                    elif precipitation > 0.1:
                        weather_code = 61
                    elif cloud_cover <= 0.15:
                        weather_code = 0
                    elif cloud_cover <= 0.5:
                        weather_code = 2
                    else:
                        weather_code = 3
                    local_hour = datetime.datetime.fromtimestamp(hr_timestamp).hour
                    result.append({
                        'time': hr_timestamp,
                        'temperature': hr_data['airTemperature']['sg'],                     # [C]
                        'pressure': hr_data['pressure']['sg'],                              # [hPa]
                        'cloudCover': cloud_cover,                                          # [0.0 - 1.0]
                        'humidity': hr_data['humidity']['sg'] / 100.0,                      # [0.0 - 1.0]
                        'precipitation': precipitation,                                     # [mm/h]
                        'windSpeed': hr_data['windSpeed']['sg'],                            # [m/s]
                        'weatherCode': weather_code,
                        'isDay': 6 <= local_hour < 20,
                        'precipitationProbability': None,
                        'provider': 'stormglass',
                    })

        return result

    @staticmethod
    def _get_open_meteo_json(url):
        logging.debug(url)
        request = Request(url, headers={'User-Agent': 'OSPy weather'})
        data = urlopen(request, timeout=WEATHER_HTTP_TIMEOUT)
        result = json.loads(data.read().decode(data.info().get_content_charset('utf-8')))
        if (not isinstance(result, dict) or result.get('error') or
                not isinstance(result.get('hourly'), dict)):
            raise ValueError(_('Invalid Open-Meteo response.'))
        return result

    @_cache('open_meteo_data')
    def _get_open_meteo_data(self, check_date):
        provider = selected_provider()
        params = {
            'latitude': self.get_lat_lon()[0],
            'longitude': self.get_lat_lon()[1],
            'hourly': ','.join(
                OPEN_METEO_HOURLY + (
                    ('precipitation_probability',)
                    if provider == 'open_meteo' else ()
                )
            ),
            'wind_speed_unit': 'ms',
            'timezone': 'auto',
            'start_date': check_date.isoformat(),
            'end_date': check_date.isoformat(),
        }
        if provider == 'chmi':
            params['models'] = 'chmi_aladin_seamless'
        url = OPEN_METEO_URL + '?' + urlencode(params)

        if 'open_meteo_json' not in self._result_cache:
            self._result_cache['open_meteo_json'] = {}
        raw_cache = self._result_cache['open_meteo_json']
        for cached_url in list(raw_cache.keys()):
            if datetime.datetime.now() - raw_cache[cached_url]['time'] > datetime.timedelta(hours=4):
                del raw_cache[cached_url]
        if url not in raw_cache:
            raw_cache[url] = {
                'time': datetime.datetime.now(),
                'data': self._get_open_meteo_json(url),
            }
            options.weather_cache = self._result_cache

        response = raw_cache[url]['data']
        hourly = response['hourly']
        times = hourly.get('time', [])
        required = ('temperature_2m', 'pressure_msl', 'cloud_cover',
                    'relative_humidity_2m', 'precipitation', 'wind_speed_10m')
        if not isinstance(times, list) or any(
                not isinstance(hourly.get(field), list) or
                len(hourly[field]) != len(times)
                for field in required):
            raise ValueError(_('Invalid Open-Meteo hourly data.'))

        try:
            self._elevation = float(response.get('elevation', 0.0) or 0.0)
        except (TypeError, ValueError):
            self._elevation = 0.0
        try:
            timezone_offset_seconds = int(response.get('utc_offset_seconds', 0) or 0)
            self._tz_offset = timezone_offset_seconds / 3600.0
        except (TypeError, ValueError):
            timezone_offset_seconds = 0
            self._tz_offset = 0

        result = []
        for index, time_text in enumerate(times):
            try:
                local_timezone = datetime.timezone(
                    datetime.timedelta(seconds=timezone_offset_seconds)
                )
                timestamp = int(
                    datetime.datetime.fromisoformat(time_text)
                    .replace(tzinfo=local_timezone)
                    .timestamp()
                )
                temperature = float(hourly['temperature_2m'][index])
                pressure = float(hourly['pressure_msl'][index])
                cloud_cover = float(hourly['cloud_cover'][index]) / 100.0
                humidity = float(hourly['relative_humidity_2m'][index]) / 100.0
                precipitation = float(hourly['precipitation'][index])
                wind_speed = float(hourly['wind_speed_10m'][index])
            except (TypeError, ValueError, IndexError):
                continue

            def optional_value(field, default=None, convert=float):
                values = hourly.get(field, [])
                try:
                    value = values[index]
                    return default if value is None else convert(value)
                except (TypeError, ValueError, IndexError):
                    return default

            result.append({
                'time': timestamp,
                'temperature': temperature,
                'pressure': pressure,
                'cloudCover': max(0.0, min(1.0, cloud_cover)),
                'humidity': max(0.0, min(1.0, humidity)),
                'precipitation': max(0.0, precipitation),
                'windSpeed': max(0.0, wind_speed),
                'weatherCode': optional_value('weather_code', 3, int),
                'isDay': bool(optional_value('is_day', 1, int)),
                'precipitationProbability': optional_value('precipitation_probability'),
                'eto': optional_value('et0_fao_evapotranspiration'),
                'provider': provider,
            })
        if not result:
            raise ValueError(_('Open-Meteo returned no usable hourly data.'))
        return result

    def get_hourly_data(self, check_date):
        if selected_provider() == 'stormglass':
            return self._get_stormglass_data(check_date)
        return self._get_open_meteo_data(check_date)

    def get_current_data(self):
        current_timestamp = int(datetime.datetime.now().replace(minute=0, second=0, microsecond=0).timestamp())
        result = [x for x in self.get_hourly_data(datetime.date.today()) if x['time'] == current_timestamp]
        return result[0] if result else {}

    def _refresh_home_forecast(self):
        today = datetime.date.today()
        fresh = []
        for forecast_date in (today, today + datetime.timedelta(days=1)):
            fresh.extend(self.get_hourly_data(forecast_date) or [])
        if fresh:
            with self._lock:
                self._forecast_snapshot = sorted(fresh, key=lambda item: item['time'])
                self._forecast_updated = time.time()

    @staticmethod
    def _forecast_icon(code):
        if code == 0:
            return 'clear'
        if code in (1, 2):
            return 'partly-cloudy'
        if code == 3:
            return 'cloudy'
        if code in (45, 48):
            return 'fog'
        if code in (71, 73, 75, 77, 85, 86):
            return 'snow'
        if code >= 95:
            return 'storm'
        if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
            return 'rain'
        return 'cloudy'

    @staticmethod
    def _forecast_description(icon):
        return {
            'clear': _('Clear sky'),
            'partly-cloudy': _('Partly cloudy'),
            'cloudy': _('Cloudy'),
            'fog': _('Fog'),
            'rain': _('Rain'),
            'snow': _('Snow'),
            'storm': _('Thunderstorm'),
        }.get(icon, _('Cloudy'))

    def get_home_forecast(self):
        """Return three non-blocking cached forecast cards for Home."""
        with self._lock:
            snapshot = [dict(item) for item in self._forecast_snapshot]
            updated = self._forecast_updated
        if not snapshot:
            return {
                'cards': [],
                'provider': provider_name(),
                'provider_url': provider_url(),
                'updated': '',
            }

        now_dt = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        cards = []
        used_times = set()
        for hour_offset in (0, 3, 6):
            target = int((now_dt + datetime.timedelta(hours=hour_offset)).timestamp())
            candidates = [item for item in snapshot if item['time'] >= target]
            if not candidates:
                continue
            item = min(candidates, key=lambda value: value['time'] - target)
            if item['time'] in used_times:
                continue
            used_times.add(item['time'])
            weather_code = item.get('weatherCode', 3)
            icon = self._forecast_icon(int(3 if weather_code is None else weather_code))
            temperature = item['temperature']
            unit = getattr(options, 'temp_unit', 'C')
            if unit == 'F':
                temperature = 32.0 + 9.0 / 5.0 * temperature
            precipitation = '{:.1f} mm'.format(item.get('precipitation', 0.0))
            probability = item.get('precipitationProbability')
            if probability is not None:
                precipitation += ' · {:.0f}%'.format(probability)
            value_time = datetime.datetime.fromtimestamp(item['time'])
            cards.append({
                'time': value_time.strftime('%H:%M' if options.time_format else '%I:%M %p').lstrip('0'),
                'temperature': '{:.1f} °{}'.format(temperature, unit),
                'precipitation': precipitation,
                'icon': icon,
                'description': self._forecast_description(icon),
            })
        return {
            'cards': cards,
            'provider': provider_name(),
            'provider_url': provider_url(),
            'updated': (
                datetime.datetime.fromtimestamp(updated).strftime('%Y-%m-%d %H:%M')
                if updated else ''
            ),
        }

    def _calc_radiation(self, coverage, fractional_day, local_hour):
        gmt_hour = local_hour - self._tz_offset
        f = math.radians(fractional_day)
        declination = 0.396372 - 22.91327 * math.cos(f) + 4.02543  * math.sin(f) - 0.387205 * math.cos(2*f) + 0.051967 * math.sin(2*f) - 0.154527 * math.cos(3*f) + 0.084798 * math.sin(3*f)
        time_correction = 0.004297 + 0.107029 * math.cos(f) - 1.837877 * math.sin(f) - 0.837378 * math.cos(2*f) - 2.340475 * math.sin(2*f)
        solar_hour = (gmt_hour + 0.5 - 12)*15 + self._lon + time_correction

        if solar_hour < -180: solar_hour += 360
        if solar_hour > 180: solar_hour -= 360

        solar_factor = math.sin(math.radians(self._lat))*math.sin(math.radians(declination))+math.cos(math.radians(self._lat))*math.cos(math.radians(declination))*math.cos(math.radians(solar_hour))
        sun_elevation = math.degrees(math.asin(solar_factor))

        clear_sky_isolation = max(0, 990 * math.sin(math.radians(sun_elevation)) - 30)
        solar_radiation = clear_sky_isolation * (1 - 0.75 * math.pow(coverage, 3.4))

        return solar_radiation, clear_sky_isolation

    # Returns a calculation of saturation vapour pressure based on temperature in degrees
    @staticmethod
    def saturation_vapour_pressure(t):
        return 0.6108 * math.exp((17.27 * t) / (t + 237.3))

    @staticmethod
    def _mean_pressure_kpa(hourly_data):
        return avg([item['pressure'] for item in hourly_data]) / 10.0

    @_cache('eto')
    def get_eto(self, check_date):
        hourly_data = self.get_hourly_data(check_date)

        provider_eto = [item.get('eto') for item in hourly_data]
        if provider_eto and all(value is not None for value in provider_eto):
            return sum(provider_eto)

        temp_avg = avg([x['temperature'] for x in hourly_data])             # [C]
        temp_min = min([x['temperature'] for x in hourly_data])             # [C]
        temp_max = max([x['temperature'] for x in hourly_data])             # [C]
        wind_speed = avg([x['windSpeed'] for x in hourly_data]) * 0.748     # [m/s] at 2m height
        humid_min = min([x['humidity'] for x in hourly_data]) * 100         # [0 - 100]
        humid_max = max([x['humidity'] for x in hourly_data]) * 100         # [0 - 100]
        pressure = self._mean_pressure_kpa(hourly_data)                      # [kPa]

        total_solar_radiation = 0
        total_clear_sky_isolation = 0

        for data in hourly_data:
            hour_datetime = datetime.datetime.fromtimestamp(data['time'])
            year_datetime = datetime.datetime(hour_datetime.year, 1, 1)
            fractional_day = (360/365.25)*(hour_datetime - year_datetime).total_seconds() / 3600 / 24
            if 'cloudCover' in data:
                solar_radiation, clear_sky_isolation = self._calc_radiation(data['cloudCover'], fractional_day, hour_datetime.hour)
                # Accumulate clear sky radiation and solar radiation on the ground
                total_solar_radiation += solar_radiation
                total_clear_sky_isolation += clear_sky_isolation

        # Solar Radiation
        r_s = total_solar_radiation * 3600 / 1000 / 1000 # MJ / m^2 / d
        # Net shortwave radiation
        r_ns = 0.77 * r_s

        # Extraterrestrial Radiation
        r_a = total_clear_sky_isolation * 3600 / 1000 / 1000 # MJ / m^2 / d
        # Clear sky solar radiation
        r_so = (0.75 + 0.00002 * self._elevation) * r_a

        sigma_t_max4 = 0.000000004903 * math.pow(temp_max + 273.16, 4)
        sigma_t_min4 = 0.000000004903 * math.pow(temp_min + 273.16, 4)
        avg_sigma_t = (sigma_t_max4 + sigma_t_min4) / 2

        d = 4098 * _Weather.saturation_vapour_pressure(temp_avg) / math.pow(temp_avg + 237.3, 2)
        g = 0.665e-3 * pressure

        es = (_Weather.saturation_vapour_pressure(temp_min) + _Weather.saturation_vapour_pressure(temp_max)) / 2
        ea = _Weather.saturation_vapour_pressure(temp_min) * humid_max / 200 + _Weather.saturation_vapour_pressure(temp_max) * humid_min / 200

        vapor_press_deficit = es - ea

        # Net longwave radiation
        r_nl = avg_sigma_t * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * r_s / max(1, r_so) - 0.35)
        # Net radiation
        r_n = r_ns - r_nl

        eto = ((0.408 * d * r_n) + (g * 900 * wind_speed * vapor_press_deficit) / (temp_avg + 273)) / (d + g * (1 + 0.34 * wind_speed))

        return eto

    @_cache('rain')
    def get_rain(self, check_date):
        result = 0.0
        hourly_data = self.get_hourly_data(check_date)
        for data in hourly_data:
            if 'precipitation' in data:
                result += data['precipitation']

        return result

    #Deprecated interfaces:
    def _deprecated(self, *args, **kwargs):
        raise Exception(_('This interface was removed, please update the plug-in!'))

    get_wunderground_history = _deprecated
    get_wunderground_forecast = _deprecated
    get_wunderground_conditions = _deprecated
    get_daily_data = _deprecated    


weather = _Weather()
