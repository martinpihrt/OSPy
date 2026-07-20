#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

# System imports
import os
from shutil import copyfile
import datetime
import time
import json
import web
from threading import Event, Thread, Timer, RLock, current_thread
import traceback
import mimetypes
import shutil
import html

# Local imports
from ospy.helpers import test_password, template_globals, check_login, save_to_options, \
    password_hash, password_salt, get_input, get_help_files, get_help_file, restart, reboot, poweroff, stop_onrain, \
    verify_csrf, read_limited_upload, safe_image_path, datetime_string
from ospy.inputs import inputs
from ospy.log import log, logEM, logEV
from ospy.options import options, rain_blocks, program_level_adjustments
from ospy.programs import programs, ProgramType
from ospy.runonce import run_once
from ospy.stations import stations
from ospy.outputs import outputs
from ospy import scheduler
from ospy import autologin
from ospy import twofactor
from ospy import health
from ospy import backup as system_backup
import plugins
from blinker import signal
from ospy.users import users
from ospy.sensors import sensors, sensors_timer

from urllib.request import urlopen
from urllib.parse import quote_plus, urlencode

try:
    import requests
except ImportError:
    log.error('webpages.py', _('Requests not found on system!'))
    log.error('webpages.py', output)


plugin_data = {}    # Empty dictionary to hold plugin based global data
pluginFtr = []      # Empty list of dicts to hold plugin data for display in footer
pluginStn = []      # Empty list of dicts to hold plugin data for display on timeline
pluginScripts = []  # Empty list of script file names for script injections requested by plugins
sensorSearch = []   # Empty list of dicts to hold sensors data for display on sensor search page
_diagnostics_process_sample = {}
_diagnostics_plugin_history = {}
_diagnostics_history_lock = RLock()
_diagnostics_history_stop = Event()
_diagnostics_history_thread = None
_DIAGNOSTICS_HISTORY_SECONDS = 7 * 24 * 60 * 60
_DIAGNOSTICS_HISTORY_POINTS = 1200
_DIAGNOSTICS_HISTORY_SAMPLE_SECONDS = 60
GITHUB_NEW_ISSUE_URL = 'https://github.com/martinpihrt/OSPy/issues/new'
FEEDBACK_TITLE_LIMIT = 120
FEEDBACK_DESCRIPTION_LIMIT = 4000
_security_event_times = {}


def _save_security_failure(key, subject, status):
    """Limit repeated unauthenticated events so they cannot flood persistent storage."""
    current_time = time.time()
    if current_time - _security_event_times.get(key, 0) < 60:
        return
    _security_event_times[key] = current_time
    if len(_security_event_times) > 500:
        stale = [item for item, saved in _security_event_times.items()
                 if current_time - saved > 3600]
        for item in stale:
            del _security_event_times[item]
    logEV.save_events_log(
        subject,
        status,
        id='Login',
        level='warning',
        category='security'
    )


def _feedback_system_information():
    from ospy import usagestats, version

    info = [
        ('OSPy version', '{} ({})'.format(version.ver_str, version.ver_date)),
    ]
    info.extend(usagestats.system_information())
    return [(str(key), str(value or '-')) for key, value in info]


def _safe_extract_zip(zip_file, target_dir):
    """Extract a ZIP archive without allowing paths outside target_dir."""
    import shutil

    target_dir = os.path.abspath(target_dir)
    target_check = os.path.normcase(target_dir)
    members = []

    for member in zip_file.infolist():
        member_name = member.filename.replace('\\', '/')
        normalized_name = os.path.normpath(member_name)

        if (
            not member_name or
            normalized_name in ('', '.') or
            os.path.isabs(member_name) or
            os.path.splitdrive(member_name)[0] or
            normalized_name == '..' or
            normalized_name.startswith('..' + os.sep)
        ):
            raise ValueError(_('Unsafe path in uploaded ZIP file: {}').format(member.filename))

        destination = os.path.abspath(os.path.join(target_dir, normalized_name))
        destination_check = os.path.normcase(destination)
        if os.path.commonpath([target_check, destination_check]) != target_check:
            raise ValueError(_('Unsafe path in uploaded ZIP file: {}').format(member.filename))

        members.append((member, destination))

    for member, destination in members:
        if member.is_dir():
            os.makedirs(destination, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            with zip_file.open(member) as source, open(destination, 'wb') as target:
                shutil.copyfileobj(source, target)


def _plugin_module_from_stack():
    try:
        plugins_dir = os.path.dirname(os.path.abspath(plugins.__file__))
        for tb in reversed(traceback.extract_stack()):
            tb_dir = os.path.dirname(os.path.abspath(tb[0]))
            if tb_dir.startswith(plugins_dir) and tb_dir != plugins_dir:
                parts = tb_dir[len(plugins_dir):].split(os.path.sep)
                while parts and not parts[0]:
                    del parts[0]
                if parts:
                    return parts[0]
    except Exception:
        log.debug('webpages.py', traceback.format_exc())
    return None


def clear_plugin_runtime_data(module):
    global pluginFtr
    pluginFtr = [entry for entry in pluginFtr if entry.get("plugin") != module]

    for entry in pluginStn:
        if len(entry) >= 3 and entry[2] == module:
            del entry[:]


def _format_display_datetime(value):
    if isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, str):
        if value.endswith('Z') and 'T' in value:
            return value[:-1].replace('T', ' ') + ' UTC'
        return value
    return value


loggedin = signal('loggedin')
def report_login():
    loggedin.send()

value_change = signal('value_change')
def report_value_change():
    value_change.send()

option_change = signal('option_change')
def report_option_change():
    option_change.send()

rebooted = signal('rebooted')
def report_rebooted():
    rebooted.send()

restarted = signal('restarted')
def report_restarted():
    restarted.send()

station_names = signal('station_names')
def report_station_names():
    station_names.send()

program_change = signal('program_change')
def report_program_change():
    program_change.send()

program_deleted = signal('program_deleted')
def report_program_deleted():
    program_deleted.send()

program_toggled = signal('program_toggled')
def report_program_toggle():
    program_toggled.send()

program_runnow = signal('program_runnow')
def report_program_runnow():
    program_runnow.send()

reppoweroff = signal('poweroff')
def report_poweroff():
    reppoweroff.send()


from web import form

signin_form = form.Form(
    form.Textbox('username', description=_('Username:')),
    form.Password('password', description=_('Password:'))
)


class InstantCacheRender(web.template.render):
    '''This class immediately starts caching all templates in the given location.'''
    def __init__(self, loc='templates', cache=None, base=None, limit=None, exclude=None, **keywords):
        web.template.render.__init__(self, loc, cache, base, **keywords)

        self._limit = limit
        self._exclude = exclude

        from threading import Thread
        t = Thread(target=self._fill_cache)
        t.daemon = True
        t.start()

    def _fill_cache(self):
        import time
        if os.path.isdir(self._loc):
            for name in os.listdir(self._loc):
                if name.endswith('.html') and \
                        (self._limit is None or name[:-5] in self._limit) and \
                        (self._exclude is None or name[:-5] not in self._exclude):
                    self._template(name[:-5])
                    time.sleep(0.1)


class WebPage(object):
    base_render = InstantCacheRender(os.path.join('ospy', 'templates'),
                                     globals=template_globals(), limit=['base']).base
    core_render = InstantCacheRender(os.path.join('ospy', 'templates'),
                                     globals=template_globals(), exclude=['base'], base=base_render)

    def __init__(self):
        cls = self.__class__

        from ospy.server import session

        try:
            # Check that the session is not None and has the 'pages' attribute
            if session is None:
                log.error('webpages.py', _('Session is not initialized.'))
                raise ValueError(_('Session is not initialized.'))

            if not hasattr(session, 'pages'):
                session.pages = []
            # Add current path to session.pages if conditions apply
            if not cls.__name__.endswith('json') and (not session.pages or session.pages[-1] != web.ctx.fullpath):
                session.pages.append(web.ctx.fullpath)

            # Keep session.pages size to a maximum of 20 items
            while len(session.pages) > 20:
                del session.pages[0]
                log.debug('webpages.py', _('Session.pages size is >20, deleting.'))

        except Exception:
            # If an error occurs, record it and restart the software
            log.error('webpages.py', traceback.format_exc())
            # OSPy software restart
            restart()

        # Plugins - add plugin_render if the module starts with 'plugins' and the class does not have it defined
        if self.__module__.startswith('plugins') and 'plugin_render' not in cls.__dict__:
            cls.plugin_render = InstantCacheRender(
                os.path.join(os.path.join(*self.__module__.split('.')), 'templates'),
                globals=template_globals(), base=self.base_render
            )


    @staticmethod
    def _redirect_back():
        from ospy.server import session
        if not hasattr(session, 'pages'):
            session.pages = []
        for page in reversed(session.pages):
            if page != web.ctx.fullpath:
                raise web.seeother(page)
        raise web.seeother('/')


class ProtectedPage(WebPage):
    def __init__(self):
        WebPage.__init__(self)
        try:
            check_login(True)
            if web.ctx.method == 'POST' and (
                self.__module__ == 'ospy.webpages' or self.__module__.startswith('plugins.')
            ):
                verify_csrf()
        except web.seeother:
            raise

class sensors_firmware(ProtectedPage):
    """Open page to allow sensor firmware modification. /firmware """
    def GET(self):
        from ospy.server import session

        qdict = web.input()
        statusCode = qdict.get('statusCode', 'None')

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        return self.core_render.sensors_firmware(statusCode)

    def _send_firmware(self, index, statusCode):
        sensor = sensors.get(index)

        last_fw_number = None
        last_fw_name = None
        last_fw_path = None

        if sensor.cpu_core == 0:
            esp32_folder_fw = os.path.join('.', 'hardware_pcb', 'sensors_pcb_fw', 'ESP32' , 'firmware')
            entries_32 = os.listdir(esp32_folder_fw)
            last_fw_32 = 0
            for i in entries_32:
                val_32 = int(i[:-4])
                if last_fw_32 < val_32:
                    last_fw_32 = val_32
                    last_fw_name = i
            last_fw_number = last_fw_32
            last_fw_path =  os.path.join(esp32_folder_fw, last_fw_name)                # ex: hardware_pcb/sensors_pcb_fw/ESP32/firmware/105.bin
        elif sensor.cpu_core == 1:
            esp8266_folder_fw = os.path.join('.', 'hardware_pcb', 'sensors_pcb_fw', 'ESP8266' , 'firmware')
            entries_8266 = os.listdir(esp8266_folder_fw)
            last_fw_8266 = 0
            for i in entries_8266:
                val_8266 = int(i[:-4])
                if last_fw_8266 < val_8266:
                    last_fw_8266 = val_8266
                    last_fw_name = i
            last_fw_number = last_fw_8266
            last_fw_path =  os.path.join(esp8266_folder_fw, last_fw_name)
        else:
            last_fw_number = None
            last_fw_name = None
            last_fw_path = None

        try:
            send_ip = '.'.join(sensor.ip_address)
            send_url = 'http://' + send_ip + '/FW_' + options.sensor_fw_passwd       # ex: http://192.168.88.207/FW_0123456789abcdef
            if last_fw_path is None:
                statusCode = 'err1'                                                  # msg = No xxx.bin file was found in the directory to send to the sensor!
                return statusCode
            try:
                with open(last_fw_path, 'rb') as file:
                    response = requests.post(send_url, files={last_fw_name: file}, timeout=options.sensor_http_timeout)
                resp_code = response.status_code
                log.debug('webpages.py', resp_code)
                if resp_code == 200:
                    statusCode = 'upl_ok'                                            # msg = The new firmware file has been sent to the sensor, wait for the sensor to respond - check if the sensor has been updated.
                elif resp_code == 404:
                    statusCode = 'err3'                                              # msg = The new firmware could not be uploaded into the sensor. Response - Not Found!
                else:
                    statusCode = 'err4'                                              # msg = The new firmware could not be uploaded into the sensor. An error has occurred!
            except:
                pass
                statusCode = 'err2'                                                  # msg = The new firmware could not be uploaded into the sensor. Sensor does not respond!

        except Exception:
            pass
            log.debug('webpages.py', traceback.format_exc())
            statusCode = 'err2'                                                      # msg = The new firmware could not be uploaded into the sensor. Sensor does not respond!

        return statusCode

    def _start_sensor_ap(self, index, statusCode):
        sensor = sensors.get(index)
        try:
            send_ip = '.'.join(sensor.ip_address)
            send_url = 'http://' + send_ip + '/AP_' + options.sensor_fw_passwd   # ex: http://192.168.88.207/AP_0123456789abcdef
            response = requests.post(send_url, timeout=options.sensor_http_timeout)
            resp_code = response.status_code
            log.debug('webpages.py', resp_code)
            if resp_code == 200:
                statusCode = 'ap_ok'                                            # msg = The sensor responded and probably started the AP manager
            elif resp_code == 404:
                statusCode = 'err5'                                             # msg = It was not processed, the command does not exist in the sensor. Do you have the latest FW version of the sensor?
            else:
                statusCode = 'err6'                                             # msg = An error, the sensor did not respond correctly!
        except Exception:
            statusCode = 'err7'                                                 # msg = Sensor does not respond!
        return statusCode

    def POST(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        statusCode = qdict.get('statusCode', 'None')
        action = qdict.get('action', '')

        if action == 'start_ap':
            statusCode = self._start_sensor_ap(int(qdict.get('index', -1)), statusCode)
            return self.core_render.sensors_firmware(statusCode)

        if action == 'firmware_update':
            statusCode = self._send_firmware(int(qdict.get('index', -1)), statusCode)
            return self.core_render.sensors_firmware(statusCode)

        cid = get_input(qdict, 'cid', False, lambda x: True)                         # cid=1 is custom form file uploading

        if 'ip_address' and 'port' and 'pass' in qdict and cid:
            ip = qdict['ip_address']
            port = qdict['port']
            pwd = qdict['pass']
            if ip =='' or port == '' or pwd == '':
                statusCode = qdict.get('statusCode', 'err9')                         # msg = IP or port or password is not inserted!
                return self.core_render.sensors_firmware(statusCode)

            protocol = None
            if 'protocol' in qdict:
                protocol = qdict['protocol']                                         # 0=http, 1=https
            if 'uploadfile' in qdict:
                i = web.input(uploadfile={})
                #web.debug(i['uploadfile'].filename)    # This is the filename
                #web.debug(i['uploadfile'].value)       # This is the file contents
                #web.debug(i['uploadfile'].file.read()) # Or use a file(-like) object
                upload_type = i.uploadfile.filename[-4:len(i.uploadfile.filename)]   # only .bin and hex file accepted
                types = ['.hex','.bin']
                if upload_type not in types:                                         # check file type is not ok
                    statusCode = qdict.get('statusCode', 'err8')                     # msg = Accepted is only *.hex or *.bin files!
                    return self.core_render.sensors_firmware(statusCode)
                fw_path = None
                fw_name = None

                if upload_type == '.bin':
                    fw_path = './ospy/data/userfw.bin'
                    fw_name = 'userfw.bin'
                elif upload_type == '.hex':
                    fw_path = './ospy/data/userfw.hex'
                    fw_name = 'userfw.hex'
                try:
                    if not os.path.isfile(fw_path):
                        fout = open(fw_path,'wb')
                        fout.write(read_limited_upload(i.uploadfile.file))
                        fout.close()
                        log.debug('webpages.py', _('File {} has sucesfully uploaded...').format(i.uploadfile.filename))
                    else:
                        os.remove(fw_path)
                        fout = open(fw_path,'wb')  # temporary file after uploading
                        fout.write(read_limited_upload(i.uploadfile.file))
                        fout.close()
                        log.debug('webpages.py', _('File has sucesfully uploaded...'))
                except ValueError as err:
                    log.error('webpages.py', str(err))
                    statusCode = qdict.get('statusCode', 'err8')
                    return self.core_render.sensors_firmware(statusCode)

                try:
                    kind = 'http://'
                    if protocol == "1":
                        kind = 'https://'
                    send_url = kind + ip + '/FW_' + pwd
                    if fw_path is not None:
                        with open(fw_path, 'rb') as file:
                            response = requests.post(send_url, files={fw_name: file}, timeout=options.sensor_http_timeout)
#todo change requests to urrlib
                        #data = {'files': open(fw_path, 'rb')}
                        #response = urlopen(send_url, data=data)
                        #print(response)

                        resp_code = response.status_code
                        log.debug('webpages.py', resp_code)
                        if resp_code == 200:
                            statusCode = qdict.get('statusCode', 'upl_ok')           # msg = The new firmware file has been sent to the sensor, wait for the sensor to respond - check if the sensor has been updated.
                            os.remove(fw_path)
                        elif resp_code == 404:
                            statusCode = qdict.get('statusCode', 'err3')             # msg = The new firmware could not be uploaded into the sensor. Response - Not Found!
                        else:
                            statusCode = qdict.get('statusCode', 'err4')             # msg = The new firmware could not be uploaded into the sensor. An error has occurred!
                except Exception:
                    pass
                    statusCode = qdict.get('statusCode', 'err2')                     # msg = The new firmware could not be uploaded into the sensor. Sensor does not respond!
                    log.debug('webpages.py', traceback.format_exc())
                    return self.core_render.sensors_firmware(statusCode)

        return self.core_render.sensors_firmware(statusCode)

class sensors_page(ProtectedPage):
    """Open all sensors page. /sensors"""

    def GET(self):
        from ospy.server import session
        global searchData

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()

        search = get_input(qdict, 'search', False, lambda x: True)

        if search:
            return self.core_render.sensors_search()

        return self.core_render.sensors()

    def POST(self):
        from ospy.server import session
        global searchData

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        action = qdict.get('action', '')

        if action == 'clean_all':
            for i in range(0, len(sensorSearch)):
                try:
                    del sensorSearch[int(i)]
                except Exception:
                    log.debug('webpages.py', traceback.format_exc())
                    pass
            return self.core_render.sensors_search()

        if action == 'delete_all':
            try: # delete all programs from sensor in program level adjustments (for soil moisture sensor)
                program = programs.get()
                for sensor in sensors.get():
                    for i in range(0, 16):
                        if sensor.soil_program[i] != "-1":
                            pid = '{}'.format(program[int(sensor.soil_program[i])-1].name)
                            del program_level_adjustments[pid]
            except Exception:
                log.debug('webpages.py', traceback.format_exc())
                pass

            while sensors.count() > 0:
                try:
                    sensor = sensors.get(sensors.count()-1)
                    sensors_timer.stop_status(sensor.name)
                    sensors.remove_sensors(sensors.count()-1)
                except Exception:
                    log.debug('webpages.py', traceback.format_exc())
                    pass
            try:
                import shutil
                shutil.rmtree(os.path.join('.', 'ospy', 'data', 'sensors'))
            except Exception:
                log.debug('webpages.py', traceback.format_exc())
                pass

        raise web.seeother('/sensors')


class sensor_page(ProtectedPage):
    """Open page to allow sensor modification. /sensor """
    def GET(self, index):
        from ospy.server import session
        import shutil

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        try:
            index = int(index)

            wlog = get_input(qdict, 'log', False, lambda x: True)      # return web page sensor log
            glog = get_input(qdict, 'glog', False, lambda x: True)     # return log json for graph
            graph = get_input(qdict, 'graph', False, lambda x: True)   # return web page sensor graph
            csvE = get_input(qdict, 'csvE', False, lambda x: True)     # return event csv file
            csvS = get_input(qdict, 'csvS', False, lambda x: True)     # return samples csv file
            clear = False

            if 'history' in qdict:
                options.sensor_graph_histories = int(qdict['history'])
                if 'sensor_graph_show_err' in qdict:
                    options.sensor_graph_show_err = True
                else:
                    options.sensor_graph_show_err = False
                raise web.seeother('/sensor/{}?graph'.format(index))

            if wlog:
                slog_file = []
                elog_file = []

                dir_name_log = os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs')
                _abs_dir_slog = os.path.abspath(dir_name_log + '/' + 'slog.json')
                _abs_dir_elog = os.path.abspath(dir_name_log + '/' + 'elog.json')

                if not os.path.isfile(_abs_dir_slog):
                    from ospy.sensors import sensors_timer
                    sensor = sensors.get(index)
                    sensors_timer.update_log(sensor, 'lgs', '-')

                if not os.path.isfile(_abs_dir_elog):
                    from ospy.sensors import sensors_timer
                    sensor = sensors.get(index)
                    sensors_timer.update_log(sensor, 'lge', '-', central_event=False)

                try:
                    with open(_abs_dir_slog) as logf:
                        slog_file =  json.load(logf)
                except IOError:
                    log.debug('webpages.py', traceback.format_exc())
                    pass

                try:
                    with open(_abs_dir_elog) as logf:
                        elog_file =  json.load(logf)
                except IOError:
                    log.debug('webpages.py', traceback.format_exc())
                    pass

                name = sensors[index].name
                stype = sensors[index].sens_type
                mtype = sensors[index].multi_type
                manufacturer = sensors[index].manufacturer
                shelly_hw_nbr = sensors[index].shelly_hw_nbr
                try:
                    return self.core_render.log_sensor(index, name, stype, mtype, slog_file, elog_file, manufacturer, shelly_hw_nbr)
                except Exception:
                    pass
                    log.debug('webpages.py', traceback.format_exc())

            elif glog:
                dir_name_glog = os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs', 'graph')
                _abs_dir_glog = os.path.abspath(dir_name_glog + '/' + 'graph.json')
                try:
                    with open(_abs_dir_glog) as logf:
                        glog_file =  json.load(logf)
                except IOError:
                    glog_file = []

                try:
                    sensor = sensors.get(index)
                    data = []
                    show_errors = options.sensor_graph_show_err
                    if 'sensor_graph_show_err' in qdict:
                        show_errors = str(qdict['sensor_graph_show_err']).lower() in ('1', 'on', 'true')

                    epoch = datetime.datetime(1970, 1, 1)                                  # first date
                    log_end = None

                    if 'dt_from' in qdict and 'dt_to' in qdict:
                        try:
                            dt_from = datetime.datetime.strptime(qdict['dt_from'], '%Y-%m-%dT%H:%M')
                            dt_to = datetime.datetime.strptime(qdict['dt_to'], '%Y-%m-%dT%H:%M')
                            log_start = int((dt_from - epoch).total_seconds())
                            log_end = int((dt_to - epoch).total_seconds())
                        except Exception:
                            log.debug('webpages.py', traceback.format_exc())
                            log_start = 0
                    else:
                        current_time = datetime.datetime.now()                              # actual date and time

                        if options.sensor_graph_histories == 0:                            # without filtering
                            check_start = current_time - datetime.timedelta(days=7300)      # actual date - 20 years
                        if options.sensor_graph_histories == 1:
                            check_start = current_time - datetime.timedelta(days=1)         # actual date - 1 day
                        if options.sensor_graph_histories == 2:
                            check_start = current_time - datetime.timedelta(days=7)         # actual date - 7 day (week)
                        if options.sensor_graph_histories == 3:
                            check_start = current_time - datetime.timedelta(days=30)        # actual date - 30 day (month)
                        if options.sensor_graph_histories == 4:
                            check_start = current_time - datetime.timedelta(days=365)       # actual date - 365 day (year)

                        log_start = int((check_start - epoch).total_seconds())             # start date for log in second (timestamp)

                    if sensor.multi_type == 9: # 16x log from probe + battery + signal
                        for i in range(0, 18):
                            temp_balances = {}
                            try:
                                if len(glog_file)>i:
                                    for key in glog_file[i]['balances']:
                                        find_key =  int(key.encode('utf8'))                            # key is in unicode ex: u'1601347000' -> find_key is int number
                                        if find_key >= log_start and (log_end is None or find_key <= log_end): # timestamp interval
                                            find_data = glog_file[i]['balances'][key]
                                            if show_errors:                                            # if is checked show error values in graph
                                                temp_balances[key] = glog_file[i]['balances'][key]     # add all values from json
                                            else:
                                                if float(find_data['total']) != -127.0:                # not checked, add values if not -127
                                                    temp_balances[key] = glog_file[i]['balances'][key]
                            except:
                                log.debug('webpages.py', traceback.format_exc())
                                pass
                            if len(glog_file)>i:
                                data.append({ 'sname': glog_file[i]['sname'], 'balances': temp_balances})
                    else:
                        for i in range(0, 3):  # 1x log from others + battery + signal
                            temp_balances = {}
                            try:
                                if len(glog_file)>i:
                                    for key in glog_file[i]['balances']:
                                        find_key =  int(key.encode('utf8'))                            # key is in unicode ex: u'1601347000' -> find_key is int number
                                        if find_key >= log_start and (log_end is None or find_key <= log_end): # timestamp interval
                                            find_data = glog_file[i]['balances'][key]
                                            if show_errors:                                            # if is checked show error values in graph
                                                temp_balances[key] = glog_file[i]['balances'][key]     # add all values from json
                                            else:
                                                if float(find_data['total']) != -127.0:                # not checked, add values if not -127
                                                    temp_balances[key] = glog_file[i]['balances'][key]
                            except:
                                log.debug('webpages.py', traceback.format_exc())
                                pass
                            if len(glog_file)>i:
                                data.append({ 'sname': glog_file[i]['sname'], 'balances': temp_balances})


                    web.header('Access-Control-Allow-Origin', '*')
                    web.header('Content-Type', 'application/json')
                    return json.dumps(data)
                except Exception:
                    log.debug('webpages.py', traceback.format_exc())
                    web.header('Access-Control-Allow-Origin', '*')
                    web.header('Content-Type', 'application/json')
                    return json.dumps([])

            elif graph:
                try:
                    name = sensors[index].name
                    stype = sensors[index].sens_type
                    mtype = sensors[index].multi_type
                    manufacturer = sensors[index].manufacturer
                    shelly_hw_nbr = sensors[index].shelly_hw_nbr
                    return self.core_render.graph_sensor(index, name, stype, mtype, manufacturer, shelly_hw_nbr)
                except Exception:
                    log.debug('webpages.py', traceback.format_exc())
                    return self.core_render.graph_sensor(index, name, stype, mtype, manufacturer, shelly_hw_nbr)

            elif csvE:
                dir_name_elog = os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs', 'elog.json')

                try:
                    with open(dir_name_elog) as logf:
                        slog_file =  json.load(logf)
                except IOError:
                    slog_file = []
                data = "Date; Time; Event\n"
                for interval in slog_file:
                    data += '; '.join([
                        interval['date'],
                        interval['time'],
                        '{}'.format(interval['event']),
                    ]) + '\n'

                web.header('Content-Type', 'text/csv')
                web.header('Content-Disposition', 'attachment; filename="event.csv"')
                return data

            elif csvS:
                dir_name_slog = os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs')
                _abs_dir_slog = os.path.abspath(dir_name_slog + '/' + 'slog.json')
                try:
                    with open(_abs_dir_slog) as logf:
                        slog_file =  json.load(logf)
                except IOError:
                    slog_file = []
                data = "Date; Time; Value; Battery; Signal\n"
                for interval in slog_file:
                    data += '; '.join([
                        interval['date'],
                        interval['time'],
                        '{}'.format(interval['value']),
                        '{}'.format(interval['battery'] if 'battery' in interval else ''),
                        '{}'.format(interval['rssi'] if 'rssi' in interval else ''),
                    ]) + '\n'

                web.header('Content-Type','text/csv')
                web.header('Content-Disposition', 'attachment; filename="sample.csv"')
                return data

            elif clear:
                try:
                    _abs_dir_path = os.path.abspath(os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs'))
                    shutil.rmtree(_abs_dir_path)
                except Exception:
                    pass
                raise web.seeother('/sensors')

        except ValueError:
            pass

        if isinstance(index, int):
            sensor = sensors.get(index)
        else:
            sensor = sensors.create_sensors()

        errorCode = qdict.get('errorCode', 'None')
        return self.core_render.sensor(sensor, errorCode)


    def POST(self, index):
        from ospy.server import session
        import shutil

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input(AL=[], AH=[], BL=[], BH=[], CL=[], CH=[], DL=[], DH=[], s_DL=[], s_DH=[],   # [] for input save multiple select
                         MDL=[], MDH=[], SL=[], SH=[], used_stations=[], used_stations_one=[], used_stations_two=[],
                         SW_C0=[], SW_C1=[], SW_C2=[], SW_C3=[], SW_C4=[], SW_C5=[], SW_C6=[],        # 7 switch closed pgm
                         SW_O0=[], SW_O1=[], SW_O2=[], SW_O3=[], SW_O4=[], SW_O5=[], SW_O6=[],        # 7 switch open pgm
                         SW_SC0=[], SW_SC1=[], SW_SC2=[], SW_SC3=[], SW_SC4=[], SW_SC5=[], SW_SC6=[], # 7 switch closed stations
                         SW_SO0=[], SW_SO1=[], SW_SO2=[], SW_SO3=[], SW_SO4=[], SW_SO5=[], SW_SO6=[]  # 7 switch open stations
                         )
        action = qdict.get('action', '')
        if action:
            try:
                index = int(index)
            except ValueError:
                raise web.seeother('/sensors')

            if action == 'enable':
                sensors[index].enabled = qdict.get('enabled', '0') == '1'
                logEV.save_events_log(
                    _('Sensor setting changed'),
                    (_('User {} enabled sensor {}.') if sensors[index].enabled else
                     _('User {} disabled sensor {}.')).format(
                        session.get('visitor'), sensors[index].name),
                    id='Sensor',
                    level='info',
                    category='configuration'
                )
                raise web.seeother('/sensors')

            if action == 'clear':
                try:
                    _abs_dir_path = os.path.abspath(os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs'))
                    shutil.rmtree(_abs_dir_path)
                except Exception:
                    pass
                raise web.seeother('/sensors')

            if action == 'delete':
                sensor_name = sensors.get(index).name
                try: # delete sensor info from footer
                    from ospy.sensors import sensors_timer
                    sensor = sensors.get(index)
                    sensors_timer.stop_status(sensor.name)
                except Exception:
                    log.debug('webpages.py', traceback.format_exc())
                    pass

                try: # delete programs from sensor in program level adjustments (for soil moisture sensor)
                    program = programs.get()
                    for i in range(0, 16):
                        if sensor.soil_program[i] != "-1":
                            pid = '{}'.format(program[int(sensor.soil_program[i])-1].name)
                            del program_level_adjustments[pid]
                except Exception:
                    log.debug('webpages.py', traceback.format_exc())
                    pass

                try: # delete log and graph
                    shutil.rmtree(os.path.join('.', 'ospy', 'data', 'sensors', str(index)))
                except Exception:
                    log.debug('webpages.py', traceback.format_exc())
                    pass

                try: # delete sensor
                    sensors.remove_sensors(index)
                except Exception:
                    log.debug('webpages.py', traceback.format_exc())
                    pass

                logEV.save_events_log(
                    _('Sensor deleted'),
                    _('User {} deleted sensor {}.').format(session.get('visitor'), sensor_name),
                    id='Sensor',
                    level='warning',
                    category='configuration'
                )

                raise web.seeother('/sensors')

        multi_type = -1
        sen_type = -1

        is_new_sensor = False
        try:
            index = int(index)
            sensor = sensors.get(index)

        except ValueError:
            sensor = sensors.create_sensors()
            is_new_sensor = True

        if session.get('category') == 'admin':
            if 's_manu' in qdict:
                sensor.manufacturer = int(qdict['s_manu'])                      # 0=Pihrt, 1=Shelly

            if 's_name' in qdict:                                               # Shelly name
                sensor.name = qdict['s_name']

            if 's_id' in qdict:                                                 # Shelly ID
                sensor.shelly_id = qdict['s_id']

            if 's_hw' in qdict:                                                 # Shelly hardware
                sensor.shelly_hw = qdict['s_hw']

            if 's_gen' in qdict:                                                # Shelly generation
                sensor.shelly_gen = qdict['s_gen']

            if 's_ip' in qdict:                                                 # Shelly IP address
                from ospy.helpers import split_ip
                ip = split_ip(qdict['s_ip'])
                sensor.ip_address = ip

            if 's_DL' in qdict:
                sensor.s_trigger_low_program = qdict['s_DL']
            if 's_DH' in qdict:
                sensor.s_trigger_high_program = qdict['s_DH']
            if 's_trigger_low_threshold' in qdict:
                sensor.s_trigger_low_threshold = qdict['s_trigger_low_threshold']
            if 's_trigger_high_threshold' in qdict:
                sensor.s_trigger_high_threshold = qdict['s_trigger_high_threshold']

            if 'name' in qdict:
                sensor.name = qdict['name']

            if 'notes' in qdict:
                sensor.notes = qdict['notes']

            if 'enable' in qdict and qdict['enable'] == 'on':
                sensor.enabled = 1
            else:
                sensor.enabled = 0

            if 'show_in_footer' in qdict and qdict['show_in_footer'] == 'on':
                sensor.show_in_footer = 1
            else:
                sensor.show_in_footer = 0

            if 'sens_type' in qdict:
                sensor.sens_type = int(qdict['sens_type'])
                sen_type = int(qdict['sens_type'])

            if 'com_type' in qdict:
                sensor.com_type = int(qdict['com_type'])

            if 'multi_type' in qdict:
                sensor.multi_type = int(qdict['multi_type'])
                multi_type = int(qdict['multi_type'])

            if 'log_samples' in qdict and qdict['log_samples'] == 'on':
                sensor.log_samples = 1
            else:
                sensor.log_samples = 0

            if 'log_event' in qdict and qdict['log_event'] == 'on':
                sensor.log_event = 1
            else:
                sensor.log_event = 0

            if 'send_email' in qdict and qdict['send_email'] == 'on':
                sensor.send_email = 1
            else:
                sensor.send_email = 0

            if 'sample_rate_min' in qdict and 'sample_rate_sec' in qdict:
                try:
                    sensor.sample_rate = int(qdict['sample_rate_min'])*60 + int(qdict['sample_rate_sec'])
                except:
                    sensor.sample_rate = 60
                    pass

            if 'liter_per_pulses' in qdict:
                sensor.liter_per_pulses = float(qdict['liter_per_pulses'])

            if 'sensitivity' in qdict:
                sensor.sensitivity = int(qdict['sensitivity'])

            if 'stabilization_time_min' in qdict and 'stabilization_time_sec' in qdict:
                sensor.stabilization_time = int(qdict['stabilization_time_min'])*60 + int(qdict['stabilization_time_sec'])

            if  sen_type == 1:                           # dry contact
                sensor.trigger_low_program = qdict['AL']
                sensor.trigger_high_program = qdict['AH']
                if 'used_stations_one' in qdict:
                    sensor.used_stations_one = qdict['used_stations_one']
                if 'used_stations_two' in qdict:
                    sensor.used_stations_two = qdict['used_stations_two']
                if 'open_msg' in qdict:
                    sensor.dry_open_msg = qdict['open_msg']
                if 'close_msg' in qdict:
                    sensor.dry_clos_msg = qdict['close_msg']

            elif sen_type == 2:                          # leak detector
                if 'BL' in qdict:
                    sensor.trigger_low_program = qdict['BL']
                if 'BH' in qdict:
                    sensor.trigger_high_program = qdict['BH']

            elif sen_type == 4:                          # motion
                sensor.trigger_low_program = ["-1"]
                sensor.trigger_high_program = qdict['CH']
                if 'motion_msg' in qdict:
                    sensor.motion_msg = qdict['motion_msg']
                if 'no_motion_msg' in qdict:
                    sensor.no_motion_msg = qdict['no_motion_msg']

            elif sen_type == 3:                          # moisture
                if 'MDL' in qdict:
                    sensor.trigger_low_program = qdict['MDL']
                if 'MDH' in qdict:
                    sensor.trigger_high_program = qdict['MDH']
                if 'trigger_low_threshold' in qdict:
                    sensor.trigger_low_threshold = qdict['Mtrigger_low_threshold']
                if 'trigger_high_threshold' in qdict:
                    sensor.trigger_high_threshold = qdict['Mtrigger_high_threshold']

            elif sen_type == 5:                          # temperature
                if 'DL' in qdict:
                    sensor.trigger_low_program = qdict['DL']
                if 'DH' in qdict:
                    sensor.trigger_high_program = qdict['DH']
                if 'trigger_low_threshold' in qdict:
                    sensor.trigger_low_threshold = qdict['trigger_low_threshold']
                if 'trigger_high_threshold' in qdict:
                    sensor.trigger_high_threshold = qdict['trigger_high_threshold']

            elif sen_type == 6 and (multi_type == 0 or multi_type == 1 or multi_type == 2 or multi_type == 3): # multi temperature 0-3
                if 'DL' in qdict:
                    sensor.trigger_low_program = qdict['DL']
                if 'DH' in qdict:
                    sensor.trigger_high_program = qdict['DH']
                if 'trigger_low_threshold' in qdict:
                    sensor.trigger_low_threshold = qdict['trigger_low_threshold']
                if 'trigger_high_threshold' in qdict:
                    sensor.trigger_high_threshold = qdict['trigger_high_threshold']

            elif sen_type == 6 and multi_type == 4:      # multi dry contact
                if 'AL' in qdict:
                    sensor.trigger_low_program = qdict['AL']
                if 'AH' in qdict:
                    sensor.trigger_high_program = qdict['AH']
                if 'used_stations_one' in qdict:
                    sensor.used_stations_one = qdict['used_stations_one']
                if 'used_stations_two' in qdict:
                    sensor.used_stations_two = qdict['used_stations_two']
                if 'open_msg' in qdict:
                    sensor.dry_open_msg = qdict['open_msg']
                if 'close_msg' in qdict:
                    sensor.dry_clos_msg = qdict['close_msg']

            elif sen_type == 6 and multi_type == 5:      # multi leak detector
                if 'BL' in qdict:
                    sensor.trigger_low_program = qdict['BL']
                if 'BH' in qdict:
                    sensor.trigger_high_program = qdict['BH']

            elif sen_type == 6 and multi_type == 6:      # multi moisture
                if 'MDL' in qdict:
                    sensor.trigger_low_program = qdict['MDL']
                if 'MDH' in qdict:
                    sensor.trigger_high_program = qdict['MDH']
                if 'trigger_low_threshold' in qdict:
                    sensor.trigger_low_threshold = qdict['Mtrigger_low_threshold']
                if 'trigger_high_threshold' in qdict:
                    sensor.trigger_high_threshold = qdict['Mtrigger_high_threshold']

            elif sen_type == 6 and multi_type == 7:      # multi motion
                sensor.trigger_low_program = ["-1"]
                if 'CH' in qdict:
                    sensor.trigger_high_program = qdict['CH']
                if 'motion_msg' in qdict:
                    sensor.motion_msg = qdict['motion_msg']
                if 'no_motion_msg' in qdict:
                    sensor.no_motion_msg = qdict['no_motion_msg']

            elif sen_type == 6 and multi_type == 8:      # multi sonic
                if 'SL' in qdict:
                    sensor.trigger_low_program = qdict['SL']
                if 'SH' in qdict:
                    sensor.trigger_high_program = qdict['SH']
                if 'distance_top' in qdict:
                    sensor.distance_top = qdict['distance_top']
                if 'distance_bottom' in qdict:
                    sensor.distance_bottom = qdict['distance_bottom']
                if 'water_minimum' in qdict:
                    sensor.water_minimum = qdict['water_minimum']
                if 'diameter' in qdict:
                    sensor.diameter = qdict['diameter']
                if 'delay_duration' in qdict:
                    sensor.delay_duration = qdict['delay_duration']
                if 'check_liters' in qdict:
                    sensor.check_liters = 1
                else:
                    sensor.check_liters = 0
                if 'use_stop' in qdict:
                    sensor.use_stop = 1
                else:
                    sensor.use_stop = 0
                if 'use_water_stop' in qdict:
                    sensor.use_water_stop = 1
                else:
                    sensor.use_water_stop = 0
                if 'used_stations' in qdict:
                    sensor.used_stations = qdict['used_stations']
                if 'enable_reg' in qdict:
                    sensor.enable_reg = 1
                else:
                    sensor.enable_reg = 0
                if 'reg_max' in qdict:
                    sensor.reg_max = qdict['reg_max']
                if 'reg_mm' in qdict:
                    sensor.reg_mm = qdict['reg_mm']
                if 'reg_ss' in qdict:
                    sensor.reg_ss = qdict['reg_ss']
                if 'reg_min' in qdict:
                    sensor.reg_min = qdict['reg_min']
                if 'reg_output' in qdict:
                    try:
                        reg_output = int(qdict['reg_output'])
                        if 0 <= reg_output < options.output_count:
                            sensor.reg_output = reg_output
                    except (TypeError, ValueError):
                        pass
                if 'trigger_low_threshold_s' in qdict:
                    sensor.trigger_low_threshold = qdict['trigger_low_threshold_s']
                if 'trigger_high_threshold_s' in qdict:
                    sensor.trigger_high_threshold = qdict['trigger_high_threshold_s']

            elif sen_type == 6 and multi_type == 9:      # multi soil moisture
                for i in range(0,16):                    # 16x soil moisture calibration
                    if 'sc{}'.format(i) in qdict:        # 16x calibration for 0% in Volt
                        sensor.soil_calibration_min[i] = float(qdict['sc{}'.format(i)])
                    if 'sd{}'.format(i) in qdict:        # 16x calibration for 100% in Volt
                        sensor.soil_calibration_max[i] = float(qdict['sd{}'.format(i)])
                    if 'SM{}'.format(i) in qdict:        # 16x adjust program xx from probe xx
                        sensor.soil_program[i] = str(qdict['SM{}'.format(i)])
                    if 'sip{}'.format(i) in qdict:       # 16x checker (inverted logic from probe)
                        if qdict['sip{}'.format(i)] == 'on':
                            sensor.soil_invert_probe_in[i] = 1
                    else:
                        sensor.soil_invert_probe_in[i] = 0
                    if 'fip{}'.format(i) in qdict:       # 16x checker (show data from probe in footer)
                        if qdict['fip{}'.format(i)] == 'on':
                            sensor.soil_show_in_footer[i] = 1
                    else:
                        sensor.soil_show_in_footer[i] = 0
                    if 'pl{}'.format(i) in qdict:        # 16x probe label
                        sensor.soil_probe_label[i] = '{}'.format(qdict['pl{}'.format(i)])

            elif sen_type == 7:
                if 'SW_O0' in qdict:
                    sensor.sw0_open_program = qdict['SW_O0']
                if 'SW_O1' in qdict:
                    sensor.sw1_open_program = qdict['SW_O1']
                if 'SW_O2' in qdict:
                    sensor.sw2_open_program = qdict['SW_O2']
                if 'SW_O3' in qdict:
                    sensor.sw3_open_program = qdict['SW_O3']
                if 'SW_O4' in qdict:
                    sensor.sw4_open_program = qdict['SW_O4']
                if 'SW_O5' in qdict:
                    sensor.sw5_open_program = qdict['SW_O5']
                if 'SW_O6' in qdict:
                    sensor.sw6_open_program = qdict['SW_O6']
                if 'SW_C0' in qdict:
                    sensor.sw0_closed_program = qdict['SW_C0']
                if 'SW_C1' in qdict:
                    sensor.sw1_closed_program = qdict['SW_C1']
                if 'SW_C2' in qdict:
                    sensor.sw2_closed_program = qdict['SW_C2']
                if 'SW_C3' in qdict:
                    sensor.sw3_closed_program = qdict['SW_C3']
                if 'SW_C4' in qdict:
                    sensor.sw4_closed_program = qdict['SW_C4']
                if 'SW_C5' in qdict:
                    sensor.sw5_closed_program = qdict['SW_C5']
                if 'SW_C6' in qdict:
                    sensor.sw6_closed_program = qdict['SW_C6']
                if 'SW_SO0' in qdict:
                    sensor.sw0_open_stations = qdict['SW_SO0']
                if 'SW_SO1' in qdict:
                    sensor.sw1_open_stations = qdict['SW_SO1']
                if 'SW_SO2' in qdict:
                    sensor.sw2_open_stations = qdict['SW_SO2']
                if 'SW_SO3' in qdict:
                    sensor.sw3_open_stations = qdict['SW_SO3']
                if 'SW_SO4' in qdict:
                    sensor.sw4_open_stations = qdict['SW_SO4']
                if 'SW_SO5' in qdict:
                    sensor.sw5_open_stations = qdict['SW_SO5']
                if 'SW_SO6' in qdict:
                    sensor.sw6_open_stations = qdict['SW_SO6']
                if 'SW_SC0' in qdict:
                   sensor.sw0_closed_stations = qdict['SW_SC0']
                if 'SW_SC1' in qdict:
                    sensor.sw1_closed_stations = qdict['SW_SC1']
                if 'SW_SC2' in qdict:
                    sensor.sw2_closed_stations = qdict['SW_SC2']
                if 'SW_SC3' in qdict:
                    sensor.sw3_closed_stations = qdict['SW_SC3']
                if 'SW_SC4' in qdict:
                    sensor.sw4_closed_stations = qdict['SW_SC4']
                if 'SW_SC5' in qdict:
                    sensor.sw5_closed_stations = qdict['SW_SC5']
                if 'SW_SC6' in qdict:
                    sensor.sw6_closed_stations = qdict['SW_SC6']

            if 'ip_address' in qdict:
                from ospy.helpers import split_ip
                ip = split_ip(qdict['ip_address'])
                sensor.ip_address = ip

            if 'mac_address' in qdict:
                sensor.mac_address = str(qdict['mac_address'].upper())

            if 'radio_id' in qdict:
                if qdict['radio_id'] != '-':
                    sensor.radio_id = int(qdict['radio_id'])

            if 'senscpu' in qdict:
                sensor.cpu_core = int(qdict['senscpu'])

            if 'sensfw' in qdict:
                sensor.fw = int(qdict['sensfw'])

            if 'eplug' in qdict:
                sensor.eplug = int(qdict['eplug'])

            if 'name' in qdict and qdict['name'] == '' and sensor.index < 0:
                errorCode = qdict.get('errorCode', 'uname')
                return self.core_render.sensor(sensor, errorCode)

            try:
                if 'name' in qdict and sensor.index < 0:
                    for sens in sensors.get():
                        if sens.name == qdict['name']:
                            errorCode = qdict.get('errorCode', 'unameis')
                            return self.core_render.sensor(sensor, errorCode)
            except:
                log.debug('webpages.py', traceback.format_exc())

        if sensor.index < 0 and session['category'] == 'admin':
            sensors.add_sensors(sensor)

        logEV.save_events_log(
            _('Sensor created') if is_new_sensor else _('Sensor updated'),
            _('User {} created sensor {}.').format(session.get('visitor'), sensor.name)
            if is_new_sensor else
            _('User {} updated sensor {}.').format(session.get('visitor'), sensor.name),
            id='Sensor',
            level='info',
            category='configuration'
        )

        raise web.seeother('/sensors')


class users_page(ProtectedPage):
    """Open all users page. /users"""

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        return self.core_render.users()

    def POST(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        if qdict.get('action', '') == 'delete_all':
            deleted_count = users.count()
            while users.count() > 0:
                users.remove_users(users.count()-1)
            logEV.save_events_log(
                _('All users deleted'),
                _('Administrator {} deleted all {} users.').format(
                    session.get('visitor'), deleted_count),
                id='Login',
                level='warning',
                category='security'
            )
        raise web.seeother('/users')


class user_page(ProtectedPage):
    """Open page to allow user modification. /user """
    def GET(self, index):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        try:
            index = int(index)

        except ValueError:
            pass

        if isinstance(index, int):
            user = users.get(index)
        else:
            user = users.create_users()

        errorCode = qdict.get('errorCode', 'None')
        return self.core_render.user(user, errorCode)


    def POST(self, index):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        if qdict.get('action', '') == 'delete':
            try:
                user_index = int(index)
                user_name = users.get(user_index).name
                users.remove_users(user_index)
                logEV.save_events_log(
                    _('User deleted'),
                    _('Administrator {} deleted user {}.').format(
                        session.get('visitor'), user_name),
                    id='Login',
                    level='warning',
                    category='security'
                )
            except ValueError:
                pass
            raise web.seeother('/users')

        try:
            index = int(index)
            user = users.get(index)

        except ValueError:
            user = users.create_users()

        user.name = ''
        password = ''

        if session.get('category') == 'admin':
            user.name = qdict['name']
            password = qdict['password']
            user.category = qdict['category']
            user.notes = qdict['notes']

        if user.name == '' and user.index < 0:
            errorCode = qdict.get('errorCode', 'uname')
            return self.core_render.user(user, errorCode)

        if len(user.name) < 5:
            errorCode = qdict.get('errorCode', 'unamelen')
            return self.core_render.user(user, errorCode)

        if password == user.name:
            errorCode = qdict.get('errorCode', 'upassuname')
            return self.core_render.user(user, errorCode)

        if password == '':
            errorCode = qdict.get('errorCode', 'upass')
            return self.core_render.user(user, errorCode)

        if len(password) < 5:
            errorCode = qdict.get('errorCode', 'unamepass')
            return self.core_render.user(user, errorCode)

        if user.name == options.admin_user:
            errorCode = qdict.get('errorCode', 'unameis')
            return self.core_render.user(user, errorCode)

        for x in range(users.count()):
            isuser = users.get(x)
            if user.name == isuser.name and user.index < 0:
                errorCode = qdict.get('errorCode', 'unameis')
                return self.core_render.user(user, errorCode)

        if user.index < 0 and session['category'] == 'admin':
            salt = password_salt()
            user.password_salt = salt
            user.password_hash = password_hash(password, salt) # actual user hash+salt for saving
            users.add_users(user)
            logEV.save_events_log(
                _('User created'),
                _('Administrator {} created user {} with category {}.').format(
                    session.get('visitor'), user.name, user.category),
                id='Login',
                level='info',
                category='security'
            )

        raise web.seeother('/users')


class image_edit_page(ProtectedPage):
    """Open page to edit images for station."""
    def GET(self, index):
        from ospy.server import session
        import os

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        errorCode = qdict.get('errorCode', 'None')

        img_path    = './ospy/images/stations/station%s.png' % str(index)
        img_path_th = './ospy/images/stations/station%s_thumbnail.png' % str(index)

        if not os.path.isfile(img_path) or not os.path.isfile(img_path_th):
            img_url = '/images?id=no_image'                           # fake default img
            errorCode = qdict.get('errorCode', 'noex')
            try:
                from PIL import Image
            except ImportError:
                errorCode = qdict.get('errorCode', 'nopil')
                log.debug('webpages.py', traceback.format_exc())
                pass
        else:
            img_url = '/images?sf=1&id=station%s' % str(index)        # station img

        return self.core_render.edit(index, img_url, errorCode)


    def POST(self, index):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()

        img_path      = './ospy/images/stations/station%s.png' % str(index)
        img_path_th   = './ospy/images/stations/station%s_thumbnail.png' % str(index)
        action = qdict.get('action', '')

        if action == 'delete':
            try:
                if os.path.isfile(img_path):
                    os.remove(img_path)
                if os.path.isfile(img_path_th):
                    os.remove(img_path_th)
                log.debug('webpages.py', _('Files {} and {} has sucesfully deleted...').format('station%s.png' % str(index),'station%s_thumbnail.png' % str(index)))
            except:
                log.debug('webpages.py', traceback.format_exc())
                pass
            raise web.seeother('/img_edit/{}'.format(index))

        if action == 'install':
            try:
                import subprocess
                cmd = ['sudo', 'apt-get', 'install', '-y', 'python3-pil']
                proc = subprocess.run(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, timeout=600, check=True)
                log.debug('webpages.py', proc.stdout.decode('utf-8', 'replace'))
                raise web.seeother('/img_edit/{}?errorCode=nopilOK'.format(index))
            except:
                log.debug('webpages.py', traceback.format_exc())
                raise web.seeother('/img_edit/{}?errorCode=nopilErr'.format(index))
        img_path_temp = './ospy/images/stations/temp%s.png' % str(index)

        if session.get('category') == 'admin':
            if 'enabled' in qdict and qdict['enabled']== 'on':
                options.high_resolution_mode = True
            else:
                options.high_resolution_mode = False

            i = web.input(uploadfile={})
            uploaded = i.get('uploadfile')
            upload_name = getattr(uploaded, 'filename', '') if uploaded is not None else ''
            upload_type = os.path.splitext(upload_name)[1].lower()
            types = ['.png', '.gif', '.jpg', '.jpeg']
            if not upload_name or upload_type not in types:            # check file type is ok
                if not os.path.isfile(img_path) or not os.path.isfile(img_path_th):
                    img_url = '/images?id=no_image'                            # fake default img
                else:
                    img_url = '/images?sf=1&id=station%s' % str(index)         # station img

                errorCode = qdict.get('errorCode', 'uplname')
                return self.core_render.edit(index, img_url, errorCode)
            else:                     # image file is valid
                try:
                    if not os.path.isfile(img_path_temp):
                        fout = open(img_path_temp,'wb')
                        fout.write(read_limited_upload(uploaded.file))
                        fout.close()
                        log.debug('webpages.py', _('File {} has sucesfully uploaded...').format(upload_name))
                    else:
                        os.remove(img_path_temp)
                        fout = open(img_path_temp,'wb')  # temporary file after uploading
                        fout.write(read_limited_upload(uploaded.file))
                        fout.close()
                        log.debug('webpages.py', _('File has sucesfully uploaded...'))
                except ValueError as err:
                    log.error('webpages.py', str(err))
                    if not os.path.isfile(img_path) or not os.path.isfile(img_path_th):
                        img_url = '/images?id=no_image'
                    else:
                        img_url = '/images?sf=1&id=station%s' % str(index)
                    errorCode = qdict.get('errorCode', 'uplname')
                    return self.core_render.edit(index, img_url, errorCode)

                try:
                    import warnings
                    from PIL import Image
                    try:
                        from PIL import UnidentifiedImageError
                    except ImportError:
                        UnidentifiedImageError = OSError
                    DecompressionBombWarning = getattr(Image, 'DecompressionBombWarning', Warning)
                    DecompressionBombError = getattr(Image, 'DecompressionBombError', Exception)
                except ImportError:
                    if os.path.isfile(img_path_temp):
                        os.remove(img_path_temp)
                    log.debug('webpages.py', traceback.format_exc())
                    if not os.path.isfile(img_path) or not os.path.isfile(img_path_th):
                        img_url = '/images?id=no_image'
                    else:
                        img_url = '/images?sf=1&id=station%s' % str(index)
                    return self.core_render.edit(index, img_url, 'nopil')

                try:
                    if os.path.isfile(img_path_temp):
                        Image.MAX_IMAGE_PIXELS = 25000000
                        with warnings.catch_warnings():
                            warnings.simplefilter('error', DecompressionBombWarning)
                            with Image.open(img_path_temp) as im:
                                im.verify()

                        with warnings.catch_warnings():
                            warnings.simplefilter('error', DecompressionBombWarning)
                            with Image.open(img_path_temp) as im:
                                size = 50,50                # resize to thumbnail
                                im.thumbnail(size)
                                im.save(img_path_th, "PNG")

                            with Image.open(img_path_temp) as im:
                                if options.high_resolution_mode:
                                    size = 1024,768         # resize original (high quality)
                                else:
                                    size = 640,480          # resize original (low quality)
                                im.thumbnail(size)
                                im.save(img_path, "PNG")

                        os.remove(img_path_temp)
                        log.debug('webpages.py', _('Files has sucesfully resized to max 60x60/640x480...'))

                except DecompressionBombError:
                    if os.path.isfile(img_path_temp):
                        os.remove(img_path_temp)
                    log.error('webpages.py', _('Uploaded image is too large to process safely.'))
                    if not os.path.isfile(img_path) or not os.path.isfile(img_path_th):
                        img_url = '/images?id=no_image'
                    else:
                        img_url = '/images?sf=1&id=station%s' % str(index)
                    return self.core_render.edit(index, img_url, 'imglarge')

                except (DecompressionBombWarning, UnidentifiedImageError, OSError, ValueError):
                    if os.path.isfile(img_path_temp):
                        os.remove(img_path_temp)
                    log.error('webpages.py', _('Cannot create resized files!'))
                    log.debug('webpages.py', traceback.format_exc())
                    if not os.path.isfile(img_path) or not os.path.isfile(img_path_th):
                        img_url = '/images?id=no_image'
                    else:
                        img_url = '/images?sf=1&id=station%s' % str(index)
                    return self.core_render.edit(index, img_url, 'imgbad')

        raise web.seeother('/stations')


class image_view_page(ProtectedPage):
    """Open page to view images for station."""
    def GET(self, index):
        import os

        qdict = web.input()
        image_type = str(get_input(qdict, 'type', 'jpg')).lower()
        if image_type not in ('jpg', 'gif'):
            image_type = 'jpg'

        if get_input(qdict, 'ip_cam', None, lambda x: x == '1') is not None:
            img_url = '/images?ip_cam=1&cam={}&type={}'.format(index, image_type)
        else:
            img_path = './ospy/images/stations/station%s.png' % str(index)
            if not os.path.isfile(img_path):
                img_url = '/images?id=no_image.png'                           # fake default img
            else:
                img_url = '/images?sf=1&id=station%s.png' % str(index)        # station img

        return self.core_render.view(img_url)


class login_page(WebPage):
    """Login page"""

    def GET(self):
        qdict = web.input()
        if 'reset_session' in qdict:
            from ospy import server
            try:
                autologin.clear_cookie()
                server.reset_session_store(remove_files=True)
                server.session.kill()
            except Exception:
                log.debug('webpages.py', traceback.format_exc())
            raise web.seeother('/login', True)

        if check_login(False):
            raise web.seeother('/')
        else:
            from ospy import server
            if server.session.get('two_factor_pending'):
                if time.time() - float(server.session.get('two_factor_started', 0)) <= 300:
                    return self.core_render.login(
                        signin_form(), None, True, server.session.get('two_factor_method'), None)
                _clear_two_factor_login()

            remembered_login = autologin.validate_cookie()
            if remembered_login:
                from ospy import server
                # Keep the current id when a remember-me cookie restores a
                # session. Browsers can send multiple requests in parallel
                # after a session expires; regenerating the id in every
                # request makes their Set-Cookie responses race and can leave
                # the browser in a /login -> / redirect loop. The id is still
                # regenerated for an interactive password login below.
                server.session.validated = True
                server.session['category'] = remembered_login['category']
                server.session['visitor'] = remembered_login['username']
                if autologin.should_log_login(remembered_login['selector']):
                    report_login()
                    if options.run_logEV:
                        logEV.save_events_log(_('Login'), _('User {} logged in from IP {} category {}').format(server.session.get('visitor'), server.session.get('ip'), server.session.get('category')), id='Login', level='info', category='security')
                    log.info('webpages.py', _('User {} logged in').format(server.session.get('visitor')))
                raise web.seeother('/', True)

            if options.first_installation:
                new_user = options.first_password_hash
            else:
                new_user = None
            return self.core_render.login(signin_form(), new_user, False, None, None)

    def POST(self):
        from ospy import server
        my_signin = signin_form()
        qdict = web.input()
        verify_csrf(qdict)

        if server.session.get('two_factor_pending'):
            attempts = int(server.session.get('two_factor_attempts', 0))
            started = float(server.session.get('two_factor_started', 0))
            if attempts >= 5 or time.time() - started > 300:
                _clear_two_factor_login()
                my_signin.note = _('The verification request expired. Please sign in again.')
                return self.core_render.login(my_signin, None, False, None, None)

            method = server.session.get('two_factor_method')
            code = qdict.get('two_factor_code', '')
            if method == twofactor.METHOD_TOTP:
                valid = twofactor.verify_totp(options.two_factor_secret, code)
            else:
                valid = twofactor.verify_email_code(
                    code,
                    server.session.get('two_factor_nonce', ''),
                    server.session.get('two_factor_code_hash', ''),
                    server.session.get('two_factor_expires', 0))
            if not valid:
                valid, remaining_codes = twofactor.consume_backup_code(
                    code, options.two_factor_backup_codes)
                if valid:
                    options.two_factor_backup_codes = remaining_codes
            if not valid:
                server.session['two_factor_attempts'] = attempts + 1
                _save_security_failure(
                    'two-factor:{}:{}'.format(
                        server.session.get('ip'), server.session.get('two_factor_user')),
                    _('Failed verification'),
                    _('Invalid two-factor verification for user {} from IP {}.').format(
                        server.session.get('two_factor_user'), server.session.get('ip'))
                )
                return self.core_render.login(
                    my_signin, None, True, method, _('The verification code is incorrect or has expired.'))

            username = server.session.get('two_factor_user')
            category = server.session.get('two_factor_category')
            remember = bool(server.session.get('two_factor_remember'))
            _clear_two_factor_login()
            server.session.regenerate_id()
            server.session['visitor'] = username
            server.session['category'] = category
            server.session.validated = True
            if remember:
                autologin.issue(username, category)
            else:
                autologin.revoke_cookie_token()
            report_login()
            if options.run_logEV:
                logEV.save_events_log(_('Login'), _('User {} logged in from IP {} category {}').format(
                    username, server.session.get('ip'), category), id='Login', level='info', category='security')
            log.info('webpages.py', _('User {} logged in').format(username))
            raise web.seeother('/', True)

        my_signin.fill(qdict)

        if not test_password(qdict.get('password', ''), qdict.get('username', '')):
            _save_security_failure(
                'login:{}:{}'.format(server.session.get('ip'), qdict.get('username', '')),
                _('Failed login'),
                _('Failed login for user {} from IP {}.').format(
                    qdict.get('username', ''), server.session.get('ip'))
            )
            my_signin.note = _('Incorrect username or password, please try again...')
            if options.first_installation:
                return self.core_render.login(my_signin, options.first_password_hash, False, None, None)
            else:
                return self.core_render.login(my_signin, None, False, None, None)
        else:
            method = (options.two_factor_method
                      if server.session.get('visitor') == options.admin_user
                      else twofactor.METHOD_NONE)
            if method in (twofactor.METHOD_TOTP, twofactor.METHOD_EMAIL):
                server.session['two_factor_pending'] = True
                server.session['two_factor_user'] = server.session.get('visitor')
                server.session['two_factor_category'] = server.session.get('category')
                server.session['two_factor_method'] = method
                server.session['two_factor_remember'] = 'remember-me' in qdict
                server.session['two_factor_started'] = time.time()
                server.session['two_factor_attempts'] = 0
                server.session['category'] = 'public'
                server.session['visitor'] = 'Unknown'
                server.session.validated = False
                if method == twofactor.METHOD_EMAIL:
                    try:
                        code, nonce, code_hash, expires = twofactor.new_email_challenge()
                        server.session['two_factor_nonce'] = nonce
                        server.session['two_factor_code_hash'] = code_hash
                        server.session['two_factor_expires'] = expires
                        twofactor.send_email_code(code)
                    except Exception:
                        log.error('webpages.py', _('Could not send the login verification e-mail.') + '\n' + traceback.format_exc())
                        _clear_two_factor_login()
                        my_signin.note = _('The verification e-mail could not be sent. Please contact the administrator.')
                        return self.core_render.login(my_signin, None, False, None, None)
                return self.core_render.login(my_signin, None, True, method, None)

            server.session.regenerate_id()
            server.session.validated = True
            if 'remember-me' in qdict:
                autologin.issue(server.session.get('visitor'), server.session.get('category'))
            else:
                autologin.revoke_cookie_token()
            report_login()
            if options.run_logEV:
                logEV.save_events_log(_('Login'), _('User {} logged in from IP {} category {}').format(server.session.get('visitor'), server.session.get('ip'), server.session.get('category')), id='Login', level='info', category='security')
            log.info('webpages.py', _('User {} logged in').format(server.session.get('visitor')))
            raise web.seeother('/', True)


def _clear_two_factor_login():
    from ospy import server
    for key in (
        'two_factor_pending', 'two_factor_user', 'two_factor_category', 'two_factor_method',
        'two_factor_remember', 'two_factor_started', 'two_factor_attempts', 'two_factor_nonce',
        'two_factor_code_hash', 'two_factor_expires'):
        try:
            del server.session[key]
        except KeyError:
            pass


class twofactor_page(ProtectedPage):
    """Configure two-factor authentication for administrator accounts."""

    def GET(self):
        from ospy import server
        if server.session.get('category') != 'admin':
            raise web.seeother('/')
        if not server.session.get('two_factor_setup_secret'):
            server.session['two_factor_setup_secret'] = twofactor.generate_secret()
        email_available, email_message = twofactor.email_plugin_status()
        qr_available = twofactor.qr_png('test') is not None
        backup_codes = server.session.get('two_factor_new_backup_codes')
        if backup_codes:
            del server.session['two_factor_new_backup_codes']
        return self.core_render.twofactor(
            options.two_factor_method, server.session.get('two_factor_setup_secret'),
            email_available, email_message, qr_available, None, backup_codes,
            bool(server.session.get('two_factor_setup_email_hash')), None, None)

    def POST(self):
        from ospy import server
        if server.session.get('category') != 'admin':
            raise web.seeother('/')
        qdict = web.input()
        action = qdict.get('action', '')
        error = None
        notice = None
        setup_secret = server.session.get('two_factor_setup_secret') or twofactor.generate_secret()
        server.session['two_factor_setup_secret'] = setup_secret

        method = options.two_factor_method
        if action == 'verify_totp':
            if twofactor.qr_png('test') is None:
                error = _('QR code support is not installed. Run python setup.py install and restart OSPy.')
            elif not twofactor.verify_totp(setup_secret, qdict.get('code', '')):
                error = _('Enter the current code from the authenticator application to finish pairing.')
            else:
                method = twofactor.METHOD_TOTP
                options.two_factor_secret = setup_secret
        elif action == 'send_email':
            available, status_message = twofactor.email_plugin_status()
            if available:
                try:
                    code, nonce, code_hash, expires = twofactor.new_email_challenge()
                    twofactor.send_email_code(code)
                    server.session['two_factor_setup_email_nonce'] = nonce
                    server.session['two_factor_setup_email_hash'] = code_hash
                    server.session['two_factor_setup_email_expires'] = expires
                    notice = _('A verification code was sent. Enter it below to enable e-mail verification.')
                except Exception:
                    log.error('webpages.py', _('Could not send the setup verification e-mail.') + '\n' + traceback.format_exc())
                    error = _('The verification e-mail could not be sent. Check the plug-in settings and try again.')
            else:
                error = status_message
        elif action == 'verify_email':
            if not twofactor.verify_email_code(
                    qdict.get('email_code', ''),
                    server.session.get('two_factor_setup_email_nonce', ''),
                    server.session.get('two_factor_setup_email_hash', ''),
                    server.session.get('two_factor_setup_email_expires', 0)):
                error = _('The e-mail verification code is incorrect or has expired.')
            else:
                method = twofactor.METHOD_EMAIL
        elif action == 'disable':
            method = twofactor.METHOD_NONE
        else:
            error = _('Unknown two-factor authentication method.')

        if error is None and action in ('verify_totp', 'verify_email', 'disable'):
            old_method = options.two_factor_method
            options.two_factor_method = method
            if method != twofactor.METHOD_TOTP:
                options.two_factor_secret = ''
            if method == twofactor.METHOD_NONE:
                options.two_factor_backup_codes = []
            elif method != old_method:
                backup_codes = twofactor.generate_backup_codes()
                options.two_factor_backup_codes = [twofactor.hash_backup_code(code) for code in backup_codes]
                server.session['two_factor_new_backup_codes'] = backup_codes
            autologin.revoke_all()
            server.session['two_factor_setup_secret'] = twofactor.generate_secret()
            for key in ('two_factor_setup_email_nonce', 'two_factor_setup_email_hash',
                        'two_factor_setup_email_expires'):
                try:
                    del server.session[key]
                except KeyError:
                    pass
            raise web.seeother('/twofactor')

        email_available, email_message = twofactor.email_plugin_status()
        return self.core_render.twofactor(
            options.two_factor_method, setup_secret, email_available, email_message,
            twofactor.qr_png('test') is not None, error, None,
            bool(server.session.get('two_factor_setup_email_hash')), notice,
            'email' if action in ('send_email', 'verify_email') else
            ('totp' if action == 'verify_totp' else options.two_factor_method))


class twofactor_qr_page(ProtectedPage):
    def GET(self):
        from ospy import server
        verify_csrf(web.input())
        if server.session.get('category') != 'admin':
            raise web.notfound()
        secret = server.session.get('two_factor_setup_secret')
        if not secret:
            raise web.notfound()
        site_name = str(options.name or '').strip()
        issuer = 'OSPy' + ((' ' + site_name) if site_name else '')
        data = twofactor.qr_png(twofactor.provisioning_uri(secret, options.admin_user, issuer))
        if data is None:
            raise web.notfound()
        web.header('Content-Type', 'image/png')
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return data


class logout_page(WebPage):
    def GET(self):
        from ospy import server
        try:
            if options.run_logEV:
                logEV.save_events_log(_('Logout'), _('User {} logged out').format(server.session.get('visitor')), id='Login', level='info', category='security')
            log.info('webpages.py', _('User {} logged out').format(server.session.get('visitor')))
            autologin.revoke_cookie_token()
            server.session.kill()
        except:
            log.debug('webpages.py', traceback.format_exc())
        finally:
            raise web.seeother('/')


class home_page(ProtectedPage):
    """Open Home page."""

    def GET(self):
        from ospy.server import session

        if session.get('category')  == 'public':
            return self.core_render.home_public()
        elif session.get('category')  == 'user':
            return self.core_render.home_user()
        elif session.get('category') == 'admin':
            return self.core_render.home_admin()
        else:
            raise web.seeother('/')


class action_page(ProtectedPage):
    """Page to perform some simple actions (mainly from the homepage)."""

    def GET(self):
        from ospy.server import session

        qdict = web.input()
        action_keys = ('stop_all', 'scheduler_enabled', 'manual_mode', 'rain_block', 'level_adjustment', 'toggle_temp', 'set_to')
        if any(key in qdict for key in action_keys):
            verify_csrf(qdict)

        stop_all = get_input(qdict, 'stop_all', False, lambda x: True)
        scheduler_enabled = get_input(qdict, 'scheduler_enabled', None, lambda x: x == '1')
        manual_mode = get_input(qdict, 'manual_mode', None, lambda x: x == '1')
        rain_block = get_input(qdict, 'rain_block', None, float)
        level_adjustment = get_input(qdict, 'level_adjustment', None, float)
        toggle_temp = get_input(qdict, 'toggle_temp', False, lambda x: True)

        if stop_all:
            if session.get('category')  == 'admin' or session.get('category')  == 'user':
                if not options.manual_mode:
                    options.scheduler_enabled = False
                    programs.run_now_program = None
                    run_once.clear()
                log.finish_run(None)
                stations.clear()
                outputs.relay_output = False
                logEV.save_events_log(
                    _('Irrigation stopped'),
                    _('User {} stopped all stations and active programs.').format(session.get('visitor')),
                    level='warning',
                    category='irrigation'
                )
            else:
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice('/', msg)

        if scheduler_enabled is not None:
            if session.get('category')  == 'admin' or session.get('category') == 'user':
                if options.scheduler_enabled != scheduler_enabled:
                    options.scheduler_enabled = scheduler_enabled
                    logEV.save_events_log(
                        _('Scheduler setting changed'),
                        (_('User {} enabled the scheduler.') if scheduler_enabled else
                         _('User {} disabled the scheduler.')).format(session.get('visitor')),
                        level='info' if scheduler_enabled else 'warning',
                        category='configuration'
                    )
            else:
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice('/', msg)

        if manual_mode is not None:
            if session.get('category')== 'admin' or session.get('category') == 'user':
                if options.manual_mode != manual_mode:
                    options.manual_mode = manual_mode
                    logEV.save_events_log(
                        _('Manual mode changed'),
                        (_('User {} enabled manual mode.') if manual_mode else
                         _('User {} disabled manual mode.')).format(session.get('visitor')),
                        level='info',
                        category='configuration'
                    )
            else:
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice('/', msg)

        if rain_block is not None:
            if session.get('category')== 'admin' or session.get('category') == 'user':
                if rain_block == 0:
                    rain_blocks.clear()  # delete all parallel rain blocks (e.g. from CHMI plugin, current loop tank monitor...)
                    logEV.save_events_log(_('Rain delay'), _('User {} removed all rain delays.').format(session.get('visitor')), id='RainDelay', level='success', category='irrigation')
                else:
                    logEV.save_events_log(_('Rain delay'), _('User {} set a rain delay of {} hours.').format(session.get('visitor'), rain_block), id='RainDelay', level='warning', category='irrigation')
                options.rain_block = datetime.datetime.now() + datetime.timedelta(hours=rain_block)
                stop_onrain()
            else:
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice('/', msg)

        if level_adjustment is not None:
            if session.get('category')== 'admin' or session.get('category') == 'user':
                options.level_adjustment = level_adjustment / 100
                logEV.save_events_log(
                    _('Irrigation level changed'),
                    _('User {} set the global irrigation level to {} percent.').format(
                        session.get('visitor'), level_adjustment),
                    level='info',
                    category='configuration'
                )
            else:
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice('/', msg)

        if toggle_temp:
            if session.get('category')== 'admin' or session.get('category') == 'user':
                options.temp_unit = "F" if options.temp_unit == "C" else "C"
                logEV.save_events_log(
                    _('Temperature unit changed'),
                    _('User {} changed the temperature unit to {}.').format(
                        session.get('visitor'), options.temp_unit),
                    level='info',
                    category='configuration'
                )
            else:
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice('/', msg)

        set_to = get_input(qdict, 'set_to', None, int)
        sid = get_input(qdict, 'sid', 0, int) - 1
        set_time = get_input(qdict, 'set_time', 0, int)

        station_can_start = (
            0 <= sid < stations.count() and stations.get(sid).enabled and
            not stations.get(sid).is_master and
            not stations.get(sid).is_master_two and
            not stations.get(sid).is_master_by_program
        )
        if (set_to is not None and 0 <= sid < stations.count() and
                options.manual_mode and (not set_to or station_can_start)):
          if session.get('category')== 'admin' or session.get('category') == 'user':
            if set_to:  # if status is on
                start = datetime.datetime.now()
                new_schedule = {
                    'active': True,
                    'program': -1,
                    'station': sid,
                    'program_name': _('Manual'),
                    'fixed': True,
                    'cut_off': 0,
                    'manual': True,
                    'blocked': False,
                    'start': start,
                    'original_start': start,
                    'end': start + datetime.timedelta(days=3650),
                    'uid': '%s-%s-%d' % (str(start), "Manual", sid),
                    'usage': stations.get(sid).usage
                }
                if set_time > 0:  # if an optional duration time is given
                    new_schedule['end'] = datetime.datetime.now() + datetime.timedelta(seconds=set_time)

                log.start_run(new_schedule)
                stations.activate(new_schedule['station'])
                logEV.save_events_log(
                    _('Station started manually'),
                    _('User {} started station {} manually.').format(
                        session.get('visitor'), stations.get(sid).name),
                    level='info',
                    category='irrigation'
                )

            else:  # If status is off
                stations.deactivate(sid)
                active = log.active_runs()
                for interval in active:
                    if interval['station'] == sid:
                        log.finish_run(interval)
                logEV.save_events_log(
                    _('Station stopped manually'),
                    _('User {} stopped station {} manually.').format(
                        session.get('visitor'), stations.get(sid).name),
                    level='info',
                    category='irrigation'
                )
          else:
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        report_value_change()
        raise web.seeother('/')  # Send browser back to home page


class programs_page(ProtectedPage):
    """Open programs page."""

    def GET(self):
        from ospy.server import session

        if session.get('category') == 'admin':
            return self.core_render.programs()
        elif session.get('category')== 'user':
            return self.core_render.programs_user()
        else:
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

    def POST(self):
        from ospy.server import session

        qdict = web.input()
        action = qdict.get('action', '')

        if action == 'runnow' and session.get('category') in ['admin', 'user']:
            index = int(qdict.get('index', -1))
            program_name = programs[index].name if 0 <= index < programs.count() else str(index + 1)
            programs.run_now(index)
            Timer(0.1, programs.calculate_balances).start()
            report_program_runnow()
            logEV.save_events_log(
                _('Program started manually'),
                _('User {} requested immediate start of program {}.').format(
                    session.get('visitor'), program_name),
                id='Programs',
                level='info',
                category='irrigation'
            )
            raise web.seeother('/')

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        if action == 'delete_all':
            deleted_count = programs.count()
            while programs.count() > 0:
                programs.remove_program(programs.count()-1)
            report_program_deleted()
            logEV.save_events_log(
                _('All programs deleted'),
                _('User {} deleted all {} programs.').format(session.get('visitor'), deleted_count),
                id='Programs',
                level='warning',
                category='configuration'
            )

        elif action == 'delete':
            index = int(qdict.get('index', -1))
            program_name = programs[index].name if 0 <= index < programs.count() else str(index + 1)
            programs.remove_program(index)
            Timer(0.1, programs.calculate_balances).start()
            report_program_deleted()
            logEV.save_events_log(
                _('Program deleted'),
                _('User {} deleted program {}.').format(session.get('visitor'), program_name),
                id='Programs',
                level='warning',
                category='configuration'
            )

        elif action == 'enable':
            index = int(qdict.get('index', -1))
            if 0 <= index < programs.count():
                programs[index].enabled = qdict.get('enabled', '0') == '1'
                Timer(0.1, programs.calculate_balances).start()
                report_program_toggle()
                logEV.save_events_log(
                    _('Program setting changed'),
                    (_('User {} enabled program {}.') if programs[index].enabled else
                     _('User {} disabled program {}.')).format(
                        session.get('visitor'), programs[index].name),
                    id='Programs',
                    level='info',
                    category='configuration'
                )

        elif action == 'copy':
            index = int(qdict.get('index', -1))
            program_name = programs[index].name if 0 <= index < programs.count() else str(index + 1)
            programs.copy_program(index)
            Timer(0.1, programs.calculate_balances).start()
            report_program_change()
            logEV.save_events_log(
                _('Program copied'),
                _('User {} copied program {}.').format(session.get('visitor'), program_name),
                id='Programs',
                level='info',
                category='configuration'
            )

        elif action == 'move':
            index = int(qdict.get('index', -1))
            programs.move_program(index, qdict.get('group_id', 'default'))
            report_program_change()

        elif action == 'add_group':
            group_name = qdict.get('group_name', '')
            programs.add_group(group_name)
            report_program_change()
            logEV.save_events_log(
                _('Program group created'),
                _('User {} created program group {}.').format(session.get('visitor'), group_name),
                id='Programs',
                level='info',
                category='configuration'
            )

        elif action == 'rename_group':
            programs.rename_group(qdict.get('group_id', 'default'), qdict.get('group_name', ''))
            report_program_change()

        elif action == 'toggle_group':
            programs.toggle_group_collapsed(qdict.get('group_id', 'default'))

        elif action == 'delete_group':
            if not programs.remove_group(qdict.get('group_id', 'default')):
                return self.core_render.notice('/programs', _('Cancel the active postponement before deleting this program group.'))
            report_program_change()

        elif action == 'copy_group':
            programs.copy_group(qdict.get('group_id', 'default'))
            Timer(0.1, programs.calculate_balances).start()
            report_program_change()

        elif action == 'enable_group':
            programs.set_group_enabled(qdict.get('group_id', 'default'), qdict.get('enabled', '0') == '1')
            Timer(0.1, programs.calculate_balances).start()
            report_program_toggle()

        elif action == 'postpone_group':
            group_id = qdict.get('group_id', '')
            target_value = qdict.get('target_start', '')
            try:
                if len(target_value) != 16:
                    raise ValueError
                target_start = datetime.datetime.strptime(target_value, '%Y-%m-%dT%H:%M')
                postponement = programs.create_group_postponement(group_id, target_start)
            except (TypeError, ValueError) as error:
                message = str(error) or _('Invalid postponement date and time.')
                return self.core_render.notice('/programs', message)

            group = programs.program_group(group_id)
            if options.run_logEV:
                logEV.save_events_log(
                    _('Programs'),
                    _('User {} postponed program group {} from {} to {}').format(
                        session.get('visitor'),
                        group['name'],
                        postponement['source_start'].strftime('%Y-%m-%d %H:%M'),
                        postponement['target_start'].strftime('%Y-%m-%d %H:%M')
                    ),
                    id='Programs',
                    level='info',
                    category='configuration'
                )
            Timer(0.1, programs.calculate_balances).start()
            report_program_change()

        elif action == 'cancel_group_postponement':
            group_id = qdict.get('group_id', '')
            postponement_id = qdict.get('postponement_id', '')
            postponement = programs.cancel_group_postponement(group_id, postponement_id)
            if postponement is None:
                return self.core_render.notice('/programs', _('The program group postponement was not found.'))

            group = programs.program_group(group_id)
            if options.run_logEV:
                logEV.save_events_log(
                    _('Programs'),
                    _('User {} cancelled postponement of program group {}').format(
                        session.get('visitor'), group['name']
                    ),
                    id='Programs',
                    level='info',
                    category='configuration'
                )
            Timer(0.1, programs.calculate_balances).start()
            report_program_change()

        raise web.seeother('/programs')

class program_page(ProtectedPage):
    """Open page to allow program modification."""

    def GET(self, index):
        qdict = web.input()
        try:
            index = int(index)
        except ValueError:
            pass

        if isinstance(index, int):
            program = programs.get(index)
        else:
            program = programs.create_program()
            program.group_id = qdict.get('group_id', 'default')
            program.set_days_simple(6*60, 30, 30, 0, [])

        report_program_change()
        return self.core_render.program(program)

    def POST(self, index):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        is_new_program = False
        try:
            index = int(index)
            program = programs.get(index)
        except ValueError:
            program = programs.create_program()
            is_new_program = True

        qdict['schedule_type'] = int(qdict['schedule_type'])

        program.name = qdict['name']
        program.stations = json.loads(qdict['stations'])
        program.group_id = qdict.get('group_id', getattr(program, 'group_id', 'default'))
        program.enabled = True if qdict.get('enabled', 'off') == 'on' else False

        if qdict['schedule_type'] == ProgramType.WEEKLY_WEATHER:
            program.cut_off = 0
            program.fixed = True
        else:
            program.cut_off = int(qdict['cut_off'])
            program.fixed = True if qdict.get('fixed', 'off') == 'on' else False

        simple = [int(qdict['simple_hour']) * 60 + int(qdict['simple_minute']),
                  int(qdict['simple_duration']),
                  int(qdict['simple_pause']),
                  int(qdict['simple_rcount']) if qdict.get('simple_repeat', 'off') == 'on' else 0]

        repeat_start_date = datetime.datetime.combine(datetime.date.today(), datetime.time.min) + \
                            datetime.timedelta(days=int(qdict['interval_delay']))

        if qdict['schedule_type'] == ProgramType.DAYS_SIMPLE:
            program.set_days_simple(*(simple + [
                                    json.loads(qdict['days'])]))

        elif qdict['schedule_type'] == ProgramType.DAYS_ADVANCED:
            program.set_days_advanced(json.loads(qdict['advanced_schedule_data']),
                                      json.loads(qdict['days']))

        elif qdict['schedule_type'] == ProgramType.REPEAT_SIMPLE:
            program.set_repeat_simple(*(simple + [
                                      int(qdict['interval']),
                                      repeat_start_date]))

        elif qdict['schedule_type'] == ProgramType.REPEAT_ADVANCED:
            program.set_repeat_advanced(json.loads(qdict['advanced_schedule_data']),
                                        int(qdict['interval']),
                                        repeat_start_date)

        elif qdict['schedule_type'] == ProgramType.WEEKLY_ADVANCED:
            program.set_weekly_advanced(json.loads(qdict['weekly_schedule_data']))

        elif qdict['schedule_type'] == ProgramType.WEEKLY_WEATHER:
            program.set_weekly_weather(int(qdict['weather_irrigation_min']),
                                       int(qdict['weather_irrigation_max']),
                                       int(qdict['weather_run_max']),
                                       int(qdict['weather_pause_ratio'])/100.0,
                                       json.loads(qdict['weather_pems_data']),
                                       )

        elif qdict['schedule_type'] == ProgramType.CUSTOM:
            program.modulo = int(qdict['interval'])*1440
            program.manual = False
            program.start = repeat_start_date
            program.schedule = json.loads(qdict['custom_schedule_data'])

        if 'control_master' in qdict:
            program.control_master = int(qdict['control_master'])

        if program.index < 0:
            programs.add_program(program)

        Timer(0.1, programs.calculate_balances).start()
        report_program_toggle()
        logEV.save_events_log(
            _('Program created') if is_new_program else _('Program updated'),
            _('User {} created program {}.').format(session.get('visitor'), program.name)
            if is_new_program else
            _('User {} updated program {}.').format(session.get('visitor'), program.name),
            id='Programs',
            level='info',
            category='configuration'
        )
        raise web.seeother('/programs')


class runonce_page(ProtectedPage):
    """Open a page to view and edit a run once program."""

    def GET(self):
        from ospy.server import session
        if session.get('category')== 'admin' or session.get('category') == 'user':
            return self.core_render.runonce()
        else:
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

    def POST(self):
        from ospy.server import session

        qdict = web.input()
        station_seconds = {}
        for station in stations.enabled_stations():
            mm_str = "mm" + str(station.index)
            ss_str = "ss" + str(station.index)
            if mm_str in qdict and ss_str in qdict:
                seconds = int(qdict[mm_str] or 0) * 60 + int(qdict[ss_str] or 0)
                station_seconds[station.index] = seconds

        if session.get('category')== 'admin' or session.get('category') == 'user':
            run_once.set(station_seconds)
            report_program_toggle()
            active_stations = len([seconds for seconds in station_seconds.values() if seconds > 0])
            logEV.save_events_log(
                _('Run-once program changed'),
                _('User {} scheduled one-time irrigation for {} stations.').format(
                    session.get('visitor'), active_stations),
                id='Programs',
                level='info',
                category='irrigation'
            )
            raise web.seeother('/')
        else:
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)


class plugins_manage_page(ProtectedPage):
    """Manage plugins page."""

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        changes = get_input(qdict, 'changes', None)
        plugins.checker.sync_installed_statuses()

        if changes is not None and changes in plugins.available():
            available_info = plugins.checker.available_version(changes)
            repo_index = available_info['repo_index'] if available_info is not None else 0
            change_list = plugins.checker.plugin_changes(changes, repo_index=repo_index, force=True)
            for change in change_list:
                change['date'] = _format_display_datetime(change.get('date', ''))
            if available_info is not None and change_list:
                available_info = available_info.copy()
                available_info['date'] = change_list[0].get('date', available_info.get('date', ''))
            if available_info is not None:
                available_info = available_info.copy()
                available_info['date'] = _format_display_datetime(available_info.get('date', ''))
            current_info = dict(options.plugin_status)
            if changes in current_info and isinstance(current_info[changes], dict):
                current_info[changes] = current_info[changes].copy()
                current_info[changes]['date'] = _format_display_datetime(current_info[changes].get('date', ''))
            return self.core_render.plugins_changes(changes, change_list, available_info, current_info)

        return self.core_render.plugins_manage()

    def POST(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        action = qdict.get('action', '')
        plugin = get_input(qdict, 'plugin', None)

        if action == 'refresh':
            plugins.checker.refresh(install_updates=False)
            raise web.seeother('/plugins_manage')

        if action == 'update_channel':
            channel = str(qdict.get('channel', '')).strip().lower()
            if channel not in plugins.PLUGIN_UPDATE_CHANNELS:
                return self.core_render.notice(
                    '/plugins_manage', _('Invalid plug-in update channel.')
                )
            if channel != plugins.plugin_update_channel():
                options.plugin_update_channel = channel
                plugins.checker.clear_repository_cache()
                plugins.checker.update()
                logEV.save_events_log(
                    _('Plug-in update channel changed'),
                    _('User {} changed the plug-in update channel to {}.').format(
                        session.get('visitor'), channel
                    ),
                    level='warning' if channel == 'beta' else 'info',
                    category='system'
                )
            raise web.seeother('/plugins_manage')

        if action == 'disable_all':
            options.enabled_plugins = []
            plugins.start_enabled_plugins()
            logEV.save_events_log(
                _('Plug-ins disabled'),
                _('User {} disabled all plug-ins.').format(session.get('visitor')),
                level='warning',
                category='system'
            )

        elif action == 'enable_all':
            skipped_plugins = []
            for plugin in plugins.available():
                enabled_candidates = list(options.enabled_plugins) + [plugin]
                compatibility = plugins.plugin_compatibility(
                    plugin, enabled_candidates
                )
                preflight = plugins.plugin_preflight(plugin)
                if compatibility['compatible'] and preflight['passed']:
                    if plugin not in options.enabled_plugins:
                        options.enabled_plugins.append(plugin)
                else:
                    skipped_plugins.append(plugin)
            options.enabled_plugins = options.enabled_plugins
            plugins.start_enabled_plugins()
            logEV.save_events_log(
                _('Plug-ins enabled'),
                _('User {} enabled all available plug-ins.').format(session.get('visitor')),
                level='info',
                category='system'
            )
            if skipped_plugins:
                return self.core_render.notice(
                    '/plugins_manage',
                    _('Some incompatible plug-ins were not enabled') +
                    ': ' + ', '.join(skipped_plugins)
                )

        elif action == 'delete_all':
            from ospy.helpers import del_rw
            import shutil
            for plugin in plugins.available():
                if plugin in options.enabled_plugins:
                    options.enabled_plugins.remove(plugin)
                shutil.rmtree(os.path.join('plugins', plugin), onerror=del_rw)
            options.enabled_plugins = options.enabled_plugins  # Explicit write to save to file
            plugins.start_enabled_plugins()
            logEV.save_events_log(
                _('Plug-ins deleted'),
                _('User {} deleted all plug-ins.').format(session.get('visitor')),
                level='warning',
                category='system'
            )
            raise web.seeother('/plugins_manage')

        elif action in ['enable', 'delete'] and plugin is not None and plugin in plugins.available():
            enable = qdict.get('enable', '0') == '1'
            if action == 'delete':
                enable = False

            if enable:
                preflight = plugins.plugin_preflight(plugin)
                if not preflight['passed']:
                    return self.core_render.notice(
                        '/plugins_manage',
                        _('Plug-in pre-activation test failed') + ': ' +
                        '; '.join(preflight['errors'])
                    )
                compatibility = plugins.plugin_compatibility(
                    plugin, list(options.enabled_plugins) + [plugin]
                )
                if not compatibility['compatible']:
                    return self.core_render.notice(
                        '/plugins_manage',
                        _('Plug-in cannot be enabled') + ': ' +
                        '; '.join(compatibility['errors'])
                    )

            if not enable and plugin in options.enabled_plugins:
                options.enabled_plugins.remove(plugin)
            elif enable and plugin not in options.enabled_plugins:
                options.enabled_plugins.append(plugin)
            options.enabled_plugins = options.enabled_plugins  # Explicit write to save to file
            plugins.start_enabled_plugins()

            if action == 'delete':
                from ospy.helpers import del_rw
                import shutil
                shutil.rmtree(os.path.join('plugins', plugin), onerror=del_rw)

            if action == 'delete':
                event_subject = _('Plug-in deleted')
                event_status = _('User {} deleted plug-in {}.').format(session.get('visitor'), plugin)
                event_level = 'warning'
            elif enable:
                event_subject = _('Plug-in enabled')
                event_status = _('User {} enabled plug-in {}.').format(session.get('visitor'), plugin)
                event_level = 'info'
            else:
                event_subject = _('Plug-in disabled')
                event_status = _('User {} disabled plug-in {}.').format(session.get('visitor'), plugin)
                event_level = 'warning'
            logEV.save_events_log(
                event_subject,
                event_status,
                level=event_level,
                category='system'
            )

            raise web.seeother('/plugins_manage')

        elif action == 'auto_update':
            options.auto_plugin_update = qdict.get('enabled', '0') == '1'
            plugins.checker.update()
            raise web.seeother('/plugins_manage')

        elif action == 'use_update':
            options.use_plugin_update = qdict.get('enabled', '0') == '1'
            plugins.checker.update()
            raise web.seeother('/plugins_manage')

        raise web.seeother('/plugins_manage')


class plugins_install_page(ProtectedPage):
    """Manage plugins page."""

    @staticmethod
    def _result_message(result):
        messages = []
        installed = result.get('installed', [])
        blocked = result.get('blocked', {})
        warnings = result.get('warnings', {})
        if installed:
            messages.append(
                _('Installed plug-ins') + ': ' + ', '.join(installed)
            )
        if blocked:
            details = []
            for plugin, reasons in sorted(blocked.items()):
                details.append('{}: {}'.format(plugin, '; '.join(reasons)))
            messages.append(
                _('Skipped incompatible plug-ins') + ': ' + ' | '.join(details)
            )
        if warnings:
            details = []
            for plugin, plugin_warnings in sorted(warnings.items()):
                details.append(
                    '{}: {}'.format(plugin, '; '.join(plugin_warnings))
                )
            messages.append(
                _('Compatibility warnings') + ': ' + ' | '.join(details)
            )
        return ' | '.join(messages)

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        plugins.checker.update()
        return self.core_render.plugins_install()


    def POST(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input(zipfile={})

        if qdict.get('action', '') == 'install_repo':
            repo = get_input(qdict, 'repo', None, int)
            plugin = get_input(qdict, 'plugin', None)
            repositories = plugins.plugin_repositories()
            if repo is not None and 0 <= repo < len(repositories):
                source_repo = repositories[repo]
                source_plugin = plugin if plugin else _('all plugins')
                log.info('webpages.py', _('Installing plug-in {} from {}').format(source_plugin, source_repo))
                try:
                    result = plugins.checker.install_repo_plugin(source_repo, plugin)
                    logEV.save_events_log(
                        _('Plug-in installation completed'),
                        _('User {} installed {} from {}.').format(
                            session.get('visitor'),
                            ', '.join(result.get('installed', [])) or source_plugin,
                            source_repo),
                        level='success',
                        category='system'
                    )
                    if result.get('blocked') or result.get('warnings'):
                        return self.core_render.notice(
                            '/plugins_install', self._result_message(result)
                        )
                except ValueError as err:
                    log.error('webpages.py', str(err))
                    logEV.save_events_log(
                        _('Plug-in installation failed'),
                        _('Plug-in installation from {} failed: {}').format(
                            source_repo, err),
                        level='error',
                        category='system'
                    )
                    return self.core_render.notice('/plugins_install', str(err))
            else:
                log.error('webpages.py', _('Invalid plug-in repository index: {}').format(repo))
                raise web.badrequest()
            self._redirect_back()

        if 'zipfile' in qdict and hasattr(qdict['zipfile'], 'file'):
            import io
            zip_file_data = qdict['zipfile'].file
            filename = getattr(qdict['zipfile'], 'filename', _('uploaded ZIP'))
            log.info('webpages.py', _('Installing custom plug-in from uploaded ZIP: {}').format(filename))
            try:
                result = plugins.checker.install_custom_plugin(
                    io.BytesIO(read_limited_upload(zip_file_data))
                )
                logEV.save_events_log(
                    _('Plug-in installation completed'),
                    _('User {} installed {} from {}.').format(
                        session.get('visitor'),
                        ', '.join(result.get('installed', [])),
                        filename),
                    level='success',
                    category='system'
                )
                if result.get('blocked') or result.get('warnings'):
                    return self.core_render.notice(
                        '/plugins_install', self._result_message(result)
                    )
            except ValueError as err:
                log.error('webpages.py', str(err))
                logEV.save_events_log(
                    _('Plug-in installation failed'),
                    _('Plug-in installation from {} failed: {}').format(filename, err),
                    level='error',
                    category='system'
                )
                return self.core_render.notice('/plugins_install', str(err))

        self._redirect_back()


def _process_memory_kb():
    try:
        if os.name == 'posix':
            with open('/proc/self/status') as fh:
                for line in fh:
                    if line.startswith('VmRSS:'):
                        return int(line.split()[1])
        return None
    except Exception:
        return None


def _update_diagnostics_plugin_history(plugin_data, now):
    cutoff = now - _DIAGNOSTICS_HISTORY_SECONDS
    active_modules = set()

    with _diagnostics_history_lock:
        for plugin in plugin_data:
            module = plugin.get('module')
            if not module:
                continue
            active_modules.add(module)
            value = plugin.get('cpu_percent')
            if value is None:
                continue
            try:
                sample = [int(now), float(value)]
            except (TypeError, ValueError):
                continue

            history = _diagnostics_plugin_history.setdefault(module, [])
            history.append(sample)
            while history and history[0][0] < cutoff:
                history.pop(0)

        for module in list(_diagnostics_plugin_history.keys()):
            if module not in active_modules:
                history = _diagnostics_plugin_history[module]
                while history and history[0][0] < cutoff:
                    history.pop(0)
                if not history:
                    _diagnostics_plugin_history.pop(module, None)


def _collect_diagnostics_plugin_history():
    """Collect one plug-in CPU sample independently of the Diagnostics page."""
    try:
        _update_diagnostics_plugin_history(plugins.plugin_diagnostics(), time.time())
    except Exception:
        log.error('webpages.py', _('Plug-in diagnostics history sampling failed.') + '\n' + traceback.format_exc())


def _diagnostics_history_worker():
    while not _diagnostics_history_stop.is_set():
        _collect_diagnostics_plugin_history()
        _diagnostics_history_stop.wait(_DIAGNOSTICS_HISTORY_SAMPLE_SECONDS)


def start_diagnostics_history():
    """Start the in-memory background sampler once plug-ins are running."""
    global _diagnostics_history_thread, _diagnostics_history_stop
    if _diagnostics_history_thread is not None and _diagnostics_history_thread.is_alive():
        return
    _diagnostics_history_stop = Event()
    _diagnostics_history_thread = Thread(
        target=_diagnostics_history_worker, name='OSPy diagnostics history')
    _diagnostics_history_thread.daemon = True
    _diagnostics_history_thread.start()


def stop_diagnostics_history():
    """Stop the background sampler without persisting its in-memory history."""
    global _diagnostics_history_thread
    _diagnostics_history_stop.set()
    if (_diagnostics_history_thread is not None and
            _diagnostics_history_thread.is_alive() and
            _diagnostics_history_thread is not current_thread()):
        _diagnostics_history_thread.join(2.0)
    _diagnostics_history_thread = None


def _limit_diagnostics_history(history):
    if len(history) <= _DIAGNOSTICS_HISTORY_POINTS:
        return history
    step = int(len(history) / _DIAGNOSTICS_HISTORY_POINTS) + 1
    return history[::step]


def _diagnostics_history_payload(module, seconds):
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        seconds = 3600
    seconds = max(60, min(_DIAGNOSTICS_HISTORY_SECONDS, seconds))

    with _diagnostics_history_lock:
        history = list(_diagnostics_plugin_history.get(module, []))

    if history:
        cutoff = history[-1][0] - seconds
        history = [sample for sample in history if sample[0] >= cutoff]

    return _limit_diagnostics_history(history)


def _diagnostics_data():
    import platform
    import threading
    import sys
    from ospy.helpers import uptime, get_cpu_temp, get_cpu_usage

    global _diagnostics_process_sample

    now = time.time()
    proc_cpu = time.process_time()
    process_cpu_percent = None
    if _diagnostics_process_sample:
        elapsed = max(0.001, now - _diagnostics_process_sample.get('time', now))
        cpu_delta = max(0.0, proc_cpu - _diagnostics_process_sample.get('cpu', proc_cpu))
        process_cpu_percent = round((cpu_delta / elapsed) * 100.0, 1)
    _diagnostics_process_sample = {'time': now, 'cpu': proc_cpu}

    load_average = []
    try:
        load_average = [round(value, 2) for value in os.getloadavg()]
    except Exception:
        pass

    system_info_link = None
    try:
        if 'system_info' in plugins.running():
            system_info_link = plugins.plugin_url(plugins.get('system_info').LINK)
    except Exception:
        pass

    system_uptime = '-'
    if os.name == 'posix' and os.path.isfile('/proc/uptime'):
        system_uptime = uptime()

    plugin_data = []
    diagnostics_error = ''
    try:
        plugin_data = plugins.plugin_diagnostics()
    except Exception:
        diagnostics_error = _('Plug-in diagnostics refresh failed.')
        log.error('webpages.py', traceback.format_exc())

    return {
        'system': {
            'cpu_usage': get_cpu_usage(),
            'cpu_temp': get_cpu_temp(options.temp_unit),
            'temp_unit': options.temp_unit,
            'uptime': system_uptime,
            'load_average': load_average,
            'platform': platform.platform(),
            'python': sys.version.split()[0],
        },
        'process': {
            'pid': os.getpid(),
            'cpu_percent': process_cpu_percent,
            'cpu_seconds': round(proc_cpu, 3),
            'memory_kb': _process_memory_kb(),
            'thread_count': threading.active_count(),
        },
        'plugins': plugin_data,
        'diagnostics_error': diagnostics_error,
        'system_info_link': system_info_link,
        'time': datetime_string(),
    }


def _health_time(timestamp):
    if not timestamp:
        return ''
    try:
        return datetime_string(datetime.datetime.fromtimestamp(float(timestamp)))
    except (TypeError, ValueError, OSError):
        return ''


def _health_item(item_id, title, status, summary, details='', updated='', link='',
                 confirmation_required=False, solution=''):
    return {
        'id': item_id,
        'title': title,
        'status': status,
        'summary': summary,
        'details': details,
        'updated': updated,
        'link': link,
        'confirmation_required': confirmation_required,
        'solution': solution,
    }


def _security_item(item_id, title, home_status, internet_status, summary,
                   details='', solution='', link='/options'):
    """Return one passive security check for both recommendation profiles."""
    return {
        'id': item_id,
        'title': title,
        'status': {
            'home': home_status,
            'internet': internet_status,
        },
        'summary': summary,
        'details': details,
        'solution': solution,
        'link': link,
    }


def _security_health_data():
    """Describe configured security controls without changing any setting."""
    items = []

    try:
        https_active = bool(web.config.session_parameters.secure)
    except Exception:
        https_active = False
    https_configured = bool(options.use_ssl or options.use_own_ssl)
    if https_active:
        https_summary = _('HTTPS is active.')
        https_details = _('Session cookies are restricted to encrypted connections.')
        https_home = https_internet = 'ok'
    elif https_configured:
        https_summary = _('HTTPS is configured, but it is not active.')
        https_details = _('Check the configured certificate and private key files, then restart OSPy.')
        https_home, https_internet = 'warning', 'error'
    else:
        https_summary = _('HTTPS is disabled.')
        https_details = _('Credentials and session data are not encrypted by OSPy during transport.')
        https_home, https_internet = 'warning', 'error'
    items.append(_security_item(
        'https', _('HTTPS'), https_home, https_internet,
        https_summary, https_details,
        _('Enable HTTPS in Options or use a trusted HTTPS reverse proxy before exposing OSPy outside the local network.'),
        '/options#security-options'
    ))

    anonymous = bool(options.no_password)
    items.append(_security_item(
        'anonymous', _('Anonymous access'),
        'error' if anonymous else 'ok',
        'error' if anonymous else 'ok',
        _('Anonymous access is enabled.') if anonymous else _('A password is required to access OSPy.'),
        _('Anyone who can reach OSPy can control it without signing in.') if anonymous else '',
        _('Disable anonymous access and use a unique administrator password.') if anonymous else '',
        '/options#users-options'
    ))

    two_factor_method = str(getattr(options, 'two_factor_method', 'none') or 'none')
    two_factor = two_factor_method in ('totp', 'email')
    items.append(_security_item(
        'two_factor', _('Two-factor authentication'),
        'ok' if two_factor else 'warning',
        'ok' if two_factor else 'error',
        _('Two-factor authentication is enabled.') if two_factor else _('Two-factor authentication is disabled.'),
        (_('Authentication application (TOTP) is configured.')
         if two_factor_method == 'totp' else
         _('E-mail verification codes are configured.')
         if two_factor_method == 'email' else
         _('A password alone protects the administrator account.')),
        '' if two_factor else _('Enable TOTP or e-mail verification and safely store the recovery codes.'),
        '/options#users-options'
    ))

    sensor_auth = bool(getattr(options, 'api_sensor_auth_required', False))
    items.append(_security_item(
        'sensor_api_auth', _('Sensor API authentication'),
        'ok' if sensor_auth else 'warning',
        'ok' if sensor_auth else 'error',
        _('Sensor reports require authentication.') if sensor_auth else _('Sensor reports do not require authentication.'),
        (_('Only authenticated sensor clients may submit measurements.') if sensor_auth else
         _('Legacy sensor firmware may submit measurements without credentials.')),
        '' if sensor_auth else _('Enable sensor API authentication after confirming that every sensor supports credentials.'),
        '/options#security-options'
    ))

    api_csrf = bool(getattr(options, 'api_csrf_required', False))
    items.append(_security_item(
        'api_csrf', _('API CSRF protection'),
        'ok' if api_csrf else 'warning',
        'ok' if api_csrf else 'error',
        _('State-changing API requests require a CSRF token.') if api_csrf else _('API CSRF protection is disabled.'),
        (_('Browser-based API clients must provide the OSPy CSRF token.') if api_csrf else
         _('Older API integrations may change OSPy state without a CSRF token.')),
        '' if api_csrf else _('Enable API CSRF protection after updating integrations that change OSPy state.'),
        '/options#security-options'
    ))

    cors_value = getattr(options, 'api_cors_allowed_origin', '*')
    cors_value = cors_value.strip() if isinstance(cors_value, str) else '*'
    cors_open = cors_value == '*'
    cors_disabled = not cors_value
    if cors_open:
        cors_summary = _('API CORS allows every browser origin.')
        cors_details = _('Any web page may read permitted OSPy API responses from a browser.')
    elif cors_disabled:
        cors_summary = _('API CORS headers are disabled.')
        cors_details = _('Cross-origin browser access to the OSPy API is not allowed.')
    else:
        cors_summary = _('API CORS is restricted to configured origins.')
        cors_details = cors_value
    items.append(_security_item(
        'cors', _('API CORS'),
        'warning' if cors_open else 'ok',
        'error' if cors_open else 'ok',
        cors_summary, cors_details,
        _('Replace the wildcard with the exact trusted browser origin, or leave the setting empty if CORS is not needed.') if cors_open else '',
        '/options#security-options'
    ))

    sensor_password = str(getattr(options, 'sensor_fw_passwd', '') or '')
    default_sensor_password = 'fg4s5b.s,trr7sw8sgyvrDfg'
    password_default = sensor_password == default_sensor_password
    password_weak = (
        len(sensor_password) < 12 or sensor_password.isdigit() or
        sensor_password.isalpha()
    )
    if not sensor_password:
        password_summary = _('The sensor password is empty.')
        password_details = _('Sensor firmware administration is not protected by a password.')
        password_home = password_internet = 'error'
    elif password_default:
        password_summary = _('The default sensor password is still configured.')
        password_details = _('The published default value must not be treated as a secret.')
        password_home = password_internet = 'error'
    elif password_weak:
        password_summary = _('The sensor password appears weak.')
        password_details = _('Use at least 12 characters with a mixture of character types.')
        password_home, password_internet = 'warning', 'error'
    else:
        password_summary = _('The sensor password is not the default and meets the basic length check.')
        password_details = _('The password value is never displayed by Diagnostics.')
        password_home = password_internet = 'ok'
    items.append(_security_item(
        'sensor_password', _('Sensor password'),
        password_home, password_internet, password_summary, password_details,
        '' if password_home == 'ok' else _('Set a unique sensor password in Options and configure the same value in every sensor.'),
        '/options#sensors-options'
    ))

    # OSPy currently sets selected response headers only on individual routes.
    # A reverse proxy may add more headers, but that cannot be verified before
    # its response leaves this process, so report the core guarantee precisely.
    items.append(_security_item(
        'http_headers', _('Security HTTP headers'), 'warning', 'error',
        _('OSPy does not add the complete recommended security header set globally.'),
        _('A reverse proxy may provide these headers, but OSPy cannot verify that configuration itself.'),
        _('Configure Content-Security-Policy, frame protection, MIME sniffing protection and a suitable Referrer-Policy on the HTTPS endpoint.'),
        '/help'
    ))

    profiles = [
        {
            'id': 'home',
            'name': _('Home network'),
            'description': _('For OSPy reachable only from a trusted local network. HTTPS, two-factor authentication and strict API controls are still recommended.'),
        },
        {
            'id': 'internet',
            'name': _('Internet access'),
            'description': _('For OSPy reachable through the Internet. HTTPS, authentication and restricted browser/API access are required.'),
        },
    ]
    summaries = {}
    for profile in ('home', 'internet'):
        statuses = [item['status'][profile] for item in items]
        summaries[profile] = (
            'error' if 'error' in statuses else
            'warning' if 'warning' in statuses else
            'ok'
        )
    return {
        'items': items,
        'profiles': profiles,
        'status': summaries,
        'time': datetime_string(),
    }


def _plugin_health_groups(plugin_data):
    """Separate immediate failures from health states that can be transitional."""
    immediate_failures = [
        plugin for plugin in plugin_data
        if plugin.get('enabled') and (
            not plugin.get('running') or plugin.get('last_error') or
            plugin.get('compatibility', {}).get('status') == 'error' or
            plugin.get('preflight', {}).get('status') == 'error'
        )
    ]
    immediate_failure_ids = {id(plugin) for plugin in immediate_failures}
    health_failures = [
        plugin for plugin in plugin_data
        if plugin.get('enabled') and
        plugin.get('health', {}).get('status') == 'error' and
        id(plugin) not in immediate_failure_ids
    ]
    warnings = [
        plugin for plugin in plugin_data
        if plugin.get('enabled') and (
            plugin.get('health', {}).get('status') == 'warning' or
            plugin.get('compatibility', {}).get('status') == 'warning' or
            plugin.get('preflight', {}).get('status') == 'warning'
        )
    ]
    return immediate_failures, health_failures, warnings


def _newest_file(paths):
    newest = None
    for path in paths:
        if not os.path.isfile(path):
            continue
        try:
            modified = os.path.getmtime(path)
            if newest is None or modified > newest[1]:
                newest = (path, modified, os.path.getsize(path))
        except OSError:
            continue
    return newest


def _runtime_health_items():
    """Convert active core issues into System status rows."""
    items = []
    for issue in health.active_issues():
        occurrence_details = '{}: {}'.format(
            _('Occurrences'), issue.get('count', 1)
        )
        if issue.get('details'):
            occurrence_details = issue['details'] + '; ' + occurrence_details
        items.append(_health_item(
            'runtime:' + issue.get('id', ''),
            issue.get('title') or _('Runtime problem'),
            issue.get('severity', 'error'),
            issue.get('summary') or _('A recoverable internal operation failed.'),
            occurrence_details,
            _health_time(issue.get('last_seen')),
            issue.get('link', ''),
            solution=issue.get('solution', ''),
        ))
    return items


def _system_health_data():
    """Build a lightweight operational overview without active hardware tests."""
    from glob import glob
    from ospy.helpers import get_external_ip, external_ip_refresh_pending

    now_ts = time.time()
    beats = health.snapshot()
    items = []

    scheduler_beat = beats.get('scheduler', {})
    scheduler_age = now_ts - scheduler_beat.get('last_success', 0)
    scheduler_alive = scheduler.scheduler.is_alive()
    scheduler_ok = scheduler_alive and scheduler_age <= 5
    scheduler_status = 'ok' if scheduler_ok else 'error'
    scheduler_summary = (
        _('Scheduler is running and responding.')
        if scheduler_ok else _('Scheduler is not responding.')
    )
    if scheduler_ok and not options.scheduler_enabled:
        scheduler_status = 'warning'
        scheduler_summary = _('Scheduler is running, but automatic scheduling is disabled.')
    items.append(_health_item(
        'scheduler', _('Scheduler'), scheduler_status, scheduler_summary,
        scheduler_beat.get('error', ''),
        _health_time(scheduler_beat.get('last_success'))
    ))

    calculation = beats.get('schedule_calculation', {})
    calc_details = calculation.get('details', {})
    calc_age = now_ts - calculation.get('last_success', 0)
    if options.manual_mode:
        calc_status = 'warning'
        calc_summary = _('Manual mode is active; automatic schedule calculation is paused.')
    elif calculation.get('last_success') and calc_age <= 10:
        calc_status = 'ok'
        calc_summary = _('The schedule was calculated successfully.')
    else:
        calc_status = 'error'
        calc_summary = _('No recent successful schedule calculation was recorded.')
    next_parts = [
        calc_details.get('next_start', ''),
        calc_details.get('next_program', ''),
        calc_details.get('next_station', ''),
    ]
    next_text = ' / '.join([part for part in next_parts if part])
    calc_description = _('Planned intervals') + ': {}'.format(
        calc_details.get('intervals', 0)
    )
    if next_text:
        calc_description += '; ' + _('Next run') + ': ' + next_text
    items.append(_health_item(
        'schedule', _('Schedule calculation'), calc_status, calc_summary,
        calc_description, _health_time(calculation.get('last_success')),
        '/programs'
    ))

    output_beat = beats.get('outputs', {})
    output_details = output_beat.get('details', {})
    master_output_beat = beats.get('master_output', {})
    master_output_details = master_output_beat.get('details', {})
    output_physical = bool(output_details.get('physical'))
    if output_beat.get('error') or master_output_beat.get('error'):
        output_status = 'error'
        output_summary = _('The last output write failed.')
    elif output_physical and output_beat.get('last_success'):
        output_status = 'ok'
        output_summary = _('The last output command was written successfully.')
    else:
        output_status = 'warning'
        output_summary = _('Physical output feedback is not available on this system.')
    output_description = '{}: {}; {}: {}'.format(
        _('Backend'), output_details.get('backend', stations.__class__.__name__),
        _('Active outputs'), output_details.get('active', len([
            state for state in stations.active() if state
        ]))
    )
    output_description += '; {}: {} ({})'.format(
        _('Master relay'),
        _('ON') if master_output_details.get('active') else _('OFF'),
        master_output_details.get('backend', '-')
    )
    if not output_details.get('feedback'):
        output_description += '; ' + _(
            'OSPy can confirm the command write, but not the physical relay state.'
        )
    items.append(_health_item(
        'outputs', _('Output hardware'), output_status, output_summary,
        output_beat.get('error') or master_output_beat.get('error') or output_description,
        _health_time(max(
            output_beat.get('last_success', 0),
            master_output_beat.get('last_success', 0)
        )), '/stations'
    ))

    enabled_sensors = [sensor for sensor in sensors.get() if sensor.enabled]
    responding_sensors = [sensor for sensor in enabled_sensors if sensor.response]
    failed_sensors = [sensor for sensor in enabled_sensors if not sensor.response]
    sensor_beat = beats.get('sensors', {})
    sensor_age = now_ts - sensor_beat.get('last_success', 0)
    if not enabled_sensors:
        sensor_status = 'unknown'
        sensor_summary = _('No sensors are enabled.')
    elif sensor_beat.get('error') or sensor_age > 10:
        sensor_status = 'error'
        sensor_summary = _('The sensor processing loop is not responding.')
    elif failed_sensors:
        sensor_status = 'warning'
        sensor_summary = _('Some enabled sensors are not responding.')
    else:
        sensor_status = 'ok'
        sensor_summary = _('All enabled sensors are responding.')
    sensor_description = '{}: {}; {}: {}; {}: {}'.format(
        _('Enabled'), len(enabled_sensors),
        _('Responding'), len(responding_sensors),
        _('Not responding'), len(failed_sensors)
    )
    if failed_sensors:
        sensor_description += '; ' + ', '.join(
            sensor.name for sensor in failed_sensors[:5]
        )
    last_sensor_response = max(
        [getattr(sensor, 'last_response', 0) for sensor in enabled_sensors] or [0]
    )
    if last_sensor_response:
        sensor_description += '; ' + _('Last sensor communication') + ': ' + (
            _health_time(last_sensor_response)
        )
    items.append(_health_item(
        'sensors', _('Sensors'), sensor_status, sensor_summary,
        sensor_beat.get('error') or sensor_description,
        _health_time(sensor_beat.get('last_success')), '/sensors'
    ))

    data_dir = os.path.abspath(os.path.join('ospy', 'data'))
    database_beat = beats.get('database', {})
    option_files = (
        glob(os.path.join(data_dir, 'default', 'options.db*')) +
        glob(os.path.join(data_dir, 'backup', 'options.db*'))
    )
    database_ok = (
        not database_beat.get('error') and bool(option_files) and
        os.path.isdir(data_dir) and os.access(data_dir, os.W_OK)
    )
    items.append(_health_item(
        'database', _('Database'), 'ok' if database_ok else 'error',
        _('The settings database and data directory are accessible.')
        if database_ok else _('The settings database or data directory is not accessible.'),
        database_beat.get('error') or (
            _('Last saved') + ': ' + _health_time(getattr(options, 'last_save', 0))
        ),
        _health_time(
            database_beat.get('last_success') or getattr(options, 'last_save', 0)
        )
    ))

    try:
        usage = shutil.disk_usage(data_dir)
        free_percent = (float(usage.free) / float(usage.total) * 100.0) if usage.total else 0
        if free_percent < 5:
            storage_status = 'error'
        elif free_percent < 15:
            storage_status = 'warning'
        else:
            storage_status = 'ok'
        storage_summary = _('Free disk space') + ': {:.1f} GB ({:.1f} %)'.format(
            usage.free / float(1024 ** 3), free_percent
        )
        storage_details = _('Used disk space') + ': {:.1f} GB'.format(
            usage.used / float(1024 ** 3)
        )
    except OSError as err:
        storage_status = 'error'
        storage_summary = _('Disk space could not be read.')
        storage_details = str(err)
    items.append(_health_item(
        'storage', _('Storage'), storage_status, storage_summary, storage_details
    ))

    plugin_diagnostics_error = False
    try:
        plugin_data = plugins.plugin_diagnostics()
    except Exception:
        plugin_data = []
        plugin_diagnostics_error = True
        log.error('webpages.py', traceback.format_exc())
    immediate_failed_plugins, health_failed_plugins, warning_plugins = (
        _plugin_health_groups(plugin_data)
    )
    failed_plugins = immediate_failed_plugins + health_failed_plugins
    if plugin_diagnostics_error or failed_plugins:
        plugin_status = 'error'
    elif warning_plugins:
        plugin_status = 'warning'
    else:
        plugin_status = 'ok'
    if plugin_diagnostics_error:
        plugin_summary = _('Plug-in status could not be read.')
    elif failed_plugins or warning_plugins:
        plugin_summary = _('Some enabled plug-ins need attention.')
    else:
        plugin_summary = _('All enabled plug-ins are running.')
    plugin_description = '{}: {}; {}: {}'.format(
        _('Enabled'), len([item for item in plugin_data if item.get('enabled')]),
        _('Problems'), len(failed_plugins) + len(warning_plugins)
    )
    problem_plugins = failed_plugins + warning_plugins
    if problem_plugins:
        plugin_description += '; ' + ', '.join(
            item.get('name') or item.get('module') for item in problem_plugins[:5]
        )
    items.append(_health_item(
        'plugins', _('Plug-ins'), plugin_status, plugin_summary,
        plugin_description, link='/plugins_manage',
        confirmation_required=(
            plugin_status == 'error' and not plugin_diagnostics_error and
            not immediate_failed_plugins and bool(health_failed_plugins)
        )
    ))

    email_modules = [
        module for module in ('email_notifications_ssl', 'email_notifications')
        if module in options.enabled_plugins
    ]
    running_plugins = plugins.running()
    if not email_modules:
        email_status = 'unknown'
        email_summary = _('No e-mail plug-in is enabled.')
        email_details = ''
    elif any(module not in running_plugins for module in email_modules):
        email_status = 'error'
        email_summary = _('An enabled e-mail plug-in is not running.')
        email_details = ', '.join(email_modules)
    elif 'email_notifications_ssl' in email_modules:
        email_ready, email_message = twofactor.email_plugin_status()
        email_status = 'ok' if email_ready else 'warning'
        email_summary = (
            _('The e-mail plug-in is running and configured.')
            if email_ready else email_message
        )
        email_details = ''
    else:
        email_status = 'ok'
        email_summary = _('The e-mail plug-in is running.')
        email_details = _('Configuration is not actively tested.')
    items.append(_health_item(
        'email', _('E-mail'), email_status, email_summary, email_details,
        link=(
            plugins.plugin_url(plugins.get(email_modules[0]).LINK)
            if email_modules and email_modules[0] in running_plugins else ''
        )
    ))

    weather_beat = beats.get('weather', {})
    weather_age = now_ts - weather_beat.get('last_success', 0)
    if not options.use_weather:
        weather_status = 'unknown'
        weather_summary = _('Weather service is disabled.')
    elif weather_beat.get('error') or weather_age > 2 * 3600:
        weather_status = 'error'
        weather_summary = _('Weather data has not been updated successfully.')
    elif options.weather_status != 1:
        weather_status = 'warning'
        weather_summary = _('Weather location or data is not ready.')
    else:
        weather_status = 'ok'
        weather_summary = _('Weather service is responding.')
    items.append(_health_item(
        'weather', _('Weather'), weather_status, weather_summary,
        weather_beat.get('error', ''),
        _health_time(weather_beat.get('last_success')), '/options#weather-options'
    ))

    external_ip = get_external_ip()
    ip_refresh_pending = external_ip == '-' and external_ip_refresh_pending()
    internet_status = (
        'ok' if external_ip != '-' else
        'warning' if ip_refresh_pending else
        'error'
    )
    items.append(_health_item(
        'internet', _('Internet'), internet_status,
        _('Internet connectivity is available.')
        if internet_status == 'ok' else
        _('Checking...') if ip_refresh_pending else
        _('Internet connectivity is not available.'),
        _('External IP address') + ': ' + external_ip
    ))

    backup_files = glob(os.path.join('ospy', 'backup', '*.zip'))
    backup_files += glob(os.path.join('plugins', 'ospy_backup', 'data', '*.zip'))
    newest_backup = _newest_file(backup_files)
    if newest_backup:
        backup_age = now_ts - newest_backup[1]
        backup_status = 'ok' if backup_age <= 30 * 24 * 3600 else 'warning'
        backup_summary = _('A backup file is available.')
        backup_details = '{}; {:.1f} MB'.format(
            os.path.basename(newest_backup[0]),
            newest_backup[2] / float(1024 ** 2)
        )
        backup_updated = _health_time(newest_backup[1])
    else:
        backup_status = 'warning'
        backup_summary = _('No backup file was found.')
        backup_details = ''
        backup_updated = ''
    items.append(_health_item(
        'backup', _('Backup'), backup_status, backup_summary,
        backup_details, backup_updated, '/options'
    ))

    items.extend(_runtime_health_items())

    item_statuses = [item['status'] for item in items]
    if 'error' in item_statuses:
        summary_status = 'error'
    elif 'warning' in item_statuses:
        summary_status = 'warning'
    elif 'ok' in item_statuses:
        summary_status = 'ok'
    else:
        summary_status = 'unknown'
    return {
        'status': summary_status,
        'items': items,
        'time': datetime_string(),
    }


class diagnostics_page(ProtectedPage):
    """System and plug-in diagnostics page."""

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        return self.core_render.diagnostics()

    def POST(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            raise web.forbidden()

        qdict = web.input()
        action = qdict.get('action', '')
        module = qdict.get('plugin', '')
        data = {'ok': False, 'message': _('Unknown action.')}

        if action == 'restart' and module in plugins.running():
            try:
                data['ok'] = plugins.reload_plugin(module)
                data['message'] = _('Restart OK') if data['ok'] else _('Restart failed.')
                logEV.save_events_log(
                    _('Plug-in restarted') if data['ok'] else _('Plug-in restart failed'),
                    _('User {} restarted plug-in {}.').format(session.get('visitor'), module)
                    if data['ok'] else
                    _('Plug-in {} could not be restarted.').format(module),
                    level='success' if data['ok'] else 'error',
                    category='system'
                )
            except Exception:
                data['message'] = traceback.format_exc()
                log.error('webpages.py', data['message'])
                logEV.save_events_log(
                    _('Plug-in restart failed'),
                    _('Plug-in {} could not be restarted.').format(module),
                    level='error',
                    category='system'
                )
        elif action == 'restart':
            data['message'] = _('Plugin is not running.')

        web.header('Content-Type', 'application/json')
        return json.dumps(data)


class api_diagnostics_json(ProtectedPage):
    """Live system and plug-in diagnostics API."""

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            raise web.forbidden()

        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        try:
            return json.dumps(_diagnostics_data())
        except Exception:
            log.error('webpages.py', traceback.format_exc())
            return json.dumps({
                'ok': False,
                'error': _('Diagnostics refresh failed.'),
                'time': datetime_string(),
            })


class api_diagnostics_history_json(ProtectedPage):
    """In-memory plug-in CPU history diagnostics API."""

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            raise web.forbidden()

        qdict = web.input()
        module = qdict.get('plugin', '')
        seconds = qdict.get('range', 3600)

        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        try:
            return json.dumps({
                'plugin': module,
                'history': _diagnostics_history_payload(module, seconds),
                'time': datetime_string(),
            })
        except Exception:
            log.error('webpages.py', traceback.format_exc())
            return json.dumps({
                'ok': False,
                'error': _('Diagnostics history refresh failed.'),
                'time': datetime_string(),
            })


class api_system_health_json(ProtectedPage):
    """Operational system health overview for the Diagnostics page."""

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            raise web.forbidden()

        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        try:
            return json.dumps(_system_health_data())
        except Exception:
            log.error('webpages.py', traceback.format_exc())
            return json.dumps({
                'ok': False,
                'error': _('System health refresh failed.'),
                'time': datetime_string(),
            })


class api_security_health_json(ProtectedPage):
    """Passive security overview for the Diagnostics page."""

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            raise web.forbidden()

        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        try:
            return json.dumps(_security_health_data())
        except Exception:
            log.error('webpages.py', traceback.format_exc())
            return json.dumps({
                'ok': False,
                'error': _('Security check failed.'),
                'time': datetime_string(),
            })


class log_page(ProtectedPage):
    """View Log"""

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()

        if 'csv' in qdict:
            events = log.finished_runs() + log.active_runs()
            data = "Date; Start Time; Zone; Duration; Program\n"
            for interval in events:
                # return only records that are visible on this day:
                duration = (interval[u'end'] - interval[u'start']).total_seconds()
                minutes, seconds = divmod(duration, 60)

                data += '; '.join([
                    interval['start'].strftime("%Y-%m-%d"),
                    interval['start'].strftime("%H:%M:%S"),
                    str(interval['station']),
                    "%02d:%02d" % (minutes, seconds),
                    interval['program_name']
                ]) + '\n'

            web.header('Content-Type', 'text/csv')
            web.header('Content-Disposition', 'attachment; filename="log.csv"')
            return data

        if 'csvEM' in qdict:
            events = logEM.finished_email()
            data = "Date; Time; Subject; Body; Status\n"
            for interval in events:
                data += '; '.join([
                    interval['date'],
                    interval['time'],
                    str(interval['subject']),
                    str(interval['body']),
                    str(interval['status']),
                ]) + '\n'

            web.header('Content-Type', 'text/csv')
            web.header('Content-Disposition', 'attachment; filename="email.csv"')
            return data

        if 'csvEV' in qdict:
            events = logEV.finished_events()
            data = "Date; Time; Level; Category; Subject; Status\n"
            for interval in events:
                data += '; '.join([
                    interval['date'],
                    interval['time'],
                    str(interval['level']),
                    str(interval['category']),
                    str(interval['subject']),
                    str(interval['status']),
                ]) + '\n'

            web.header('Content-Type', 'text/csv')
            web.header('Content-Disposition', 'attachment; filename="events.csv"')
            return data

        watering_records = log.finished_runs()
        email_records = logEM.finished_email()
        events_records = logEV.finished_events()

        try:
            return self.core_render.log(watering_records, email_records, events_records)
        except:
            log.debug('webpages.py', traceback.format_exc())
            raise web.seeother('/')

    def POST(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        action = qdict.get('action', '')
        if action == 'clear':
            log.clear_runs()
            raise web.seeother('/log#station-log')
        elif action == 'clearALL':
            log.clear_all_runs()
            raise web.seeother('/log#station-log')
        elif action == 'clearEM':
            logEM.clear_email()
            raise web.seeother('/log#email-log')
        elif action == 'clearEV':
            logEV.clear_events()
            raise web.seeother('/log#events-log')

        watering_records = log.finished_runs()
        email_records = logEM.finished_email()
        events_records = logEV.finished_events()

        if session.get('category') == 'admin':
            return self.core_render.log(watering_records, email_records, events_records)
        elif session.get('category')== 'user':
            return self.core_render.log_user(watering_records, email_records, events_records)
        else:
            raise web.seeother('/')

class options_page(ProtectedPage):
    """Open the options page for viewing and editing."""

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        errorCode = qdict.get('errorCode', 'none')

        stored_backups = []
        for backup_info in system_backup.list_system_backups():
            stored_backups.append({
                'display_name': html.escape(backup_info['name']),
                'query': urlencode({'file': backup_info['name']}),
                'size_mb': backup_info['size'] / float(1024 * 1024),
                'date': datetime.datetime.fromtimestamp(backup_info['modified']).strftime('%Y-%m-%d %H:%M:%S'),
            })
        return self.core_render.options(errorCode, stored_backups)

    def POST(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        changing_language = False

        qdict = web.input()

        location_changed = qdict.get('location', options.location) != options.location
        map_selected = qdict.get('weather_map_selected', '0') == '1'
        location_mode = qdict.get('weather_location_mode', 'search')
        if location_changed and not map_selected:
            location_mode = 'search'
        if location_mode == 'coordinates':
            try:
                latitude = float(qdict.get('weather_lat', ''))
                longitude = float(qdict.get('weather_lon', ''))
                if not -90.0 <= latitude <= 90.0 or not -180.0 <= longitude <= 180.0:
                    raise ValueError()
                options.weather_lat = '{:.7f}'.format(latitude).rstrip('0').rstrip('.')
                options.weather_lon = '{:.7f}'.format(longitude).rstrip('0').rstrip('.')
                options.weather_location_mode = 'coordinates'
                options.weather_status = 1
            except (TypeError, ValueError):
                raise web.seeother('/options?errorCode=weather_coordinates')
        else:
            options.weather_location_mode = 'search'

        if 'lang' in qdict:
            log.debug('webpages.py', _('Changing language web={} options={}').format(qdict['lang'], options.lang))
            if qdict['lang'] != options.lang:     # if changed languages
                changing_language = True
                save_to_options(qdict)

        if 'master' in qdict:
            m = int(qdict['master'])
            if m < 0:
                stations.master = None
            elif m < stations.count():
                stations.master = m

        if 'master_two' in qdict:
            m = int(qdict['master_two'])
            if m < 0:
                stations.master_two = None
            elif m < stations.count():
                stations.master_two = m

        if 'old_password' in qdict and qdict['old_password'] != "":
            try:
                from ospy.helpers import password_hash, password_salt, test_password
                if test_password(qdict['old_password'], options.admin_user):
                    if qdict['new_password'] == "":
                        raise web.seeother('/options?errorCode=pw_blank')
                    elif qdict['new_password'] == qdict['check_password']:
                        options.password_salt = password_salt()
                        options.password_hash = password_hash(qdict['new_password'], options.password_salt)
                        options.first_installation = False
                        autologin.revoke_all()
                        logEV.save_events_log(
                            _('Password changed'),
                            _('User {} changed the administrator password.').format(session.get('visitor')),
                            id='Login',
                            level='warning',
                            category='security'
                        )
                    else:
                        raise web.seeother('/options?errorCode=pw_mismatch')
                else:
                    raise web.seeother('/options?errorCode=pw_wrong')

                from ospy.server import session
                session.kill()
                raise web.seeother('/')    # after change password -> logout
            except KeyError:
                pass

        if 'revoke_autologin' in qdict and qdict['revoke_autologin'] == '1':
            autologin.revoke_all()
            logEV.save_events_log(
                _('Remembered logins revoked'),
                _('User {} revoked all remembered logins.').format(session.get('visitor')),
                id='Login',
                level='warning',
                category='security'
            )
            raise web.seeother('/options')

        if 'rbt' in qdict and qdict['rbt'] == '1':
            logEV.save_events_log(
                _('System restart requested'),
                _('User {} requested a Linux system restart.').format(session.get('visitor')),
                level='warning',
                category='system'
            )
            report_rebooted()
            reboot(wait=3) # Linux HW software
            msg = _('The system (Linux) will now restart (restart started by the user in the OSPy settings), please wait for the page to reload.')
            return self.core_render.notice('/', msg)

        if 'rstrt' in qdict and qdict['rstrt'] == '1':
            logEV.save_events_log(
                _('OSPy restart requested'),
                _('User {} requested an OSPy restart.').format(session.get('visitor')),
                level='warning',
                category='system'
            )
            report_restarted()
            restart(wait=3)    # OSPy software
            msg = _('The OSPy will now restart (restart started by the user in the OSPy settings), please wait for the page to reload.')
            return self.core_render.notice('/', msg)

        if 'pwrdwn' in qdict and qdict['pwrdwn'] == '1':
            logEV.save_events_log(
                _('System shutdown requested'),
                _('User {} requested a Linux system shutdown.').format(session.get('visitor')),
                level='warning',
                category='system'
            )
            report_poweroff()
            poweroff(wait=15)   # shutll HW system
            msg = _('The system (Linux) is now shutting down... The system must be switched on again by the user (switching off and on your HW device).')
            return self.core_render.notice('/', msg)

        if 'deldef' in qdict and qdict['deldef'] == '1':
            from ospy import server
            from ospy.helpers import ospy_to_default
            try:
                report_restarted()
                stations.clear()
                server.stop()
                server.session.kill()
                ospy_to_default()
                restart(wait=3)    # OSPy software
            except:
                log.debug('webpages.py', traceback.format_exc())
                server.session.kill()
                server.stop()
                server.start()
                raise web.seeother('/')

        save_to_options(qdict)
        report_option_change()
        logEV.save_events_log(
            _('System settings updated'),
            _('User {} saved the system settings.').format(session.get('visitor')),
            level='info',
            category='configuration'
        )

        if changing_language:
            log.debug('webpages.py', _('Changing language -> restarting.'))
            options.save_now()
            report_restarted()
            restart(wait=3)    # OSPy software
            msg = _('A language change has been made in the settings, the OSPy will now restart and load the selected language.')
            return self.core_render.notice('/', msg)

        raise web.seeother('/')


class stations_page(ProtectedPage):
    """Stations page"""

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        return self.core_render.stations()

    def POST(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()

        recalc = False
        for s in range(0, stations.count()):
            stations[s].name = qdict["%d_name" % s]
            stations[s].usage = float(qdict.get("%d_usage" % s, 1.0))
            stations[s].precipitation = float(qdict.get("%d_precipitation" % s, 10.0))
            stations[s].capacity = float(qdict.get("%d_capacity" % s, 10.0))
            stations[s].eto_factor = float(qdict.get("%d_eto_factor" % s, 1.0))
            stations[s].enabled = True if qdict.get("%d_enabled" % s, 'off') == 'on' else False
            stations[s].ignore_rain = True if qdict.get("%d_ignore_rain" % s, 'off') == 'on' else False
            if stations.master is not None or stations.master_two is not None or options.master_relay:
                if "%d_master_type" % s in qdict:
                    mtype = int(qdict["%d_master_type" % s])
                    stations[s].activate_master = True if mtype == 1 else False
                    stations[s].activate_master_two = True if mtype == 2 else False
                    stations[s].activate_master_by_program = True if mtype == 3 else False
                    stations[s].master_type = mtype

            balance_adjust = float(qdict.get("%d_balance_adjust" % s, 0.0))
            if balance_adjust != 0.0:
                calc_day = datetime.datetime.now().date() - datetime.timedelta(days=1)
                stations[s].balance[calc_day]['intervals'].append({
                                'program': -1,
                                'program_name': 'Balance adjustment',
                                'done': True,
                                'irrigation': balance_adjust
                            })
                stations[s].balance[calc_day]['total'] += balance_adjust
                recalc = True
            stations[s].notes = qdict["%d_notes" % s]

        if recalc:
            Timer(0.1, programs.calculate_balances).start()

        report_station_names()
        logEV.save_events_log(
            _('Station settings updated'),
            _('User {} saved settings for {} stations.').format(
                session.get('visitor'), stations.count()),
            level='info',
            category='configuration'
        )
        raise web.seeother('/')

class feedback_page(ProtectedPage):
    """Prepare a GitHub issue with optional non-identifying system details."""

    REPORT_TYPES = {
        'bug': ('Bug report', 'Bug'),
        'feature': ('Feature request', 'Feature'),
        'question': ('Question', 'Question'),
    }

    @staticmethod
    def _allowed():
        from ospy.server import session
        return session.get('category') in ('admin', 'user')

    def _render(self, report_type='bug', issue_title='', description='',
                include_system=True, error=None):
        return self.core_render.feedback(
            report_type, issue_title, description, include_system,
            _feedback_system_information(), error
        )

    def GET(self):
        if not self._allowed():
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        web.header('Referrer-Policy', 'no-referrer')
        return self._render()

    def POST(self):
        if not self._allowed():
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        web.header('Referrer-Policy', 'no-referrer')
        qdict = web.input()
        report_type = str(qdict.get('report_type', 'bug')).strip().lower()
        issue_title = ' '.join(str(qdict.get('issue_title', '')).split())
        description = str(qdict.get('description', '')).strip()
        include_system = qdict.get('include_system', '') == '1'

        if report_type not in self.REPORT_TYPES:
            return self._render('bug', issue_title, description, include_system,
                                _('Select a valid report type.'))
        if not issue_title:
            return self._render(report_type, issue_title, description, include_system,
                                _('Enter a short report title.'))
        if len(issue_title) > FEEDBACK_TITLE_LIMIT:
            return self._render(report_type, issue_title, description, include_system,
                                _('The report title is too long.'))
        if not description:
            return self._render(report_type, issue_title, description, include_system,
                                _('Describe the problem, idea, or question.'))
        if len(description) > FEEDBACK_DESCRIPTION_LIMIT:
            return self._render(report_type, issue_title, description, include_system,
                                _('The report description is too long.'))

        report_label, title_prefix = self.REPORT_TYPES[report_type]
        body = '## Report type\n{}\n\n## Description\n{}'.format(
            report_label, description
        )

        if include_system:
            system_lines = []
            for key, value in _feedback_system_information():
                system_lines.append('- **{}:** `{}`'.format(
                    key.replace('`', "'"), value.replace('`', "'")
                ))
            body += '\n\n## OSPy system information\n' + '\n'.join(system_lines)

        body += '\n\n---\nPrepared by the OSPy feedback form. Review before submitting.'
        github_url = GITHUB_NEW_ISSUE_URL + '?' + urlencode({
            'title': '[{}] {}'.format(title_prefix, issue_title),
            'body': body,
        })
        raise web.seeother(github_url)


class help_page(ProtectedPage):
    """Help page"""

    def GET(self):
        from ospy.server import session

        qdict = web.input()
        id = get_input(qdict, 'id')
        if id is not None:
            web.header('Content-Type', 'text/html')
            return get_help_file(id)

        docs = get_help_files()

        if session.get('category') == 'admin':
            return self.core_render.help(docs)
        elif session.get('category')== 'user':
            return self.core_render.help_user(docs)
        else:
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

class db_unreachable_page(ProtectedPage):
    """Failed to reach download."""

    def GET(self):
        msg = _('System component is unreachable or busy. Please wait (try again later).')
        return self.core_render.notice('/download', msg)

class download_page(ProtectedPage):
    """Download OSPy backup file with settings"""
    def GET(self):
        from ospy.server import session
        from ospy.helpers import ASCI_convert
        import os
        import time

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        try:
            qdict = web.input(file=None)
            backup_path = system_backup.system_backup_path(qdict.get('file')) if qdict.get('file') else None
            created = False
            if qdict.get('file') and backup_path is None:
                return self.core_render.notice('/options', _('The selected system backup was not found.'))
            if backup_path is None:
                download_name = '{}_backup_{}.zip'.format(ASCI_convert(options.name).decode("utf-8"), time.strftime("%d.%m.%Y_%H-%M-%S"))   # Example: ospy_backup_4.12.2020_18-40-20.zip
                options.save_now()
                backup_path = system_backup.create_system_backup(reason='manual')
                created = True
                log.info('webpages.py', _('System backup created successfully.') + ' ' + os.path.basename(backup_path))
            else:
                download_name = os.path.basename(backup_path)
                log.info('webpages.py', _('Stored system backup downloaded.') + ' ' + download_name)
            if options.run_logEV:
                logEV.save_events_log(
                    _('System backup'),
                    (_('User {} created a system backup.') if created else
                     _('User {} downloaded a stored system backup.')).format(session.get('visitor')),
                    id='Backup', level='success', category='system'
                )
            web.header('Content-type', 'application/zip')
            web.header('Content-Length', os.path.getsize(backup_path))
            web.header('Content-Disposition', 'attachment; filename=%s' % download_name)

            def stream_backup():
                with open(backup_path, 'rb') as source:
                    while True:
                        chunk = source.read(64 * 1024)
                        if not chunk:
                            break
                        yield chunk
            return stream_backup()

        except Exception:
            log.debug('webpages.py', traceback.format_exc())
            raise web.seeother('/')


class upload_page(ProtectedPage):
    """Upload ospy_backup.zip file with settings and images for stations"""
    def GET(self):
        raise web.seeother('/')

    def POST(self):
        from ospy.helpers import mkdir_p, del_rw
        from ospy import server
        import os
        import shutil

        if server.session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        upload_path = os.path.join('ospy', 'upload')

        i = web.input(uploadfile={})

        restore_started = False
        try:
            if os.path.exists(upload_path):                                     # Deleting old folder upload
                log.debug('webpages.py', _('Deleting folder upload.'))
                shutil.rmtree(upload_path, onerror=del_rw)

            if not os.path.exists(upload_path):                                 # Create new folder for upload
                log.debug('webpages.py', _('Creating folder upload.'))
                mkdir_p(upload_path)

            # import cgi
            # 0 ==> unlimited input upload
            # cgi.maxlen = 10 * 1024 * 1024 # 10MB
            # print cgi.maxlen
            log.debug('webpages.py', _('Uploading file {}.').format(i.uploadfile.filename))
            upload_type = os.path.splitext(i.uploadfile.filename or '')[1].lower()
            if upload_type == '.zip':                                           # Check file type
                archive_path = os.path.join(upload_path, 'ospy_upload.zip')
                with open(archive_path, 'wb') as fout:
                    fout.write(read_limited_upload(i.uploadfile.file))

                log.debug('webpages.py', _('Validating the uploaded system backup.'))
                staging, manifest = system_backup.stage_restore(archive_path)
                options.save_now()
                if options.run_logEV:
                    logEV.save_events_log(
                        _('System restore'),
                        _('User {} requested restoration of a system backup.').format(server.session.get('visitor')),
                        id='Backup', level='warning', category='system'
                    )
                rollback_path = system_backup.create_system_backup(reason='before restore')
                log.info('webpages.py', _('A safety backup was created before restoration.') + ' ' + os.path.basename(rollback_path))

                report_restarted()
                stations.clear()
                # The current request would otherwise try to save itself into
                # the session shelf after server.stop() has closed that shelf.
                # Restoring a system backup intentionally signs the browser
                # out and lets the restarted process create a fresh session.
                server.session.kill()
                server.stop()
                restore_started = True
                system_backup.apply_staged_restore(staging)
                restart(wait=3)

                msg = _('The backup was verified and restored successfully. OSPy is restarting.')
                if manifest.get('legacy'):
                    msg += ' ' + _('A legacy backup without a manifest was restored.')
                return self.core_render.notice('/', msg)
            else:
                errorCode = "pw_filename"
                return self.core_render.options(errorCode)

        except (system_backup.BackupError, ValueError) as error:
            log.warning('webpages.py', _('System backup restore was rejected: {}').format(error))
            if restore_started:
                restart(wait=1)
            return self.core_render.notice('/options', _('The system backup cannot be restored: {}').format(error))
        except Exception:
            log.debug('webpages.py', traceback.format_exc())
            if restore_started:
                restart(wait=1)
            return self.core_render.notice('/options', _('The system backup could not be restored. No verified data was installed.'))


def _ssl_file_path(filename):
    if filename not in ('fullchain.pem', 'privkey.pem'):
        return None
    return os.path.join('.', 'ssl', filename)


def _write_ssl_file(filename, data):
    from ospy.helpers import mkdir_p

    target = _ssl_file_path(filename)
    if target is None:
        raise ValueError(_('File name is not fullchain.pem or privkey.pem, please retry.'))

    mkdir_p(os.path.dirname(target))
    tmp_target = target + '.tmp'
    with open(tmp_target, 'wb') as fh:
        fh.write(data)

    if filename == 'privkey.pem':
        try:
            os.chmod(tmp_target, 0o600)
        except Exception:
            log.debug('webpages.py', _('Could not set private key permissions.'))
    else:
        try:
            os.chmod(tmp_target, 0o644)
        except Exception:
            pass

    os.replace(tmp_target, target)


def _validate_ssl_pem(filename, data):
    from OpenSSL import crypto

    if filename == 'fullchain.pem':
        crypto.load_certificate(crypto.FILETYPE_PEM, data)
        return
    if filename == 'privkey.pem':
        crypto.load_privatekey(crypto.FILETYPE_PEM, data)
        return
    raise ValueError(_('File name is not fullchain.pem or privkey.pem, please retry.'))


def _ssl_subject_alt_names(common_name):
    from ospy.helpers import is_fqdn, valid_ip

    names = []
    common_name = (common_name or 'localhost').strip()
    if valid_ip(common_name):
        names.append('IP:{}'.format(common_name))
    elif is_fqdn(common_name) or common_name.lower() == 'localhost':
        names.append('DNS:{}'.format(common_name))

    if common_name.lower() != 'localhost':
        names.append('DNS:localhost')

    return ', '.join(names)


def _ssl_common_name():
    from ospy.helpers import is_fqdn, valid_ip

    common_name = (options.domain_ssl or 'localhost').strip()
    if valid_ip(common_name) or is_fqdn(common_name) or common_name.lower() == 'localhost':
        try:
            common_name.encode('ascii')
            return common_name
        except UnicodeEncodeError:
            pass
    return 'localhost'


class upload_page_SSL(ProtectedPage):
    """Upload certificate file to SSL dir, fullchain.pem or privkey.pem"""
    def GET(self):
        raise web.seeother('/')

    def POST(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        qdict = web.input()
        if 'generate' in qdict and qdict['generate'] == '1':   # generating own SSL certificate to ssl folder
            try:
                log.debug('webpages.py', _('Try-ing generating SSL certificate...'))

                from OpenSSL import crypto
                import secrets

                # create a key pair
                k = crypto.PKey()
                k.generate_key(crypto.TYPE_RSA, 2048)

                # create a self-signed cert
                common_name = _ssl_common_name()
                cert = crypto.X509()
                cert.get_subject().C = "EU"                # your country
                cert.get_subject().ST = "Czechia"          # your state
                cert.get_subject().L = "Prague"            # location
                cert.get_subject().O = "OSPy sprinkler"    # organization
                cert.get_subject().OU = "opensprinkler.cz" # this field is the name of the department or organization unit making the request
                cert.get_subject().CN = common_name # common name
                cert.get_subject().emailAddress = "admin@opensprinkler.cz" # e-mail
                cert.set_serial_number(secrets.randbits(128))
                cert.gmtime_adj_notBefore(0)
                cert.gmtime_adj_notAfter(10*365*24*60*60)
                cert.set_issuer(cert.get_subject())
                cert.set_pubkey(k)
                san = _ssl_subject_alt_names(common_name)
                if san:
                    cert.add_extensions([
                        crypto.X509Extension(b'basicConstraints', True, b'CA:FALSE'),
                        crypto.X509Extension(b'keyUsage', True, b'digitalSignature,keyEncipherment'),
                        crypto.X509Extension(b'extendedKeyUsage', False, b'serverAuth'),
                        crypto.X509Extension(b'subjectAltName', False, san.encode('ascii')),
                    ])
                cert.sign(k, 'sha256')

                _write_ssl_file('fullchain.pem', crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
                _write_ssl_file('privkey.pem', crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

                log.debug('webpages.py', _('OK'))

                errorCode = "pw_generateSSLOK"
                return self.core_render.options(errorCode)

            except Exception:
                pass
                log.debug('webpages.py', traceback.format_exc())
                errorCode = "pw_generateSSLERR"
                return self.core_render.options(errorCode)

        i = web.input(uploadfile={})
        try:
            filename = getattr(i.uploadfile, 'filename', '').replace('\\', '/').split('/')[-1]
            if filename == 'fullchain.pem' or filename == 'privkey.pem':
                upload_data = read_limited_upload(i.uploadfile.file)
                _validate_ssl_pem(filename, upload_data)
                _write_ssl_file(filename, upload_data)

                log.debug('webpages.py', _('Upload SSL file %s') % filename)
                #report_restarted()
                #restart(3)
                #return self.core_render.restarting(home_page)
                errorCode = "pw_filenameSSLOK"
                return self.core_render.options(errorCode)
            else:
                errorCode = "pw_filenameSSL"
                return self.core_render.options(errorCode)

        except ValueError:
            log.debug('webpages.py', traceback.format_exc())
            errorCode = "pw_filenameSSL"
            return self.core_render.options(errorCode)
        except Exception:
            log.debug('webpages.py', traceback.format_exc())
            return self.core_render.options()

class images_page(ProtectedPage):
    """Return pictures with information about board connection - for help page."""

    def GET(self):

        import mimetypes

        try:
            qdict = web.input()

            id = get_input(qdict, 'id')                                   # id = name for image (ex: station1.png)
            s_folder = get_input(qdict, 'sf', None, lambda x: x == '1')   # sf = 1 read from folder: images/stations else from images/
            ip_cam = get_input(qdict, 'ip_cam', None, lambda x: x == '1')

            if ip_cam is not None:
                cam_nr = str(get_input(qdict, 'cam', '1'))
                if not cam_nr.isdigit() or int(cam_nr) < 1:
                    cam_nr = '1'
                else:
                    cam_nr = str(int(cam_nr))

                image_type = str(get_input(qdict, 'type', 'jpg')).lower()
                if image_type not in ('jpg', 'gif'):
                    image_type = 'jpg'

                download_name = os.path.join(plugins.plugin_data_dir('ip_cam'), '{}.{}'.format(cam_nr, image_type))
                if not os.path.isfile(download_name):
                    fallback_id = 'station{}_thumbnail.png'.format(cam_nr)
                    download_name = safe_image_path(fallback_id, station_folder=True)
                if not download_name or not os.path.isfile(download_name):
                    download_name = safe_image_path('no_image_thumbnail.png')

                if download_name and os.path.isfile(download_name):
                    content = mimetypes.guess_type(download_name)[0]
                    web.header('Content-type', content)
                    web.header('Content-Length', os.path.getsize(download_name))
                    web.header('Cache-Control', 'no-store')
                    img = open(download_name,'rb')
                    return img.read()
                return None

            if id is not None:
                download_name = safe_image_path(id, station_folder=s_folder is not None)

                if download_name and os.path.isfile(download_name):     # exists image?
                    content = mimetypes.guess_type(download_name)[0]
                    web.header('Content-type', content)
                    web.header('Content-Length', os.path.getsize(download_name))
                    web.header('Content-Disposition', 'attachment; filename=%s' % os.path.basename(download_name))
                    img = open(download_name,'rb')
                    return img.read()
                else:
                    return None
        except:
            pass
            return None

################################################################################
# APIs                                                                         #
################################################################################
class api_status_json(ProtectedPage):
    """Simple Status API"""
    def GET(self):
        statuslist = []
        try:
            for station in stations.get():
                if station.enabled or station.is_master or station.is_master_two:
                    status = {
                        'station': station.index,
                        'status': 'on' if station.active else 'off',
                        'reason': 'master' if station.is_master or station.is_master_two else '',
                        'master': 1 if station.is_master else 0,
                        'master_two': 1 if station.is_master_two else 0,
                        'programName': '',
                        'remaining': 0}

                    if not station.is_master or not station.is_master_two:
                        if options.manual_mode:
                            status['programName'] = 'Manual Mode'
                            if station.active:
                                active = log.active_runs()
                                for interval in active:
                                    if not interval['blocked'] and interval['station'] == station.index:
                                        status['reason'] = 'program'
                                        status['remaining'] = max(0, (interval['end'] -
                                                                  datetime.datetime.now()).total_seconds())
                        else:
                            if station.active:
                                active = log.active_runs()
                                for interval in active:
                                    if not interval['blocked'] and interval['station'] == station.index:
                                        status['programName'] = interval['program_name']
                                        status['reason'] = 'program'
                                        status['remaining'] = max(0, (interval['end'] -
                                                                  datetime.datetime.now()).total_seconds())
                            elif not options.scheduler_enabled:
                                status['reason'] = 'system_off'
                            elif not station.ignore_rain and inputs.rain_sensed():
                                status['reason'] = 'rain_sensed'
                            elif not station.ignore_rain and rain_blocks.seconds_left():
                                status['reason'] = 'rain_delay'

                    statuslist.append(status)
        except:
            pass

        web.header('Content-Type', 'application/json')
        return json.dumps(statuslist)


class api_log_json(ProtectedPage):
    """Simple Log API"""
    def GET(self):
        qdict = web.input()
        data = []
        try:
            if 'date' in qdict:
                # date parameter filters the log values returned; "yyyy-mm-dd" format
                date = datetime.datetime.strptime(qdict['date'], "%Y-%m-%d").date()
                check_start = datetime.datetime.combine(date, datetime.time.min)
                check_end = datetime.datetime.combine(date, datetime.time.max)
                log_start = check_start - datetime.timedelta(days=1)
                log_end = check_end + datetime.timedelta(days=1)

                events = scheduler.combined_schedule(log_start, log_end)
                for interval in events:
                    # Return only records that are visible on this day:
                    if check_start <= interval['start'] <= check_end or check_start <= interval['end'] <= check_end:
                        data.append(self._convert(interval))
        except:
            pass

        web.header('Content-Type', 'application/json')
        return json.dumps(data)

    def _convert(self, interval):
            duration = (interval['end'] - interval['start']).total_seconds()
            minutes, seconds = divmod(duration, 60)
            return {
                'program': interval['program'],
                'program_name': interval['program_name'],
                'active': interval['active'],
                'manual': interval.get('manual', False),
                'fixed': True,
                'cut_off': interval['cut_off'],
                'blocked': interval.get('blocked', False),
                'station': interval['station'],
                'date': interval['start'].strftime("%Y-%m-%d"),
                'start': interval['start'].strftime("%H:%M:%S"),
                'duration': "%02d:%02d" % (minutes, seconds)
            }


class api_balance_json(ProtectedPage):
    """Balance API"""

    def GET(self):
        statuslist = []
        try:
            epoch = datetime.date(1970, 1, 1)

            for station in stations.get():
                if station.enabled and any(station.index in program.stations for program in programs.get()):
                    statuslist.append({
                        'station': station.name,
                        'balances': {int((key - epoch).total_seconds()): value for key, value in station.balance.items()}})
        except:
            pass

        web.header('Content-Type', 'application/json')
        return json.dumps(statuslist, indent=2)



class showInFooter(object):
    """Enables plugins to display e.g. sensor readings in the footer of OSPy's UI"""

    def __init__(self, label="", val="", unit="", button=""):
        self._label = label
        self._val = val
        self._unit = unit
        self._button = button
        self._plugin = _plugin_module_from_stack()
        self._timestamp = datetime.datetime.now()   # Adding timestamp
        self._hash = self._generate_hash()          # Create hash for unique identification
        if self._val:                               # If val is not empty, we add the item
            self._add_to_pluginFtr()                # Add to pluginFtr only if val is not empty

    def _generate_hash(self):
        """Generates a hash for comparison based on plugin and label."""
        return hash((self._plugin, self._label))

    def _add_to_pluginFtr(self):
        """Adds or updates an item in pluginFtr based on label"""
        # Check for empty content
        if not self._val:
            return  # If val is empty, do not add the item

        for item in pluginFtr:
            # Compare by hash (label)
            if item.get("hash") == self._hash:
                # If an item with the same label exists, update its values
                item["val"] = self._val
                item["unit"] = self._unit
                item["button"] = self._button
                item["timestamp"] = self._timestamp
                item["plugin"] = self._plugin
                return

        # If no item with the same label exists, add a new item
        pluginFtr.append({
            "label": self._label,
            "val": self._val,
            "unit": self._unit,
            "button": self._button,
            "timestamp": self._timestamp,   # Add timestamp
            "hash": self._hash,             # Store hash for future duplicate checks
            "plugin": self._plugin
        })

        #self.remove_old_entries()

    @property
    def label(self):
        return self._label if self._label else _('Label not set')

    @label.setter
    def label(self, text):
        self._label = text
        self._hash = self._generate_hash()  # Update hash
        self._add_to_pluginFtr()

    @property
    def val(self):
        return self._val if self._val != "" else _('Value not set')

    @val.setter
    def val(self, num):
        self._val = num
        self._add_to_pluginFtr()

    @property
    def unit(self):
        return self._unit if self._unit else _('Unit not set')

    @unit.setter
    def unit(self, text):
        self._unit = text
        self._add_to_pluginFtr()

    @property
    def button(self):
        return self._button if self._button else '-'

    @button.setter
    def button(self, text):
        self._button = text
        self._add_to_pluginFtr()

    def remove_old_entries(self):
        """Removes items that are older than X minutes"""
        now = datetime.datetime.now()
        threshold = datetime.timedelta(minutes=5)  # Set threshold to 5 minutes
        global pluginFtr
        try:
            # Create a copy of the current list to avoid modifying the list during iteration
            filtered_entries = [entry for entry in pluginFtr if (now - entry["timestamp"]).total_seconds() < threshold.total_seconds()]
            # Update pluginFtr with the filtered list
            pluginFtr = filtered_entries
        except Exception:
            log.debug('webpages.py', traceback.format_exc())


class showOnTimeline:
    """Used to display plugin data next to station time countdown on home page timeline."""

    def __init__(self, val="", unit=""):
        self._val = val
        self._unit = unit
        self._plugin = _plugin_module_from_stack()
        self._idx = len(pluginStn)

        # Append a new entry to pluginStn with the initial values
        pluginStn.append([self._unit, self._val, self._plugin])

    @property
    def clear(self):
        if 0 <= self._idx < len(pluginStn):
            del pluginStn[self._idx][:]  # Remove elements of list but keep empty list
        else:
            self._handle_index_error()

    @property
    def unit(self):
        return self._unit if self._unit else _('Unit not set')

    @unit.setter
    def unit(self, text):
        self._unit = text
        if 0 <= self._idx < len(pluginStn):
            if len(pluginStn[self._idx]) >= 2:
                pluginStn[self._idx][0] = self._unit
        else:
            self._handle_index_error()

    @property
    def val(self):
        return self._val if self._val else _('Value not set')

    @val.setter
    def val(self, num):
        self._val = num
        if 0 <= self._idx < len(pluginStn):
            if len(pluginStn[self._idx]) >= 2:
                pluginStn[self._idx][1] = self._val
        else:
            self._handle_index_error()

    def _handle_index_error(self):
        """Logs and reports an index error."""
        log.error('webpages.py', _('Index {} is out of range for pluginStn list.').format(self._idx))


class api_plugin_data(ProtectedPage):
    """Simple plugin data API"""

    def GET(self):
        footer_data = []
        station_data = []
        sensor_data = []
        data = {}

        try:
            if options.show_plugin_data:
                # Plugin data in footer
                for i, v in enumerate(pluginFtr):
                    footer_data.append({
                        "id": i,
                        "label": v["label"],
                        "val": v["val"],
                        "unit": v["unit"],
                        "button": v["button"],
                    })
                # plugin data in timeline
                for v in pluginStn:
                    if len(v) < 2:
                        continue
                    found = False
                    for i, (station_id, _) in enumerate(station_data):
                        if station_id == v[0]:
                            station_data[i] = (v[0], v[1])
                            found = True
                            break
                    if not found:
                        station_data.append((v[0], v[1]))

            if options.show_sensor_data:
                from ospy.sensors import sensors_timer
                sensor_data = sensors_timer.read_status()

            data["fdata"] = footer_data
            data["sdata"] = station_data
            data["sendata"] = sensor_data
        except:
            pass

        web.header('Content-Type', 'application/json')
        return json.dumps(data)

class api_update_status(ProtectedPage):
    """Simple plugins update and ospy system update status API"""

    def GET(self):
        from ospy.server import session

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        pl_data = []
        data = {}
        must_update = 0
        os_state = 0
        os_avail = '0.0.0'
        os_curr  = '0.0.0'
        os_change  = ''

        running_list = plugins.running()
        current_info = options.plugin_status

        if options.use_plugin_update:
            plugins.checker.sync_installed_statuses()
            current_info = options.plugin_status
            for plugin in plugins.available():
                running = plugin in running_list
                available_info = plugins.checker.available_version(plugin)
                if available_info is not None:
                    if plugin in current_info and current_info[plugin]['hash'] != available_info['hash']:
                        pl_data.append((must_update, plugins.plugin_name(plugin)))
                        must_update += 1
            data["plugin_name"]   = pl_data                   # name of plugins where must be updated
            data["plugins_state"] = must_update               # status whether it is necessary to update the plugins (count plugins)
        else:
            data["plugin_name"]   = []
            data["plugins_state"] = 0

        try:
            if options.use_plugin_update:                     # if the update is not enabled in the plugins settings, the window with an available update will not pop up on the home page.
                from plugins import system_update
                os_state = system_update.get_all_values()[0]  # 0 = Plugin is not enabled, 1= Up-to-date, 2= New OSPy version is available,
                os_avail = system_update.get_all_values()[1]  # Available new OSPy version
                os_curr  = system_update.get_all_values()[2]  # Actual OSPy version
                os_change = system_update.get_all_values()[3] # Changes

            data["ospy_state"] = os_state
            data["ospy_aval"]  = os_avail
            data["ospy_curr"]  = os_curr
            data["chang"]      = os_change

        except Exception:
            data["ospy_state"] = os_state
            data["ospy_aval"]  = os_avail
            data["ospy_curr"]  = os_curr
            data["chang"]      = os_change
            pass

        web.header('Content-Type', 'application/json')
        return json.dumps(data)


class api_update_footer(ProtectedPage):
    """Simple footer value status API"""
    def GET(self):
        from ospy.server import session
        from ospy.helpers import uptime, get_cpu_temp, get_cpu_usage, get_external_ip, get_ip

        data = {}
        try:
            data["cpu_temp"]    = get_cpu_temp(options.temp_unit)
            data["cpu_usage"]   = get_cpu_usage()
            data["sys_uptime"]  = uptime()
            data["ip"]          = get_external_ip()
            data["ip_local"]    = get_ip()
        except:
            log.error('webpages.py', traceback.format_exc())
            pass

        web.header('Content-Type', 'application/json')
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return json.dumps(data)


class api_search_sensors(ProtectedPage):
    """APi for Available sensors that are not assigned"""

    def GET(self):
        from ospy.server import session
        searchData = []

        if session.get('category') != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice('/', msg)

        try:
            searchData.extend(sensorSearch) if sensorSearch not in searchData else searchData
        except:
            log.error('webpages.py', traceback.format_exc())
            pass

        web.header('Content-Type', 'application/json')
        return json.dumps(searchData)
