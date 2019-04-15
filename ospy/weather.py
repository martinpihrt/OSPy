#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Rimco'

# System imports
import logging
import traceback
import urllib2
import json
import urllib
import datetime
import time
import math
from threading import Thread, Lock

from ospy.options import options


def _cache(cache_name):
    def cache_decorator(func):
        def func_wrapper(self, check_date):
            if 'location' not in self._result_cache or options.location != self._result_cache['location'] or \
                    'elevation' not in self._result_cache or options.elevation != self._result_cache['elevation']:
                self._result_cache = {
                    'location': options.location,
                    'elevation': options.elevation
                }
            if cache_name not in self._result_cache:
                self._result_cache[cache_name] = {}

            for key in self._result_cache[cache_name].keys():
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
        self._tz_offset = 0
        self._determine_location = True
        self._result_cache = options.weather_cache

        options.add_callback('location', self._option_cb)
        options.add_callback('darksky_key', self._option_cb)
        options.add_callback('elevation', self._option_cb)

        self._sleep_time = 0
        self.start()

    def _option_cb(self, key, old, new):
        self._determine_location = True
        self.update()

    def add_callback(self, function):
        if function not in self._callbacks:
            self._callbacks.append(function)

    def remove_callback(self, function):
        if function in self._callbacks:
            self._callbacks.remove(function)

    def update(self):
        self._sleep_time = 0

    def _sleep(self, secs):
        self._sleep_time = secs
        while self._sleep_time > 0:
            time.sleep(1)
            self._sleep_time -= 1

    def run(self):
        time.sleep(5)  # Some delay to allow internet to initialize
        while True:
            try:
                try:
                    if self._determine_location:
                        self._determine_location = False
                        self._find_location()
                finally:
                    for function in self._callbacks:
                        function()

                self._sleep(3600)
            except Exception:
                logging.warning('Weather error:\n' + traceback.format_exc())
                self._sleep(6*3600)

    def _find_location(self):
        if options.location and options.darksky_key:
            data = urllib2.urlopen(
                "https://nominatim.openstreetmap.org/search?q=%s&format=json" % urllib.quote_plus(options.location))
            data = json.load(data)
            if not data:
                raise Exception('No location found: ' + options.location + '.')
            else:
                self._lat = float(data[0]['lat'])
                self._lon = float(data[0]['lon'])
                logging.debug('Location found: %s, %s', self._lat, self._lon)

    def get_lat_lon(self):
        if self._lat is None or self._lon is None:
            self._determine_location = True  # Let the weather thread try again when it wakes up
            raise Exception('No location coordinates available!')
        return self._lat, self._lon

    @_cache('darksky_data')
    def _get_darksky_data(self, check_date):
        if isinstance(check_date, datetime.datetime):
            check_date = check_date.date()

        date_str = ''
        if check_date <= datetime.date.today():
            date_str = ',' + check_date.strftime('%Y-%m-%dT00:00:00')
        url = "https://api.darksky.net/forecast/%s/%s,%s%s?exclude=minutely,alerts,flags&extend=hourly&units=si" % ((options.darksky_key,) + self.get_lat_lon() + (date_str,))

        # We cache results for previous days, but we also want to have a short term cache for predictions:
        if 'darksky_json' not in self._result_cache:
            self._result_cache['darksky_json'] = {}

        for key in self._result_cache['darksky_json'].keys():
            if datetime.datetime.now() - self._result_cache['darksky_json'][key]['time'] > datetime.timedelta(minutes=10):
                del self._result_cache['darksky_json'][key]

        if url not in self._result_cache['darksky_json']:
            logging.debug(url)
            self._result_cache['darksky_json'][url] = {'time': datetime.datetime.now(),
                                                       'data': json.load(urllib2.urlopen(url))}
            options.weather_cache = self._result_cache

        if 'offset' in self._result_cache['darksky_json'][url]['data']:
            self._tz_offset = self._result_cache['darksky_json'][url]['data']['offset']
        elif self._tz_offset == 0:
            logging.warning('No timezone offset found, ETo might be incorrect.')

        return self._result_cache['darksky_json'][url]['data']

    def get_hourly_data(self, check_date):
        if isinstance(check_date, datetime.datetime):
            check_date = check_date.date()

        return [x for x in self._get_darksky_data(check_date)['hourly']['data'] if datetime.datetime.fromtimestamp(x['time']).date() == check_date]

    def get_daily_data(self, check_date):
        if isinstance(check_date, datetime.datetime):
            check_date = check_date.date()

        matching_days_data = [x for x in self._get_darksky_data(check_date)['daily']['data'] if datetime.datetime.fromtimestamp(x['time']).date() == check_date]

        return matching_days_data[0] if matching_days_data else {}

    def get_current_data(self):
        return self._get_darksky_data(datetime.date.today() + datetime.timedelta(days=1))['currently']

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

    @_cache('eto')
    def get_eto(self, check_date):
        if isinstance(check_date, datetime.datetime):
            check_date = check_date.date()

        hourly_data = self.get_hourly_data(check_date)

        total_solar_radiation = 0
        total_clear_sky_isolation = 0
        temp_avg = 0
        humid_min = 100
        humid_max = 0
        for data in hourly_data:
            hour_datetime = datetime.datetime.fromtimestamp(data['time'])
            year_datetime = datetime.datetime(hour_datetime.year, 1, 1)
            fractional_day = (360/365.25)*(hour_datetime - year_datetime).total_seconds() / 3600 / 24
            if 'cloudCover' in data:
                solar_radiation, clear_sky_isolation = self._calc_radiation(data['cloudCover'], fractional_day, hour_datetime.hour)

                # Accumulate clear sky radiation and solar radiation on the ground
                total_solar_radiation += solar_radiation
                total_clear_sky_isolation += clear_sky_isolation

            if 'temperature' in data:
                temp_avg += data['temperature'] / len(hourly_data)
            if 'humidity' in data:
                humid_min = min(humid_min, data['humidity'] * 100)
                humid_max = max(humid_max, data['humidity'] * 100)

        daily_data = self.get_daily_data(check_date)
        # m/s at 2m above ground
        wind_speed = daily_data.get('windSpeed', 0.0) * 0.748

        pressure = daily_data.get('pressure', 1000) / 10 # kPa
        temp_min = daily_data.get('temperatureMin', 20) # degrees C
        temp_max = daily_data.get('temperatureMax', 20) # degrees C

        # Solar Radiation
        r_s = total_solar_radiation * 3600 / 1000 / 1000 # MJ / m^2 / d
        # Net shortwave radiation
        r_ns = 0.77 * r_s

        # Extraterrestrial Radiation
        r_a = total_clear_sky_isolation * 3600 / 1000 / 1000 # MJ / m^2 / d
        # Clear sky solar radiation
        r_so = (0.75 + 0.00002 * options.elevation) * r_a

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
        if isinstance(check_date, datetime.datetime):
            check_date = check_date.date()

        result = 0.0
        hourly_data = self.get_hourly_data(check_date)
        for data in hourly_data:
            if 'precipIntensity' in data and 'precipProbability' in data:
                result += data['precipIntensity'] * data['precipProbability']

        return result

    #Deprecated interfaces:
    def _deprecated(self, *args, **kwargs):
        raise Exception('This interface was removed because Weather Underground API has stopped, please update the plug-in!')

    get_wunderground_history = _deprecated
    get_wunderground_forecast = _deprecated
    get_wunderground_conditions = _deprecated


weather = _Weather()