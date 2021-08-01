# -*- coding: utf-8 -*-
from __future__ import absolute_import
from functools import reduce
__author__ = 'Rimco'

# System imports
from datetime import datetime
from threading import Timer
import logging
import shelve
from . import i18n
from . import helpers
import traceback
import os
import time
import glob

OPTIONS_FILE = './ospy/data/options.db'
OPTIONS_GLOB = './ospy/data/*options.db'

class _Options(object):
    # Using an array to preserve order
    OPTIONS = [
        #######################################################################
        # System ##############################################################
        {
            "key": "name",
            "name": _('System name'),
            "default": u'OpenSprinkler Pi',
            "help": _('Unique name of this OpenSprinkler system.'),
            "category": _('System')
        },
        {
            "key": "theme",
            "name": _('System theme'),
            "default": "basic",
            "options": helpers.themes,
            "help": _('Determines the look of the GUI.'),
            "category": _('System')
        },
        {
            "key": "time_format",
            "name": _('24-hour clock'),
            "default": True,
            "help": _('Display times in 24 hour format (as opposed to AM/PM style.)'),
            "category": _('System')
        },
        {
            "key": "HTTP_web_ip",
            "name": _('HTTP IP addr'),
            "default": "0.0.0.0",
            "help": _('IP Address used for HTTP server socket.  IPv4 or IPv6 address (effective after reboot.)'),
            "category": _('System'),
        },
        {
            "key": "web_port",
            "name": _('HTTP/S port'),
            "default": 8080,
            "help": _('HTTP/S port (effective after reboot.)'),
            "category": _('System'),
            "min": 1,
            "max": 65535
        },
        {
            "key": "show_plugin_data",
            "name": _('Show plugins on home'),
            "default": True,
            "help": _('Show data from plugins on home page.'),
            "category": _('System')
        },
        {
            "key": "show_sensor_data",
            "name": _('Show sensors on home'),
            "default": True,
            "help": _('Show data from sensors on home page.'),
            "category": _('System')
        },        
        {
            "key": "show_images",
            "name": _('Show pictures at stations'),
            "default": False,
            "help": _('Show pictures of stations on the homepage.'),
            "category": _('System')
        },        
        {
            "key": "enabled_plugins",
            "name": _('Enabled plug-ins'),
            "default": []
        },
        {
            "key": "plugin_status",
            "name": _('Plug-in status'),
            "default": {}
        },
        {
            "key": "plugin_readme_error",
            "name": _('ImportError: Failed loading extension partial_gfm'),
            "default": False
        },
        {
            "key": "ospy_readme_error",
            "name": _('ImportError: Failed loading extension partial_gfm'),
            "default": False
        },        
        {
            "key": "auto_plugin_update",
            "name": _('Automatic plug-in updates'),
            "default": False
        },
        {
            "key": "use_plugin_update",
            "name": _('Enable plug-in check status updates'),
            "default": False
        },
        {
            "key": "lang",
            "name": "", #_('System language'),
            "default": "default",
            "help": "", #_('Language localizations for this OpenSprinkler system. (effective after reboot.)'),
            "category": _('System')
        },
        #######################################################################
        # Weather  ############################################################
        {
            "key": "use_weather",
            "name": _('Use Weather'),
            "default": False,
            "help": _('Enabling or disabling connection to service Dark Sky.'),
            "category": _('Weather')
        },
        {
            "key": "darksky_key",
            "name": _('Dark Sky API key'),
            "default": "",
            "help": _('To make use of local weather conditions, a Dark Sky API key is needed.'),
            "category": _('Weather')
        },
        {
            "key": "location",
            "name": _('Location'),
            "default": u' ',
            "help": _('City name or zip code. Used to determine location via OpenStreetMap for weather information.'),
            "category": _('Weather')
        },
        {
            "key": "elevation",
            "name": _('Elevation (m)'),
            "default": 0,
            "help": _('Elevation of this location in meters.'),
            "category": _('Weather'),
            "min": 0,
            "max": 10000
        },
        #######################################################################
        # Users ############################################################
        {
            "key": "no_password",
            "name": _('Disable security'),
            "default": False,
            "help": _('Allow anonymous users to access the system without a password.'),
            "category": _('Users')
        },
        {
            "key": "admin_user",
            "name": _('Administrator name'),
            "default": "admin",
            "help": _('Administrator login name for login to the OSPy.'),
            "category": _('Users')
        },
        #######################################################################
        # Security ############################################################        
        {
            "key": "use_ssl",
            "name": _('Use HTTPS access'),
            "default": False,
            "help": _('Read HELP/Web Interface Guide. SSL certificate via Lets Encrypt certification authority (effective after reboot.)'),
            "category": _('Security')
        },
        {
            "key": "domain_ssl",
            "name": _('Domain name'),
            "default": "Localhost",
            "help": _('Domain name for generating SSL certificate via Lets Encrypt certification authority. Example: home.sprinkler.com'),
            "category": _('Security')
        },    
        {
            "key": "use_own_ssl",
            "name": _('Use Own HTTPS access'),
            "default": False,
            "help": _('SSL certificate via own file without certification authority (effective after reboot.)'),
            "category": _('Security')
        }, 
        #######################################################################
        # Sensors ############################################################# 
        {
            "key": "sensor_fw_passwd",
            "name": _('Password for uploading'),
            "default": "fg4s5b.s,trr7sw8sgyvrDfg",
            "help": _('Password for uploading firmware from OSPy to sensor (for all used sensors - the same password must be used in sensor options.)'),
            "category": _('Sensors')
        },               
        {
            "key": "aes_key",
            "name": _('AES key for sensors'),
            "default": "",
            "help": _('AES key for sensors. Len 16 character (for all used sensors - the same code must be used in Arduino code in sensor.)'),
            "category": _('Sensors')
        },
        #######################################################################
        # Station Handling ####################################################
        {
            "key": "max_usage",
            "name": _('Maximum usage'),
            "default": 1.0,
            "help": _('Determines how schedules of different stations are combined. 0 is no limit. 1 is sequential in case all stations have a usage of 1.'),
            "category": _('Station Handling')
        },
        {
            "key": "output_count",
            "name": _('Number of outputs'),
            "default": 8,
            "help": _('The number of outputs available (8 + 8*extensions)'),
            "category": _('Station Handling'),
            "min": 8,
            "max": 1000
        },
        {
            "key": "station_delay",
            "name": _('Station delay'),
            "default": 0,
            "help": _('Station delay time (in seconds), between 0 and 3600.'),
            "category": _('Station Handling'),
            "min": 0,
            "max": 3600
        },
        {
            "key": "min_runtime",
            "name": _('Minimum runtime'),
            "default": 0,
            "help": _('Skip the station delay if the run time was less than this value (in seconds), between 0 and 86400.'),
            "category": _('Station Handling'),
            "min": 0,
            "max": 86400
        },
        #######################################################################
        # Configure Master ####################################################
        {
            "key": "master_relay",
            "name": _('Activate relay'),
            "default": False,
            "help": _('Also activate the relay as master output.'),
            "category": _('Configure Master')
        },
        {
            "key": "master_on_delay",
            "name": _('Master on delay'),
            "default": 0,
            "help": _('Master on delay (in seconds), between -1800 and +1800.'),
            "category": _('Configure Master'),
            "min": -1800,
            "max": +1800
        },
        {
            "key": "master_off_delay",
            "name": _('Master off delay'),
            "default": 0,
            "help": _('Master off delay (in seconds), between -1800 and +1800.'),
            "category": _('Configure Master'),
            "min": -1800,
            "max": +1800
        },
        {
            "key": "master_on_delay_two",
            "name": _('Master two on delay'),
            "default": 0,
            "help": _('Master two on delay (in seconds), between -1800 and +1800.'),
            "category": _('Configure Master'),
            "min": -1800,
            "max": +1800
        },
        {
            "key": "master_off_delay_two",
            "name": _('Master two off delay'),
            "default": 0,
            "help": _('Master two off delay (in seconds), between -1800 and +1800.'),
            "category": _('Configure Master'),
            "min": -1800,
            "max": +1800
        },
        #######################################################################
        # Rain Sensor #########################################################
        {
            "key": "rain_sensor_enabled",
            "name": _('Use rain sensor'),
            "default": False,
            "help": _('Use rain sensor.'),
            "category": _('Rain Sensor')
        },
        {
            "key": "rain_sensor_no",
            "name": _('Normally open'),
            "default": True,
            "help": _('Rain sensor default.'),
            "category": _('Rain Sensor')
        },
        #######################################################################
        # Logging #############################################################
        {
            "key": "run_log",
            "name": _('Enable run log'),
            "default": False,
            "help": _('Log all runs - note that repetitive writing to an SD card can shorten its lifespan.'),
            "category": _('Logging')
        },
        {
            "key": "run_entries",
            "name": _('Max run entries'),
            "default": 100,
            "help": _('Number of run entries to save to disk, 0=no limit.'),
            "category": _('Logging'),
            "min": 0,
            "max": 1000
        },
        {  
            "key": "run_logEM",
            "name": _('Enable email log'),
            "default": False,
            "help": _('Log all emails - note that repetitive writing to an SD card can shorten its lifespan.'),
            "category": _('Logging')
        },
        {
            "key": "run_entriesEM",
            "name": _('Max email entries'),
            "default": 100,
            "help": _('Number of email entries to save to disk, 0=no limit.'),
            "category": _('Logging'),
            "min": 0,
            "max": 1000
        },
        {  
            "key": "run_logEV",
            "name": _('Enable events log'),
            "default": False,
            "help": _('Log all events - note that repetitive writing to an SD card can shorten its lifespan.'),
            "category": _('Logging')
        },
        {
            "key": "run_entriesEV",
            "name": _('Max events entries'),
            "default": 100,
            "help": _('Number of events entries to save to disk, 0=no limit.'),
            "category": _('Logging'),
            "min": 0,
            "max": 1000
        },        
        {
            "key": "run_sensor_entries",
            "name": _('Max sensor entries'),
            "default": 100,
            "help": _('Number of sensor entries to save to disk, 0=no limit.'),
            "category": _('Logging'),
            "min": 0,
            "max": 1000
        },        
        {
            "key": "debug_log",
            "name": _('Enable debug log'),
            "default": False,
            "help": _('Log all internal events (for debugging purposes).'),
            "category": _('Logging')
        },
        #######################################################################
        # Not in Options page as-is ###########################################
        {
            "key": "scheduler_enabled",
            "name": _('Enable scheduler'),
            "default": True,
        },
        {
            "key": "manual_mode",
            "name": _('Manual operation'),
            "default": False,
        },
        {
            "key": "high_resolution_mode",
            "name": _('Image resolution'),
            "default": False,
        },        
        {
            "key": "level_adjustment",
            "name": _('Level adjustment set by the user (fraction)'),
            "default": 1.0,
        },
        {
            "key": "rain_block",
            "name": _('Rain block (rain delay) set by the user (datetime)'),
            "default": datetime(1970, 1, 1),
        },
        {
            "key": "temp_unit",
            "name": _('C/F'),
            "default": 'C',
        },
        {
            "key": "password_hash",
            "name": _('Current password hash'),
            "default": "opendoor",
        },
        {
            "key": "password_salt",
            "name": _('Current password salt'),
            "default": "",
        },
        {
            "key": "password_time",
            "name": _('Current password decryption time'),
            "default": 0,
        },
        {
            "key": "logged_runs",
            "name": _('The runs that have been logged'),
            "default": []
        },
        {
            "key": "logged_email",
            "name": _('The email that have been logged'),
            "default": []
        },
        {
            "key": "logged_events",
            "name": _('The events that have been logged'),
            "default": []
        },        
        {
            "key": "weather_cache",
            "name": _('ETo and rain value cache'),
            "default": {}
        },
        {
            "key": "weather_lat",
            "name": _('Location latitude'),
            "default": {}
        },
        {
            "key": "weather_lon",
            "name": _('Location longtitude'),
            "default": {}
        },
        {
            "key": "weather_status",
            "name": _('Weather status'),
            "default": 0
        },
        {
            "key": "sensor_graph_histories",
            "name": _('Graph histories'),
            "default": 2
        },
        {
            "key": "sensor_graph_show_err",
            "name": _('Show also errors'),
            "default": False,
        },
        {
            "key": "log_filter_server",
            "name": _('Filter for logs - event: server'),
            "default": True,
        },
        {
            "key": "log_filter_rain_sensor",
            "name": _('Filter for logs - event: rain sensor'),
            "default": True,
        },
        {
            "key": "log_filter_rain_delay",
            "name": _('Filter for logs - event: rain delay'),
            "default": False,
        },        
        {
            "key": "log_filter_internet",
            "name": _('Filter for logs - event: internet not found'),
            "default": False,
        }, 
        {
            "key": "log_filter_login",
            "name": _('Filter for logs - event: user login'),
            "default": False,
        },                                           
    ]

    def __init__(self):
        self._values = {}
        self._write_timer = None
        self._callbacks = {}
        self._block = []

        for info in self.OPTIONS:
            self._values[info["key"]] = info["default"]

        for ext in ['', '.tmp', '.bak']:
            try:
                db = shelve.open(OPTIONS_FILE + ext)
                if db.keys():
                    self._values.update(db)
                    db.close()
                    break
                else:
                    db.close()
            except Exception:
                pass

        if not self.password_salt:  # Password is not hashed yet
            from ospy.helpers import password_salt
            from ospy.helpers import password_hash

            self.password_salt = password_salt()
            self.password_hash = password_hash(self.password_hash, self.password_salt)

        if not self.aes_key: # aes key is not created
            from ospy.helpers import now, password_hash
            self.aes_key = password_hash(str(now()), 'notarandomstring')[:16]

    def __del__(self):
        if self._write_timer is not None:
            self._write_timer.cancel()

    def add_callback(self, key, function):
        if key not in self._callbacks:
            self._callbacks[key] = {
                'last_value': getattr(self, key),
                'functions': []
            }

        if function not in self._callbacks[key]['functions']:
            self._callbacks[key]['functions'].append(function)

    def remove_callback(self, key, function):
        if key in self._callbacks:
            if function in self._callbacks[key]['functions']:
                self._callbacks[key]['functions'].remove(function)

    def __str__(self):
        import pprint

        pp = pprint.PrettyPrinter(indent=2)
        return pp.pformat(self._values)

    def __getattr__(self, item):
        if item.startswith('_'):
            result = super(_Options, self).__getattribute__(item)
        else:
            result = self._values[item]
        return result

    def __setattr__(self, key, value):
        if key.startswith('_'):
            super(_Options, self).__setattr__(key, value)
        else:
            self._values[key] = value

            if key in self._callbacks:
                if value != self._callbacks[key]['last_value']:
                    for cb in self._callbacks[key]['functions']:
                        try:
                            cb(key, self._callbacks[key]['last_value'], value)
                        except Exception:
                            logging.error(_('Callback failed') + ': ' + str(traceback.format_exc()))
                    self._callbacks[key]['last_value'] = value

            # Only write after 1 second without any more changes
            if self._write_timer is not None:
                self._write_timer.cancel()
            self._write_timer = Timer(1.0, self._write)
            self._write_timer.start()

    def __delattr__(self, item):
        if item.startswith('_'):
            super(_Options, self).__delattr__(item)
        else:
            del self._values[item]

            # Only write after 1 second without any more changes
            if self._write_timer is not None:
                self._write_timer.cancel()
            self._write_timer = Timer(1.0, self._write)
            self._write_timer.start()

    # Makes it possible to use this class like options[<item>]
    __getitem__ = __getattr__

    # Makes it possible to use this class like options[<item>] = <value>
    __setitem__ = __setattr__

    # Makes it possible to use this class like del options[<item>]
    __delitem__ = __delattr__

    def __contains__(self, item):
        return item in self._values

    def _write(self):
        """This function saves the current data to disk. Use a timer to limit the call rate."""
        try:
            logging.debug(_('Saving options to disk'))
            
            for tmp_file in glob.glob(OPTIONS_GLOB + '.tmp'):
                os.remove(tmp_file)

            if os.path.isfile(OPTIONS_FILE + '.tmp'):
                os.remove(OPTIONS_FILE + '.tmp')
                
            db = shelve.open(OPTIONS_FILE + '.tmp')
            db.clear()
            db.update(self._values)
            db.close()

            if os.path.isfile(OPTIONS_FILE + '.bak') and time.time() - os.path.getmtime(OPTIONS_FILE + '.bak') > 3600\
                    and os.path.isfile(OPTIONS_FILE) and (os.path.getsize(OPTIONS_FILE + '.bak') >= os.path.getsize(OPTIONS_FILE) * 0.9 or
                                                          time.time() - os.path.getmtime(OPTIONS_FILE + '.bak') > 7*3600):
                os.remove(OPTIONS_FILE + '.bak')

            if os.path.isfile(OPTIONS_FILE):
                if not os.path.isfile(OPTIONS_FILE + '.bak'):
                    os.rename(OPTIONS_FILE, OPTIONS_FILE + '.bak')
                else:
                    os.remove(OPTIONS_FILE)

            if os.path.isfile(OPTIONS_FILE + '.tmp'):
                os.rename(OPTIONS_FILE + '.tmp', OPTIONS_FILE)
        except Exception:
            logging.warning(_('Saving error') + ': ' + str(traceback.format_exc()))

    def get_categories(self):
        result = []
        for info in self.OPTIONS:
            if "category" in info and info["category"] not in result:
                result.append(info["category"])
        return result

    def get_options(self, category=None):
        if category is None:
            result = [opt["key"] for opt in self.OPTIONS]
        else:
            result = []
            for info in self.OPTIONS:
                if "category" in info and info["category"] == category:
                    result.append(info["key"])
        return result

    def get_info(self, option):
        return self.OPTIONS[option]

    @staticmethod
    def cls_name(obj, key=""):
        tpy = (obj if isinstance(obj, type) else type(obj))
        return 'Cls_' + tpy.__module__ + '_' + tpy.__name__ + '_' + str(key).replace(' ', '_')

    def load(self, obj, key=""):
        cls = self.cls_name(obj, key)
        self._block.append(cls)
        try:
            values = getattr(self, cls)
            for name, value in values.iteritems():
                setattr(obj, name, value)
        except KeyError:
            pass
        self._block.remove(cls)

    def save(self, obj, key=""):
        cls = self.cls_name(obj, key)
        if cls not in self._block:
            values = {}
            exclude = obj.SAVE_EXCLUDE if hasattr(obj, 'SAVE_EXCLUDE') else []
            for attr in [att for att in dir(obj) if not att.startswith('_') and att not in exclude]:
                if not hasattr(getattr(obj, attr), '__call__'):
                    values[attr] = getattr(obj, attr)

            setattr(self, cls, values)

    def erase(self, obj, key=""):
        cls = self.cls_name(obj, key)
        if hasattr(self, cls):
            delattr(self, cls)

    def available(self, obj, key=""):
        cls = self.cls_name(obj, key)
        return hasattr(self, cls)

options = _Options()


class _LevelAdjustments(dict):
    def __init__(self):
        super(_LevelAdjustments, self).__init__()

    def total_adjustment(self):
        return max(0.0, min(5.0, reduce(lambda x, y: x * y, self.values(), options.level_adjustment)))

level_adjustments = _LevelAdjustments()


class _RainBlocks(dict):
    def __init__(self):
        super(_RainBlocks, self).__init__()

    def block_end(self):
        return max(self.values() + [options.rain_block])

    def seconds_left(self):
        return max(0, (self.block_end() - datetime.now()).total_seconds())

rain_blocks = _RainBlocks()

