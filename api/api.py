from __future__ import absolute_import

__author__ = 'Teodor Yantcheff' # Changed: Martin Pihrt (Added logging to ospy log instead of logger. Added support for sensors.)

from .utils import *

from ospy import version
from ospy.stations import stations
from ospy.options import options, level_adjustments
from ospy.programs import programs, ProgramType
from ospy.log import log
from ospy import helpers
from ospy.sensors import sensors
from ospy.helpers import print_report, datetime_string

import json
import traceback
import web


class Stations(object):

    def _station_to_dict(self, station):
        # This is automatic and over all the keys that a _Station has
        # return {k: getattr(station, k) for k in dir(station) if not k.startswith('_') and k is not 'SAVE_EXCLUDE'}

        return {
            'id': station.index,  # TODO: Exchange index for URI ?
            'name': station.name,
            'enabled': station.enabled,
            'ignore_rain': station.ignore_rain,
            'is_master': station.is_master,
            'is_master_two': station.is_master_two,
            'activate_master': station.activate_master,
            'activate_master_two': station.activate_master_two,
            'remaining_seconds': station.remaining_seconds,
            'running': station.active,
            'usage': str(station.usage),
            'precipitation': str(station.precipitation),
            'capacity': str(station.capacity),
            'eto_factor': str(station.eto_factor),  
            'balance': str(station.balance)                                  
        }

    def _dict_to_station(self, sid, data):
        for k, v in data.iteritems():
            log.debug('api.py',  _(u'station id:{} key: {} value: {}').format(sid, k, v))
            try:
                stations[sid].__setattr__(k, v)
            except:
                log.error('api.py', _(u'Error setting station {}, {} to {}').format(sid, k, v)) 

    @does_json
    def GET(self, station_id=None):
        log.debug('api.py', ('GET /stations/{}').format(station_id if station_id else ''))
        if station_id:
            return self._station_to_dict(stations[int(station_id)])
        else:
            l = [self._station_to_dict(s) for s in stations]
            # stations_type = type(stations).__name__  # .strip('_')
            # return {'type': stations_type, 'stations': l}
            return l

    @auth
    @does_json
    def POST(self, station_id=None):
        log.debug('api.py', ('POST /stations/{}').format(station_id if station_id else ''))

        action = web.input().get('do', '').lower()
        station_id = int(station_id)
        if action == 'start':
            log.debug('api.py',  _(u'Starting station {} ({})').format(station_id, stations[station_id].name))
            stations.activate(station_id)
        elif action == 'stop':
            log.debug('api.py',  _(u'Stopping station {} ({})').format(station_id, stations[station_id].name))
            stations.deactivate(station_id)
        else:
            log.error('api.py',  _(u'Unknown station action: {}').format(action))
            raise badrequest()

        return self._station_to_dict(stations[station_id])

    @auth
    @does_json
    def PUT(self, station_id=None):
        log.debug('api.py', ('PUT /stations/{}').format(station_id if station_id else ''))
        update = json.loads(web.data())
        if station_id:
            station_id = int(station_id)
            self._dict_to_station(station_id, update)
            return self._station_to_dict(stations[station_id])
        else:
            for sid, upd in enumerate(update):
                self._dict_to_station(sid, upd)
            return [self._station_to_dict(s) for s in stations]

    @auth
    @does_json
    def DELETE(self, station_id=None):
        log.debug('api.py', ('DELETE /stations/{}').format(station_id if station_id else ''))
        raise web.nomethod()

    def OPTIONS(self, station_id=None):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')


class Programs(object):

    def _program_to_dict(self, program):
        # return {k: getattr(program, k) for k in dir(program) if not k.startswith('_') and k is not 'SAVE_EXCLUDE'}
        return {
            'id': program.index,
            'name': program.name,
            'stations': program.stations,
            'enabled': program.enabled,
            'type': program.type,
            'type_name': ProgramType.NAMES.get(program.type, ''),
            'type_data': program.type_data,
            'summary': program.summary(),
            'schedule': program.schedule,
            'modulo': program.modulo,
            'manual': program.manual,
            'start': program.start,
        }

    def _dict_to_program(self, prog, data):
        set_method_table = {
            ProgramType.DAYS_SIMPLE: prog.set_days_simple,
            ProgramType.REPEAT_SIMPLE: prog.set_repeat_simple,
            ProgramType.DAYS_ADVANCED: prog.set_days_advanced,
            ProgramType.REPEAT_ADVANCED: prog.set_repeat_advanced,
            ProgramType.WEEKLY_ADVANCED: prog.set_weekly_advanced,
            ProgramType.WEEKLY_WEATHER: prog.set_weekly_weather
        }

        for k, v in data.iteritems():
            log.debug('api.py',  _(u'Setting program property key: {} to value: {}').format(k, v))
            try:
                if k not in self.EXCLUDED_KEYS:
                    prog.__setattr__(k, v)
            except:
                log.error('api.py',  _(u'Error setting program property key: {} to value: {}').format(k, v))

            if prog.type is ProgramType.CUSTOM:
                # CUSTOM
                prog.modulo = data['modulo']
                prog.manual = False
                try:
                    prog.start = datetime.fromtimestamp(data['start'])
                except:
                    prog.start = datetime.now()
                prog.schedule = data['schedule']
            else:
                # All other types
                program_set = set_method_table[prog.type]
                program_set(*data['type_data'])

    def __init__(self):
        self.EXCLUDED_KEYS = [
            'type_name', 'summary', 'schedule'
        ]

    @does_json
    def GET(self, program_id):
        log.debug('api.py', ('GET /programs/{}').format(program_id if program_id else ''))

        if program_id:
            program_id = int(program_id)
            return self._program_to_dict(programs[program_id])
        else:
            return [self._program_to_dict(p) for p in programs]

    @auth
    @does_json
    def POST(self, program_id):
        log.debug('api.py', ('POST /programs/{}').format(program_id if program_id else ''))

        if program_id:
            action = web.input().get('do', '').lower()
            program_id = int(program_id)
            if action == 'runnow':
                log.debug('api.py',  _(u'Starting program {} ({})').format(program_id, programs[program_id].name))
                programs.run_now(program_id)
            elif action == 'stop':
                pass  # TODO
            else:
                log.error('api.py',  _(u'Unknown program action: {}').format(action))
                raise badrequest()
            return self._program_to_dict(programs[program_id])
        else:
            program_data = json.loads(web.data())

            p = programs.create_program()
            p.type = program_data.get('type', ProgramType.DAYS_SIMPLE)
            if p.type == ProgramType.DAYS_SIMPLE:
                p.set_days_simple(0, 30, 0, 0, [])  # some sane defaults

            self._dict_to_program(p, program_data)  # some sane defaults

            # p.enabled = False
            programs.add_program(p)
            return self._program_to_dict(programs.get(p.index))

    @auth
    @does_json
    def PUT(self, program_id):
        log.debug('api.py', ('PUT /programs/{}').format(program_id if program_id else ''))
        if program_id:
            program_id = int(program_id)
            program_data = json.loads(web.data())
            self._dict_to_program(programs[program_id], program_data)

            return self._program_to_dict(programs[program_id])
        else:
            raise badrequest()

    @auth
    @does_json
    def DELETE(self, program_id):
        log.debug('api.py', ('DELETE /programs/{}').format(program_id if program_id else ''))
        if program_id:
            programs.remove_program(int(program_id))
        else:
            while programs.count() > 0:
                programs.remove_program(programs.count()-1)

    def OPTIONS(self, program_id):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')


class Options(object):

    def __init__(self):
        """ Stuff that is not to be sent over the API, assuming it's of no interest to potential clients"""
        self.EXCLUDED_OPTIONS = [
            'password_hash', 'password_salt', 'theme', 'logged_runs', 'time_format'
        ]

        """ Options array in the format
          <option_key> : {
                            'name': OPTIONS[option_key]['name']
                            'help': OPTIONS[option_key]['help']
                            .
                            .
                         }
        """
        self.ANNOTATED_OPTIONS = {
            key: {
                opt_key: options.OPTIONS[i].get(opt_key, '')
                for opt_key in ['name', 'help', 'category', 'default', 'min', 'max']
            }
            for i, key in enumerate(options.get_options()) if key not in self.EXCLUDED_OPTIONS
        }

    @does_json
    def GET(self):
        log.debug('api.py', 'GET ' + self.__class__.__name__)
        a = web.input().get('annotated', '').lower()
        if a in ['true', 'yes', 'annotated', '1']:
            opts = {o: {'value': options[o]} for o in self.ANNOTATED_OPTIONS}
            for k in opts.iterkeys():
                # "inject" current option value into the dictionary under "value"
                opts[k].update(self.ANNOTATED_OPTIONS[k])
            return opts
        else:
            return {opt: options[opt] for opt in options.get_options() if opt not in self.EXCLUDED_OPTIONS}

    @auth
    # @does_json
    def PUT(self):
        log.debug('api.py', 'PUT ' + self.__class__.__name__)
        update = json.loads(web.data())
        all_options = options.get_options()
        for key, val in update.iteritems():
            if key in all_options and key not in self.EXCLUDED_OPTIONS:
                try:
                    options[key] = val
                except:
                    log.error('api.py',  _(u'Error updating {} to {}').format(key, val))
                    raise badrequest('{"error": "Error setting option \'{}\' to \'{}\'"}').format(key, val)
            else:
                log.debug('api.py', _(u'Skipping key {}').format(key))
        return self.GET()

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS')


class Logs(object):

    def _runlog_to_dict(self, log_entry):
        return {
            'start': log_entry['start'],
            'end': log_entry['end'],
            'duration': str(log_entry['end'] - log_entry['start']).split('.')[0],  # pass it as a baked string to the client
            'manual': log_entry['manual'],
            'station': log_entry['station'],
            'station_name': stations[log_entry['station']].name,
            'program_id': log_entry['program'],
            'program_name': log_entry['program_name'],
        }

    @does_json
    def GET(self):
        log.debug('api.py', 'GET logs ' + self.__class__.__name__)
        return [self._runlog_to_dict(fr) for fr in log.finished_runs()]
        # web.header('Cache-Control', 'no-cache')
        # web.header('Content-Type', 'application/json')
        # web.header('Access-Control-Allow-Origin', '*')
        # import datetime
        # return datetime.datetime.now()
        # return '[{"start": "2014-10-23T21:25:25", "station": 2, "end": "2014-10-23T21:25:30", "duration": "0:00:05", "station_name": "Station 03ttt", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": "2014-10-23T21:25:30", "station": 3, "end": "2014-10-23T21:25:35", "duration": "0:00:05", "station_name": "Station 04 dest", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": "2014-10-23T21:25:35", "station": 4, "end": "2014-10-23T21:25:40", "duration": "0:00:05", "station_name": "Station 05", "manual": true, "program_name": "Run-Once", "program_id": -1}]'
        # return '[{"start": 1414605866, "station": 0, "end": 1414605881, "duration": "0:00:15", "station_name": "Station 01", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": 1414605881, "station": 2, "end": 1414605896, "duration": "0:00:15", "station_name": "Station 03", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": 1414605896, "station": 5, "end": 1414605911, "duration": "0:00:15", "station_name": "Station 06", "manual": true, "program_name": "Run-Once", "program_id": -1}]'

    @auth
    @does_json
    def DELETE(self):
        log.debug('api.py', 'DELETE ' + self.__class__.__name__)
        log.clear_runs()

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, DELETE, OPTIONS')


class System(object):
    @does_json
    def GET(self):
        log.debug('api.py', 'GET ' + self.__class__.__name__)
        return {
            'version': version.ver_str,
            'CPU_temperature': helpers.get_cpu_temp(),
            'release_date': version.ver_date,
            'uptime': helpers.uptime(),
            'platform': helpers.determine_platform(),
            'rpi_revision': helpers.get_rpi_revision(),
            'total_adjustment': level_adjustments.total_adjustment()
        }

    @auth
    @does_json
    def POST(self):
        log.debug('api.py', 'POST ' + self.__class__.__name__)
        action = web.input().get('do', '').lower()

        if action == 'reboot':
            log.info('api.py',  _(u'System reboot requested via API'))
            helpers.reboot()

        elif action == 'restart':
            log.info('api.py',  _(u'OSPy service restart requested via API'))
            helpers.restart()

        elif action == 'poweroff':
            log.info('api.py',  _(u'System poweroff requested via API'))
            helpers.poweroff()

        else:
            log.error('api.py',  _(u'Unknown system action: {}').format(action))
            raise badrequest()

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')

class Sensors(object):
    def _convert(self, sensor):
        return {
            'id':int(sensor.index),
            'enabled': True if sensor.enabled else False,
            'senstype': sensor.sens_type,
            'senscom': sensor.com_type,
            'logsamples': True if sensor.log_samples else False,
            'logevent': True if sensor.log_event else False,
            'sendemail': True if sensor.send_email else False,
            'samplerate': sensor.sample_rate,
            'lastreadvalue': str(sensor.last_read_value),
            'sensitivity': sensor.sensitivity,
            'stabilizationtime': sensor.stabilization_time,
            'triglowpgm': str(sensor.trigger_low_program),
            'trighighpgm': str(sensor.trigger_high_program),
            'triglowval': str(sensor.trigger_low_threshold),
            'trighighval': str(sensor.trigger_high_threshold),
            'lastbattery': str(sensor.last_battery),
            'rssi': str(sensor.rssi),
            'response': sensor.response,
            'last_response': sensor.last_response,
            'last_response_datetime': sensor.last_response_datetime,
            'fw': sensor.fw,
            'show_in_footer': sensor.show_in_footer,
            'cpu_core': sensor.cpu_core,
            'sonic_top': sensor.sonic_top,
            'sonic_bot': sensor.sonic_bot,
        }

    @does_json
    def GET(self, sensor_id=None):
        log.debug('api.py', ('GET /sensors/{}').format(sensor_id if sensor_id else ''))

        if sensor_id:
            id = int(sensor_id)
            if(id < sensors.count()):
                    sensor = sensors.get(id)
                    return (self._convert(sensor))
            else:
                return []   
        else:
            for sensor in sensors.get():
                return (self._convert(sensor))    

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')  


class Sensor(object):
    #@auth
    @does_json
    def POST(self):
        log.debug('api.py', 'POST ' + self.__class__.__name__)
        from ospy.helpers import now, split_ip, decrypt_data, encrypt_data
        from ospy.webpages import sensorSearch

        qdict  = web.input()
        jqdict = json.loads(qdict['do'].lower())        
        sqdict = qdict['sec']

        decrypt_secret = decrypt_data(options.aes_key, sqdict)

        log.debug('api.py',  _(u'Sensor input IP: {} MAC: {} SECURE: {}.').format(jqdict['ip'], jqdict['mac'].upper(), decrypt_secret))

        if 'ip' and 'mac' in jqdict and 'sec' in qdict:
            find_sens = {
                'name':  jqdict['name'],
                'ip':  jqdict['ip'],
                'real_ip': web.ctx.env['REMOTE_ADDR'],
                'mac': jqdict['mac'].upper(),
                'radio': '-',    
                'type': jqdict['stype'],
                'com': jqdict['scom'],
                'secret': decrypt_secret,
                'fw': jqdict['fw'],
                'cpu_core': jqdict['cpu']
            }  

            for sensor in sensors.get():
                ip = split_ip(jqdict['ip'])              
                if sensor.ip_address == ip and sensor.mac_address.upper() == jqdict['mac'].upper() and sensor.encrypt == decrypt_secret:
                    if 'cpu' in jqdict and jqdict['cpu'] is not None:
                        sensor.cpu_core = int(jqdict['cpu'])
                    if 'rssi' in jqdict and jqdict['rssi'] is not None:
                        sensor.rssi = int(jqdict['rssi'])                               # ex: value is 88  -> real 88% 
                    if 'batt' in jqdict and jqdict['batt'] is not None:
                        sensor.last_battery = (float(jqdict['batt']))/10.0              # ex: value is 132 -> real 13.2V
                    if 'stype' in jqdict and jqdict['stype'] is not None:
                        sen_type = int(jqdict['stype'])                                 # 'None'=0, 'Dry Contact'=1, 'Leak Detector'=2, 'Moisture'=3, 'Motion'=4, 'Temperature'=5
                        if sen_type == 1:                       
                            sensor.last_read_value = int(jqdict['drcon'])
                        elif sen_type == 2:                      
                            sensor.last_read_value = (float(jqdict['lkdet']))/10.0      # ex: value is 132 -> real 13.2%
                        elif sen_type == 3:                      
                            sensor.last_read_value = (float(jqdict['humi']))/10.0       # ex: value is 132 -> real 13.2%
                        elif sen_type == 4:                      
                            sensor.last_read_value = int(jqdict['moti'])
                        elif sen_type == 5:           
                            if options.temp_unit == 'F':          
                                sensor.last_read_value = (float(jqdict['temp'])*1.8 + 32)/10.0 # Fahrenheit ex: value is 132 -> real 13.2F
                            else:     
                                sensor.last_read_value = (float(jqdict['temp']))/10.0          # Celsius ex: value is 132 -> real 13.2C
                        elif sen_type == 6:                                                    # multisensor     
                            read_val = []   
                            try:  
                                if options.temp_unit == 'F':          
                                    read_val.append((float(jqdict['temp'])*1.8 + 32)/10.0)     # DS1
                                    read_val.append((float(jqdict['temp2'])*1.8 + 32)/10.0)    # DS2
                                    read_val.append((float(jqdict['temp3'])*1.8 + 32)/10.0)    # DS3
                                    read_val.append((float(jqdict['temp4'])*1.8 + 32)/10.0)    # DS4
                                else:     
                                    read_val.append((float(jqdict['temp']))/10.0)                              
                                    read_val.append((float(jqdict['temp2']))/10.0)
                                    read_val.append((float(jqdict['temp3']))/10.0)
                                    read_val.append((float(jqdict['temp4']))/10.0)
                                read_val.append(int(jqdict['drcon']))                          # dry contact
                                read_val.append((float(jqdict['lkdet']))/10.0)                 # leak detector 
                                read_val.append((float(jqdict['humi']))/10.0)                  # moisture
                                read_val.append(int(jqdict['moti']))                           # motion
                                if 'son' in jqdict and jqdict['son'] is not None:              # sonic
                                    read_val.append(int(jqdict['son']))
                                else:
                                    read_val.append(int(-1))    

                                sensor.last_read_value = read_val
                            except:    
                                pass
                                print_report('api.py', traceback.format_exc())

                    sensor.last_response = now()
                    sensor.last_response_datetime = datetime_string()

                    if sensor.response != 1:
                        sensor.response = 1

                    if sensor.fw != jqdict['fw']:
                        sensor.fw = jqdict['fw']      

                    log.debug('api.py',  _(u'Input for sensor: {} successfully.').format(sensor.index))

                else:
                    log.error('api.py',  _(u'Received data (IP or MAC or SEC) do not match!'))
    
            try:
                for i in range(0, len(sensorSearch)):
                    ss = sensorSearch[int(i)]
                    if str(ss["mac"]) == str(find_sens["mac"]) and str(ss["ip"]) == str(find_sens["ip"]):  # mac and ip match
                        a_name = u' '.join(ss["name"]).encode('utf-8')
                        b_name = u' '.join(find_sens["name"]).encode('utf-8')
                        if str(ss["type"]) != str(find_sens["type"]):                                      # type not match 
                            try:
                                del sensorSearch[int(i)]
                            except:
                                pass    
                            break
                        elif a_name != b_name:                                                             # name not match 
                            try:
                                del sensorSearch[int(i)]
                            except:
                                pass    
                            break  
                        elif str(ss["com"]) != str(find_sens["com"]):                                      # com not match 
                            try:
                                del sensorSearch[int(i)]
                            except:
                                pass    
                            break
                        elif str(ss["fw"]) != str(find_sens["fw"]):                                        # fw not match 
                            try:
                                del sensorSearch[int(i)]
                            except:
                                pass    
                            break 
                        elif str(ss["secret"]) != str(find_sens["secret"]):                                # secret not match 
                            try:
                                del sensorSearch[int(i)]
                            except:
                                pass    
                            break                                      

                sensorSearch.append(find_sens) if find_sens not in sensorSearch else sensorSearch         

            except:
                pass
                print_report('api.py', traceback.format_exc())
                    
        else:
            log.error('api.py',  _(u'Received data is not correct!'))
            raise badrequest()            

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'POST, OPTIONS')


def get_app():
    urls = (
        # Stations
        r'/stations(?:/(?P<station_id>\d+))?/?', 'Stations',
        # Programs
        r'/programs(?:/(?P<program_id>\d+))?/?', 'Programs',
        # Options
        r'/options/?', 'Options',
        # Logs
        r'/logs/?', 'Logs',
        # System
        r'/system/?', 'System',
        # Sensors
        r'/sensors(?:/(?P<sensor_id>\d+))?/?', 'Sensors', 
        # Sensor
        r'/sensor/?', 'Sensor',       
    )
    return web.application(urls, globals()) 