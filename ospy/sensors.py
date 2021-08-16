# -*- coding: utf-8 -*-
__author__ = u'Martin Pihrt'

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
from ospy.options import options, rain_blocks
from ospy.helpers import now, password_hash, datetime_string, mkdir_p
from ospy.log import log, logEM
from ospy.programs import programs
from ospy.stations import stations
from ospy.scheduler import predicted_schedule, combined_schedule

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
        self.multi_type = 0             # selector multi type 0-9: 'Temperature DS1, DS2, DS3, DS4', 'Dry Contact', 'Leak Detector', 'Moisture', 'Motion', 'Ultrasonic', 'Soil moisture'
        self.notes = ""                 # notes for sensor
        self.log_samples = 0            # log samples
        self.last_log_samples = now()   # last log samples millis
        self.log_event = 0              # log event
        self.send_email  = 0            # send e-mail  
        self.sample_rate = 60           # sample rate 
        self.last_read_value = [""]*9   # last read value (actual)
        self.prev_read_value = -127     # prev read value
        self.sensitivity = 0            # sensitivity
        self.stabilization_time = 5     # stabilization time
        self.liter_per_pulses = 0.5     # leak detector (xx liter/one pulses from detector)
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
        self.last_response_datetime = ""# last response (datetime string)
        self.last_low_report = now()    # now in moisture, temperature
        self.last_good_report = now()   # now in moisture, temperature
        self.last_high_report = 0       # now in moisture, temperature
        self.show_in_footer = 1         # show sensor data in footer on home page
        self.cpu_core = 0               # 0 = ESP32, 1 = ESP8266, 2 = todo
        self.used_stations_one = ["-1"] # Selected stations for the scheduler will stop in dry open contact
        self.used_stations_two = ["-1"] # Selected stations for the scheduler will stop in dry close contact
        # used in ultrasonic sensor
        self.distance_top = 10          # The distance from the sensor to the maximum water level in the tank in cm
        self.distance_bottom = 95       # The distance from the sensor to the minimum water level in the tank in cm
        self.water_minimum = 10         # The water level from the bottom to the minimum water level in the tank
        self.diameter = 100             # Cylinder diameter for volume calculation in cm
        self.check_liters = 0           # Display as liters or m3
        self.use_stop = 0               # Stop stations if minimum water level
        self.use_water_stop = 0         # If the level sensor fails, the above selected stations in the scheduler will stop
        self.enable_reg = 0             # If checked regulation is enabled
        self.used_stations = ["-1"]     # Selected stations for the scheduler will stop in ultrasonic sensor
        self.reg_max = 100              # If the measured water level exceeds this set value, the output is activated
        self.reg_mm = 60                # Maximum run time in activate min
        self.reg_ss = 0                 # Maximum run time in activate sec
        self.reg_min = 90               # If the measured water level falls below this set value, the output is deactivated
        self.reg_output = 0             # Select Output for regulation
        self.delay_duration = 0         # rain delay if water is not in tank (water minimum)
        self.aux_mini = 1               # Auxiliary value true and false for triggering events only when changed (water minimum)
        self.aux_reg_u = 1              # Auxiliary value true and false for triggering events only when changed (regulation >)
        self.aux_reg_d = 1              # Auxiliary value true and false for triggering events only when changed (regulation <)
        self.aux_reg_p = 1              # Auxiliary value true and false for triggering events only when changed (probe fault)
        # used in soil moisture sensor
        self.soil_last_read_value = [""]*16   # last soil read value (actual)
        self.soil_prev_read_value = [-127]*16 # prev soil read value
        self.soil_calibration_min = [0.00]*16 # calibration for soil probe (0 %)
        self.soil_calibration_max = [3.00]*16 # calibration for soil probe (100 %)
        self.soil_program = ["-1"]*16         # program for soil moisture
 
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
        self.last_msg = u''
        self.err_msg = u''
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

    def update_flow_records(name, flow, stations):
        """Add flow to the list of entries if the data set is not already full.  Return the mean"""

        path = os.path.join('.', 'ospy', 'data', 'sensors', name, 'fm', stations)
        directory = os.path.dirname(path)
        mkdir_p(directory)
        a = array('L')
        try:
            file_entries = os.path.getsize(path)>>2
            with open(path, 'r') as f:
                a.fromfile(f, file_entries)
        except (OSError, IOError) as e:
            if e.errno == errno.ENOENT:
                file_entries = 0
            else:
                raise
        except Exception, e:
            raise

        if file_entries < 50:
            a.append(flow)
            with open(path, 'wb') as f:
                a.tofile(f)

        return float(sum(a))/len(a)
            
    def update_log(self, sensor, lg, msg, action='', msg_calculation=''):
        """ Update samples and events in logs """
        try:
            kind = 'slog' if lg == 'lgs' else 'elog'   
            nowg = time.gmtime(now())

            logline = {}
            logline["date"] = time.strftime('%Y-%m-%d', nowg)
            logline["time"] = time.strftime('%H:%M:%S', nowg)
            if kind == 'slog':   # sensor samples
                if type(msg) == list:        # example soil sensor is list with 16 values
                    for i in range(0, len(msg)):
                        logline["list_{}".format(i)] = u"{}".format(msg[i])
                        if msg_calculation:
                            logline["calcul_{}".format(i)] = u"{}".format(msg_calculation[i])
                    logline["value"] = u"{}".format(msg)
                else:
                    if type(msg) == float:
                        msg = u"{0:.1f}".format(msg)
                    logline["value"] = u"{}".format(msg)

                try: # for graph
                    timestamp = int(time.time())
                    glog_dir = os.path.join('.', 'ospy', 'data', 'sensors', str(sensor.index), 'logs', 'graph')
                    graph_data = self._read_log(glog_dir + '/' + 'graph.json')
                    gdata = {}
                    if type(msg) == list:
                        #for i in range(0, len(msg)):
                        #   gdata = {"total": u"{}".format(msg[i])}
                        #   graph_data[i]["balances"].update({timestamp: gdata})
                        gdata = {"total": u"{}".format(msg[0])}
                        graph_data[0]["balances"].update({timestamp: gdata})
                    else:
                        gdata = {"total": u"{}".format(msg)}
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
                    logging.debug(traceback.format_exc())
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

    def get_percent(self, level, dbot, dtop):
        """ Return level 0-100% """
        try:
            if level >= 0:
                perc = float(level)/float((int(dbot)-int(dtop)))
                perc = float(perc)*100.0 
                if perc > 100.0:
                    perc = 100.0
                if perc < 0.0:
                    perc = -1.0
                return int(perc)
            else:
                return -1
        except:
            logging.debug(traceback.format_exc())
            return -1

    def get_volume(self, level, diameter, inltr=False):
        """ Return volume calculation from cylinder diameter and water column height in m3 """
        try:
            import math
            r = float(diameter)/2.0
            area = math.pi*r*r               # calculate area of circle
            volume = area*level              # volume in cm3
            if inltr:                        # display in liters
                volume = volume*0.001        # convert from cm3 to liter (1 cm3 = 0.001 liter)
            else:
                volume = volume/1000000.0    # convert from cm3 to m3
            volume = round(volume, 2)        # round only two decimals
            return volume
        except:
            logging.debug(traceback.format_exc())
            return -1

    def maping(self, x, in_min, in_max, out_min, out_max):
        """ Return value from map. example (x=1023,0,1023,0,100) -> x=1023 return 100 """
        return ((x - in_min) * (out_max - out_min)) / ((in_max - in_min) + out_min)

    def get_tank_cm(self, level, dbot, dtop):
        """ Return tank level in cm from bottom """
        try:
            if level < 0:
                return -1
            tank_cm = self.maping(level, int(dbot), int(dtop), 0, (int(dbot)-int(dtop)))
            if tank_cm >= 0:
                return tank_cm
            else:
                return -1
        except:
            return -1

    def set_stations_in_scheduler_off(self, sensor):
        """Stoping selected station in scheduler."""
        try:
            current_time  = datetime.datetime.now()
            check_start = current_time - datetime.timedelta(days=1)
            check_end = current_time + datetime.timedelta(days=1)

            # In manual mode we cannot predict, we only know what is currently running and the history
            if options.manual_mode:
                active = log.finished_runs() + log.active_runs()
            else:
                active = combined_schedule(check_start, check_end)

            ending = False

            # active stations
            for entry in active:
                for used_stations in sensor.used_stations:            # selected stations for stoping
                    if str(entry['station']) == str(used_stations):   # is this station in selected stations? 
                        log.finish_run(entry)                         # save end in log 
                        stations.deactivate(entry['station'])         # stations to OFF
                        ending = True   

            if ending:
                logging.info(_(u'Stoping stations in scheduler'))
        except:
            logging.debug(traceback.format_exc())
            pass

    def set_stations_one_in_scheduler_off(self, sensor):
        """Stoping selected station in scheduler."""
        try:
            current_time  = datetime.datetime.now()
            check_start = current_time - datetime.timedelta(days=1)
            check_end = current_time + datetime.timedelta(days=1)

            # In manual mode we cannot predict, we only know what is currently running and the history
            if options.manual_mode:
                active = log.finished_runs() + log.active_runs()
            else:
                active = combined_schedule(check_start, check_end)

            ending = False

            # active stations
            for entry in active:
                for used_stations in sensor.used_stations_one:        # selected stations for stoping
                    if str(entry['station']) == str(used_stations):   # is this station in selected stations? 
                        log.finish_run(entry)                         # save end in log 
                        stations.deactivate(entry['station'])         # stations to OFF
                        ending = True   

            if ending:
                logging.info(_(u'Stoping stations in scheduler'))
        except:
            logging.debug(traceback.format_exc())
            pass            

    def set_stations_two_in_scheduler_off(self, sensor):
        """Stoping selected station in scheduler."""
        try:
            current_time  = datetime.datetime.now()
            check_start = current_time - datetime.timedelta(days=1)
            check_end = current_time + datetime.timedelta(days=1)

            # In manual mode we cannot predict, we only know what is currently running and the history
            if options.manual_mode:
                active = log.finished_runs() + log.active_runs()
            else:
                active = combined_schedule(check_start, check_end)

            ending = False

            # active stations
            for entry in active:
                for used_stations in sensor.used_stations_two:        # selected stations for stoping
                    if str(entry['station']) == str(used_stations):   # is this station in selected stations? 
                        log.finish_run(entry)                         # save end in log 
                        stations.deactivate(entry['station'])         # stations to OFF
                        ending = True   

            if ending:
                logging.info(_(u'Stoping stations in scheduler'))
        except:
            logging.debug(traceback.format_exc())
            pass            

    def check_sensors(self):
        ###  HELP for sensor type
        # last_read_value[xx] and prev_read_value[xx] array
        # 0 ds1
        # 1 ds2
        # 2 ds3
        # 3 ds4
        # 4 dry contact
        # 5 leak detector
        # 6 moisture
        # 7 motion
        # 8 sonic
        # 9 soil moisture 
        # sens_type: 'None', 'Dry Contact', 'Leak Detector', 'Moisture', 'Motion', 'Temperature', 'Multi'
        # multi_type: 'Temperature DS1, DS2, DS3, DS4', 'Dry Contact', 'Leak Detector', 'Moisture', 'Motion', 'Ultrasonic', 'Soil moisture'
        for sensor in sensors.get():
            time_dif = int(now() - sensor.last_response)                      # last input from sensor
            if time_dif >= 120:                                               # timeout 120 seconds
                if sensor.response != 0:
                    sensor.response = 0                                       # reseting status green circle to red (on sensors page)
                    # reseting all saved values
                    if sensor.sens_type == 1:                                 # Dry Contact
                        sensor.last_read_value[4] = -127
                    if sensor.sens_type == 2:                                 # Leak Detector
                        sensor.last_read_value[5] = -127
                    if sensor.sens_type == 3:                                 # Moisture
                        sensor.last_read_value[6] = -127
                    if sensor.sens_type == 4:                                 # Motion
                        sensor.last_read_value[7] = -127
                    if sensor.sens_type == 5:                                 # Temperature
                        sensor.last_read_value[0] = -127
                    if sensor.sens_type == 6:
                        if sensor.multi_type == 0:                            # Multi Temperature 1
                            sensor.last_read_value[0] = -127
                        if sensor.multi_type == 1:                            # Multi Temperature 2
                            sensor.last_read_value[1] = -127
                        if sensor.multi_type == 2:                            # Multi Temperature 3
                            sensor.last_read_value[2] = -127
                        if sensor.multi_type == 3:                            # Multi Temperature 4
                            sensor.last_read_value[3] = -127
                        if sensor.multi_type == 4:                            # Multi Dry Contact
                            sensor.last_read_value[4] = -127
                        if sensor.multi_type == 5:                            # Multi Leak Detector
                            sensor.last_read_value[5] = -127
                        if sensor.multi_type == 6:                            # Multi Moisture
                            sensor.last_read_value[6] = -127
                        if sensor.multi_type == 7:                            # Multi Motion
                            sensor.last_read_value[7] = -127
                        if sensor.multi_type == 8:                            # Multi Ultrasonic
                            sensor.last_read_value[8] = -127
                        if sensor.multi_type == 9:                            # Multi Soil moisture probe 1 - probe 16
                            sensor.soil_last_read_value = [-127]*16                                                                                                                                                                        

            if sensor.sens_type == 0:                                         # not selected
                return

            if sensor.enabled == 0:                                           # not enabled
                if sensor.show_in_footer:
                    self.start_status(sensor.name, _(u'Out of order'), sensor.index)
                return    

            changed_state = False

            ### Dry Contact, Motion, Multi Dry Contact, Multi Motion ###
            if sensor.sens_type == 1 or sensor.sens_type == 4 or (sensor.sens_type == 6 and sensor.multi_type == 4) or (sensor.sens_type == 6 and sensor.multi_type == 7):
                if sensor.response:                                           # sensor is enabled and response is OK  
                    state = -127
                    if sensor.sens_type == 1:  # type is Dry Contact
                        try:
                            state = sensor.last_read_value[4]
                            if state == 1:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Closed Contact'), sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Open Contact'), sensor.index)
                            if state == -127:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                        except:
                            sensor.last_read_value[4] = -127
                            pass   
                        if sensor.last_read_value[4] != sensor.prev_read_value:
                            sensor.prev_read_value = sensor.last_read_value[4]
                            changed_state = True
                    elif sensor.sens_type == 4:  # type is Motion
                        try:
                            state = sensor.last_read_value[7]
                            if state == 1:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Motion Detected'), sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'No Motion'), sensor.index)
                            if state == -127:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                        except:
                            sensor.last_read_value[7] = -127
                            pass
                        if sensor.last_read_value[7] != sensor.prev_read_value:
                            sensor.prev_read_value = sensor.last_read_value[7]
                            changed_state = True
                    elif sensor.sens_type == 6 and sensor.multi_type == 4:    # multi Dry Contact
                        try:
                            state = sensor.last_read_value[4]
                            if state == 1:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Closed Contact'), sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Open Contact'), sensor.index)
                            if state == -127:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                        except:
                            sensor.last_read_value[4] = -127
                            pass
                        if sensor.last_read_value[4] != sensor.prev_read_value:
                            sensor.prev_read_value = sensor.last_read_value[4]
                            changed_state = True
                    elif sensor.sens_type == 6 and sensor.multi_type == 7:
                        try:  
                            state = sensor.last_read_value[7]                 # multi Motion 
                            if state == 1:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Motion Detected'), sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'No Motion'), sensor.index)
                            if state == -127:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Probe Error'), sensor.index)                                    
                        except:
                            sensor.last_read_value[7] = -127
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
                            self.set_stations_two_in_scheduler_off(sensor)
 
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
                            self.set_stations_one_in_scheduler_off(sensor) 

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

                    self.err_msg = _(u'Sensor: {} response!').format(sensor.name)

                else:
                    self.err_msg = _(u'Sensor: {} not response!').format(sensor.name)
                    if self.last_msg != self.err_msg:
                        self.last_msg = self.err_msg
                        logging.warning(self.err_msg)
                    if sensor.show_in_footer:
                        self.start_status(sensor.name, _(u'Not response!'), sensor.index)

            ### Moisture, Temperature, Multi Moisture, Multi Temperature ###
            if sensor.sens_type == 3 or sensor.sens_type == 5 or (sensor.sens_type == 6 and sensor.multi_type == 0) or \
                (sensor.sens_type == 6 and sensor.multi_type == 1) or (sensor.sens_type == 6 and sensor.multi_type == 2) or \
                (sensor.sens_type == 6 and sensor.multi_type == 3) or (sensor.sens_type == 6 and sensor.multi_type == 6):
                if sensor.response:                                             # sensor is enabled and response is OK  
                    state = -127
                    if sensor.sens_type == 3:                                   # type is Moisture
                        try:
                            state = sensor.last_read_value[6]
                        except:
                            sensor.last_read_value[6] = -127
                            pass
                        if sensor.show_in_footer:
                            if state == -127:
                                self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                            else:
                                self.start_status(sensor.name, _(u'Moisture {}%').format(state), sensor.index)
                    elif sensor.sens_type == 5:                                 # type is Temperature
                        try:
                            state = sensor.last_read_value[0]
                        except:
                            sensor.last_read_value[0] = -127
                            pass
                        if sensor.show_in_footer:
                            if state == -127:
                                self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                            else:
                                if options.temp_unit == 'C':
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2103' % state, sensor.index)
                                else:
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2109' % state, sensor.index)
                    elif sensor.sens_type == 6 and sensor.multi_type == 0:
                        try:
                            state = sensor.last_read_value[0]                   # multi Temperature DS1  
                        except:
                            sensor.last_read_value[0] = -127
                            pass
                        if state == -127:
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                        else:
                            if options.temp_unit == 'C':
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2103' % state, sensor.index)
                            else:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2109' % state, sensor.index)
                    elif sensor.sens_type == 6 and sensor.multi_type == 1:
                        try:
                            state = sensor.last_read_value[1]                   # multi Temperature DS2 
                        except:
                            sensor.last_read_value[1] = -127 
                            pass
                        if state == -127:
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                        else:
                            if options.temp_unit == 'C':
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2103' % state, sensor.index)
                            else:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2109' % state, sensor.index)
                    elif sensor.sens_type == 6 and sensor.multi_type == 2:
                        try:
                            state = sensor.last_read_value[2]                   # multi Temperature DS3
                        except:
                            sensor.last_read_value[2] = -127
                            pass
                        if state == -127:
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                        else:
                            if options.temp_unit == 'C':
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2103' % state, sensor.index)
                            else:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2109' % state, sensor.index)
                    elif sensor.sens_type == 6 and sensor.multi_type == 3:
                        try:
                            state = sensor.last_read_value[3]                   # multi Temperature DS4 
                        except:
                            sensor.last_read_value[3] = -127
                            pass
                        if state == -127:
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                        else:
                            if options.temp_unit == 'C':
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2103' % state, sensor.index)
                            else:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _(u'Temperature') + u' %.1f \u2109' % state, sensor.index)
                    elif sensor.sens_type == 6 and sensor.multi_type == 6:   
                        try:
                            state = sensor.last_read_value[6]                   # multi Moisture
                        except:
                            sensor.last_read_value[6] = -127
                            pass
                        if state == -127:
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                        else:
                            if sensor.show_in_footer:
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
                            if sensor.log_samples:
                                self.update_log(sensor, 'lgs', state, action)          # wait for reading to be updated
                        if major_change:
                            self._trigger_programs(sensor, sensor.trigger_high_program)

                    elif state < float(sensor.trigger_low_threshold) and changed_state:
                        (major_change, status_update) = self._check_low_trigger(sensor)
                        sensor.last_low_report = now()
                        action = _(u'Low Trigger') if major_change else _(u'Low Value')
                        if status_update:
                            if sensor.log_samples:
                                self.update_log(sensor, 'lgs', state, action)          # wait for reading to be updated
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
                        if sensor.send_email:
                            text = _(u'Sensor') + u': {} ({})'.format(sensor.name, self.status[sensor.index][1])
                            subj = _(u'Sensor Change')
                            body = _(u'Sensor Change') + u': {} ({})'.format(sensor.name,  self.status[sensor.index][1])
                            self._try_send_mail(body, text, attachment=None, subject=subj)

                    if sensor.log_samples:                                             # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', state)                      # lge is event, lgs is samples   

                    self.err_msg = _(u'Sensor: {} response!').format(sensor.name)

                else:
                    self.err_msg = _(u'Sensor: {} not response!').format(sensor.name)
                    if self.last_msg != self.err_msg:
                        self.last_msg = self.err_msg
                        logging.warning(self.err_msg)
                    if sensor.show_in_footer:
                        self.start_status(sensor.name, _(u'Not response!'), sensor.index)

            ### Leak Detector, Multi Leak Detector ###
            if sensor.sens_type == 2 or (sensor.sens_type == 6 and sensor.multi_type == 5): 
                if sensor.response:                                           # sensor is enabled and response is OK  
                    state = -127
                    liters_per_sec = -1
                    if sensor.sens_type == 2:
                        try:
                            state = sensor.last_read_value[5]                 # type is Leak Detector 
                            liters_per_sec = float(sensor.liter_per_pulses)*state
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _(u'Leak {}l/s').format(liters_per_sec), sensor.index) 
                        except:
                            sensor.last_read_value[5] = -127.0
                            if sensor.show_in_footer: 
                                self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                            pass
                        if sensor.last_read_value[5] != sensor.prev_read_value[5]:
                            sensor.prev_read_value[5] = sensor.last_read_value[5]
                            changed_state = True
                    elif sensor.sens_type == 6 and sensor.multi_type == 5:
                        try:
                            state = sensor.last_read_value[5]                # multi Leak Detector
                            liters_per_sec = float(sensor.liter_per_pulses)*state
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _(u'Leak {}l/s').format(liters_per_sec), sensor.index)
                        except:
                            sensor.last_read_value[5] = -127
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                            pass
                        if sensor.last_read_value[5] != sensor.prev_read_value:    
                            sensor.prev_read_value = sensor.last_read_value[5]
                            changed_state = True

# todo reaction Leak Detector(run progams and send email and log lge, add to status errors)

                    if sensor.log_samples:                                                               # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', liters_per_sec)                               # lge is event, lgs is samples 

                    self.err_msg = _(u'Sensor: {} response!').format(sensor.name)

                else:
                    self.err_msg = _(u'Sensor: {} not response!').format(sensor.name)
                    if self.last_msg != self.err_msg:
                        self.last_msg = self.err_msg
                        logging.warning(self.err_msg)
                    if sensor.show_in_footer:
                        self.start_status(sensor.name, _(u'Not response!'), sensor.index)

            ### Multi Sonic ###
            if sensor.sens_type == 6 and sensor.multi_type == 8:
                if sensor.response:                                          # sensor is enabled and response is OK  
                    state = -127
                    try:
                        state = sensor.last_read_value[8]                    # multi Sonic
                    except:
                        pass
                        sensor.last_read_value[8] = -127
                        if sensor.show_in_footer:
                            self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                        if sensor.use_water_stop:                            # If the level sensor fails, the above selected stations in the scheduler will stop
                            self.set_stations_in_scheduler_off(sensor)

                    if sensor.last_read_value[8] != sensor.prev_read_value:
                        sensor.prev_read_value = sensor.last_read_value[8]
                        changed_state = True

                    level_in_tank = 0
                    volume_in_tank = 0
                    percent_in_tank = 0

                    if state > 0:
                        if changed_state:
                            sensor.aux_reg_p = 1

                        level_in_tank = self.get_tank_cm(state, sensor.distance_bottom, sensor.distance_top)            # tank level in cm from ping
                        percent_in_tank = self.get_percent(level_in_tank, sensor.distance_bottom, sensor.distance_top)  # percent in tank from tank level

                        if sensor.check_liters:
                            # in liters 
                            volume_in_tank = self.get_volume(level_in_tank, sensor.diameter, True)                      # volume in tank from tank level in liters
                            tempText = str(volume_in_tank) + ' ' + _(u'liters') + ', ' + str(level_in_tank) + ' ' + _(u'cm') + ' (' + str(percent_in_tank) + ' ' + (u'%)')
                        else:
                            # in m3
                            volume_in_tank = self.get_volume(level_in_tank, sensor.diameter, False)                     # volume in tank from tank level in m3
                            tempText = str(volume_in_tank) + ' ' + _(u'm3') + ', ' + str(level_in_tank) + ' ' + _(u'cm') + ' (' + str(percent_in_tank) + ' ' + (u'%)')

                        if sensor.show_in_footer:
                            self.start_status(sensor.name,  u'{}'.format(tempText), sensor.index)
                    else:
                        if sensor.show_in_footer:
                            self.start_status(sensor.name, _(u'Probe Error'), sensor.index)
                        if sensor.use_water_stop: # If the level sensor fails, the above selected stations in the scheduler will stop
                            if int(sensor.aux_reg_p)==1:
                                sensor.aux_reg_p = 0
                                self.set_stations_in_scheduler_off(sensor)
                                if sensor.log_event:
                                    self.update_log(sensor, 'lge', _(u'Probe Error'))
                                if sensor.send_email: # Send Email?
                                    text = _(u'Sensor') + u': {}'.format(sensor.name)
                                    subj = _(u'Sensor {}').format(sensor.name)
                                    body = _(u'Sensor Notification') + u': ' + _(u'Probe Error')
                                    self._try_send_mail(body, text, attachment=None, subject=subj)

                    ### regulation water in tank if enable regulation ###
                    if level_in_tank > 0 and sensor.enable_reg:                           # if enable regulation "maximum water level"
                            reg_station = stations.get(int(sensor.reg_output))
                            ### level > regulation maximum ###
                            if level_in_tank > int(sensor.reg_max):                       # if actual level in tank > set maximum water level
                                if int(sensor.aux_reg_u)==1:
                                    sensor.aux_reg_u = 0
                                    sensor.aux_reg_d = 1
                                    regulation_text = _(u'Regulation set ON.') + ' ' + ' (' + _(u'Output') + ' ' +  str(reg_station.index+1) + ').'
                                   
                                    start = datetime.datetime.now()
                                    sid = reg_station.index
                                    end = datetime.datetime.now() + datetime.timedelta(seconds=int(sensor.reg_ss), minutes=int(sensor.reg_mm))
                                    new_schedule = {
                                        'active': True,
                                        'program': -1,
                                        'station': sid,
                                        'program_name': u'{}'.format(sensor.name),
                                        'fixed': True,
                                        'cut_off': 0,
                                        'manual': True,
                                        'blocked': False,
                                        'start': start,
                                        'original_start': start,
                                        'end': end,
                                        'uid': '%s-%s-%d' % (str(start), "Manual", sid),
                                        'usage': stations.get(sid).usage
                                    }

                                    log.start_run(new_schedule)
                                    stations.activate(new_schedule['station'])
                                    if sensor.log_event:
                                        self.update_log(sensor, 'lge', u'{}'.format(regulation_text))
                
                            ### level < regulation minimum ### 
                            if level_in_tank < int(sensor.reg_min):
                                if int(sensor.aux_reg_d)==1:
                                    sensor.aux_reg_u = 1
                                    sensor.aux_reg_d = 0
                                    regulation_text = _(u'Regulation set OFF.') + ' ' + ' (' + _(u'Output') + ' ' +  str(reg_station.index+1) + ').'
                                    sid = reg_station.index
                                    stations.deactivate(sid)
                                    active = log.active_runs()
                                    for interval in active:
                                        if interval['station'] == sid:
                                            log.finish_run(interval)
                                    if sensor.log_event:
                                        self.update_log(sensor, 'lge', u'{}'.format(regulation_text))

                    ### level in tank has minimum +5cm refresh ###
                    if level_in_tank > int(sensor.water_minimum)+5 and int(sensor.aux_mini)==0:
                        sensor.aux_mini = 1
                        action = _(u'Normal Trigger') 
                        if sensor.log_samples:
                            self.update_log(sensor, 'lgs', level_in_tank, action)
                        delaytime = int(sensor.delay_duration) # if the level in the tank rises above the minimum +5 cm, the delay is deactivated
                        regulation_text = _(u'Water in Tank') + ' > ' + str(int(sensor.water_minimum)+5) + _(u'cm')
                        if sensor.log_event:
                            self.update_log(sensor, 'lge', u'{}'.format(regulation_text))
                        rd_text = None
                        if delaytime > 0:
                            if sensor.name in rain_blocks:
                                del rain_blocks[sensor.name]
                                rd_text = _(u'Removing Rain delay')
                                if sensor.log_event:
                                    self.update_log(sensor, 'lge', u'{}'.format(rd_text))
                        if sensor.send_email: # Send Email?
                            text = _(u'Sensor') + u': {} ({})'.format(sensor.name, regulation_text)
                            subj = _(u'Sensor {}').format(sensor.name)
                            body = _(u'Sensor has water') + u': {}'.format(regulation_text)
                            if rd_text is not None:
                                body += '<br>' + rd_text
                            self._try_send_mail(body, text, attachment=None, subject=subj)

                    ### level in tank has minimum ### 
                    if level_in_tank <= int(sensor.water_minimum) and int(sensor.aux_mini)==1 and not options.manual_mode and level_in_tank > 1: # level value is lower
                        sensor.aux_mini = 0
                        action = _(u'Low Trigger') 
                        if sensor.log_samples:
                            self.update_log(sensor, 'lgs', level_in_tank, action) 
                        if sensor.use_stop:   # Stop stations if minimum water level?
                            self.set_stations_in_scheduler_off(sensor)
                            regulation_text = _(u'Water in Tank') + ' < ' + str(sensor.water_minimum) + ' ' + _(u'cm') + _(u'!')
                            if sensor.log_event:
                                self.update_log(sensor, 'lge', u'{}'.format(regulation_text))
                            delaytime = int(sensor.delay_duration)
                            rd_text = None
                            if delaytime > 0: # if there is no water in the tank and the stations stop, then we set the rain delay for this time for blocking
                                rain_blocks[sensor.name] = datetime.datetime.now() + datetime.timedelta(hours=float(delaytime))
                                rd_text = _(u'Rain delay') + ' ' + str(delaytime) + ' ' + _(u'hours.')
                                if sensor.log_event:
                                    self.update_log(sensor, 'lge', u'{}'.format(rd_text))
                                if sensor.send_email: # Send Email?
                                    text = _(u'Sensor') + u': {} ({})'.format(sensor.name, regulation_text)
                                    subj = _(u'Sensor {}').format(sensor.name)
                                    body = _(u'Sensor has water minimum') + u': {}'.format(regulation_text)
                                    if rd_text is not None:
                                        body += '<br>' + rd_text
                                    self._try_send_mail(body, text, attachment=None, subject=subj)
                            self.set_stations_in_scheduler_off(sensor)

                    ### log samples ###
                    if sensor.log_samples:                                             # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', level_in_tank)              # lge is event, lgs is samples

                    self.err_msg = _(u'Sensor: {} response!').format(sensor.name)

                else:
                    self.err_msg = _(u'Sensor: {} not response!').format(sensor.name)
                    if self.last_msg != self.err_msg:
                        self.last_msg = self.err_msg
                        logging.warning(self.err_msg)
                    if sensor.show_in_footer:
                        self.start_status(sensor.name, _(u'Not response!'), sensor.index)

            ### Multi Soil ###
            if sensor.sens_type == 6 and sensor.multi_type == 9:
                if sensor.response:                                                    # sensor is enabled and response is OK
                    state = [-127]*16
                    calculate_soil = [0.0]*16
                    try:
                        for i in range(0, 16):
                            state[i] = sensor.soil_last_read_value[i]                  # multi Soil probe 1 - 16
                            val = float(state[i])
                            if val < 0:
                                calculate_soil[i] = 0.0
                            else:
                                if val > sensor.soil_calibration_max:
                                    val = sensor.soil_calibration_max
                                if val < sensor.soil_calibration_min:
                                    val = sensor.soil_calibration_min
                                calculate_soil[i] = self.maping(val, sensor.soil_calibration_min, sensor.soil_calibration_max, 0.0, 100.0) # val, min in, max in, to out min, to out max
                        # TODO
                        #ms_text = _(u'...')
                        #if sensor.log_event:
                        #        self.update_log(sensor, 'lge', u'{}'.format(ms_text))
                        #if sensor.send_email:
                            #em_text = _(u'...')
                            #text = _(u'Sensor') + u': {} ({})'.format(sensor.name, em_text)
                            #subj = _(u'Sensor {}').format(sensor.name)
                            #body = _(u'Sensor ....') + u': {}'.format(em_text)
                            #if em_text is not None:
                                #body += '<br>' + em_text
                            #self._try_send_mail(body, text, attachment=None, subject=subj)

                        if sensor.log_samples:                                         # sensor is enabled and enabled log samples
                            if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                                sensor.last_log_samples = now()
                                self.update_log(sensor, 'lgs', state, msg_calculation = calculate_soil)  # lge is event, lgs is samples

                    except:
                        logging.warning(_(u'Sensor error: {}').format(traceback.format_exc()))
                        pass

                else:
                    self.err_msg = _(u'Sensor: {} not response!').format(sensor.name)
                    if self.last_msg != self.err_msg:
                        self.last_msg = self.err_msg
                        logging.warning(self.err_msg)
                    if sensor.show_in_footer:
                        self.start_status(sensor.name, _(u'Not response!'), sensor.index)        

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