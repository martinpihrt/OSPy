#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Rimco'

# System imports
import logging
import traceback
import urllib2
import json
import urllib
import re
import os
import shutil
import datetime
import time
import math
from threading import Thread, Lock

from ospy.options import options
from ospy.log import log
from ospy.helpers import mkdir_p, try_float


def _cache(cache_name):
    def cache_decorator(func):
        def func_wrapper(self, check_date):
            if 'location' not in self._result_cache or self._location != self._result_cache['location'] or \
                    'elevation' not in self._result_cache or options.elevation != self._result_cache['elevation']:
                self._result_cache = {
                    'location': self._location,
                    'elevation': options.elevation
                }
            if cache_name not in self._result_cache:
                self._result_cache[cache_name] = {}

            if check_date not in self._result_cache[cache_name] or (datetime.date.today() - check_date).days <= 1:
                try:
                    self._result_cache[cache_name][check_date] = func(self, check_date)
                    options.weather_cache = self._result_cache
                except Exception:
                    if check_date not in self._result_cache[cache_name]:
                        raise
                    
                for key in self._result_cache[cache_name].keys():
                    if (datetime.date.today() - key).days > 30:
                        del self._result_cache[cache_name][key]

            return self._result_cache[cache_name][check_date]
        return func_wrapper
    return cache_decorator


class _Weather(Thread):
    cloud_coverage = {
        "Blowing Sand":                   0.6,
        "Blowing Snow":                   1.0,
        "Blowing Widespread Dust":        0.6,
        "Clear":                          0.0,
        "Cloudy":                         1.0,
        "Drizzle":                        0.8,
        "Dust Whirls":                    0.0,
        "Flurries":                       1.0,
        "Fog Patches":                    0.4,
        "Fog":                            0.8,
        "Freezing Drizzle":               0.8,
        "Freezing Fog":                   0.8,
        "Freezing Rain":                  1.0,
        "Funnel Cloud":                   0.9,
        "Hail Showers":                   0.8,
        "Hail":                           1.0,
        "Haze":                           0.6,
        "Ice Crystals":                   0.6,
        "Ice Pellet Showers":             0.8,
        "Ice Pellets":                    1.0,
        "Low Drifting Sand":              0.4,
        "Low Drifting Snow":              0.4,
        "Low Drifting Widespread Dust":   0.4,
        "Mist":                           0.3,
        "Mostly Cloudy":                  0.8,
        "Mostly Sunny":                   0.5,
        "Overcast":                       1.0,
        "Partial Fog":                    0.6,
        "Partly Cloudy":                  0.5,
        "Partly Sunny":                   0.8,
        "Patches of Fog":                 0.4,
        "Rain Mist":                      0.5,
        "Rain Showers":                   0.8,
        "Rain":                           1.0,
        "Sand":                           0.6,
        "Sandstorm":                      0.6,
        "Scattered Clouds":               0.4,
        "Shallow Fog":                    0.5,
        "Sleet":                          1.0,
        "Small Hail Showers":             0.6,
        "Small Hail":                     1.0,
        "Smoke":                          0.6,
        "Snow Blowing Snow Mist":         1.0,
        "Snow Grains":                    1.0,
        "Snow Showers":                   0.8,
        "Snow":                           1.0,
        "Spray":                          0.4,
        "Squalls":                        0.5,
        "Sunny":                          0.0,
        "Thunderstorm":                   0.9,
        "Thunderstorms":                  0.9,
        "Thunderstorms and Ice Pellets":  1.0,
        "Thunderstorms and Rain":         1.0,
        "Thunderstorms and Snow":         1.0,
        "Thunderstorms with Hail":        1.0,
        "Thunderstorms with Small Hail":  0.9,
        "Unknown Precipitation":          0.5,
        "Unknown":                        0.5,
        "Volcanic Ash":                   0.6,
        "Widespread Dust":                0.6,
    }

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self._lock = Lock()
        self._callbacks = []

        self._location = options.location
        self._wunderground_key = options.wunderground_key
        self._use_wunderground = options.use_wunderground
        self._requests = []
        self._lid = ""
        self._tz = None
        self._lat = 0
        self._lon = 0
        self._determine_location = True
        self._result_cache = options.weather_cache

        options.add_callback('location', self._option_cb)
        options.add_callback('wunderground_key', self._option_cb)
        options.add_callback('elevation', self._option_cb)

        self._sleep_time = 0
        self.start()

    def _option_cb(self, key, old, new):
        setattr(self, '_' + key, new)
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
        while True:
            try:
                try:
                    if self._determine_location:
                        self._determine_location = False
                        self._find_location()
                finally:
                    for function in self._callbacks:
                        function()

                    self._remove_wunderground_data([
                        'conditions_',
                        'forecast10day_',
                        'history_',
                        'hourly_',
                        'hourly10day_'
                    ])

                self._sleep(3600)
            except Exception:
                logging.warning('Weather error:\n' + traceback.format_exc())
                self._sleep(6*3600)

    def _find_location(self):
        if self._location and self._wunderground_key and self._use_wunderground:
            lid = ""
            if re.search("pws:", self._location):
                lid = self._location
            else:
                data = urllib2.urlopen(
                    "http://autocomplete.wunderground.com/aq?h=0&query=" + urllib.quote_plus(options.location))
                data = json.load(data)
                if data is not None:
                    lid = "zmw:" + data['RESULTS'][0]['zmw']

            self._lid = lid

            geo = self._get_wunderground_data('geolookup', None, True)
            self._lat = float(geo['location']['lat'])
            self._lon = float(geo['location']['lon'])

    def get_lid(self):
        if self._lid == "":
            raise Exception('No Location ID found!')
        return self._lid

    def _get_query_path(self, query, name=None):
        if name is None:
            name = query

        query += '/q/' + self.get_lid() + '.json'
        name += '/q/' + self.get_lid() + '.json'

        path = os.path.join('ospy', 'data', 'wunderground', name.replace(':', '_'))
        return query, path

    def _get_wunderground_data(self, query, name=None, force=False):
        with self._lock:
            query, path = self._get_query_path(query, name)
            mkdir_p(os.path.dirname(path))

            try_nr = 1
            data = {}
            while try_nr <= 2:
                try:
                    if not os.path.exists(path) or (force and time.time() - os.path.getmtime(path) > 2 * 3600):
                        # Max 5 calls per minute:
                        self._requests.append(time.time())
                        if len(self._requests) > 5:
                            del self._requests[0]
                            if self._requests[-1] - self._requests[0] < 60:
                                logging.info('Waiting for weather information.')
                                time.sleep(60 - (self._requests[-1] - self._requests[0]))

                        with open(path, 'wb') as fh:
                            print query
                            req = urllib2.urlopen("http://api.wunderground.com/api/" + self._wunderground_key + "/" + query)
                            while True:
                                chunk = req.read(20480)
                                if not chunk:
                                    break
                                fh.write(chunk)

                    try:
                        with file(path, 'r') as fh:
                            data = json.load(fh)
                    except ValueError:
                        raise Exception('Failed to read ' + path + '.')

                    if data is not None:
                        if 'error' in data['response']:
                            raise Exception(path + ': ' + str(data['response']['error']))
                    else:
                        raise Exception('JSON decoding failed.')

                except Exception as err:
                    if try_nr < 2:
                        log.debug(str(err), 'Retrying.')
                        os.remove(path)
                    else:
                        raise
                try_nr += 1

            return data

    def _remove_wunderground_data(self, prefixes):
        root = os.path.join('ospy', 'data', 'wunderground')
        # Delete old files
        for prefix in prefixes:
            check_date = datetime.date.today()
            day_delta = datetime.timedelta(days=1)
            keep_folders = []
            for index in range(30):
                datestring = check_date.strftime('%Y%m%d')
                keep_folders.append(prefix + datestring)
                check_date -= day_delta
            if os.path.isdir(root):
                for folder in os.listdir(root):
                    if folder.startswith(prefix) and folder not in keep_folders:
                        path = os.path.join(root, folder)
                        if os.path.isdir(path):
                            shutil.rmtree(path)

    def _get_history(self, check_date):
        datestring = check_date.strftime('%Y%m%d')
        request = "history_" + datestring

        if isinstance(check_date, datetime.datetime):
            check_date = check_date.date()

        _, path = self._get_query_path(request)
        force = os.path.isfile(path) and datetime.datetime.fromtimestamp(os.path.getmtime(path)).date() <= check_date

        data = self._get_wunderground_data(request, force=force)

        if data and len(data['history']['dailysummary']) == 0:
            data = self._get_wunderground_data(request, force=True)

        return data


    ################################################################################
    # Info queries:                                                                #
    ################################################################################
    def get_wunderground_history(self, days_history):
        if days_history == 0:
            return {}

        check_date = datetime.date.today()
        day_delta = datetime.timedelta(days=1)

        info = {}
        for index in range(-1, -1 - days_history, -1):
            check_date -= day_delta
            data = self._get_history(check_date)

            if data and len(data['history']['dailysummary']) > 0:
                info[index] = data['history']['dailysummary'][0]

        result = {}
        for index, day_info in info.iteritems():
            result[index] = {
                'temp_c': try_float(day_info['maxtempm'], 20),
                'rain_mm': try_float(day_info['precipm']),
                'wind_ms': try_float(day_info['meanwindspdm']) / 3.6,
                'humidity': try_float(day_info['humidity'], 50)
            }

        return result

    def get_wunderground_conditions(self, force=True):
        datestring = datetime.date.today().strftime('%Y%m%d')
        data = self._get_wunderground_data("conditions", "conditions_" + datestring, force)

        day_info = data['current_observation']

        result = {
            'temperature_string': day_info['temperature_string'],
            'temp_c': try_float(day_info['temp_c'], 20),
            'temp_f': try_float(day_info['temp_f'], 68),
            'rain_mm': try_float(day_info['precip_today_metric']),
            'wind_ms': try_float(day_info['wind_kph']) / 3.6,
            'humidity': try_float(day_info['relative_humidity'].replace('%', ''), 50)
        }
        return result

    def get_wunderground_forecast(self, days_forecast):
        datestring = datetime.date.today().strftime('%Y%m%d')
        request = "forecast10day", "forecast10day_" + datestring
        data = self._get_wunderground_data(*request)

        if data and len(data['forecast']['simpleforecast']['forecastday']) == 0:
            data = self._get_wunderground_data(*request, force=True)

        info = {}
        for day_index, entry in enumerate(data['forecast']['simpleforecast']['forecastday']):
            info[day_index] = entry

        result = {}
        for index, day_info in info.iteritems():
            if index <= days_forecast:
                if day_info['qpf_allday']['mm'] is None:
                    day_info['qpf_allday']['mm'] = 0
                result[index] = {
                    'temp_c': try_float(day_info['high']['celsius'], 20),
                    'rain_mm': try_float(day_info['qpf_allday']['mm']),
                    'wind_ms': try_float(day_info['avewind']['kph']) / 3.6,
                    'humidity': try_float(day_info['avehumidity'], 50)
                }

        return result

    @staticmethod
    def _datetime(data_date):
        if 'month' in data_date:
            data_date['mon'] = data_date['month']
        if 'day' in data_date:
            data_date['mday'] = data_date['day']
        return datetime.datetime(int(data_date['year']),
                                 int(data_date['mon']),
                                 int(data_date['mday']),
                                 int(data_date['hour']),
                                 int(data_date['min']))

    @staticmethod
    def _year(data_date):
        return datetime.datetime(int(data_date['year']), 1, 1)

    # Returns a calculation of saturation vapour pressure based on temperature in degrees
    @staticmethod
    def saturation_vapour_pressure(t):
        return 0.6108 * math.exp((17.27 * t) / (t + 237.3))
    
    def _calc_coverage(self, condition):
        coverage = 0.5
        modifiers = {
            '': lambda x: x,
            'Light ': lambda x: max(0.0, x*1.5 - 0.5),
            'Heavy ': lambda x: min(1.0, x*0.5 + 0.5),
            'Chance ': lambda x: x*0.5,
            'Chance of ': lambda x: x*0.5,
            'Chance of a ': lambda x: x*0.5,
        }

        for mod, fcn in modifiers.iteritems():
            if condition.startswith(mod) and condition[len(mod):] in self.cloud_coverage:
                coverage = fcn(self.cloud_coverage[condition[len(mod):]])
                break

        return coverage

    def _calc_radiation(self, coverage, fractional_day, hour):
        f = math.radians(fractional_day)
        declination = 0.396372 - 22.91327 * math.cos(f) + 4.02543  * math.sin(f) - 0.387205 * math.cos(2*f) + 0.051967 * math.sin(2*f) - 0.154527 * math.cos(3*f) + 0.084798 * math.sin(3*f)
        time_correction = 0.004297 + 0.107029 * math.cos(f) - 1.837877 * math.sin(f) - 0.837378 * math.cos(2*f) - 2.340475 * math.sin(2*f)
        solar_hour = (hour + 0.5 - 12)*15 + self._lon + time_correction

        if solar_hour < -180: solar_hour += 360
        if solar_hour > 180: solar_hour -= 360

        solar_factor = math.sin(math.radians(self._lat))*math.sin(math.radians(declination))+math.cos(math.radians(self._lat))*math.cos(math.radians(declination))*math.cos(math.radians(solar_hour))
        sun_elevation = math.degrees(math.asin(solar_factor))

        clear_sky_isolation = max(0, 990 * math.sin(math.radians(sun_elevation)) - 30)
        solar_radiation = clear_sky_isolation * (1 - 0.75 * math.pow(coverage, 3.4))

        return solar_radiation, clear_sky_isolation

    def _calc_eto(self, total_solar_radiation, total_clear_sky_isolation, data):
        # Solar Radiation
        r_s = total_solar_radiation * 3600 / 1000 / 1000 # MJ / m^2 / d
        # Net shortwave radiation
        r_ns = 0.77 * r_s

        # Extraterrestrial Radiation
        r_a = total_clear_sky_isolation * 3600 / 1000 / 1000 # MJ / m^2 / d
        # Clear sky solar radiation
        r_so = (0.75 + 0.00002 * options.elevation) * r_a

        # m/s at 2m above ground
        wind_speed = try_float(data['meanwindspdm']) * 1000 / 3600 * 0.748

        pressure = try_float(data['meanpressurem'], 1000) / 10 # kPa

        temp_avg = try_float(data['meantempm'], 20) # degrees C
        temp_min = try_float(data['mintempm'], 20) # degrees C
        temp_max = try_float(data['maxtempm'], 20) # degrees C
        humid_max = try_float(data['maxhumidity'], 50) # %
        humid_min = try_float(data['minhumidity'], 50) # %

        sigma_t_max4 = 0.000000004903 * math.pow(temp_max + 273.16, 4)
        sigma_t_min4 = 0.000000004903 * math.pow(temp_min + 273.16, 4)
        avg_sigma_t = (sigma_t_max4 + sigma_t_min4) / 2

        d = 4098 * self.saturation_vapour_pressure(temp_avg) / math.pow(temp_avg + 237.3, 2)
        g = 0.665e-3 * pressure

        es = (self.saturation_vapour_pressure(temp_min) + self.saturation_vapour_pressure(temp_max)) / 2
        ea = self.saturation_vapour_pressure(temp_min) * humid_max / 200 + self.saturation_vapour_pressure(temp_max) * humid_min / 200

        vapor_press_deficit = es - ea

        # Net longwave radiation
        r_nl = avg_sigma_t * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * r_s / max(1, r_so) - 0.35)
        # Net radiation
        r_n = r_ns - r_nl

        eto = ((0.408 * d * r_n) + (g * 900 * wind_speed * vapor_press_deficit) / (temp_avg + 273)) / (d + g * (1 + 0.34 * wind_speed))

        return eto

    @_cache('eto')
    def get_eto(self, check_date):
        if isinstance(check_date, datetime.datetime):
            check_date = check_date.date()

        if check_date < datetime.date.today():
            return self._get_history_eto(check_date)
        elif check_date > datetime.date.today():
            return self._get_future_eto(check_date)
        elif datetime.datetime.now().hour < 12:
            return self._get_future_eto(check_date)
        else:
            return self._get_history_eto(check_date)

    def _get_history_eto(self, check_date):
        data = self._get_history(check_date)
        result = 2.0

        coverages = {}
        for observation in data['history']['observations']:
            hour = int(observation['utcdate']['hour'])
            if hour not in coverages:
                coverages[hour] = {
                    'fractional_day': (360/365.25)*(self._datetime(observation['utcdate']) - self._year(observation['utcdate'])).total_seconds() / 3600 / 24,
                    'coverage': []
                }

            coverage = self._calc_coverage(observation['conds'])
            coverages[hour]['coverage'].append(coverage)

        total_solar_radiation = 0
        total_clear_sky_isolation = 0
        for hour, coverage in coverages.iteritems():
            cov = sum(coverage['coverage']) / max(1, len(coverage['coverage']))
            solar_radiation, clear_sky_isolation = self._calc_radiation(cov, coverage['fractional_day'], hour)

            # Accumulate clear sky radiation and solar radiation on the ground
            total_solar_radiation += solar_radiation
            total_clear_sky_isolation += clear_sky_isolation

        if data and len(data['history']['dailysummary']) > 0:
            result = self._calc_eto(total_solar_radiation, total_clear_sky_isolation, data['history']['dailysummary'][0])

        return result

    def _get_todays_eto(self, check_date):
        datestring = datetime.date.today().strftime('%Y%m%d')
        hourly_data = self._get_wunderground_data("hourly", "hourly_" + datestring)
        today_data = self._get_wunderground_data("conditions", "conditions_" + datestring)

        if isinstance(check_date, datetime.datetime):
            check_date = check_date.date()

        summaries = {
            'meanwindspdm': (lambda x: sum(x) / max(1, len(x)), 'wspd', 'metric'),
            'meantempm': (lambda x: sum(x) / max(1, len(x)), 'temp', 'metric'),
            'mintempm': (lambda x: min(x), 'temp', 'metric'),
            'maxtempm': (lambda x: max(x), 'temp', 'metric'),
            'maxhumidity': (lambda x: max(x), 'humidity'),
            'minhumidity': (lambda x: min(x), 'humidity'),
        }
        summary = {}
        for key in summaries.keys():
            summary[key] = []

        coverages = {}
        for observation in hourly_data['hourly_forecast']:
            current_date = datetime.datetime.utcfromtimestamp(int(observation['FCTTIME']['epoch']))
            year_date = datetime.datetime(current_date.year, 1, 1)
            if current_date.date() == check_date:
                hour = current_date.hour
                if hour not in coverages:
                    coverages[hour] = {
                        'fractional_day': (360/365.25)*(current_date - year_date).total_seconds() / 3600 / 24,
                        'coverage': []
                    }

                coverage = self._calc_coverage(observation['condition'])
                coverages[hour]['coverage'].append(coverage)

                for key, search in summaries.iteritems():
                    elem_data = observation
                    for elem in search[1:]:
                        elem_data = elem_data[elem]
                    summary[key].append(try_float(elem_data))

        for key, search in summaries.iteritems():
            summary[key] = search[0](summary[key])

        # No pressure hourly, use conditions data:
        summary['meanpressurem'] = try_float(today_data['current_observation']['pressure_mb'], 1000)

        total_solar_radiation = 0
        total_clear_sky_isolation = 0
        for hour, coverage in coverages.iteritems():
            cov = sum(coverage['coverage']) / max(1, len(coverage['coverage']))
            solar_radiation, clear_sky_isolation = self._calc_radiation(cov, coverage['fractional_day'], hour)

            # Accumulate clear sky radiation and solar radiation on the ground
            total_solar_radiation += solar_radiation
            total_clear_sky_isolation += clear_sky_isolation

        return self._calc_eto(total_solar_radiation, total_clear_sky_isolation, summary)

    def _get_future_eto(self, check_date):
        datestring = datetime.date.today().strftime('%Y%m%d')
        request = "hourly10day", "hourly10day_" + datestring
        hourly_data = self._get_wunderground_data(*request)

        if hourly_data and len(hourly_data['hourly_forecast']) == 0:
            hourly_data = self._get_wunderground_data(*request, force=True)
        
        today_data = self._get_wunderground_data("conditions", "conditions_" + datestring)

        if isinstance(check_date, datetime.datetime):
            check_date = check_date.date()

        summaries = {
            'meanwindspdm': (lambda x: sum(x) / max(1, len(x)), 'wspd', 'metric'),
            'meantempm': (lambda x: sum(x) / max(1, len(x)), 'temp', 'metric'),
            'mintempm': (lambda x: min(x), 'temp', 'metric'),
            'maxtempm': (lambda x: max(x), 'temp', 'metric'),
            'maxhumidity': (lambda x: max(x), 'humidity'),
            'minhumidity': (lambda x: min(x), 'humidity'),
        }
        summary = {}
        for key in summaries.keys():
            summary[key] = []

        coverages = {}
        for observation in hourly_data['hourly_forecast']:
            current_date = datetime.datetime.utcfromtimestamp(int(observation['FCTTIME']['epoch']))
            year_date = datetime.datetime(current_date.year, 1, 1)
            if current_date.date() == check_date:
                hour = current_date.hour
                if hour not in coverages:
                    coverages[hour] = {
                        'fractional_day': (360/365.25)*(current_date - year_date).total_seconds() / 3600 / 24,
                        'coverage': []
                    }

                coverage = self._calc_coverage(observation['condition'])
                coverages[hour]['coverage'].append(coverage)

                for key, search in summaries.iteritems():
                    elem_data = observation
                    for elem in search[1:]:
                        elem_data = elem_data[elem]
                    summary[key].append(try_float(elem_data))

        for key, search in summaries.iteritems():
            summary[key] = search[0](summary[key])

        # No pressure forecast, use today's data:
        summary['meanpressurem'] = try_float(today_data['current_observation']['pressure_mb'], 1000)
        day_delta = (check_date - datetime.date.today()).total_seconds() / 3600 / 24
        if today_data['current_observation']['pressure_trend'] == '+':
            summary['meanpressurem'] += day_delta
        elif today_data['current_observation']['pressure_trend'] == '-':
            summary['meanpressurem'] -= day_delta

        total_solar_radiation = 0
        total_clear_sky_isolation = 0
        for hour, coverage in coverages.iteritems():
            cov = sum(coverage['coverage']) / max(1, len(coverage['coverage']))
            solar_radiation, clear_sky_isolation = self._calc_radiation(cov, coverage['fractional_day'], hour)

            # Accumulate clear sky radiation and solar radiation on the ground
            total_solar_radiation += solar_radiation
            total_clear_sky_isolation += clear_sky_isolation

        return self._calc_eto(total_solar_radiation, total_clear_sky_isolation, summary)

    @_cache('rain')
    def get_rain(self, check_date):
        if isinstance(check_date, datetime.datetime):
            check_date = check_date.date()

        result = 0.0
        if check_date < datetime.date.today() or (check_date == datetime.date.today() and datetime.datetime.now().hour >= 12):
            history_data = self._get_history(check_date)
            if history_data and len(history_data['history']['dailysummary']) > 0:
                result = try_float(history_data['history']['dailysummary'][0]['precipm'])

        if check_date >= datetime.date.today():
            datestring = datetime.date.today().strftime('%Y%m%d')
            request = "forecast10day", "forecast10day_" + datestring
            future_data = self._get_wunderground_data(*request)

            if future_data and len(future_data['forecast']['simpleforecast']['forecastday']) == 0:
                future_data = self._get_wunderground_data(*request, force=True)

            day_left = 1.0
            if check_date == datetime.date.today():
                day_time = datetime.datetime.now().time()
                day_left -= (day_time.hour * 60 + day_time.minute) / 24.0 / 60

            for entry in future_data['forecast']['simpleforecast']['forecastday']:
                if self._datetime(entry['date']).date() == check_date:
                    if entry['qpf_allday']['mm'] is None:
                        entry['qpf_allday']['mm'] = 0
                    result += day_left * try_float(entry['qpf_allday']['mm'])
                    break
                    
        return result



weather = _Weather()
