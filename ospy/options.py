#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

# System imports
from datetime import datetime, date
from threading import Timer
import logging
import shelve
import shutil
import threading
import copy

from . import i18n
from . import helpers
import traceback
import os
import time
import glob
from functools import reduce

_DATA_DIR = os.environ.get('OSPY_DATA_DIR', './ospy/data')
OPTIONS_FILE = os.path.join(_DATA_DIR, 'default', 'options.db')
OPTIONS_TMP = os.path.join(_DATA_DIR, 'tmp', 'options.db')
OPTIONS_BACKUP = os.path.join(_DATA_DIR, 'backup', 'options.db')
OPTIONS_WRITE_STOP_TIMEOUT = 5.0

class _Options(object):
    # Using an array to preserve order
    OPTIONS = [
        #######################################################################
        # System ##############################################################
        {
            "key": "name",
            "name": _('System name'),
            "default": 'OpenSprinkler Pi 3',
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
            "default": False,
            "help": _('Show data from plugins on home page.'),
            "category": _('System')
        },
        {
            "key": "show_sensor_data",
            "name": _('Show sensors on home'),
            "default": False,
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
            "key": "station_image_source",
            "name": _('Station picture source'),
            "default": "Station images",
            "options": ["Station images", "IP Cam JPG", "IP Cam GIF"],
            "help": _('Choose whether station pictures on the home page use uploaded station images or cached images from the IP Cam plug-in. This is used only when station pictures are enabled.'),
            "category": _('System')
        },
        {
            "key": "show_icons",
            "name": _('Show icons instead of text'),
            "default": True,
            "help": _('When activated, in header menu will display icons instead of text.'),
            "category": _('System')
        },
        {
            "key": "show_scroll_top",
            "name": _('Show back to top button'),
            "default": False,
            "help": _('Show a button for scrolling back to the top of the page after the page is scrolled down.'),
            "category": _('System')
        },
        {
            "key": "scroll_top_position",
            "name": _('Back to top position'),
            "default": "right",
            "options": ["left", "right"],
            "help": _('Choose whether the back to top button is shown at the bottom left or bottom right of the page.'),
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
            "key": "ping_ip",
            "name": _('IP for DNS ping'),
            "default": "8.8.8.8",
            "help": _('IP address for pinging a DNS server that is outside the internal network. If ping is not available, all network operations (log, user downloads, certificates) are skipped.'),
            "category": _('System')
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
            "help": _('Enabling or disabling connection to service Stormglass.io.'),
            "category": _('Weather')
        },
        {
            "key": "stormglass_key",
            "name": _('Storm Glass API key'),
            "default": "",
            "help": _('To make use of local weather conditions, a Storm Glass API key is needed.'),
            "category": _('Weather')
        },
        {
            "key": "location",
            "name": _('Location'),
            "default": '',
            "help": _('City name or zip code. Used to determine location via OpenStreetMap for weather information.'),
            "category": _('Weather')
        },
        {
            "key": "weather_location_mode",
            "name": _('Weather location mode'),
            "default": "search"
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
        {
            "key": "two_factor_method",
            "name": _('Two-factor authentication method'),
            "default": "none"
        },
        {
            "key": "two_factor_secret",
            "name": _('Two-factor authentication secret'),
            "default": ""
        },
        {
            "key": "two_factor_backup_codes",
            "name": _('Two-factor backup codes'),
            "default": []
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
        {
            "key": "api_cors_allowed_origin",
            "name": _('API CORS allowed origin'),
            "default": "*",
            "help": _('Allowed browser origin for API CORS requests. Use * to allow any origin, enter one origin such as https://example.com, enter multiple origins separated by commas, or leave empty to disable CORS headers. This affects browser-based API clients only.'),
            "category": _('Security')
        },
        {
            "key": "api_jsonp_enabled",
            "name": _('Enable API JSONP'),
            "default": False,
            "help": _('Allow legacy API JSONP responses via the callback query parameter. Keep disabled unless an old integration requires JSONP, because normal API clients should use JSON with CORS instead.'),
            "category": _('Security')
        },
        {
            "key": "api_sensor_auth_required",
            "name": _('Require sensor API auth'),
            "default": False,
            "help": _('Require HTTP Basic authentication for sensor reports sent to /api/sensor. Keep disabled for older sensor firmware that cannot send credentials.'),
            "category": _('Security')
        },
        {
            "key": "api_csrf_required",
            "name": _('Require API CSRF token'),
            "default": False,
            "help": _('Require a CSRF token for state-changing API requests. Keep disabled for older integrations that use only HTTP Basic authentication.'),
            "category": _('Security')
        },
        {
            "key": "max_upload_size_mb",
            "name": _('Maximum upload size'),
            "default": 25,
            "help": _('Maximum uploaded file size in MB for backup restore, SSL files, station images, and custom sensor firmware. Use 0 for no application limit.'),
            "category": _('Security'),
            "min": 0,
            "max": 2048
        },
        #######################################################################
        # Sensors ############################################################# 
        {
            "key": "sensor_fw_passwd",
            "name": _('Password FW'),
            "default": "fg4s5b.s,trr7sw8sgyvrDfg",
            "help": _('Password for uploading firmware from OSPy to sensor (for all used sensors - the same password must be used in sensor options.)'),
            "category": _('Sensors')
        },
        {
            "key": "sensor_http_timeout",
            "name": _('Sensor HTTP timeout'),
            "default": 10,
            "help": _('Timeout in seconds for HTTP requests sent from OSPy to sensors.'),
            "category": _('Sensors'),
            "min": 1,
            "max": 120
        },
        #######################################################################
        # Station Handling ####################################################
        {
            "key": "max_usage",
            "name": _('Maximum usage'),
            "default": 1.0,
            "help": _('Determines how station runs are combined. 0 means no limit. 1 means one station at a time when each station has usage 1. This also affects when the pause between stations is inserted.'),
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
            "name": _('Pause between stations'),
            "default": 0,
            "help": _('Pause inserted between sequential station runs when the scheduler cannot run them at the same time, in seconds between 0 and 3600. This does not shift a station against the master station. Example: with maximum usage 1 and station usage 1, value 30 starts the next station 30 seconds after the previous station ends.'),
            "category": _('Station Handling'),
            "min": 0,
            "max": 3600
        },
        {
            "key": "min_runtime",
            "name": _('Minimum runtime'),
            "default": 0,
            "help": _('Skip the pause between stations when the previous run was shorter than this value, in seconds between 0 and 86400. Example: with pause 30 and minimum runtime 10, a station that ran only 5 seconds will not force the 30 second pause.'),
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
            "name": _('Master start offset'),
            "default": 0,
            "help": _('Time offset for starting master station 1 relative to the station start, in seconds between -1800 and +1800. Negative values start the master earlier; positive values start it later. Example: -10 starts the master 10 seconds before the station, +10 starts it 10 seconds after the station.'),
            "category": _('Configure Master'),
            "min": -1800,
            "max": +1800
        },
        {
            "key": "master_off_delay",
            "name": _('Master stop offset'),
            "default": 0,
            "help": _('Time offset for stopping master station 1 relative to the station end, in seconds between -1800 and +1800. Negative values stop the master earlier; positive values keep it running longer. Example: -5 stops the master 5 seconds before the station ends, +20 stops it 20 seconds after the station ends.'),
            "category": _('Configure Master'),
            "min": -1800,
            "max": +1800
        },
        {
            "key": "master_on_delay_two",
            "name": _('Master two start offset'),
            "default": 0,
            "help": _('Time offset for starting master station 2 relative to the station start, in seconds between -1800 and +1800. Negative values start the master earlier; positive values start it later. Example: -10 starts master 2 10 seconds before the station, +10 starts it 10 seconds after the station.'),
            "category": _('Configure Master'),
            "min": -1800,
            "max": +1800
        },
        {
            "key": "master_off_delay_two",
            "name": _('Master two stop offset'),
            "default": 0,
            "help": _('Time offset for stopping master station 2 relative to the station end, in seconds between -1800 and +1800. Negative values stop the master earlier; positive values keep it running longer. Example: -5 stops master 2 5 seconds before the station ends, +20 stops it 20 seconds after the station ends.'),
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
        {
            "key": "rain_set_delay",
            "name": _('Set rain delay'),
            "default": False,
            "help": _('When the rain sensor is activated, the rain delay is set (this is suitable, for example, for blocking programs for a longer time than provided by the rain sensor).'),
            "category": _('Rain Sensor')
        },
        {
            "key": "rain_sensor_delay",
            "name": _('Rain delay time'),
            "default": 48,
            "help": _('Rain delay time (in hours), between 0 and 500.'),
            "category": _('Rain Sensor'),
            "min": 0,
            "max": 500
        },
        #######################################################################
        # Diagnostics #########################################################
        {
            "key": "show_diagnostics_modal_home",
            "name": _('Show diagnostic errors on the home page'),
            "default": True,
            "help": _('Show a red diagnostic error window to administrators on the home page. Diagnostic errors have priority over update notifications.'),
            "category": _('Diagnostics')
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
        {
            "key": "web_log",
            "name": _('Enable web log'),
            "default": False,
            "help": _('Logging of internal events from the web server (for debugging it is necessary to enable the debug log and then restart OSPy). Deteriorates page loading speed.'),
            "category": _('Logging')
        },
        #######################################################################
        # Hardware ############################################################
        {
            "key": "shift_register_speed",
            "name": _('Shift register speed'),
            "default": False,
            "help": _('This setting controls the clock speed for the shift register (74HC595) that controls the output relay. In some cases, it is advisable to reduce the speed to 10us. If the checkbox is not selected, the default speed is used. Otherwise, the speed will be reduced. (If you have no problems with timing, ignore this option.) False = maximum, clock according to the system (typically 0.5–2 MHz). True = approx. 100 kHz (safe for 74HC595 even with longer cables). Commonly recommended safe speed: around 50–200 kHz, i.e. approximately 5–20 µs delay between clock pulses.'),
            "category": _('Hardware')
        },        
        #######################################################################
        # Not in Options page as-is ###########################################
        {
            "key": "first_password_hash",
            "name": _('New installation generated password hash'),
            "default": "",
        }, 
        {
            "key": "first_installation",
            "name": _('New installation'),
            "default": True,
        },        
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
            "key": "plugin_rain_blocks",
            "name": _('Rain blocks (rain delays) set by plug-ins (datetime dictionary)'),
            "default": {},
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
            "default": ""
        },
        {
            "key": "weather_lon",
            "name": _('Location longtitude'),
            "default": ""
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
            "default": True,
        },        
        {
            "key": "log_filter_internet",
            "name": _('Filter for logs - event: internet not found'),
            "default": False,
        }, 
        {
            "key": "log_filter_login",
            "name": _('Filter for logs - event: user login'),
            "default": True,
        },
        {
            "key": "last_save",
            "name": _('Timestamp of the last database save'),
            "default": time.time()
        }                                                   
    ]

    def __init__(self):
        self._values = {}
        self._write_timer = None
        self._callbacks = {}
        self._block = []
        self._lock = threading.RLock()
        self._load_source = None
        self._load_errors = []

        for info in self.OPTIONS:
            self._values[info["key"]] = copy.deepcopy(info["default"])

        # UPGRADE from v2 (does not delete old files):
        if not os.path.isdir(os.path.dirname(OPTIONS_FILE)):
            helpers.mkdir_p(os.path.dirname(OPTIONS_FILE))
            for old_options in ['./ospy/data/options.db', './ospy/data/options.db.dat', './ospy/data/options.db.bak', './ospy/data/options.db.tmp']:
                if os.path.isfile(old_options):
                    shutil.copy(old_options, OPTIONS_FILE)
                    break

        for options_file in [OPTIONS_FILE, OPTIONS_TMP, OPTIONS_BACKUP]:
            try:
                if (os.path.isdir(os.path.dirname(options_file)) and
                        glob.glob(options_file + '*')):
                    loaded = self._read_candidate(options_file)
                    if loaded:
                        self._values.update(loaded)
                        self._load_source = options_file
                        break
            except Exception as err:
                self._load_errors.append((options_file, str(err)))

        if self._load_errors:
            for failed_path, error in self._load_errors:
                logging.warning(
                    _('Ignoring invalid settings database {}: {}').format(
                        failed_path, error
                    )
                )
        if self._load_source and self._load_source != OPTIONS_FILE:
            logging.warning(
                _('Settings were recovered from {}.').format(self._load_source)
            )

        for coordinate_key in ('weather_lat', 'weather_lon'):
            coordinate = self._values.get(coordinate_key, '')
            if isinstance(coordinate, (int, float)) and not isinstance(coordinate, bool):
                self._values[coordinate_key] = str(coordinate)
            elif not isinstance(coordinate, str):
                self._values[coordinate_key] = ''

        self._values.pop('auto_login_key', None)

        try:
            if not self.first_password_hash:                                                     # First default installation password is not hashed yet
                import secrets
                self.first_password_hash = secrets.token_hex(8)

            if not self.password_salt and self.password_hash == 'opendoor':                      # Password is not hashed yet
                from ospy.helpers import password_salt, password_hash
                self.password_salt = password_salt()
                self.password_hash = password_hash(self.first_password_hash, self.password_salt) # Set password hash for "admin"
                self.admin_user = 'admin'                                                        # Set user name to "admin" 
            else:
                if self.password_hash != 'opendoor':                                             # Installation is old and has changed password (is not opendoor)
                    if self.first_installation:
                        self.first_installation = False
        except:
            helpres.print_report('options.py', traceback.format_exc())

    @staticmethod
    def _compatible_value(default, value, key=''):
        if key in ('weather_lat', 'weather_lon'):
            return isinstance(value, (str, int, float)) and not isinstance(value, bool)
        if key == 'ip_address':
            if not isinstance(value, (list, tuple)) or len(value) != 4:
                return False
            try:
                return all(
                    not isinstance(part, bool) and
                    isinstance(part, (str, int)) and
                    (not isinstance(part, str) or part.isdigit()) and
                    0 <= int(part) <= 255
                    for part in value
                )
            except (TypeError, ValueError):
                return False
        if key == 'reg_output':
            return (
                isinstance(value, int) and not isinstance(value, bool)
            ) or (
                isinstance(value, str) and value.lstrip('-').isdigit()
            )
        # Historic and current OSPy code legitimately stores these object
        # fields with more than one primitive type. They are configuration or
        # last-observation values, not arbitrary objects. Accept their real
        # runtime representations while keeping strict validation elsewhere.
        if key in ('enabled', 'fixed'):
            return isinstance(value, bool) or (
                isinstance(value, int) and not isinstance(value, bool) and
                value in (0, 1)
            )
        if key == 'fw':
            return (
                isinstance(value, int) and not isinstance(value, bool)
            ) or (
                isinstance(value, str) and value.isdigit()
            )
        if key == 'last_response':
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if key in ('last_battery', 'rssi'):
            return isinstance(value, (str, int, float)) and not isinstance(value, bool)
        if key == 'prev_read_value':
            if isinstance(value, (str, int, float, bool)):
                return True
            if isinstance(value, list):
                return all(
                    isinstance(item, (str, int, float, bool))
                    for item in value
                )
            return False
        if isinstance(default, bool):
            return isinstance(value, bool)
        if isinstance(default, int) and not isinstance(default, bool):
            return isinstance(value, int) and not isinstance(value, bool)
        if isinstance(default, float):
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if isinstance(default, datetime):
            return isinstance(value, datetime)
        if isinstance(default, date):
            return isinstance(value, date)
        if default is None:
            return value is None or (isinstance(value, int) and not isinstance(value, bool))
        return isinstance(value, type(default))

    def _validate_candidate(self, values):
        if not isinstance(values, dict):
            raise ValueError(_('Settings database does not contain a dictionary.'))

        definitions = {item['key']: item for item in self.OPTIONS}
        startup_bounds = {
            'web_port': (1, 65535),
            'output_count': (1, 4096),
            'max_upload_size_mb': (0, 10240),
        }
        for key, value in values.items():
            if key.startswith('Cls_'):
                if not isinstance(value, dict):
                    raise ValueError(
                        _('Stored object {} is not a dictionary.').format(key)
                    )
                continue
            definition = definitions.get(key)
            if definition is None:
                continue
            default = definition['default']
            if not self._compatible_value(default, value, key):
                raise ValueError(
                    _('Invalid value type for setting {}.').format(key)
                )
            if key in startup_bounds:
                minimum, maximum = startup_bounds[key]
                if value < minimum:
                    raise ValueError(
                        _('Setting {} is below its minimum.').format(key)
                    )
                if value > maximum:
                    raise ValueError(
                        _('Setting {} is above its maximum.').format(key)
                    )
        return values

    def _read_candidate(self, options_file):
        db = None
        try:
            db = shelve.open(options_file, flag='r')
            keys = list(db.keys())
            if not keys:
                return None
            raw = {key: db[key] for key in keys}
            converted = self._convert_str_to_datetime(raw)
            return self._validate_candidate(converted)
        finally:
            if db is not None:
                db.close()

    def recovery_messages(self):
        """Return user-facing descriptions of settings recovery at startup."""
        messages = [
            _('Ignored invalid settings database {}: {}').format(path, error)
            for path, error in self._load_errors
        ]
        if self._load_source and self._load_source != OPTIONS_FILE:
            messages.append(
                _('Settings were recovered from {}.').format(self._load_source)
            )
        if self._load_errors and self._load_source is None:
            messages.append(
                _('No valid settings database was found; safe defaults are being used.')
            )
        return messages


    def __del__(self):
        self.cancel_pending_write()

    def cancel_pending_write(self, timeout=OPTIONS_WRITE_STOP_TIMEOUT):
        """Cancel and drain the delayed writer without starting a new write."""
        lock = getattr(self, '_lock', None)
        if lock is None:
            return True

        timer = None
        with lock:
            timer = self._write_timer
            self._write_timer = None
            if timer is not None:
                timer.cancel()

        # cancel() cannot stop a Timer whose callback has already begun. Wait
        # until that callback leaves _write() before its directory is cleaned.
        if (timer is not None and timer is not threading.current_thread() and
                timer.is_alive()):
            timer.join(max(0.0, float(timeout)))
        return timer is None or not timer.is_alive()

    def flush(self):
        """Persist pending option changes synchronously during shutdown."""
        if not self.cancel_pending_write():
            return False
        self._write()
        return True

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
        elif item not in self._values:
            raise AttributeError
        else:
            result = self._values[item]
        return result

    def __setattr__(self, key, value):
        if key.startswith('_'):
            super(_Options, self).__setattr__(key, value)
        else:
            with self._lock:
                self._values[key] = value

                if key in self._callbacks:
                    if value != self._callbacks[key]['last_value']:
                        for cb in self._callbacks[key]['functions']:
                            try:
                                cb(key, self._callbacks[key]['last_value'], value)
                            except Exception:
                                logging.error('Callback failed:\n' + traceback.format_exc())
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
            with self._lock:
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

    def _convert_datetime_to_str(self, inp):
        if isinstance(inp, dict):
            result = {}
            for k in inp:
                result[self._convert_datetime_to_str(k)] = self._convert_datetime_to_str(inp[k])
        elif isinstance(inp, list):
            result = []
            for v in inp:
                result.append(self._convert_datetime_to_str(v))
        elif isinstance(inp, datetime):
            result = 'DATETIME:' + inp.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(inp, date):
            result = 'DATE:' + inp.strftime('%Y-%m-%d')
        else:
            result = inp
        return result

    def _convert_str_to_datetime(self, inp):
        if isinstance(inp, dict) or isinstance(inp, shelve.Shelf):
            result = {}
            for k in inp:
                result[self._convert_str_to_datetime(k)] = self._convert_str_to_datetime(inp[k])
        elif isinstance(inp, list):
            result = []
            for v in inp:
                result.append(self._convert_str_to_datetime(v))
        elif isinstance(inp, str) and inp.startswith('DATETIME:'):
            result = datetime.strptime(inp[9:], '%Y-%m-%d %H:%M:%S')
        elif isinstance(inp, str) and inp.startswith('DATE:'):
            result = datetime.strptime(inp[5:15], '%Y-%m-%d').date()
        else:
            result = inp
        return result

    def _write(self):
        """This function saves the current data to disk. Use a timer to limit the call rate."""
        try:
            with self._lock:
                logging.debug(_('Saving options to disk'))

                options_dir = os.path.dirname(OPTIONS_FILE)
                tmp_dir = os.path.dirname(OPTIONS_TMP)
                backup_dir = os.path.dirname(OPTIONS_BACKUP)

                if os.path.isdir(tmp_dir):
                    shutil.rmtree(tmp_dir)
                helpers.mkdir_p(tmp_dir)

                from dbm.dumb import open as dumb_open

                db = shelve.Shelf(dumb_open(OPTIONS_TMP))
                db.clear()
                db.update(self._values)

                db['last_save'] = time.time()
                db.close()

                remove_backup = True
                try:
                    db = shelve.open(OPTIONS_BACKUP)
                    if time.time() - db['last_save'] < 3600:
                        remove_backup = False
                    else:
                        logging.debug(_('Files in OPTIONS_BACKUP are older than 1 hour.'))   
                    db.close()
                except Exception:
                    pass
                del db

                if os.path.isdir(backup_dir) and remove_backup:
                    for i in range(10):
                        try:
                            logging.debug(_('I will try to delete the BACKUP_DIR.'))
                            shutil.rmtree(backup_dir)
                            break
                        except Exception:
                            time.sleep(0.2)
                    else:
                        logging.debug(_('I will try deleting directory BACKUP_DIR.'))
                        shutil.rmtree(backup_dir)

                if os.path.isdir(options_dir):
                    if not os.path.isdir(backup_dir):
                        logging.debug(_('I will try moving directory OPTIONS_DIR to BACKUP_DIR.'))
                        shutil.move(options_dir, backup_dir)
                    else:
                        for i in range(10):
                            try:
                                logging.debug(_('I will try to delete the OPTIONS_DIR.'))
                                shutil.rmtree(options_dir)
                                break
                            except Exception:
                                time.sleep(0.2)
                        else:
                            logging.debug(_('I will try deleting directory OPTIONS_DIR.'))
                            shutil.rmtree(options_dir)

                logging.debug(_('I will try moving directory TMP_DIR to OPTIONS_DIR.'))
                shutil.move(tmp_dir, options_dir)

                from dbm import whichdb

                logging.debug(_('Saved db as %s'), whichdb(OPTIONS_FILE))
                from ospy.health import heartbeat
                heartbeat(
                    'database',
                    backend=whichdb(OPTIONS_FILE) or '',
                    path=os.path.abspath(OPTIONS_FILE)
                )
        except Exception:
            error = traceback.format_exc()
            try:
                from ospy.health import heartbeat
                heartbeat('database', ok=False, message=error,
                          path=os.path.abspath(OPTIONS_FILE))
            except Exception:
                pass
            logging.warning(_('Saving error:\n') + error)

    def save_now(self):
        """Write pending option changes immediately."""
        if self._write_timer is not None:
            self._write_timer.cancel()
            self._write_timer = None
        self._write()

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
            if not isinstance(values, dict):
                raise ValueError(_('Stored object data is not a dictionary.'))
            for name, value in values.items():
                if name.startswith('_') or not hasattr(obj, name):
                    continue
                try:
                    current = getattr(obj, name)
                    if not self._compatible_value(current, value, name):
                        raise ValueError(
                            _('Stored value has an incompatible type.')
                        )
                    setattr(obj, name, value)
                except Exception as err:
                    logging.warning(
                        _('Ignoring invalid stored field {}.{}: {}').format(
                            cls, name, err
                        )
                    )
        except AttributeError:
            pass
        except Exception as err:
            logging.warning(
                _('Ignoring invalid stored object {}: {}').format(cls, err)
            )
        finally:
            if cls in self._block:
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
        return max(0.0, min(5.0, reduce(lambda x, y: x * y, list(self.values()), options.level_adjustment)))

level_adjustments = _LevelAdjustments()


class _RainBlocks(dict):
    def __init__(self):
        super(_RainBlocks, self).__init__()
        now = datetime.now()
        for name, end in options.plugin_rain_blocks.items():
            if isinstance(end, datetime) and end > now:
                super(_RainBlocks, self).__setitem__(name, end)
        if dict(self) != options.plugin_rain_blocks:
            self._persist()

    def _persist(self):
        options.plugin_rain_blocks = dict(self)
        options.save_now()

    def __setitem__(self, key, value):
        super(_RainBlocks, self).__setitem__(key, value)
        self._persist()

    def __delitem__(self, key):
        super(_RainBlocks, self).__delitem__(key)
        self._persist()

    def clear(self):
        super(_RainBlocks, self).clear()
        self._persist()

    _POP_SENTINEL = object()

    def pop(self, key, default=_POP_SENTINEL):
        if default is self._POP_SENTINEL:
            result = super(_RainBlocks, self).pop(key)
        else:
            result = super(_RainBlocks, self).pop(key, default)
        self._persist()
        return result

    def update(self, *args, **kwargs):
        super(_RainBlocks, self).update(*args, **kwargs)
        self._persist()

    def block_end(self):
        return max(list(self.values()) + [options.rain_block])

    def seconds_left(self):
        return max(0, (self.block_end() - datetime.now()).total_seconds())

rain_blocks = _RainBlocks()


class _ProgramLevelAdjustments(dict):
    def __init__(self):
        super(_ProgramLevelAdjustments, self).__init__()

program_level_adjustments = _ProgramLevelAdjustments()
