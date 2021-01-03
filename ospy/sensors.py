# -*- coding: utf-8 -*-
__author__ = 'Martin Pihrt'

# System imports
from threading import Thread
import traceback
import logging
import traceback
import time
import datetime
import subprocess
import os
import json

# Local imports
from ospy.options import options
from ospy.helpers import now, password_hash, datetime_string, mkdir_p
from ospy.log import log, logEM
from ospy.programs import programs
#from ospy.runonce import run_once
#from ospy.stations import stations

### Sensors ###
class _Sensor(object):
    SAVE_EXCLUDE = ['SAVE_EXCLUDE', 'index', '_sensors']

    def __init__(self, sensors_instance, index):
        self._sensors = sensors_instance
        self.name = ""                  # sensor name        
        self.encrypt = password_hash(str(now()), 'notarandomstring')[:16] # sensor security encrypted code
        self.enabled = 0                # sensor enable or disable
        self.sens_type = 0              # selector sensor type: 0-5 'None', 'Dry Contact', 'Leak Detector', 'Moisture', 'Motion', 'Temperature', 'Multi'
        self.com_type = 0               # selector sensor communication type 0-1: 'Wi-Fi/LAN', 'Radio'
        self.multi_type = 0             # selector multi type 0-7: 'Temperature DS1, DS2, DS3, DS4', 'Dry Contact', 'Leak Detector', 'Moisture', 'Motion'
        self.notes = ""                 # notes for sensor
        self.log_samples = 0            # log samples
        self.last_log_samples = 0       # last log samples millis
        self.log_event = 0              # log event
        self.send_email  = 0            # send e-mail  
        self.sample_rate = 60           # sample rate 
        self.last_read_value = ""       # last read value (actual)
        self.prev_read_value = ""       # prev read value
        self.sensitivity = 0            # sensitivity
        self.stabilization_time = 0     # stabilization time
        self.trigger_low_program = []   # open program
        self.trigger_high_program = []  # close Program
        self.trigger_low_threshold = "" # low threshold
        self.trigger_high_threshold = ""# high threshold
        self.ip_address = [0,0,0,0]     # ip address for sensor 
        self.mac_address = ""           # mac address for sensor
        self.last_battery = ""          # battery voltage  
        self.rssi = ""                  # rssi signal
        self.radio_id = 0               # radio id
        self.response = 0               # response 0 = offline, 1 = online
        self.fw = 0                     # sensor firmware (ex: 100 is 1.00)
        self.last_response = now()      # last response (last now time when the sensor sent data)

        options.load(self, index) 

    @property
    def index(self):
        try:
            return self._sensors.get().index(self)
        except ValueError:
            return -1    

    def __setattr__(self, key, value):
        try:
            super(_Sensor, self).__setattr__(key, value)
            if not key.startswith('_') and key not in self.SAVE_EXCLUDE:
                options.save(self, self.index)
        except ValueError:  # No index available yet
            logging.debug(traceback.format_exc())
            pass                                             
                

class _Sensors(object):
    def __init__(self):
        self._sensors = []
        self._loading = True
        options.load(self)
        self._loading = False

        try:
            logging.debug(_(u'Loading sensors...'))
            i = 0
            while options.available(_Sensor, i):
                self._sensors.append(_Sensor(self, i)) 
                i += 1   
        except:
            logging.debug(traceback.format_exc())
            pass                

    def add_sensors(self, sensor=None):
        try:
            if sensor is None:
                sensor = _Sensor(self, len(self._sensors))
            self._sensors.append(sensor)
            options.save(sensor, sensor.index)
            logging.debug(_(u'Adding new sensor: {} with id: {}').format(sensor.name,sensor.index))
        except:
            logging.debug(traceback.format_exc())
            pass

    def create_sensors(self):
        """Returns a new sensor, but doesn't add it to the list."""
        try:
            return _Sensor(self, -1-len(self._sensors))
        except:
            logging.debug(traceback.format_exc())
            pass       

    def remove_sensors(self, index):
        try:
            if 0 <= index < len(self._sensors):
                del self._sensors[index]

            for i in range(index, len(self._sensors)):
                options.save(self._sensors[i], i)       # Save sensor using new indices

            options.erase(_Sensor, len(self._sensors))  # Remove info in last index
            logging.debug(_(u'Removing sensor id: {}').format(index))
        except:
            logging.debug(traceback.format_exc())
            pass

    def count(self):
        return len(self._sensors)

    def get(self, index=None):
        try:
            if index is None:
                result = self._sensors[:]
            else:
                result = self._sensors[index]
            return result
        except:
            logging.debug(traceback.format_exc())
            pass

    def __setattr__(self, key, value):
        super(_Sensors, self).__setattr__(key, value)
        if not key.startswith('_') and not self._loading:
            options.save(self)            

    __getitem__ = get
    

sensors = _Sensors()


### Timing loop for sensors ###
class _Sensors_Timer(Thread):
    def __init__(self):
        super(_Sensors_Timer, self).__init__()
        self.status = {}
        self._sleep_time = 0
        self.daemon = True
    
    def add_status(self, id, msg):
        if id in self.status:
            self.status[id] += '\n' + msg
        else:
            self.status[id] = msg

    def start_status(self, id, msg):
        if id in self.status:
            del self.status[id]
        self.add_status(id, msg)

    def stop_status(self, id):
        if id in self.status:
            del self.status[id]        

    def update(self):
        self._sleep_time = 0

    def _sleep(self, secs):
        self._sleep_time = secs
        while self._sleep_time > 0:
            time.sleep(1)
            self._sleep_time -= 1

    def _try_send_mail(self, text, logtext, attachment=None, subject=None):
        try:
            from plugins.email_notifications import try_mail 
            try_mail(text, logtext, attachment, subject)      
        except:
            log.debug(u'sensors.py', _(u'E-mail not send! The Email Notifications plug-in is not found in OSPy or not correctly setuped.'))
            pass  

    def _read_log(self, dir_name):
        try:
            with open(dir_name) as logf:
                return json.load(logf)
        except IOError:
            return []

    def _write_log(self, dir_name, data):
        try:
            with open(dir_name, 'w') as outfile:
                json.dump(data, outfile)
        except Exception:
            logging.debug(traceback.format_exc())
            
    def update_log(self, sensor, lg, msg, action=''):  # lg (lge is event, lgs is samples)
        try:
            kind = 'slog' if lg == 'lgs' else 'elog'   
            nowg = time.gmtime(now())

            logline = {}
            logline["date"] = time.strftime('%Y-%m-%d', nowg)
            logline["time"] = time.strftime('%H:%M:%S', nowg)
            if kind == 'slog':
                if type(msg) == float:
                    msg = "{0:.1f}".format(msg)
                logline["value"] = str(msg)
                if action:
                    logline["action"] = action
                else:
                    logline["action"] = ''   
            else:
                logline["event"] = str(msg)

            log_dir = os.path.join('.', 'ospy', 'data', 'sensors', str(sensor.index), 'logs')
            if not os.path.isdir(log_dir):
                mkdir_p(log_dir) # ensure dir and file exists after config restore
                logging.debug(_(u'Dir not exists, creating dir: {}').format(log_dir))
            
            log_ref = str(log_dir) + '/' + str(kind)
            if not os.path.isfile(log_ref + '.json'):
                subprocess.call(['touch', log_ref + '.json'])
                logging.debug(_(u'File not exists, creating file: {}').format(str(kind) + '.json'))
            
            try:
                log = self._read_log(log_ref + '.json')
            except:   
                log = []

            log.insert(0, logline)
            if options.run_sensor_entries > 0:        # 0 = unlimited
               log = log[:options.run_sensor_entries] # limit records from options
            self._write_log(log_ref + '.json', log)
            logging.debug(_(u'Updating sensor log to file successfully.')) 
        
        except Exception:
            logging.debug(traceback.format_exc())


    def check_sensors(self):
        for sensor in sensors.get():
            time_dif = int(now() - sensor.last_response)                      # last input from sensor
            if time_dif >= 120:                                               # timeout 120 seconds
                if sensor.response != 0:
                    sensor.response = 0                                       # reseting status green circle to red (on sensors page)  

            if not sensor.enabled:
                return

            if sensor.sens_type == 0:
                return   

            changed_state = False    

            if sensor.last_read_value != sensor.prev_read_value:    
                sensor.prev_read_value = sensor.last_read_value
                changed_state = True

            ### Dry Contact, Motion, Multi Dry Contact, Multi Motion ###
            if sensor.sens_type == 1 or sensor.sens_type == 4 or (sensor.sens_type == 6 and sensor.multi_type == 4) or (sensor.sens_type == 6 and sensor.multi_type == 7):
                if sensor.response:                                           # sensor is enabled and response is OK  
                    state = -1
                    if   sensor.sens_type == 1:
                        state =  int(sensor.last_read_value)                  # type is Dry Contact   
                    elif sensor.sens_type == 4: 
                        state =  int(sensor.last_read_value)                  # type is Motion
                    elif sensor.sens_type == 6 and sensor.multi_type == 4:      
                        state =  int(sensor.last_read_value[4])               # multi Dry Contact
                    elif sensor.sens_type == 6 and sensor.multi_type == 7:    
                        state =  int(sensor.last_read_value[7])               # multi Motion  
                                                 
                    if state == 1  and changed_state:                                                    # is closed 
                        if sensor.sens_type == 1 or (sensor.sens_type == 6 and sensor.multi_type == 4):  # Dry Contact or multi Dry Contact 
                            text = _(u'Sensor') + u': {} ({})'.format(sensor.name, _(u'closed and triggered.'))
                            subj = _(u'Sensor Read Success')
                            body = _(u'Successfully read sensor') + u': {} ({})'.format(sensor.name, _(u'closed and triggered.')) 
                            if sensor.log_event:                                                         # sensor is enabled and enabled log           
                                self.update_log(sensor, 'lge', _(u'Closed Trigger'))                     # lge is event, lgs is samples
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj)                               
                        else:                                                                            # Motion or multi Motion 
                            text = _(u'Sensor') + u': {} ({})'.format(sensor.name, _(u'motion detected and triggered.'))
                            subj = _(u'Sensor Read Success')
                            body = _(u'Successfully read sensor') + u': {} ({})'.format(sensor.name, _(u'motion detected and triggered.'))
                            if sensor.log_event:                                                         # sensor is enabled and enabled log           
                                self.update_log(sensor, 'lge', _(u'Motion Trigger')) 
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj)                                
                        self.start_status(sensor.name, text)

                    elif state == 0  and changed_state:                                                  # is open
                        if sensor.sens_type == 1 or (sensor.sens_type == 6 and sensor.multi_type == 4):  # Dry Contact or multi Dry Contact
                            text = _(u'Sensor') + u': {} ({})'.format(sensor.name, _(u'open and triggered.'))
                            subj = _(u'Sensor Read Success')
                            body = _(u'Successfully read sensor') + u': {} ({})'.format(sensor.name, _(u'open and triggered.')) 
                            if sensor.log_event:                                                         # sensor is enabled and enabled log 
                                self.update_log(sensor, 'lge', _(u'Open Trigger'))
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj)
                        else:                                                                            # Motion or multi Motion
                            text = _(u'Sensor') + u': {} ({})'.format(sensor.name, _(u'no motion detected.'))
                            subj = _(u'Sensor Read Success')
                            body = _(u'Successfully read sensor') + u': {} ({})'.format(sensor.name, _(u'no motion detected.')) 
                            if sensor.log_event:                                                         # sensor is enabled and enabled log           
                                self.update_log(sensor, 'lge', _(u'No Motion'))
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj)   
                        self.start_status(sensor.name, text)  

                    if sensor.log_samples:                                                               # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', state)                                        # lge is event, lgs is samples    

                # else:
                    # if not response...action                           

    def run(self):
        self._sleep(3)
        while True:
            try:
                self.check_sensors()
                self._sleep(1)

            except Exception:
                logging.warning(_(u'Sensors timer loop error: {}').format(traceback.format_exc()))
                self._sleep(5)

        
sensors_timer = _Sensors_Timer()

