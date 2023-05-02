#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = u'Rimco'

# System imports
import logging
import traceback
from ospy.helpers import is_python2, avg

if is_python2():
    from urllib2 import urlopen
    from urllib import quote_plus
else:
    from urllib.request import urlopen, Request
    from urllib.parse import quote_plus

import json
import datetime
import time
import math
from threading import Thread, Lock

from ospy.options import options

from . import i18n
   

def _cache(cache_name):
    def cache_decorator(func):
        def func_wrapper(self, check_date):
            if isinstance(check_date, datetime.datetime):
                check_date = check_date.date()

            if 'location' not in self._result_cache or options.location != self._result_cache['location']:
                self._result_cache.clear()
                self._result_cache['location'] = options.location

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

        options.add_callback('location', self._option_cb)
        options.add_callback('stormglass_key', self._option_cb)
        options.add_callback('weather_lat', self._option_cb)            # from home page weather status (latitude)
        options.add_callback('weather_lon', self._option_cb)            # from home page weather status (longtitude)
        options.add_callback('weather_status', self._option_cb)         # from home page weather status (msg code)

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
 
                    options.weather_status = 1

                self._sleep(3600)
            except Exception:
                logging.warning(_('Weather error:') + ' ' + traceback.format_exc())
                self._sleep(6*3600)

    def _find_location(self):
        if options.location and options.stormglass_key:
            data = urlopen(
                "https://nominatim.openstreetmap.org/search?q=%s&format=json" % quote_plus(options.location))
            data = json.loads(data.read().decode(data.info().get_content_charset('utf-8')))
            if not data:
                options.weather_status = 0 # Weather - No location found!
                raise Exception(_('No location found:') + ' ' + options.location + '.')
            else:
                self._lat = float(data[0]['lat'])
                self._lon = float(data[0]['lon'])
                options.weather_lat = str(float(data[0]['lat']))
                options.weather_lon = str(float(data[0]['lon']))
                options.weather_status = 1 # found
                url = "https://api.stormglass.io/v2/elevation/point?lat=%s&lng=%s" % self.get_lat_lon()
                self._elevation = self._get_stormglass_json(url)['data']['elevation']
                logging.debug(_('Location found: %s, %s at %.1fm above sea level'), self._lat, self._lon, self._elevation)

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
        data = urlopen(request)
        return json.loads(data.read().decode(data.info().get_content_charset('utf-8')))

    @_cache('stormglass_data')
    def _get_stormglass_data(self, check_date):
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
                    result.append({
                        'time': hr_timestamp,
                        'temperature': hr_data['airTemperature']['sg'],                     # [C]
                        'pressure': hr_data['pressure']['sg'],                              # [hPa]
                        'cloudCover': hr_data['cloudCover']['sg'] / 100.0,                  # [0.0 - 1.0]
                        'humidity': hr_data['humidity']['sg'] / 100.0,                      # [0.0 - 1.0]
                        'precipitation': hr_data['precipitation']['sg'],                    # [mm/h]
                        'windSpeed': hr_data['windSpeed']['sg'],                            # [m/s]
                    })

        return result

    def get_hourly_data(self, check_date):
        return self._get_stormglass_data(check_date)        

    def get_current_data(self):
        current_timestamp = int(datetime.datetime.now().replace(minute=0, second=0, microsecond=0).timestamp())
        result = [x for x in self.get_hourly_data(datetime.date.today()) if x['time'] == current_timestamp]
        return result[0] if result else {}

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
        hourly_data = self.get_hourly_data(check_date)

        temp_avg = avg([x['temperature'] for x in hourly_data])             # [C]
        temp_min = min([x['temperature'] for x in hourly_data])             # [C]
        temp_max = max([x['temperature'] for x in hourly_data])             # [C]
        wind_speed = avg([x['windSpeed'] for x in hourly_data]) * 0.748     # [m/s] at 2m height
        humid_min = min([x['humidity'] for x in hourly_data]) * 100         # [0 - 100]
        humid_max = max([x['humidity'] for x in hourly_data]) * 100         # [0 - 100]
        pressure = avg([x['windSpeed'] for x in hourly_data]) / 10          # [kPa]        

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