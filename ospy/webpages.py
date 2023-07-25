#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = u'Rimco'

# System imports
import os
from shutil import copyfile
import datetime
import json
import web
from threading import Timer
import traceback

# Local imports
from ospy.helpers import test_password, template_globals, check_login, save_to_options, \
    password_hash, password_salt, get_input, get_help_files, get_help_file, restart, reboot, poweroff, print_report
from ospy.inputs import inputs
from ospy.log import log, logEM, logEV
from ospy.options import options
from ospy.options import rain_blocks, program_level_adjustments
from ospy.programs import programs
from ospy.programs import ProgramType
from ospy.runonce import run_once
from ospy.stations import stations
from ospy import scheduler
import plugins
from blinker import signal
from ospy.users import users
from ospy.sensors import sensors, sensors_timer

from urllib.request import urlopen
from urllib.parse import quote_plus

try:
    import requests

except ImportError:
    print_report('usagestats.py', _('Requests not found, installing. Please wait...'))
    cmd = "sudo apt-get install python-requests"
    proc = subprocess.Popen(cmd,stderr=subprocess.STDOUT,stdout=subprocess.PIPE,shell=True)
    output = proc.communicate()[0]
    print_report('usagestats.py', output)
       
    try: 
        import requests
    except:
        pass

plugin_data = {}  # Empty dictionary to hold plugin based global data
pluginFtr = []    # Empty list of dicts to hold plugin data for display in footer
pluginStn = []    # Empty list of dicts to hold plugin data for display on timeline
sensorSearch = [] # Empty list of dicts to hold sensors data for display on sensor search page

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
    form.Password('password', description=_('Password:')),
    validators=[
        form.Validator(
            _('Incorrect username or password, please try again...'),
            lambda x: test_password(x["password"], x["username"])
        )  
    ]
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
                if name.endswith(u'.html') and \
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
            if not cls.__name__.endswith('json') and (not session.pages or session.pages[-1] != web.ctx.fullpath):
                session.pages.append(web.ctx.fullpath)
            while len(session.pages) > 5:
                del session.pages[0]
        except:
            print_report('webpages.py', traceback.format_exc())
            restart()    # OSPy software restart

        if self.__module__.startswith('plugins') and 'plugin_render' not in cls.__dict__:
            cls.plugin_render = InstantCacheRender(os.path.join(os.path.join(*self.__module__.split(u'.')), u'templates'), globals=template_globals(), base=self.base_render)

    @staticmethod
    def _redirect_back():
        from ospy.server import session
        for page in reversed(session.pages):
            if page != web.ctx.fullpath:
                raise web.seeother(page)
        raise web.seeother('/')


class ProtectedPage(WebPage):
    def __init__(self):
        WebPage.__init__(self)
        try:
            check_login(True)
        except web.seeother:
            raise

class sensors_firmware(ProtectedPage):
    """Open page to allow sensor firmware modification. /firmware """
    def GET(self):
        from ospy.server import session
        import os

        qdict = web.input()
        statusCode = qdict.get('statusCode', 'None')
        
        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

        if 'aid' in qdict:
            index = int(qdict['aid'])
            sensor = sensors.get(index)
            try: 
                send_ip = '.'.join(sensor.ip_address) 
                send_url = 'http://' + send_ip + '/AP_' + options.sensor_fw_passwd   # ex: http://192.168.88.207/AP_0123456789abcdef
                response = requests.post(send_url)
                resp_code = response.status_code
                print_report('webpages.py', resp_code)
                if resp_code == 200:
                    statusCode = qdict.get('statusCode', 'ap_ok')                    # msg = The sensor responded and probably started the AP manager
                elif resp_code == 404:
                    statusCode = qdict.get('statusCode', 'err5')                     # msg = It was not processed, the command does not exist in the sensor. Do you have the latest FW version of the sensor?                   
                else:
                    statusCode = qdict.get('statusCode', 'err6')                     # msg = An error, the sensor did not respond correctly!
                return self.core_render.sensors_firmware(statusCode)
            except:
                pass
                statusCode = qdict.get('statusCode', 'err7')                         # msg = Sensor does not respond!
                return self.core_render.sensors_firmware(statusCode)
        
        if 'id' in qdict:
            index = int(qdict['id'])
            sensor = sensors.get(index)
        else:
            return self.core_render.sensors_firmware(statusCode)

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
                statusCode = qdict.get('statusCode', 'err1')                         # msg = No xxx.bin file was found in the directory to send to the sensor!
                return self.core_render.sensors_firmware(statusCode)
            try:
                with open(last_fw_path, 'rb') as file:
                    response = requests.post(send_url, files={last_fw_name: file})
                resp_code = response.status_code
                print_report('webpages.py', resp_code)
                if resp_code == 200:
                    statusCode = qdict.get('statusCode', 'upl_ok')                   # msg = The new firmware file has been sent to the sensor, wait for the sensor to respond - check if the sensor has been updated.
                elif resp_code == 404:
                    statusCode = qdict.get('statusCode', 'err3')                     # msg = The new firmware could not be uploaded into the sensor. Response - Not Found!                    
                else:
                    statusCode = qdict.get('statusCode', 'err4')                     # msg = The new firmware could not be uploaded into the sensor. An error has occurred!    
            except:
                pass
                statusCode = qdict.get('statusCode', 'err2')                         # msg = The new firmware could not be uploaded into the sensor. Sensor does not respond!
                    
        except:
            pass
            print_report('webpages.py', traceback.format_exc())
            statusCode = qdict.get('statusCode', 'err2')                             # msg = The new firmware could not be uploaded into the sensor. Sensor does not respond! 

        return self.core_render.sensors_firmware(statusCode)

    def POST(self):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

        qdict = web.input()
        statusCode = qdict.get('statusCode', 'None')
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
                if not os.path.isfile(fw_path):
                    fout = open(fw_path,'wb') 
                    fout.write(i.uploadfile.file.read()) 
                    fout.close()
                    log.debug('webpages.py', _('File {} has sucesfully uploaded...').format(i.uploadfile.filename))
                else:
                    os.remove(fw_path) 
                    fout = open(fw_path,'wb')  # temporary file after uploading
                    fout.write(i.uploadfile.file.read()) 
                    fout.close()         
                    log.debug('webpages.py', _('File has sucesfully uploaded...')) 

                try:
                    kind = 'http://'
                    if protocol == "1":
                        kind = 'https://'
                    send_url = kind + ip + '/FW_' + pwd
                    if fw_path is not None:
                        with open(fw_path, 'rb') as file:
                            response = requests.post(send_url, files={fw_name: file})
#todo change requests to urrlib                            
                        #data = {'files': open(fw_path, 'rb')}
                        #response = urlopen(send_url, data=data)
                        #print(response)
                             
                        resp_code = response.status_code
                        print_report('webpages.py', resp_code)
                        if resp_code == 200:
                            statusCode = qdict.get('statusCode', 'upl_ok')           # msg = The new firmware file has been sent to the sensor, wait for the sensor to respond - check if the sensor has been updated.
                            os.remove(fw_path)
                        elif resp_code == 404:
                            statusCode = qdict.get('statusCode', 'err3')             # msg = The new firmware could not be uploaded into the sensor. Response - Not Found!                    
                        else:
                            statusCode = qdict.get('statusCode', 'err4')             # msg = The new firmware could not be uploaded into the sensor. An error has occurred!    
                except:
                    pass
                    statusCode = qdict.get('statusCode', 'err2')                     # msg = The new firmware could not be uploaded into the sensor. Sensor does not respond!
                    print_report('webpages.py', traceback.format_exc())
                    return self.core_render.sensors_firmware(statusCode)

        return self.core_render.sensors_firmware(statusCode)

class sensors_page(ProtectedPage):
    """Open all sensors page. /sensors"""

    def GET(self):
        from ospy.server import session
        global searchData

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

        qdict = web.input()

        delete_all = get_input(qdict, 'delete_all', False, lambda x: True)
        search = get_input(qdict, 'search', False, lambda x: True) 
        clean_all = get_input(qdict, 'clean_all', False, lambda x: True)

        if clean_all:
            for i in range(0, len(sensorSearch)):
                try:
                    del sensorSearch[int(i)]
                except:
                    print_report('webpages.py', traceback.format_exc())
                    pass
            return self.core_render.sensors_search()
          
        if delete_all:
            try: # delete all programs from sensor in program level adjustments (for soil moisture sensor)
                program = programs.get()
                for sensor in sensors.get():
                    for i in range(0, 16):
                        if sensor.soil_program[i] != "-1":
                            pid = '{}'.format(program[int(sensor.soil_program[i])-1].name)
                            del program_level_adjustments[pid]
            except:
                print_report('webpages.py', traceback.format_exc())
                pass

            while sensors.count() > 0:
                try:
                    sensor = sensors.get(sensors.count()-1)
                    sensors_timer.stop_status(sensor.name)
                    sensors.remove_sensors(sensors.count()-1)
                except:
                    print_report('webpages.py', traceback.format_exc())
                    pass
            try:
                import shutil
                shutil.rmtree(os.path.join('.', 'ospy', 'data', 'sensors'))
            except:
                print_report('webpages.py', traceback.format_exc())
                pass    

        if search:
            return self.core_render.sensors_search()                

        return self.core_render.sensors()


class sensor_page(ProtectedPage):
    """Open page to allow sensor modification. /sensor """
    def GET(self, index):
        from ospy.server import session
        import shutil

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)        

        qdict = web.input()
        try:
            index = int(index)
            
            delete = get_input(qdict, 'delete', False, lambda x: True)
            enable = get_input(qdict, 'enable', None, lambda x: x == '1')
            log = get_input(qdict, 'log', False, lambda x: True)       # return web page sensor log
            glog = get_input(qdict, 'glog', False, lambda x: True)     # return log json for graph
            graph = get_input(qdict, 'graph', False, lambda x: True)   # return web page sensor graph
            csvE = get_input(qdict, 'csvE', False, lambda x: True)     # return event csv file
            csvS = get_input(qdict, 'csvS', False, lambda x: True)     # return samples csv file
            clear = get_input(qdict, 'clear', False, lambda x: True)   # clear event and samples

            if 'history' in qdict:
                options.sensor_graph_histories = int(qdict['history'])
                if 'sensor_graph_show_err' in qdict:
                    options.sensor_graph_show_err = True
                else:
                    options.sensor_graph_show_err = False
                raise web.seeother('/sensor/{}?graph'.format(index))

            if delete:
                try: # delete sensor info from footer
                    from ospy.sensors import sensors_timer
                    sensor = sensors.get(index)
                    sensors_timer.stop_status(sensor.name)
                except:
                    print_report('webpages.py', traceback.format_exc())
                    pass

                try: # delete programs from sensor in program level adjustments (for soil moisture sensor)
                    program = programs.get()
                    for i in range(0, 16):
                        if sensor.soil_program[i] != "-1":
                            pid = '{}'.format(program[int(sensor.soil_program[i])-1].name)
                            del program_level_adjustments[pid]
                except:
                    print_report('webpages.py', traceback.format_exc())
                    pass

                try: # delete log and graph
                    shutil.rmtree(os.path.join('.', 'ospy', 'data', 'sensors', str(index)))
                except:
                    print_report('webpages.py', traceback.format_exc())
                    pass

                try: # delete sensor
                    sensors.remove_sensors(index)
                except:
                    print_report('webpages.py', traceback.format_exc())
                    pass

                raise web.seeother('/sensors')

            elif enable is not None:
                sensors[index].enabled = enable
                raise web.seeother('/sensors') 

            elif log:
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
                    sensors_timer.update_log(sensor, 'lge', '-')

                try:
                    with open(_abs_dir_slog) as logf:
                        slog_file =  json.load(logf)
                except IOError:
                    print_report('webpages.py', traceback.format_exc())
                    pass

                try:
                    with open(_abs_dir_elog) as logf:
                        elog_file =  json.load(logf)
                except IOError:
                    print_report('webpages.py', traceback.format_exc())
                    pass
                
                name = sensors[index].name
                stype = sensors[index].sens_type
                mtype = sensors[index].multi_type
                try:
                    return self.core_render.log_sensor(index, name, stype, mtype, slog_file, elog_file) 
                except:
                    pass
                    print_report('webpages.py', traceback.format_exc())

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
                    epoch = datetime.date(1970, 1, 1)                                      # first date
                    current_time  = datetime.date.today()                                  # actual date

                    if options.sensor_graph_histories == 0:                                # without filtering
                        check_start  = current_time - datetime.timedelta(days=7300)        # actual date - 20 years
                    if options.sensor_graph_histories == 1:
                        check_start  = current_time - datetime.timedelta(days=1)           # actual date - 1 day
                    if options.sensor_graph_histories == 2:
                        check_start  = current_time - datetime.timedelta(days=7)           # actual date - 7 day (week)
                    if options.sensor_graph_histories == 3:
                        check_start  = current_time - datetime.timedelta(days=30)          # actual date - 30 day (month)
                    if options.sensor_graph_histories == 4:
                        check_start  = current_time - datetime.timedelta(days=365)         # actual date - 365 day (year)

                    log_start = int((check_start - epoch).total_seconds())                 # start date for log in second (timestamp)

                    if sensor.multi_type == 9: # 16x log from probe + battery + signal
                        for i in range(0, 18):
                            temp_balances = {}
                            try:
                                if len(glog_file)>0:
                                    for key in glog_file[i]['balances']:
                                        find_key =  int(key.encode('utf8'))                            # key is in unicode ex: u'1601347000' -> find_key is int number
                                        if find_key >= log_start:                                      # timestamp interval 
                                            find_data = glog_file[i]['balances'][key]
                                            if options.sensor_graph_show_err:                          # if is checked show error values in graph
                                                temp_balances[key] = glog_file[i]['balances'][key]     # add all values from json
                                            else:
                                                if float(find_data['total']) != -127.0:                # not checked, add values if not -127
                                                    temp_balances[key] = glog_file[i]['balances'][key]
                            except:
                                print_report('webpages.py', traceback.format_exc())
                                pass
                            data.append({ 'sname': glog_file[i]['sname'], 'balances': temp_balances})
                    else:
                        for i in range(0, 3):  # 1x log from others + battery + signal
                            temp_balances = {}
                            try:
                                if len(glog_file)>0:
                                    for key in glog_file[i]['balances']:
                                        find_key =  int(key.encode('utf8'))                            # key is in unicode ex: u'1601347000' -> find_key is int number
                                        if find_key >= log_start:                                      # timestamp interval 
                                            find_data = glog_file[i]['balances'][key]
                                            if options.sensor_graph_show_err:                          # if is checked show error values in graph
                                                temp_balances[key] = glog_file[i]['balances'][key]     # add all values from json
                                            else:
                                                if float(find_data['total']) != -127.0:                # not checked, add values if not -127
                                                    temp_balances[key] = glog_file[i]['balances'][key]
                            except:
                                print_report('webpages.py', traceback.format_exc())
                                pass
                            data.append({ 'sname': glog_file[i]['sname'], 'balances': temp_balances})


                    web.header('Access-Control-Allow-Origin', '*')
                    web.header('Content-Type', 'application/json')
                    return json.dumps(data)
                except:
                    print_report('webpages.py', traceback.format_exc())
                    web.header('Access-Control-Allow-Origin', '*')
                    web.header('Content-Type', 'application/json')
                    return json.dumps([])

            elif graph:
                try:
                    name = sensors[index].name
                    stype = sensors[index].sens_type
                    mtype = sensors[index].multi_type
                    return self.core_render.graph_sensor(index, name, stype, mtype) 
                except:    
                    print_report('webpages.py', traceback.format_exc())
                    return self.core_render.graph_sensor(index, name, stype, mtype)                    

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
                except:
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

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)        

        qdict = web.input(AL=[], AH=[], BL=[], BH=[], CL=[], CH=[], DL=[], DH=[], # ... [] for input save multiple select
                         MDL=[], MDH=[], SL=[], SH=[], used_stations=[], used_stations_one=[], used_stations_two=[],
                         SW_C0=[], SW_C1=[], SW_C2=[], SW_C3=[], SW_C4=[], SW_C5=[], SW_C6=[],        # 7 switch closed pgm
                         SW_O0=[], SW_O1=[], SW_O2=[], SW_O3=[], SW_O4=[], SW_O5=[], SW_O6=[],        # 7 switch open pgm
                         SW_SC0=[], SW_SC1=[], SW_SC2=[], SW_SC3=[], SW_SC4=[], SW_SC5=[], SW_SC6=[], # 7 switch closed stations
                         SW_SO0=[], SW_SO1=[], SW_SO2=[], SW_SO3=[], SW_SO4=[], SW_SO5=[], SW_SO6=[]  # 7 switch open stations
                         )                         
        multi_type = -1
        sen_type = -1

        try:
            index = int(index)
            sensor = sensors.get(index)

        except ValueError:
            sensor = sensors.create_sensors()

        if session['category'] == 'admin':
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

            if 'senscode' in qdict: 
                if len(qdict['senscode'])>16 or len(qdict['senscode'])<16:
                    errorCode = qdict.get('errorCode', 'ucode')
                    return self.core_render.sensor(sensor, errorCode)
                else:
                    sensor.encrypt = qdict['senscode']

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
                sensor.trigger_low_program = qdict['BL']
                sensor.trigger_high_program = qdict['BH']

            elif sen_type == 4:                          # motion
                sensor.trigger_low_program = ["-1"]
                sensor.trigger_high_program = qdict['CH']
                if 'motion_msg' in qdict:
                    sensor.motion_msg = qdict['motion_msg']
                if 'no_motion_msg' in qdict:
                    sensor.no_motion_msg = qdict['no_motion_msg']

            elif sen_type == 3:                          # moisture
                sensor.trigger_low_program = qdict['MDL']
                sensor.trigger_high_program = qdict['MDH']
                if 'trigger_low_threshold' in qdict:
                    sensor.trigger_low_threshold = qdict['Mtrigger_low_threshold'] 
                if 'trigger_high_threshold' in qdict:
                    sensor.trigger_high_threshold = qdict['Mtrigger_high_threshold']

            elif sen_type == 5:                          # temperature
                sensor.trigger_low_program = qdict['DL']
                sensor.trigger_high_program = qdict['DH']
                if 'trigger_low_threshold' in qdict:
                    sensor.trigger_low_threshold = qdict['trigger_low_threshold'] 
                if 'trigger_high_threshold' in qdict:
                    sensor.trigger_high_threshold = qdict['trigger_high_threshold']

            elif sen_type == 6 and (multi_type == 0 or multi_type == 1 or multi_type == 2 or multi_type == 3): # multi temperature 0-3
                sensor.trigger_low_program = qdict['DL']
                sensor.trigger_high_program = qdict['DH']
                if 'trigger_low_threshold' in qdict:
                    sensor.trigger_low_threshold = qdict['trigger_low_threshold'] 
                if 'trigger_high_threshold' in qdict:
                    sensor.trigger_high_threshold = qdict['trigger_high_threshold']

            elif sen_type == 6 and multi_type == 4:      # multi dry contact
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

            elif sen_type == 6 and multi_type == 5:      # multi leak detector
                sensor.trigger_low_program = qdict['BL']
                sensor.trigger_high_program = qdict['BH']

            elif sen_type == 6 and multi_type == 6:      # multi moisture
                sensor.trigger_low_program = qdict['MDL']
                sensor.trigger_high_program = qdict['MDH']
                if 'trigger_low_threshold' in qdict:
                    sensor.trigger_low_threshold = qdict['Mtrigger_low_threshold'] 
                if 'trigger_high_threshold' in qdict:
                    sensor.trigger_high_threshold = qdict['Mtrigger_high_threshold']

            elif sen_type == 6 and multi_type == 7:      # multi motion
                sensor.trigger_low_program = ["-1"]
                sensor.trigger_high_program = qdict['CH']
                if 'motion_msg' in qdict:
                    sensor.motion_msg = qdict['motion_msg']
                if 'no_motion_msg' in qdict:
                    sensor.no_motion_msg = qdict['no_motion_msg']

            elif sen_type == 6 and multi_type == 8:      # multi sonic
                sensor.trigger_low_program = qdict['SL']
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
                    sensor.reg_output = qdict['reg_output']
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
                sensor.sw0_open_program = qdict['SW_O0']
                sensor.sw1_open_program = qdict['SW_O1']
                sensor.sw2_open_program = qdict['SW_O2']
                sensor.sw3_open_program = qdict['SW_O3']
                sensor.sw4_open_program = qdict['SW_O4']
                sensor.sw5_open_program = qdict['SW_O5']
                sensor.sw6_open_program = qdict['SW_O6']
                sensor.sw0_closed_program = qdict['SW_C0'] 
                sensor.sw1_closed_program = qdict['SW_C1']
                sensor.sw2_closed_program = qdict['SW_C2']
                sensor.sw3_closed_program = qdict['SW_C3']
                sensor.sw4_closed_program = qdict['SW_C4']
                sensor.sw5_closed_program = qdict['SW_C5']
                sensor.sw6_closed_program = qdict['SW_C6']
                sensor.sw0_open_stations = qdict['SW_SO0']
                sensor.sw1_open_stations = qdict['SW_SO1']
                sensor.sw2_open_stations = qdict['SW_SO2']
                sensor.sw3_open_stations = qdict['SW_SO3']
                sensor.sw4_open_stations = qdict['SW_SO4']
                sensor.sw5_open_stations = qdict['SW_SO5']
                sensor.sw6_open_stations = qdict['SW_SO6']
                sensor.sw0_closed_stations = qdict['SW_SC0']
                sensor.sw1_closed_stations = qdict['SW_SC1']
                sensor.sw2_closed_stations = qdict['SW_SC2']
                sensor.sw3_closed_stations = qdict['SW_SC3']
                sensor.sw4_closed_stations = qdict['SW_SC4']
                sensor.sw5_closed_stations = qdict['SW_SC5']
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
                print_report('webpages.py', traceback.format_exc())

        if sensor.index < 0 and session['category'] == 'admin':
            sensors.add_sensors(sensor)

        raise web.seeother('/sensors')


class users_page(ProtectedPage):
    """Open all users page. /users"""

    def GET(self):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

        qdict = web.input()
        delete_all = get_input(qdict, 'delete_all', False, lambda x: True)
        if delete_all:
            while users.count() > 0:
                users.remove_users(users.count()-1)
        return self.core_render.users()


class user_page(ProtectedPage):
    """Open page to allow user modification. /user """
    def GET(self, index):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)        

        qdict = web.input()
        try:
            index = int(index)
            delete = get_input(qdict, 'delete', False, lambda x: True)
            if delete and session['category'] == 'admin':
                users.remove_users(index)
                raise web.seeother('/users')

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

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)        

        qdict = web.input()
        try:
            index = int(index)
            user = users.get(index)

        except ValueError:
            user = users.create_users()

        user.name = ''
        password = ''

        if session['category'] == 'admin':
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

        raise web.seeother('/users')


class image_edit_page(ProtectedPage):
    """Open page to edit images for station."""
    def GET(self, index):
        from ospy.server import session
        import os

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)        
        
        qdict = web.input() 
        errorCode = qdict.get('errorCode', 'None')
        delete = get_input(qdict, 'delete', False, lambda x: True)
        install = get_input(qdict, 'install', False, lambda x: True)

        img_path    = './ospy/images/stations/station%s.png' % str(index)
        img_path_th = './ospy/images/stations/station%s_thumbnail.png' % str(index)

        if delete and session[u'category'] == 'admin':
            try:
                if os.path.isfile(img_path):
                    os.remove(img_path)
                if os.path.isfile(img_path_th):
                    os.remove(img_path_th)
                log.debug('webpages.py', _('Files {} and {} has sucesfully deleted...').format('station%s.png' % str(index),'station%s_thumbnail.png' % str(index)))
            except:
                print_report('webpages.py', traceback.format_exc())
                pass

        if not os.path.isfile(img_path) or not os.path.isfile(img_path_th): 
            img_url = '/images?id=no_image'                           # fake default img
            errorCode = qdict.get('errorCode', 'noex')
            try:
                from PIL import Image
            except ImportError:
                errorCode = qdict.get('errorCode', 'nopil')
                print_report('webpages.py', traceback.format_exc())
                pass
        else:
            img_url = '/images?sf=1&id=station%s' % str(index)        # station img

        if install and session['category'] == 'admin':
            try:
                import subprocess
                cmd = "sudo pip install Pillow"
                proc = subprocess.Popen(cmd,stderr=subprocess.STDOUT,stdout=subprocess.PIPE,shell=True)
                output = proc.communicate()[0]
                log.debug('webpages.py', '{}'.format(output))
                errorCode = qdict.get('errorCode', 'nopilOK')
            except:
                errorCode = qdict.get('errorCode', 'nopilErr')
                print_report('webpages.py', traceback.format_exc())
                pass

        return self.core_render.edit(index, img_url, errorCode)


    def POST(self, index):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)        

        qdict = web.input()

        img_path      = './ospy/images/stations/station%s.png' % str(index)
        img_path_th   = './ospy/images/stations/station%s_thumbnail.png' % str(index)
        img_path_temp = './ospy/images/stations/temp%s.png' % str(index)

        if session['category'] == 'admin':
            if 'enabled' in qdict and qdict['enabled']== 'on':
                options.high_resolution_mode = True
            else:
                options.high_resolution_mode = False 
                   
            i = web.input(uploadfile={})
            web.debug(i['uploadfile'].filename)    # This is the filename
            #web.debug(i['uploadfile'].value)       # This is the file contents
            #web.debug(i['uploadfile'].file.read()) # Or use a file(-like) object
            upload_type = i.uploadfile.filename[-4:len(i.uploadfile.filename)] # only .png file accepted
            types = ['.png','.gif']
            if upload_type not in types:            # check file type is ok
                if not os.path.isfile(img_path) or not os.path.isfile(img_path_th): 
                    img_url = '/images?id=no_image'                            # fake default img
                else:
                    img_url = '/images?sf=1&id=station%s' % str(index)         # station img 
            
                errorCode = qdict.get('errorCode', 'uplname') 
                return self.core_render.edit(index, img_url, errorCode)
            else:                     # file is png continue
                if not os.path.isfile(img_path_temp):
                    fout = open(img_path_temp,'wb') 
                    fout.write(i.uploadfile.file.read()) 
                    fout.close()
                    log.debug('webpages.py', _('File {} has sucesfully uploaded...').format(i.uploadfile.filename))
                else:
                    os.remove(img_path_temp) 
                    fout = open(img_path_temp,'wb')  # temporary file after uploading
                    fout.write(i.uploadfile.file.read()) 
                    fout.close()         
                    log.debug('webpages.py', _('File has sucesfully uploaded...'))

                try:
                    from PIL import Image           # pip install Pillow

                    if os.path.isfile(img_path_temp):
                        im = Image.open(img_path_temp)
                        size = 50,50                # resize to thumbnail
                        im.thumbnail(size)
                        im.save(img_path_th, "PNG")
                        im = Image.open(img_path_temp)
                        if options.high_resolution_mode:
                            size = 1024,768         # resize original (high quality)
                        else:
                            size = 640,480          # resize original (low quality)
                        im.thumbnail(size)
                        im.save(img_path, "PNG")
                        os.remove(img_path_temp)
                        log.debug('webpages.py', _('Files has sucesfully resized to max 60x60/640x480...'))
 
                except:
                    pass
                    log.error('webpages.py', _('Cannot create resized files!'))
                    print_report('webpages.py', traceback.format_exc())

        raise web.seeother('/stations')   

 
class image_view_page(ProtectedPage):
    """Open page to view images for station."""
    def GET(self, index):
        import os

        img_path    = './ospy/images/stations/station%s.png' % str(index)   
        if not os.path.isfile(img_path): 
            img_url = '/images?id=no_image'                           # fake default img
        else:
            img_url = '/images?sf=1&id=station%s' % str(index)        # station img

        return self.core_render.view(img_url)


class login_page(WebPage):
    """Login page"""

    def GET(self):
        if check_login(False):
            raise web.seeother('/')
        else:
            if options.first_installation:
                new_user = options.first_password_hash
            else:
                new_user = None        
            return self.core_render.login(signin_form(), new_user)

    def POST(self):
        my_signin = signin_form()

        if not my_signin.validates():
            if options.first_installation:
                return self.core_render.login(my_signin, options.first_password_hash)
            else:
                return self.core_render.login(my_signin, None)    
        else:
            from ospy import server
            server.session.validated = True
            report_login()
            if options.run_logEV:
                logEV.save_events_log( _('Login'), _('User {} logged in').format(server.session['visitor']), id='Login')
            log.info('webpages.py', _('User {} logged in').format(server.session['visitor']))
            raise web.seeother('/')


class logout_page(WebPage):
    def GET(self):
        from ospy.server import session
        session.kill()
        raise web.seeother('/')


class home_page(ProtectedPage):
    """Open Home page."""

    def GET(self):
        from ospy.server import session

        if session['category'] == 'public':
            return self.core_render.home_public()            
        elif session['category'] == 'user':
            return self.core_render.home_user()
        elif session['category'] == 'admin':
            return self.core_render.home_admin()
        else:
            raise web.seeother('/')            


class action_page(ProtectedPage):
    """Page to perform some simple actions (mainly from the homepage)."""

    def GET(self):
        from ospy.server import session

        qdict = web.input()

        stop_all = get_input(qdict, 'stop_all', False, lambda x: True)
        scheduler_enabled = get_input(qdict, 'scheduler_enabled', None, lambda x: x == '1')
        manual_mode = get_input(qdict, 'manual_mode', None, lambda x: x == '1')
        rain_block = get_input(qdict, 'rain_block', None, float)
        level_adjustment = get_input(qdict, 'level_adjustment', None, float)
        toggle_temp = get_input(qdict, 'toggle_temp', False, lambda x: True)

        if stop_all:
            if session['category'] == 'admin' or session['category'] == 'user':
                if not options.manual_mode:
                    options.scheduler_enabled = False
                    programs.run_now_program = None
                    run_once.clear()
                log.finish_run(None)
                stations.clear()
            else:    
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice(home_page, msg)                

        if scheduler_enabled is not None:
            if session['category'] == 'admin' or session['category'] == 'user':
                options.scheduler_enabled = scheduler_enabled
            else:    
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice(home_page, msg)                

        if manual_mode is not None:
            if session['category'] == 'admin' or session['category'] == 'user':
                options.manual_mode = manual_mode
            else:    
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice(home_page, msg)                

        if rain_block is not None:
            if session['category'] == 'admin' or session['category'] == 'user':
                options.rain_block = datetime.datetime.now() + datetime.timedelta(hours=rain_block)
                logEV.save_events_log( _('Rain delay'), _('User has set a delay {} hours').format(rain_block), id=u'RainDelay')
            else:    
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice(home_page, msg)                

        if level_adjustment is not None:
            if session['category'] == 'admin' or session['category'] == 'user':
                options.level_adjustment = level_adjustment / 100
            else:    
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice(home_page, msg)                

        if toggle_temp:
            if session['category'] == 'admin' or session['category'] == 'user':
                options.temp_unit = "F" if options.temp_unit == "C" else "C"
            else:    
                msg = _('You do not have access to this section, ask your system administrator for access.')
                return self.core_render.notice(home_page, msg)                

        set_to = get_input(qdict, 'set_to', None, int)
        sid = get_input(qdict, 'sid', 0, int) - 1
        set_time = get_input(qdict, 'set_time', 0, int)

        if set_to is not None and 0 <= sid < stations.count() and options.manual_mode:
          if session['category'] == 'admin' or session['category'] == 'user':
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

            else:  # If status is off
                stations.deactivate(sid)
                active = log.active_runs()
                for interval in active:
                    if interval['station'] == sid:
                        log.finish_run(interval)
          else:    
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)              

        report_value_change()
        raise web.seeother('/')  # Send browser back to home page


class programs_page(ProtectedPage):
    """Open programs page."""

    def GET(self):
        from ospy.server import session

        qdict = web.input()
        delete_all = get_input(qdict, 'delete_all', False, lambda x: True)
        if delete_all and session['category'] == 'admin':
            while programs.count() > 0:
                programs.remove_program(programs.count()-1)
            report_program_deleted()

        if session['category'] == 'admin':
            return self.core_render.programs()
        elif session['category'] == 'user': 
            return self.core_render.programs_user()
        else:    
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)            
   

class program_page(ProtectedPage):
    """Open page to allow program modification."""

    def GET(self, index):
        from ospy.server import session

        qdict = web.input()
        try:
            index = int(index)
            delete = get_input(qdict, 'delete', False, lambda x: True)
            runnow = get_input(qdict, 'runnow', False, lambda x: True)
            enable = get_input(qdict, 'enable', None, lambda x: x == '1')
            if delete and session['category'] == 'admin':
                programs.remove_program(index)
                Timer(0.1, programs.calculate_balances).start()
                report_program_deleted()
                raise web.seeother('/programs')
            elif runnow:
                programs.run_now(index)
                Timer(0.1, programs.calculate_balances).start()
                report_program_runnow()
                raise web.seeother('/')
            elif enable is not None:
                programs[index].enabled = enable
                Timer(0.1, programs.calculate_balances).start()
                report_program_toggle()
                raise web.seeother('/programs')
        except ValueError:
            pass

        if isinstance(index, int):
            program = programs.get(index)
        else:
            program = programs.create_program()
            program.set_days_simple(6*60, 30, 30, 0, [])

        report_program_change()
        return self.core_render.program(program)

    def POST(self, index):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

        qdict = web.input()
        try:
            index = int(index)
            program = programs.get(index)
        except ValueError:
            program = programs.create_program()

        qdict['schedule_type'] = int(qdict['schedule_type'])

        program.name = qdict['name']
        program.stations = json.loads(qdict['stations'])
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
        raise web.seeother('/programs')


class runonce_page(ProtectedPage):
    """Open a page to view and edit a run once program."""

    def GET(self):
        return self.core_render.runonce()

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

        if session['category'] == 'admin' or session['category'] == 'user':
            run_once.set(station_seconds)
            report_program_toggle()
            raise web.seeother('/')
        else:
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)            


class plugins_manage_page(ProtectedPage):
    """Manage plugins page."""

    def GET(self):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)        

        qdict = web.input()
        plugin = get_input(qdict, 'plugin', None)
        delete = get_input(qdict, 'delete', False, lambda x: True)
        enable = get_input(qdict, 'enable', None, lambda x: x == '1')
        disable_all = get_input(qdict, 'disable_all', False, lambda x: True)
        enable_all = get_input(qdict, 'enable_all', False, lambda x: True)
        delete_all = get_input(qdict, 'delete_all', False, lambda x: True)
        auto_update = get_input(qdict, 'auto', None, lambda x: x == '1')
        use_update = get_input(qdict, 'use', None, lambda x: x == '1')

        if disable_all:
            options.enabled_plugins = []
            plugins.start_enabled_plugins()

        if enable_all:
            for plugin in plugins.available():
               if plugin not in options.enabled_plugins:
                  options.enabled_plugins.append(plugin)
            plugins.start_enabled_plugins()

        if delete_all:
            from ospy.helpers import del_rw
            import shutil
            for plugin in plugins.available():
                if plugin in options.enabled_plugins:
                    options.enabled_plugins.remove(plugin)
                shutil.rmtree(os.path.join('plugins', plugin), onerror=del_rw)  
            options.enabled_plugins = options.enabled_plugins  # Explicit write to save to file
            plugins.start_enabled_plugins()
            raise web.seeother('/plugins_manage')

        if plugin is not None and plugin in plugins.available():
            if delete:
                enable = False

            if enable is not None:
                if not enable and plugin in options.enabled_plugins:
                    options.enabled_plugins.remove(plugin)
                elif enable and plugin not in options.enabled_plugins:
                    options.enabled_plugins.append(plugin)
                options.enabled_plugins = options.enabled_plugins  # Explicit write to save to file
                plugins.start_enabled_plugins()

            if delete:
                from ospy.helpers import del_rw
                import shutil
                shutil.rmtree(os.path.join('plugins', plugin), onerror=del_rw)

            raise web.seeother('/plugins_manage')

        if auto_update is not None:
            options.auto_plugin_update = auto_update
            raise web.seeother('/plugins_manage')
        
        if use_update is not None:
            options.use_plugin_update = use_update
            raise web.seeother('/plugins_manage')

        return self.core_render.plugins_manage()


class plugins_install_page(ProtectedPage):
    """Manage plugins page."""

    def GET(self):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)        

        qdict = web.input()
        repo = get_input(qdict, 'repo', None, int)
        plugin = get_input(qdict, 'plugin', None)
        install = get_input(qdict, 'install', False, lambda x: True)

        if install and repo is not None:
            plugins.checker.install_repo_plugin(plugins.REPOS[repo], plugin)
            self._redirect_back()

        plugins.checker.update()
        return self.core_render.plugins_install()


    def POST(self):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)        

        qdict = web.input(zipfile={})

        zip_file_data = qdict['zipfile'].file
        plugins.checker.install_custom_plugin(zip_file_data)

        self._redirect_back()


class log_page(ProtectedPage):
    """View Log"""

    def GET(self):
        from ospy.server import session

        qdict = web.input()

        if 'clear' in qdict and session['category'] == 'admin':
            log.clear_runs()
            raise web.seeother('/log')

        if 'clearEM' in qdict and session['category'] == 'admin':
            logEM.clear_email()
            raise web.seeother('/log')

        if 'clearEV' in qdict and session['category'] == 'admin':
            logEV.clear_events()
            raise web.seeother('/log')

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
            data = "Date; Time; Subject; Status\n"
            for interval in events:
                data += '; '.join([
                    interval['date'],
                    interval['time'],
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
            print_report('webpages.py', traceback.format_exc())
            raise web.seeother('/')

    def POST(self):
        from ospy.server import session      

        qdict = web.input()

        log_filter_server = get_input(qdict, 'log_filter_server', False, lambda x: True)
        log_filter_internet = get_input(qdict, 'log_filter_internet', False, lambda x: True)
        log_filter_rain_sensor = get_input(qdict, 'log_filter_rain_sensor', False, lambda x: True)
        log_filter_rain_delay = get_input(qdict, 'log_filter_rain_delay', False, lambda x: True)
        log_filter_login = get_input(qdict, 'log_filter_login', False, lambda x: True)
        
        options.log_filter_server = log_filter_server
        options.log_filter_internet = log_filter_internet
        options.log_filter_rain_sensor = log_filter_rain_sensor
        options.log_filter_rain_delay = log_filter_rain_delay
        options.log_filter_login = log_filter_login

        watering_records = log.finished_runs()
        email_records = logEM.finished_email()
        events_records = logEV.finished_events()

        if session['category'] == 'admin':
            return self.core_render.log(watering_records, email_records, events_records)
        elif session['category'] == 'user':
            return self.core_render.log_user(watering_records, email_records, events_records)
        else:
            raise web.seeother('/')

class options_page(ProtectedPage):
    """Open the options page for viewing and editing."""

    def GET(self):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

        qdict = web.input()
        errorCode = qdict.get('errorCode', 'none')

        return self.core_render.options(errorCode)

    def POST(self):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

        changing_language = False

        qdict = web.input()

        if 'lang' in qdict:
            if qdict['lang'] != options.lang:     # if changed languages
                changing_language = True

        if 'aes_gener' in qdict and qdict['aes_gener'] == '1':
            from ospy.helpers import now, password_hash
            options.aes_key = password_hash(str(now()), 'notarandomstring')[:16]
            raise web.seeother('/options?errorCode=pw_aesGenerOK') 

        if 'aes_key' in qdict and len(qdict['aes_key'])>16:
            raise web.seeother('/options?errorCode=pw_aeslenERR')
        elif 'aes_key' in qdict and len(qdict['aes_key'])<16:
            raise web.seeother('/options?errorCode=pw_aeslenERR')
        else:
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
                    else:
                        raise web.seeother('/options?errorCode=pw_mismatch')
                else:
                    raise web.seeother('/options?errorCode=pw_wrong')

                from ospy.server import session
                session.kill()
                raise web.seeother('/')    # after change password -> logout
            except KeyError:
                pass
   
        if 'rbt' in qdict and qdict['rbt'] == '1':
            report_rebooted()
            reboot(block=True) # Linux HW software 
            msg = _('The system (Linux) will now restart (restart started by the user in the OSPy settings), please wait for the page to reload.')
            return self.core_render.notice(home_page, msg) 

        if 'rstrt' in qdict and qdict['rstrt'] == '1':
            report_restarted()
            restart()    # OSPy software
            msg = _('The OSPy will now restart (restart started by the user in the OSPy settings), please wait for the page to reload.')
            return self.core_render.notice(home_page, msg)
        
        if 'pwrdwn' in qdict and qdict['pwrdwn'] == '1':
            report_poweroff()
            poweroff(wait=15, block=True)   # shutll HW system
            msg = _('The system (Linux) is now shutting down ... The system must be switched on again by the user (switching off and on your HW device).')
            return self.core_render.notice(home_page, msg) 

        if 'deldef' in qdict and qdict['deldef'] == '1':
            from ospy import server
            from ospy.helpers import ospy_to_default
            try:        
                report_restarted()
                stations.clear()
                server.stop()
                server.session.kill()
                ospy_to_default()
                restart()    # OSPy software
            except:
                print_report('webpages.py', traceback.format_exc())
                server.session.kill()
                server.stop()
                server.start()
                raise web.seeother('/')

        if changing_language:
            report_restarted()
            restart()    # OSPy software
            msg = _('A language change has been made in the settings, the OSPy will now restart and load the selected language.')
            return self.core_render.notice(home_page, msg)

        report_option_change()
        raise web.seeother('/')


class stations_page(ProtectedPage):
    """Stations page"""

    def GET(self):
        return self.core_render.stations()

    def POST(self):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

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
        raise web.seeother('/')

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

        if session['category'] == 'admin':
            return self.core_render.help(docs)
        elif session['category'] == 'user':
            return self.core_render.help_user(docs)
        else:
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)                    
        
class db_unreachable_page(ProtectedPage):
    """Failed to reach download."""

    def GET(self):
        msg = _('System component is unreachable or busy. Please wait (try again later).')
        return self.core_render.notice('/download', msg)

class download_page(ProtectedPage):
    """Download OSPy backup file with settings"""
    def GET(self):
        from ospy.server import session
        from ospy.helpers import mkdir_p, del_rw, ASCI_convert
        import os
        import time
        import shutil

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

        def _read_log(path):
            """Read file"""
            try:
                with open(path, 'rb') as fh:
                    return fh.read()
            except IOError:
                print_report('webpages.py', traceback.format_exc())
                return []

        try:
            ospy_root = './ospy/'
            backup_path = ospy_root + 'backup'                                                # Where is backup zip file
            backup_name = 'ospy_backup' 
            dir_name = ospy_root + 'data'
            download_name = '{}_backup_{}.zip'.format(ASCI_convert(options.name).decode("utf-8"), time.strftime("%d.%m.%Y_%H-%M-%S"))   # Example: ospy_backup_4.12.2020_18-40-20.zip

            if os.path.exists(backup_path):                                                   # Deleting old folder backup
                log.debug('webpages.py', _('Deleting folder backup.'))
                shutil.rmtree(backup_path, onerror=del_rw)

            if not os.path.exists(backup_path):                                               # Create new folder for backup
                log.debug('webpages.py', _('Creating folder backup.'))
                mkdir_p(backup_path)

            if os.path.exists(backup_path):                                                   # Create zip backup
                log.debug('webpages.py', _('Creating backup zip file.'))
                shutil.make_archive(backup_path + '/' + backup_name, 'zip', root_dir=dir_name)

            if os.path.exists(backup_path):
                log.debug('webpages.py', _('File {} is created successfully.').format(download_name))
                import mimetypes
                content = mimetypes.guess_type(backup_path + '/' + backup_name + '.zip')[0]
                web.header('Content-type', content)
                web.header('Content-Length', os.path.getsize(backup_path + '/' + backup_name + '.zip'))
                web.header('Content-Disposition', 'attachment; filename=%s'%download_name)
                #web.header('Transfer-Encoding', 'chunked')                                   # https://webpy.org/cookbook/streaming_large_files
                return _read_log(backup_path + '/' + backup_name + '.zip')
            else:
                log.error('webpages.py', _(u'System component is unreachable or busy. Please wait (try again later).'))
                msg = _('System component is unreachable or busy. Please wait (try again later).')
                return self.core_render.notice(u'/download', msg)
             
        except Exception:
            print_report('webpages.py', traceback.format_exc())
            raise web.seeother('/')


class upload_page(ProtectedPage):
    """Upload ospy_backup.zip file with settings and images for stations"""
    
    def GET(self):
        raise web.seeother('/')

    def POST(self):
        from ospy.helpers import ospy_to_default, mkdir_p, del_rw
        from ospy import server
        import os
        from zipfile import ZipFile
        from distutils.dir_util import copy_tree
        import shutil

        if server.session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

        ospy_root = './ospy/'
        upload_path = ospy_root + 'upload'

        i = web.input(uploadfile={})

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
            upload_type = i.uploadfile.filename[-4:len(i.uploadfile.filename)]  # Only .zip file accepted
            if upload_type == '.zip':                                           # Check file type
                fout = open(upload_path + '/ospy_upload.zip', 'wb')             # Write uploaded file to upload folder
                fout.write(i.uploadfile.file.read()) 
                fout.close() 
                
                log.debug('webpages.py', _('Uploading to folder OK, now extracting zip file.'))

                with ZipFile(upload_path + '/ospy_upload.zip', mode='r') as zf: # Extract zip file
                    zf.extractall(ospy_root + 'upload/ospy_upload')
                    log.debug('webpages.py', _('Extracted from zip OK.'))

                report_restarted()

                # we delete all settings before ospy recovery

                stations.clear()                
                server.stop()
                server.session.kill()

                ospy_to_default(del_upload=False)

                print_report('webpages.py', _('Copy extrated folders with files to data dir.'))
                fromDirectory = os.path.join('ospy', 'upload', 'ospy_upload')
                toDirectory = os.path.join('ospy', 'data')
                copy_tree(fromDirectory, toDirectory)                          # Copy from to

                restart()                                                      # Restart OSPy software

                msg = _('Restoring backup files sucesfully, now restarting OSPy...')
                return self.core_render.notice(home_page, msg)
            else:
                errorCode = "pw_filename" 
                return self.core_render.options(errorCode)

        except Exception:
            print_report('webpages.py', traceback.format_exc())
            return self.core_render.options()


class upload_page_SSL(ProtectedPage):
    """Upload certificate file to SSL dir, fullchain.pem or privkey.pem"""
    
    def GET(self):
        raise web.seeother('/')

    def POST(self):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

        SSL_FOLDER = './ssl'
        OPTIONS_FILE_FULL = SSL_FOLDER + '/fullchain.pem' # cert file
        OPTIONS_FILE_PRIV = SSL_FOLDER + '/privkey.pem'   # key file

        qdict = web.input()
        if 'generate' in qdict and qdict['generate'] == '1':   # generating own SSL certificate to ssl folder
            try:
                print_report('webpages.py', _('Try-ing generating SSL certificate...'))
                log.debug('webpages.py', _('Try-ing generating SSL certificate...'))

                from OpenSSL import crypto, SSL
                # openssl version
                # sudo apt-get install openssl
                from time import gmtime, mktime
                import random
  
                # create a key pair
                k = crypto.PKey()
                k.generate_key(crypto.TYPE_RSA, 2048)
 
                # create a self-signed cert
                cert = crypto.X509()
                cert.get_subject().C = "EU"                # your country
                cert.get_subject().ST = "Czechia"          # your state
                cert.get_subject().L = "Prague"            # location 
                cert.get_subject().O = "OSPy sprinkler"    # organization
                cert.get_subject().OU = "opensprinkler.cz" # this field is the name of the department or organization unit making the request
                cert.get_subject().CN = options.domain_ssl # common name
                cert.get_subject().emailAddress = "admin@opensprinkler.cz" # e-mail
                cert.set_serial_number(random.randint(1000, 1000000))
                cert.gmtime_adj_notBefore(0)
                cert.gmtime_adj_notAfter(10*365*24*60*60)
                cert.set_issuer(cert.get_subject())
                cert.set_pubkey(k)
                cert.sign(k, 'sha256')

                open(OPTIONS_FILE_FULL, "wb").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
                open(OPTIONS_FILE_PRIV, "wb").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

                print_report('webpages.py', _('OK'))
                log.debug('webpages.py', _('OK'))

                errorCode = "pw_generateSSLOK"
                return self.core_render.options(errorCode)

            except Exception:
                pass
                print_report('webpages.py', traceback.format_exc())
                log.debug('webpages.py', traceback.format_exc())
                errorCode = "pw_generateSSLERR"
                return self.core_render.options(errorCode)

        i = web.input(uploadfile={})
        try:
            if i.uploadfile.filename == 'fullchain.pem' or i.uploadfile.filename == 'privkey.pem':
               
                if os.path.isfile(OPTIONS_FILE_FULL) and i.uploadfile.filename == 'fullchain.pem':  # is old files in folder ssl?
                    if os.path.isfile(OPTIONS_FILE_FULL):        # exists file fullchain.pem?
                        os.remove(OPTIONS_FILE_FULL)             # remove file
                        log.debug('webpages.py', _('Remove fullchain.pem...'))
                if os.path.isfile(OPTIONS_FILE_PRIV) and i.uploadfile.filename == 'privkey.pem':    # is old files in folder ssl?        
                    if os.path.isfile(OPTIONS_FILE_PRIV):        # exists file privkey.pem?
                        os.remove(OPTIONS_FILE_PRIV)             # remove file  
                        log.debug('webpages.py', _('Remove privkey.pem...'))

                fout = open('./ssl/' + i.uploadfile.filename,'wb')
                fout.write(i.uploadfile.file.read())
                fout.close()

                log.debug('webpages.py', _('Upload SSL file %s') %i.uploadfile.filename)
                #report_restarted()
                #restart(3)
                #return self.core_render.restarting(home_page)
                errorCode = "pw_filenameSSLOK"
                return self.core_render.options(errorCode)
            else:        
                errorCode = "pw_filenameSSL" 
                return self.core_render.options(errorCode)

        except Exception:
            return self.core_render.options()

class images_page(ProtectedPage):
    """Return pictures with information about board connection - for help page."""

    def GET(self):

        import mimetypes

        try:
            qdict = web.input()

            id = get_input(qdict, 'id')                                   # id = name for image (ex: station1.png)
            s_folder = get_input(qdict, 'sf', None, lambda x: x == '1')   # sf = 1 read from folder: images/stations else from images/

            if id is not None:
                if s_folder is not None:
                    download_name = 'ospy/images/stations/' + id
                else:
                    download_name = 'ospy/images/' + id

                if os.path.isfile(download_name):     # exists image? 
                    content = mimetypes.guess_type(download_name)[0]
                    web.header('Content-type', content)
                    web.header('Content-Length', os.path.getsize(download_name))
                    web.header('Content-Disposition', 'attachment; filename=%s' % str(id))
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

        web.header('Content-Type', 'application/json')
        return json.dumps(statuslist)


class api_log_json(ProtectedPage):
    """Simple Log API"""

    def GET(self):
        qdict = web.input()
        data = []
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
        epoch = datetime.date(1970, 1, 1)

        for station in stations.get():
            if station.enabled and any(station.index in program.stations for program in programs.get()):
                statuslist.append({
                    'station': station.name,
                    'balances': {int((key - epoch).total_seconds()): value for key, value in station.balance.items()}})

        web.header('Content-Type', 'application/json')
        return json.dumps(statuslist, indent=2)


class showInFooter(object):
    """Enables plugins to display e.g. sensor reagings in the footer of OSPy's UI"""

    def __init__(self, label = "", val = "", unit = "", button = ""):
        self._label = label
        self._val = val
        self._unit = unit
        self._button = button
        self._idx = None
        
        self._idx = len(pluginFtr)
        pluginFtr.append({"label": self._label, "val": self._val, "unit": self._unit, "button": self._button})

    @property
    def label(self):
        if not self._label:
            return _('Label not set')
        else:
            return self._label
    
    @label.setter
    def label(self, text):
        self._label = text
        if self._label:
            pluginFtr[self._idx]["label"] = self._label + ": "

    @property
    def val(self):
        if self._val == "":
            return _('Value not set')
        else:
            return self._val

    @val.setter
    def val(self, num):
        self._val = num
        pluginFtr[self._idx]["val"] = self._val

    @property
    def unit(self):
        if not self.unit:
            return _('Unit not set')
        else:
            return self._unit
    
    @unit.setter
    def unit(self, text):
        self._unit = text
        pluginFtr[self._idx]["unit"] = " " + self._unit

    @property
    def button(self):
        if not self.button:
            return '-'
        else:
            return self._button

    @button.setter
    def button(self, text):
        self._button = text
        pluginFtr[self._idx]["button"] = self._button


class showOnTimeline:
    """ Used to display plugin data next to station time countdown on home page timeline. """

    def __init__(self, val = "", unit = ""):
        self._val = val
        self._unit = unit
        self._idxs = None

        self._idxs = len(pluginStn)
        pluginStn.append([self._val, self._unit])

    @property
    def clear(self):
        del pluginStn[self._idx][:] #  Remove elements of list but keep empty list

    @property
    def unit(self):
        if not self.unit:
            return _('Unit not set')
        else:
            return self._unit

    @unit.setter
    def unit(self, text):
        self._unit = text
        pluginStn[self._idx][0] = self._unit


    @property
    def val(self):
        if not self._val:
            return _('Value not set')
        else:
            return self._val

    @val.setter
    def val(self, num):
        self._val = num
        pluginStn[self._idx][1] = self._val

class api_plugin_data(ProtectedPage):
    """Simple plugin data API"""

    def GET(self):
        footer_data = []
        station_data = []
        sensor_data = []
        data = {}

        if options.show_plugin_data:
            for i, v in enumerate(pluginFtr):
                footer_data.append((i, v["val"]))
            for v in pluginStn:
                station_data.append((v[1]))

        if options.show_sensor_data: 
            from ospy.sensors import sensors_timer 
            sensor_data = sensors_timer.read_status()

        data["fdata"] = footer_data
        data["sdata"] = station_data
        data["sendata"] = sensor_data

        web.header('Content-Type', 'application/json')
        return json.dumps(data)

class api_update_status(ProtectedPage):
    """Simple plugins update and ospy system update status API"""

    def GET(self):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)

        pl_data = []
        data = {}
        must_update = 0
        os_state = 0
        os_avail = '0.0.0'
        os_curr  = '0.0.0'
        os_change  = ''

        running_list = plugins.running()
        current_info = options.plugin_status

        for plugin in plugins.available():
            running = plugin in running_list
            available_info = plugins.checker.available_version(plugin)
            if available_info is not None:
                if plugin in current_info and current_info[plugin]['hash'] != available_info['hash']:
                    pl_data.append((must_update, plugins.plugin_name(plugin)))
                    must_update += 1

        if options.use_plugin_update is not None:             # if the update is not enabled in the plugins settings, the window with an available update will not pop up on the home page. 
            data["plugin_name"]   = pl_data                   # name of plugins where must be updated
            data["plugins_state"] = must_update               # status whether it is necessary to update the plugins (count plugins)
        else:
            data["plugin_name"]   = []
            data["plugins_state"] = 0

        try:
            if options.use_plugin_update is not None:         # if the update is not enabled in the plugins settings, the window with an available update will not pop up on the home page.
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
        from ospy.helpers import uptime, get_cpu_temp, get_cpu_usage, get_external_ip
        
        data = {}
        data["cpu_temp"]    = get_cpu_temp(options.temp_unit)
        data["cpu_usage"]   = get_cpu_usage()
        data["sys_uptime"]  = uptime()
        data["ip"]          = get_external_ip()

        web.header('Content-Type', 'application/json')
        return json.dumps(data)   


class api_search_sensors(ProtectedPage):
    """APi for Available sensors that are not assigned"""

    def GET(self):
        from ospy.server import session

        if session['category'] != 'admin':
            msg = _('You do not have access to this section, ask your system administrator for access.')
            return self.core_render.notice(home_page, msg)
        
        searchData = []
        searchData.extend(sensorSearch) if sensorSearch not in searchData else searchData

        web.header('Content-Type', 'application/json')
        return json.dumps(searchData)