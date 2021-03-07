# -*- coding: utf-8 -*-
__author__ = 'Martin Pihrt'

# System imports
from threading import Thread, Timer
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
        self.last_log_samples = now()   # last log samples millis
        self.log_event = 0              # log event
        self.send_email  = 0            # send e-mail  
        self.sample_rate = 60           # sample rate 
        self.last_read_value = ""       # last read value (actual)
        self.prev_read_value = "-"      # prev read value
        self.sensitivity = 0            # sensitivity
        self.stabilization_time = 5     # stabilization time
        self.trigger_low_program = ["-1"] # open program (-1 is default none program)
        self.trigger_high_program = ["-1"]# close Program
        self.trigger_low_threshold = "10" # low threshold
        self.trigger_high_threshold = "30"# high threshold
        self.ip_address = [0,0,0,0]     # ip address for sensor 
        self.mac_address = ""           # mac address for sensor
        self.last_battery = ""          # battery voltage  
        self.rssi = ""                  # rssi signal
        self.radio_id = 0               # radio id
        self.response = 0               # response 0 = offline, 1 = online
        self.fw = 0                     # sensor firmware (ex: 100 is 1.00)
        self.last_response = 0          # last response (last now time when the sensor sent data)
        self.last_low_report = now()    # now in moisture, temperature
        self.last_good_report = now()   # now in moisture, temperature
        self.last_high_report = 0       # now in moisture, temperature
        self.show_in_footer = 1         # show sensor data in footer on home page        

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
        self.status = []
        self._sleep_time = 0
        self.daemon = True
    
    def start_status(self, name, msg, btn):
        try:
            for i in range(0, self.len_status()-1):
                if name in self.status[i]:
                    del self.status[i]
            self.status.append((name, msg, btn))
        except:
            pass    
           
    def stop_status(self, name):
        try: 
            for i in range(0, self.len_status()):
                if name in self.status[i]:
                    del self.status[i] #self.status.pop(i)
        except:
            pass            

    def read_status(self):
        return self.status

    def len_status(self):
        return int(len(self.status))   

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

    def _check_high_trigger(self, sensor):
        major_change = True
        status_update = True
        if int(sensor.last_low_report) < int(sensor.last_high_report) or int(sensor.last_good_report) < int(sensor.last_high_report):
            major_change = False
        if not major_change and int(now()) - int(sensor.last_high_report) < 3600:
            status_update = False
        return (major_change, status_update)

    def _check_low_trigger(self, sensor):
        major_change = True
        status_update = True
        if int(sensor.last_high_report) < int(sensor.last_low_report) and int(sensor.last_good_report) < int(sensor.last_low_report):
            major_change = False
        if not major_change and int(now()) - int(sensor.last_low_report) < 3600:
            status_update = False
        return (major_change, status_update)

    def _check_good_trigger(self, sensor):
        major_change = True
        status_update = True
        if int(sensor.last_low_report) < int(sensor.last_good_report) and int(sensor.last_low_report) < int(sensor.last_good_report):
            major_change = False
        if not major_change and int(now()) - int(sensor.last_good_report) < 3600:
            status_update = False
        if int(sensor.last_low_report) == 0 and int(sensor.last_high_report) == 0:
            major_change = False # if no problem dont report on startup    
        return (major_change, status_update)         

    def _trigger_programs(self, sensor, program_list=None):
        try:
            if program_list is None:
                return

            if len(program_list) > 0:
                for p in program_list:
                    if int(p) == -1:
                        return
                    index = int(p)-1
                    logging.debug(_(u'The sensor tries to start the {} (id: {})').format(programs[index].name, p))
                    programs.run_now_program = None                                                                  
                    programs.run_now(index)
                    Timer(0.1, programs.calculate_balances).start()
                    self.update_log(sensor, 'lge', _(u'Starting {}').format(programs[index].name))    
        except:
            logging.debug(traceback.format_exc())
            pass
            
    def update_log(self, sensor, lg, msg, action=''):  # lg (lge is event, lgs is samples)
        try:
            kind = 'slog' if lg == 'lgs' else 'elog'   
            nowg = time.gmtime(now())

            logline = {}
            logline["date"] = time.strftime('%Y-%m-%d', nowg)
            logline["time"] = time.strftime('%H:%M:%S', nowg)
            if kind == 'slog':   # sensor samples
                if type(msg) == float:
                    msg = u"{0:.1f}".format(msg)
                logline["value"] = u"{}".format(msg)

                try: # for graph
                    timestamp = int(time.time())
                    gdata = {"total": u"{}".format(msg)}
                    glog_dir = os.path.join('.', 'ospy', 'data', 'sensors', str(sensor.index), 'logs', 'graph')
                    graph_data = self._read_log(glog_dir + '/' + 'graph.json')
                    graph_data[0]["balances"].update({timestamp: gdata})
                    self._write_log(glog_dir + '/' + 'graph.json', graph_data)
                    logging.debug(_(u'Updating sensor graph log to file successfully.'))                    
                except:
                    glog_dir = os.path.join('.', 'ospy', 'data', 'sensors', str(sensor.index), 'logs', 'graph')
                    if not os.path.isdir(glog_dir):
                        mkdir_p(glog_dir) # ensure dir and file exists after config restore
                    logging.debug(_(u'Dir not exists, creating dir: {}').format(glog_dir))
                    if not os.path.isfile(glog_dir + '/' + 'graph.json'):
                        subprocess.call(['touch', 'graph.json'])
                        logging.debug(_(u'File not exists, creating file: {}').format('graph.json'))
                    graph_def_data = [{"sname": u"{}".format(sensor.name), "balances": {}}]
                    self._write_log(glog_dir + '/' + 'graph.json', graph_def_data)
                    pass

                if action:
                    logline["action"] = u"{}".format(action)
                else:
                    logline["action"] = ''   
            else:                # sensor event log
                logline["event"] = u"{}".format(msg)

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

            ### Dry Contact, Motion, Multi Dry Contact, Multi Motion ###
            if sensor.sens_type == 1 or sensor.sens_type == 4 or (sensor.sens_type == 6 and sensor.multi_type == 4) or (sensor.sens_type == 6 and sensor.multi_type == 7):
                if sensor.response:                                           # sensor is enabled and response is OK  
                    state = -1
                    if   sensor.sens_type == 1:
                        try:
                            state =  int(sensor.last_read_value)              # type is Dry Contact 
                            if state == 1:
                                if sensor.show_in_footer:                                        
                                    self.start_status(sensor.name, _(u'Closed Contact'), sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:                                        
                                    self.start_status(sensor.name, _(u'Open Contact'), sensor.index)                                    
                        except:
                            sensor.last_read_value = -127
                            state =  int(sensor.last_read_value)
                            if sensor.show_in_footer:                                        
                                self.start_status(sensor.name, _(u'Change not yet loaded'), sensor.index) 
                            pass   
                        if sensor.last_read_value != sensor.prev_read_value:    
                            sensor.prev_read_value = sensor.last_read_value
                            changed_state = True  
                    elif sensor.sens_type == 4: 
                        try:
                            state =  int(sensor.last_read_value)              # type is Motion
                            if state == 1:
                                if sensor.show_in_footer:                                        
                                    self.start_status(sensor.name, _(u'Motion Detected'), sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:                                        
                                    self.start_status(sensor.name, _(u'No Motion'), sensor.index)                             
                        except:
                            sensor.last_read_value = -127
                            state =  int(sensor.last_read_value)
                            if sensor.show_in_footer:                                        
                                self.start_status(sensor.name, _(u'Change not yet loaded'), sensor.index)                            
                            pass                             
                        if sensor.last_read_value != sensor.prev_read_value:    
                            sensor.prev_read_value = sensor.last_read_value
                            changed_state = True                         
                    elif sensor.sens_type == 6 and sensor.multi_type == 4:      
                        try:
                            state =  int(sensor.last_read_value[4])           # multi Dry Contact
                            if state == 1:
                                if sensor.show_in_footer:                                        
                                    self.start_status(sensor.name, _(u'Closed Contact'), sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:                                        
                                    self.start_status(sensor.name, _(u'Open Contact'), sensor.index)                            
                        except:
                            sensor.last_read_value = [-127,-127,-127,-127,-127,-127,-127,-127]
                            state =  int(sensor.last_read_value[4])
                            if sensor.show_in_footer:                                        
                                self.start_status(sensor.name, _(u'Change not yet loaded'), sensor.index)                            
                            pass                              
                        if sensor.last_read_value[4] != sensor.prev_read_value:    
                            sensor.prev_read_value = sensor.last_read_value[4]
                            changed_state = True                         
                    elif sensor.sens_type == 6 and sensor.multi_type == 7:  
                        try:  
                            state =  int(sensor.last_read_value[7])           # multi Motion 
                            if state == 1:
                                if sensor.show_in_footer:                                        
                                    self.start_status(sensor.name, _(u'Motion Detected'), sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:                                        
                                    self.start_status(sensor.name, _(u'No Motion'), sensor.index)                             
                        except:
                            sensor.last_read_value = [-127,-127,-127,-127,-127,-127,-127,-127]
                            state =  int(sensor.last_read_value[7])
                            if sensor.show_in_footer:                                        
                                self.start_status(sensor.name, _(u'Change not yet loaded'), sensor.index)
                            pass                             
                        if sensor.last_read_value[7] != sensor.prev_read_value:    
                            sensor.prev_read_value = sensor.last_read_value[7]
                            changed_state = True                                
                                                 
                    if state == 1  and changed_state:                                                    # is closed 
                        if sensor.sens_type == 1 or (sensor.sens_type == 6 and sensor.multi_type == 4):  # Dry Contact or multi Dry Contact 
                            text = _(u'Sensor') + u': {} ({})'.format(sensor.name, _(u'Closed Contact'))
                            subj = _(u'Sensor Read Success')
                            body = _(u'Successfully read sensor') + u': {} ({})'.format(sensor.name, _(u'Closed Contact')) 
                            if sensor.log_event:                                                         # sensor is enabled and enabled log           
                                self.update_log(sensor, 'lge', _(u'Closed Contact'))                     # lge is event, lgs is samples
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj)
                            self._trigger_programs(sensor, sensor.trigger_high_program) 
 
                        else:                                                                            # Motion or multi Motion 
                            text = _(u'Sensor') + u': {} ({})'.format(sensor.name, _(u'Motion Detected'))
                            subj = _(u'Sensor Read Success')
                            body = _(u'Successfully read sensor') + u': {} ({})'.format(sensor.name, _(u'Motion Detected'))
                            if sensor.log_event:                                                         # sensor is enabled and enabled log           
                                self.update_log(sensor, 'lge', _(u'Motion Detected')) 
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj)  
                            self._trigger_programs(sensor, sensor.trigger_high_program) 

                    elif state == 0  and changed_state:                                                  # is open
                        if sensor.sens_type == 1 or (sensor.sens_type == 6 and sensor.multi_type == 4):  # Dry Contact or multi Dry Contact
                            text = _(u'Sensor') + u': {} ({})'.format(sensor.name, _(u'Open Contact'))
                            subj = _(u'Sensor Read Success')
                            body = _(u'Successfully read sensor') + u': {} ({})'.format(sensor.name, _(u'Open Contact')) 
                            if sensor.log_event:                                                         # sensor is enabled and enabled log 
                                self.update_log(sensor, 'lge', _(u'Open Contact'))
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj)
                            self._trigger_programs(sensor, sensor.trigger_low_program) 

                        else:                                                                            # Motion or multi Motion
                            text = _(u'Sensor') + u': {} ({})'.format(sensor.name, _(u'No Motion'))
                            subj = _(u'Sensor Read Success')
                            body = _(u'Successfully read sensor') + u': {} ({})'.format(sensor.name, _(u'No Motion')) 
                            if sensor.log_event:                                                         # sensor is enabled and enabled log           
                                self.update_log(sensor, 'lge', _(u'No Motion'))
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj)  

                    if sensor.log_samples:                                                               # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', state)                                        # lge is event, lgs is samples 

                else:
                    logging.warning(_(u'Sensor: {} not response!').format(sensor.name))
                    if sensor.show_in_footer:
                        self.start_status(sensor.name, _(u'Not response!'), sensor.index)              

            ### Moisture, Temperature, Multi Moisture, Multi Temperature ###
            if sensor.sens_type == 3 or sensor.sens_type == 5 or (sensor.sens_type == 6 and sensor.multi_type == 0) or \
                (sensor.sens_type == 6 and sensor.multi_type == 1) or (sensor.sens_type == 6 and sensor.multi_type == 2) or \
                (sensor.sens_type == 6 and sensor.multi_type == 3) or (sensor.sens_type == 6 and sensor.multi_type == 6):
                if sensor.response:                                           # sensor is enabled and response is OK  
                    state = -1.0
                    if   sensor.sens_type == 3:
                        try:
                            state =  float(sensor.last_read_value)              # type is Moisture      
                        except:
                            sensor.last_read_value = -127
                            state =  float(sensor.last_read_value) 
                            pass
                        if sensor.show_in_footer: 
                            if state == -127:
                                self.start_status(sensor.name, _(u'Moisture probe fault?'), sensor.index)
                            else:                                       
                                self.start_status(sensor.name, _(u'Moisture {}%').format(state), sensor.index)                                 
                    elif sensor.sens_type == 5: 
                        try:
                            state =  float(sensor.last_read_value)              # type is Temperature                                         
                        except:
                            sensor.last_read_value = -127
                            state =  float(sensor.last_read_value) 
                            pass  
                        if sensor.show_in_footer: 
                            if state == -127:
                                self.start_status(sensor.name, _(u'Temperature probe fault?'), sensor.index)
                            else:  
                                if options.temp_unit == 'C':                                     
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2103' % state, sensor.index)
                                else:
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2109' % state, sensor.index)                                                            
                    elif sensor.sens_type == 6 and sensor.multi_type == 0:    
                        try:
                            state =  float(sensor.last_read_value[0])           # multi Temperature DS1  
                        except:
                            sensor.last_read_value = [-127,-127,-127,-127,-127,-127,-127,-127]
                            state =  float(sensor.last_read_value[0]) 
                            pass                     
                        if state == -127:
                            self.start_status(sensor.name, _(u'Temperature probe fault?'), sensor.index)
                        else:  
                            if options.temp_unit == 'C':                                     
                                self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2103' % state, sensor.index)
                            else:
                                self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2109' % state, sensor.index)                                    
                    elif sensor.sens_type == 6 and sensor.multi_type == 1:    
                        try:
                            state =  float(sensor.last_read_value[1])          # multi Temperature DS2 
                        except:
                            sensor.last_read_value = [-127,-127,-127,-127,-127,-127,-127,-127]
                            state =  float(sensor.last_read_value[1]) 
                            pass  
                        if state == -127:
                            self.start_status(sensor.name, _(u'Temperature probe fault?'), sensor.index)
                        else:  
                            if options.temp_unit == 'C':                                     
                                self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2103' % state, sensor.index)
                            else:
                                self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2109' % state, sensor.index)                                                       
                    elif sensor.sens_type == 6 and sensor.multi_type == 2:  
                        try:  
                            state =  float(sensor.last_read_value[2])          # multi Temperature DS3         
                        except:
                            sensor.last_read_value = [-127,-127,-127,-127,-127,-127,-127,-127]
                            state =  float(sensor.last_read_value[2]) 
                            pass     
                        if state == -127:
                            self.start_status(sensor.name, _(u'Temperature probe fault?'), sensor.index)
                        else:  
                            if options.temp_unit == 'C':                                     
                                self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2103' % state, sensor.index)
                            else:
                                self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2109' % state, sensor.index)                                                    
                    elif sensor.sens_type == 6 and sensor.multi_type == 3:   
                        try: 
                            state =  float(sensor.last_read_value[3])          # multi Temperature DS4 
                        except:
                            sensor.last_read_value = [-127,-127,-127,-127,-127,-127,-127,-127]
                            state =  float(sensor.last_read_value[3]) 
                            pass  
                        if state == -127:
                            self.start_status(sensor.name, _(u'Temperature probe fault?'), sensor.index)
                        else:  
                            if options.temp_unit == 'C':                                     
                                self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2103' % state, sensor.index)
                            else:
                                self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2109' % state, sensor.index)                                                       
                    elif sensor.sens_type == 6 and sensor.multi_type == 6:   
                        try:                       
                            state =  float(sensor.last_read_value[6])          # multi Moisture                                                          
                        except:
                            sensor.last_read_value = [-127,-127,-127,-127,-127,-127,-127,-127]
                            state =  float(sensor.last_read_value[6]) 
                            pass  
                        if state == -127:
                            self.start_status(sensor.name, _(u'Moisture probe fault?'), sensor.index)
                        else:  
                            self.start_status(sensor.name, _(u'Moisture {}%').format(state), sensor.index)                                                     

                    if state != sensor.prev_read_value:
                       sensor.prev_read_value = state
                       changed_state = True

                    major_change = False
                    status_update = False   

                    if state > float(sensor.trigger_high_threshold) and changed_state:
                        (major_change, status_update) = self._check_high_trigger(sensor)
                        sensor.last_high_report = now()
                        action = _(u'High Trigger') if major_change else _(u'High Value')
                        if status_update:
                            self.update_log(sensor, 'lgs', state, action)              # wait for reading to be updated
                        if major_change:
                            self._trigger_programs(sensor, sensor.trigger_high_program)                             

                    elif state < float(sensor.trigger_low_threshold) and changed_state:
                        (major_change, status_update) = self._check_low_trigger(sensor)
                        sensor.last_low_report = now()
                        action = _(u'Low Trigger') if major_change else _(u'Low Value')
                        if status_update:
                            self.update_log(sensor, 'lgs', state, action)              # wait for reading to be updated
                        if major_change:
                            self._trigger_programs(sensor, sensor.trigger_low_program)                              
                    else:
                        if changed_state:
                            (major_change, status_update) = self._check_good_trigger(sensor)
                            sensor.last_good_report = now()
                            action = _(u'Normal Trigger') if major_change else _(u'Normal Value')
                            if status_update:
                                self.update_log(sensor, 'lgs', state, action)          # wait for reading to be updated     

                    if major_change:                       
                        self.update_log(sensor, 'lge', self.status[sensor.index][1])
                        if sensor.send_email:
                            text = _(u'Sensor') + u': {} ({})'.format(sensor.name, self.status[sensor.index][1])
                            subj = _(u'Sensor Change')
                            body = _(u'Sensor Change') + u': {} ({})'.format(sensor.name,  self.status[sensor.index][1])
                            self._try_send_mail(body, text, attachment=None, subject=subj)                                                     

                    if sensor.log_samples:                                             # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', state)                      # lge is event, lgs is samples   

                else:
                    logging.warning(_(u'Sensor: {} not response!').format(sensor.name))
                    self.start_status(sensor.name, _(u'Not response!'), sensor.index)              

            ### Leak Detector, Multi Leak Detector ###
            if sensor.sens_type == 2 or (sensor.sens_type == 6 and sensor.multi_type == 5): 
                if sensor.response:                                           # sensor is enabled and response is OK  
                    state = -1.0
                    if   sensor.sens_type == 2:
                        try:
                            state =  float(sensor.last_read_value)            # type is Leak Detector 
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _(u'Leak {}l/s').format(state), sensor.index) 
                        except:
                            sensor.last_read_value = -127.0
                            state =  float(sensor.last_read_value) 
                            if sensor.show_in_footer: 
                                self.start_status(sensor.name, _(u'Leak probe fault?'), sensor.index)
                            pass  
                        if sensor.last_read_value != sensor.prev_read_value:    
                            sensor.prev_read_value = sensor.last_read_value
                            changed_state = True                      
                    elif sensor.sens_type == 6 and sensor.multi_type == 5:
                        try:      
                            state =  float(sensor.last_read_value[5])           # multi Leak Detector
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _(u'Leak {}l/s').format(state), sensor.index)                            
                        except:
                            sensor.last_read_value = [-127.0,-127.0,-127.0,-127.0,-127.0,-127.0,-127.0,-127.0]
                            state =  float(sensor.last_read_value[5]) 
                            if sensor.show_in_footer: 
                                self.start_status(sensor.name, _(u'Leak probe fault?'), sensor.index)                            
                            pass                              
                        if sensor.last_read_value[5] != sensor.prev_read_value:    
                            sensor.prev_read_value = sensor.last_read_value[5]
                            changed_state = True

# todo reaction Leak Detector(run progams and send email and log lge, add to status)

                    if sensor.log_samples:                                                               # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', state)                                        # lge is event, lgs is samples 
                else:
                    logging.warning(_(u'Sensor: {} not response!').format(sensor.name))
                    if sensor.show_in_footer:
                        self.start_status(sensor.name, _(u'Not response!'), sensor.index)                                                                                                              
                           

    def run(self):
        self._sleep(3)
        while True:
            try:
                self.check_sensors()
                self._sleep(1)
                #print(self.read_status())

            except Exception:
                logging.warning(_(u'Sensors timer loop error: {}').format(traceback.format_exc()))
                self._sleep(5)

        
sensors_timer = _Sensors_Timer()

