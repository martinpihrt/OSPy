#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Martin Pihrt'

# System imports
from threading import Thread, Timer
import traceback
import traceback
import time
import datetime
import subprocess
import os
import json

# Local imports
from ospy.options import options, rain_blocks, program_level_adjustments
from ospy.helpers import now, datetime_string, mkdir_p
from ospy.log import log, logEM
from ospy.programs import programs
from ospy.stations import stations
from ospy.scheduler import predicted_schedule, combined_schedule

### Sensors ###
class _Sensor(object):
    SAVE_EXCLUDE = ['SAVE_EXCLUDE', 'index', '_sensors']

    def __init__(self, sensors_instance, index):
        self._sensors = sensors_instance
        self.manufacturer = 0           # manufacturer 0=pihrt sensor, 1=shelly
        self.name = ""                  # sensor name
        self.enabled = 0                # sensor enable or disable
        self.sens_type = 0              # selector sensor type: 0-7 'None', 'Dry Contact', 'Leak Detector', 'Moisture', 'Motion', 'Temperature', 'Multi', 'Multi Contact'
        self.com_type = 0               # selector sensor communication type 0-1: 'Wi-Fi/LAN', 'Radio'
        self.multi_type = 0             # selector multi type 0-9: 'Temperature DS1, DS2, DS3, DS4', 'Dry Contact', 'Leak Detector', 'Moisture', 'Motion', 'Ultrasonic', 'Soil moisture'
        self.notes = ""                 # notes for sensor
        self.log_samples = 0            # log samples
        self.last_log_samples = now()   # last log samples millis
        self.log_event = 0              # log event
        self.send_email  = 0            # send e-mail  
        self.sample_rate = 60           # sample rate 
        self.last_read_value = [""]*10  # last read value (actual)
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
        self.last_voltage = ""          # main source voltage
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
        self.soil_last_read_value = [""]*17      # last soil read value (actual)
        self.soil_prev_read_value = [-127]*17    # prev soil read value
        self.soil_calibration_min = [3.00]*17    # calibration for soil probe (0 %)
        self.soil_calibration_max = [0.00]*17    # calibration for soil probe (100 %)
        self.soil_invert_probe_in = [1]*17       # 1= inverted probe type (ex: 100 % = 0V, 0% = 3,3V)
        self.soil_show_in_footer = [1]*17        # 1= show, 0= hide
        self.soil_program = ["-1"]*17            # program for soil moisture
        self.soil_probe_label = [_('Probe')]*17  # label for soil moisture probe
        # for events log and email
        self.last_msg = [0]*10
        self.err_msg = [0]*10
        # custom event naming 
        self.dry_open_msg = _('Open Contact')     # dry contact open
        self.dry_clos_msg = _('Closed Contact')   # dry contact closed
        self.motion_msg = _('Motion Detected')    # motion
        self.no_motion_msg = _('No Motion')       # no motion
        # email plugin type
        self.eplug = 0                            # 0 = e-mail notifications, 1 = e-mail notifications SSL
        # 7 button controller programs
        self.sw0_open_program = ["-1"]            # open program (-1 is default none program)
        self.sw1_open_program = ["-1"]            # open program (-1 is default none program)
        self.sw2_open_program = ["-1"]            # open program (-1 is default none program)
        self.sw3_open_program = ["-1"]            # open program (-1 is default none program)
        self.sw4_open_program = ["-1"]            # open program (-1 is default none program)
        self.sw5_open_program = ["-1"]            # open program (-1 is default none program)
        self.sw6_open_program = ["-1"]            # open program (-1 is default none program)
        self.sw0_closed_program = ["-1"]          # closed program (-1 is default none program)
        self.sw1_closed_program = ["-1"]          # closed program (-1 is default none program)
        self.sw2_closed_program = ["-1"]          # closed program (-1 is default none program)
        self.sw3_closed_program = ["-1"]          # closed program (-1 is default none program)
        self.sw4_closed_program = ["-1"]          # closed program (-1 is default none program)
        self.sw5_closed_program = ["-1"]          # closed program (-1 is default none program)
        self.sw6_closed_program = ["-1"]          # closed program (-1 is default none program)
        # 7 button controller stations
        self.sw0_open_stations = ["-1"]           # open stations (-1 is default none)
        self.sw1_open_stations = ["-1"]           # open stations (-1 is default none)
        self.sw2_open_stations = ["-1"]           # open stations (-1 is default none)
        self.sw3_open_stations = ["-1"]           # open stations (-1 is default none)
        self.sw4_open_stations = ["-1"]           # open stations (-1 is default none)
        self.sw5_open_stations = ["-1"]           # open stations (-1 is default none)
        self.sw6_open_stations = ["-1"]           # open stations (-1 is default none)
        self.sw0_closed_stations = ["-1"]         # closed stations (-1 is default none)
        self.sw1_closed_stations = ["-1"]         # closed stations (-1 is default none)
        self.sw2_closed_stations = ["-1"]         # closed stations (-1 is default none)
        self.sw3_closed_stations = ["-1"]         # closed stations (-1 is default none)
        self.sw4_closed_stations = ["-1"]         # closed stations (-1 is default none)
        self.sw5_closed_stations = ["-1"]         # closed stations (-1 is default none)
        self.sw6_closed_stations = ["-1"]         # closed stations (-1 is default none)
        # Shelly sensors
        self.shelly_id = ""                       # this can be obtained from Shelly. Example: b0b21c1368aa
        self.shelly_hw = ""                       # depending on the type of device, data will be read (e.g. temperature and humidity, output states, etc.)
        self.shelly_hw_nbr = -1                   # depending on the type of device, data will be read as number -1 is unknow nex: 0=Shelly Plus HT, 1=Shelly Plus Plug S, 2=Shelly Pro 2PM, 3=Shelly 1PM Mini, 4=Shelly 2.5, 5=Shelly Pro 4PM, 6=Shelly 1 Mini, 7=Shelly 2PM Addon, 8=Shelly 1PM Addon, 9= Shelly H&T
        self.shelly_gen = ""                      # generation of Shelly devices gen1, gen2+
        self.s_trigger_low_program = ["-1"]       # open program (-1 is default none program)
        self.s_trigger_high_program = ["-1"]      # close Program
        self.s_trigger_low_threshold = "10"       # low threshold
        self.s_trigger_high_threshold = "30"      # high threshold
        options.load(self, index) 

    @property
    def index(self):
        try:
            return self._sensors.get().index(self)
        except ValueError:
            return -1    

    def __setattr__(self, key, value):
        try:
            # Do not perform any additional logic during object initialization.
            if not hasattr(self, "SAVE_EXCLUDE"):
                super().__setattr__(key, value)
                return

            # Set attribute normally
            super().__setattr__(key, value)

            # Save changes if attribute is not in the exception list
            if not key.startswith('_') and key not in self.SAVE_EXCLUDE:
                options.save(self, self.index)
        except ValueError:  # When the index is not available
            log.debug('sensors.py', traceback.format_exc())
        except Exception as e:
            log.error('sensors.py', _('Error setting attribute {}: {}').format(key, e))

class _Sensors(object):
    def __init__(self):
        self._sensors = []
        self._loading = True
        options.load(self)
        self._loading = False

        try:
            log.debug('sensors.py', _('Loading sensors...'))
            i = 0
            while options.available(_Sensor, i):
                self._sensors.append(_Sensor(self, i)) 
                i += 1   
        except:
            log.debug('sensors.py', traceback.format_exc())
            pass                

    def add_sensors(self, sensor=None):
        try:
            if sensor is None:
                sensor = _Sensor(self, len(self._sensors))
            self._sensors.append(sensor)
            options.save(sensor, sensor.index)
            log.debug('sensors.py', _('Adding new sensor: {} with id: {}').format(sensor.name,sensor.index))
        except:
            log.debug('sensors.py', traceback.format_exc())
            pass

    def create_sensors(self):
        """Returns a new sensor, but doesn't add it to the list."""
        try:
            return _Sensor(self, -1-len(self._sensors))
        except:
            log.debug('sensors.py', traceback.format_exc())
            pass       

    def remove_sensors(self, index):
        try:
            if 0 <= index < len(self._sensors):           
                del self._sensors[index]

            for i in range(index, len(self._sensors)):
                options.save(self._sensors[i], i)       # Save sensor using new indices

            options.erase(_Sensor, len(self._sensors))  # Remove info in last index
            log.debug('sensors.py', _('Removing sensor id: {}').format(index))
        except:
            log.debug('sensors.py', traceback.format_exc())
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
            log.debug('sensors.py', traceback.format_exc())
            pass

    def __setattr__(self, key, value):
        super(_Sensors, self).__setattr__(key, value)
        if not key.startswith(u'_') and not self._loading:
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

    def _try_send_mail(self, text, logtext, attachment=None, subject=None, eplug=0):
        try:
            try_mail = None
            if eplug==0: # email_notifications
                from plugins.email_notifications import try_mail
            if eplug==1: # email_notifications SSL
                from plugins.email_notifications_ssl import try_mail
            if try_mail is not None:
                try_mail(text, logtext, attachment, subject)
        except:
            log.debug('sensors.py', _('E-mail not send! The Email Notifications plug-in is not found in OSPy or not correctly setuped.'))
            pass

    def _read_log(self, dir_name):
        try:
            import os
            _abs_dir_name = os.path.abspath(dir_name)
            with open(_abs_dir_name, 'r') as logf:
                return json.load(logf)
        except IOError:
            return []

    def _write_log(self, dir_name, data):
        try:
            import os
            _abs_dir_name = os.path.abspath(dir_name)
            with open(_abs_dir_name, 'w') as outfile:
                json.dump(data, outfile)
        except Exception:
            log.debug('sensors.py', traceback.format_exc())

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
                    log.debug('sensors.py', _('The sensor tries to start the {} (id: {})').format(programs[index].name, p))
                    programs.run_now_program = None                                                                  
                    programs.run_now(index)
                    Timer(0.1, programs.calculate_balances).start()
                    self.update_log(sensor, 'lge', _('Starting {}').format(programs[index].name))    
        except:
            log.debug('sensors.py', traceback.format_exc())
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
        except Exception:
            raise

        if file_entries < 50:
            a.append(flow)
            with open(path, 'wb') as f:
                a.tofile(f)

        return float(sum(a))/len(a)
            
    def update_log(self, sensor, lg, msg, action='', msg_calculation='', battery=None, rssi=None):
        """ Update samples and events in logs """
        try:
            kind = 'slog' if lg == 'lgs' else 'elog'   
            nowg = time.gmtime(now())

            logline = {}
            logline["date"] = time.strftime('%Y-%m-%d', nowg)
            logline["time"] = time.strftime('%H:%M:%S', nowg)
            if kind == 'slog':               # sensor samples
                if type(msg) == list:        # example soil sensor is list with 16 values
                    for i in range(0, len(msg)):
                        logline["list_{}".format(i)] = "{}".format(msg[i])
                        if msg_calculation:
                            logline["calcul_{}".format(i)] = "{}".format(msg_calculation[i])
                    logline["value"] = "{}".format(msg)
                else:
                    if type(msg) == float:
                        msg = "{0:.1f}".format(msg)
                    logline["value"] = "{}".format(msg)

                if battery is not None:      # sensor battery voltage
                    if type(battery) == float:
                        battery = "{0:.1f}".format(float(battery))
                        logline["battery"] = "{}".format(battery)
                    else:
                        logline["battery"] = "{}".format(battery)

                if rssi is not None:         # sensor Wi-Fi percent
                    if type(rssi) == float:
                        rssi = "{0:.1f}".format(rssi)
                        logline["rssi"] = "{}".format(float(rssi))
                    else:
                        logline["rssi"] = "{}".format(rssi)
                
                glog_dir = os.path.join('.', 'ospy', 'data', 'sensors', str(sensor.index), 'logs', 'graph')
                _abs_glog_dir = os.path.abspath(glog_dir)
                
                try: # for graph
                    timestamp = int(time.time())
                    if not os.path.isdir(_abs_glog_dir):
                        mkdir_p(_abs_glog_dir) # ensure dir and file exists after config restore
                        log.debug('sensors.py',_('Dir not exists, creating dir: {}').format(_abs_glog_dir))
                    if not os.path.isfile(_abs_glog_dir + '/' + 'graph.json'):
                        subprocess.call(['touch', _abs_glog_dir + '/' + 'graph.json'])
                        log.debug('sensors.py', _('File not exists, creating file: {}').format('graph.json'))
                    
                    graph_data = self._read_log(_abs_glog_dir + '/' + 'graph.json')
                    gdata = {}
                    if type(msg) == list:
                        msg_len = len(msg)
                        for i in range(0, msg_len):
                            gdata = {"total": "{}".format(msg[i])}
                            graph_data[i]["balances"].update({timestamp: gdata})    # value eg: 16x soil probe
                        if battery is not None and rssi is not None:
                            gdata = {"total": "{}".format(battery)}                 # battery voltage
                            graph_data[msg_len+1]["balances"].update({timestamp: gdata})
                            gdata = {"total": "{}".format(rssi)}                    # WiFi/radio signal
                            graph_data[msg_len+2]["balances"].update({timestamp: gdata})
                    else:
                        gdata = {"total": "{}".format(msg)}                         # value eg: temperature 
                        graph_data[0]["balances"].update({timestamp: gdata})
                        if battery is not None and rssi is not None:
                            gdata = {"total": "{}".format(battery)}                 # battery voltage
                            graph_data[1]["balances"].update({timestamp: gdata})
                            gdata = {"total": "{}".format(rssi)}                    # WiFi/radio signal
                            graph_data[2]["balances"].update({timestamp: gdata})
                    self._write_log(glog_dir + '/' + 'graph.json', graph_data)
                    log.debug('sensors.py', _('Updating sensor graph log to file successfully.'))
                except:
                    if not os.path.isdir(_abs_glog_dir):
                        mkdir_p(_abs_glog_dir) # ensure dir and file exists after config restore
                        log.debug('sensors.py',_('Dir not exists, creating dir: {}').format(_abs_glog_dir))
                    if not os.path.isfile(_abs_glog_dir + '/' + 'graph.json'):
                        subprocess.call(['touch', _abs_glog_dir + '/' + 'graph.json'])
                        log.debug('sensors.py', _('File not exists, creating file: {}').format('graph.json'))
                    if sensor.multi_type == 9: # 16x log from probe
                        graph_def_data = []
                        for i in range(0, 17):
                            graph_def_data.append({"sname": "{}".format(sensor.soil_probe_label[int(i)]), "balances": {}})
                        if sensor.manufacturer == 0:
                            graph_def_data.append({"sname": "{}".format(_('Battery')), "balances": {}})
                        else:
                            graph_def_data.append({"sname": "{}".format(_('Voltage')), "balances": {}})
                        graph_def_data.append({"sname": "{}".format(_('Signal')), "balances": {}})
                    else:                      # only 1x log
                        graph_def_data = []
                        graph_def_data.append({"sname": "{}".format(sensor.name), "balances": {}})
                        if sensor.manufacturer == 0:
                            graph_def_data.append({"sname": "{}".format(_('Battery')), "balances": {}})
                        else:
                            graph_def_data.append({"sname": "{}".format(_('Voltage')), "balances": {}})
                        graph_def_data.append({"sname": "{}".format(_('Signal')), "balances": {}}) 
                    self._write_log(_abs_glog_dir + '/' + 'graph.json', graph_def_data)
                    log.debug('sensors.py', traceback.format_exc())
                    pass

                if action:
                    logline["action"] = '{}'.format(action.encode('utf-8').decode('utf-8'))

            else:                # sensor event log
                logline["event"] = '{}'.format(msg.encode('utf-8').decode('utf-8'))

            log_dir = os.path.join('.', 'ospy', 'data', 'sensors', str(sensor.index), 'logs')
            if not os.path.isdir(log_dir):
                mkdir_p(log_dir) # ensure dir and file exists after config restore
                log.debug('sensors.py', _('Dir not exists, creating dir: {}').format(log_dir))
            
            log_ref = str(log_dir) + '/' + str(kind)
            if not os.path.isfile(log_ref + '.json'):
                subprocess.call(['touch', log_ref + '.json'])
                log.debug('sensors.py', _('File not exists, creating file: {}').format(str(kind) + '.json'))
            
            try:
                _log = self._read_log(log_ref + '.json')
            except:
                _log = []

            _log.insert(0, logline)
            if options.run_sensor_entries > 0:           # 0 = unlimited
               _log = _log[:options.run_sensor_entries]  # limit records from options
            self._write_log(log_ref + '.json', _log)
            log.debug('sensors.py', _('Updating sensor log to file successfully.')) 
        
        except Exception:
            log.debug('sensors.py', traceback.format_exc())

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
            log.debug('sensors.py', traceback.format_exc())
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
            log.debug('sensors.py', traceback.format_exc())
            return -1

    def maping(self, OldValue, OldMin, OldMax, NewMin, NewMax):
        """ Convert a number range to another range """
        OldRange = OldMax - OldMin
        NewRange = NewMax - NewMin
        if OldRange == 0:
            NewValue = NewMin
        else:
            NewRange = NewMax - NewMin
            NewValue = (((OldValue - OldMin) * NewRange) / OldRange) + NewMin
        return NewValue

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

    def _set_stations_in_scheduler_off(self, stations_list):
        """Stoping selected station in scheduler from list."""
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
                for used_stations in stations_list:                   # selected stations for stoping
                    if str(entry['station']) == str(used_stations):   # is this station in selected stations? 
                        log.finish_run(entry)                         # save end in log 
                        stations.deactivate(entry['station'])         # stations to OFF
                        ending = True   

            if ending:
                log.debug('sensors.py', _('Stoping stations in scheduler'))
        except:
            log.debug('sensors.py', traceback.format_exc())
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
        # sens_type: 'None', 'Dry Contact', 'Leak Detector', 'Moisture', 'Motion', 'Temperature', 'Multi', 'Multi Contact'
        # multi_type: 'Temperature DS1, DS2, DS3, DS4', 'Dry Contact', 'Leak Detector', 'Moisture', 'Motion', 'Ultrasonic', 'Soil moisture'
        # manufacturer: 0=Pihrt.com, 1=Shelly.com
        for sensor in sensors.get():
            time_dif = int(now() - sensor.last_response)                      # last input from sensor
            if time_dif >= 120:                                               # timeout 120 seconds
                if sensor.response != 0:
                    sensor.response = 0                                       # reseting status green circle to red (on sensors page)
                    # reseting all saved values
                    if sensor.manufacturer == 0:                              # Pihrt.com manufacturer
                        if sensor.sens_type == 1:                             # Dry Contact
                            sensor.last_read_value[4] = -127
                        if sensor.sens_type == 2:                             # Leak Detector
                            sensor.last_read_value[5] = -127
                        if sensor.sens_type == 3:                             # Moisture
                            sensor.last_read_value[6] = -127
                        if sensor.sens_type == 4:                             # Motion
                            sensor.last_read_value[7] = -127
                        if sensor.sens_type == 5:                             # Temperature
                            sensor.last_read_value[0] = -127
                        if sensor.sens_type == 6:
                            if sensor.multi_type == 0:                        # Multi Temperature 1
                                sensor.last_read_value[0] = -127
                            if sensor.multi_type == 1:                        # Multi Temperature 2
                                sensor.last_read_value[1] = -127
                            if sensor.multi_type == 2:                        # Multi Temperature 3
                                sensor.last_read_value[2] = -127
                            if sensor.multi_type == 3:                        # Multi Temperature 4
                                sensor.last_read_value[3] = -127
                            if sensor.multi_type == 4:                        # Multi Dry Contact
                                sensor.last_read_value[4] = -127
                            if sensor.multi_type == 5:                        # Multi Leak Detector
                                sensor.last_read_value[5] = -127
                            if sensor.multi_type == 6:                        # Multi Moisture
                                sensor.last_read_value[6] = -127
                            if sensor.multi_type == 7:                        # Multi Motion
                                sensor.last_read_value[7] = -127
                            if sensor.multi_type == 8:                        # Multi Ultrasonic
                                sensor.last_read_value[8] = -127
                            if sensor.multi_type == 9:                        # Multi Soil moisture probe 1 - probe 16
                                sensor.soil_last_read_value = [-127]*16

                    if sensor.manufacturer == 1:                              # Shely manufacturer
                        sensor.last_read_value[0] = []                        # Output list
                        sensor.last_read_value[1] = []                        # Power list
                        sensor.last_read_value[2] = []                        # Temperature list
                        sensor.last_read_value[3] = []                        # Humidity list
                        sensor.prev_read_value = -127

            changed_state = False

            ### Dry Contact, Motion, Multi Dry Contact, Multi Motion ###
            if sensor.sens_type == 1 or sensor.sens_type == 4 or (sensor.sens_type == 6 and sensor.multi_type == 4) or (sensor.sens_type == 6 and sensor.multi_type == 7):
                if sensor.response and sensor.enabled and sensor.manufacturer == 0:   # sensor is enabled and response is OK and is pihrt.com sensor HW
                    state = -127
                    if sensor.sens_type == 1:  # type is Dry Contact
                        try:
                            state = sensor.last_read_value[4]
                            if state == 1:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, sensor.dry_clos_msg, sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, sensor.dry_open_msg, sensor.index)
                            if state == -127:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Probe Error'), sensor.index)
                        except:
                            sensor.last_read_value[4] = -127
                            pass   
                        if sensor.last_read_value[4] != sensor.prev_read_value:
                            sensor.prev_read_value = sensor.last_read_value[4]
                            changed_state = True
                        sensor.err_msg[4] = 1
                        if sensor.last_msg[4] != sensor.err_msg[4]:
                            sensor.last_msg[4] = sensor.err_msg[4]
                            log.debug('sensors.py', _('Sensor: {} now response').format(sensor.name))
                            if sensor.send_email:
                                text = _('Now response')
                                subj = _('Sensor {}').format(sensor.name)
                                body = text
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            if sensor.log_event:                                   # event log
                                self.update_log(sensor, 'lge', _('Now response'))
                    if sensor.sens_type == 4:  # type is Motion
                        try:
                            state = sensor.last_read_value[7]
                            if state == 1:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, sensor.motion_msg, sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, sensor.no_motion_msg, sensor.index)
                            if state == -127:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Probe Error'), sensor.index)
                        except:
                            sensor.last_read_value[7] = -127
                            pass
                        if sensor.last_read_value[7] != sensor.prev_read_value:
                            sensor.prev_read_value = sensor.last_read_value[7]
                            changed_state = True
                        sensor.err_msg[7] = 1
                        if sensor.last_msg[7] != sensor.err_msg[7]:
                            sensor.last_msg[7] = sensor.err_msg[7]
                            log.debug('sensors.py', _('Sensor: {} now response').format(sensor.name))
                            if sensor.send_email:
                                text = _('Now response')
                                subj = _('Sensor {}').format(sensor.name)
                                body = text
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            if sensor.log_event:                                   # event log
                                self.update_log(sensor, 'lge', _('Now response'))
                    if sensor.sens_type == 6 and sensor.multi_type == 4:    # multi Dry Contact
                        try:
                            state = sensor.last_read_value[4]
                            if state == 1:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, sensor.dry_clos_msg, sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, sensor.dry_open_msg, sensor.index)
                            if state == -127:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Probe Error'), sensor.index)
                        except:
                            sensor.last_read_value[4] = -127
                            pass
                        if sensor.last_read_value[4] != sensor.prev_read_value:
                            sensor.prev_read_value = sensor.last_read_value[4]
                            changed_state = True
                        sensor.err_msg[4] = 1
                        if sensor.last_msg[4] != sensor.err_msg[4]:
                            sensor.last_msg[4] = sensor.err_msg[4]
                            log.debug('sensors.py', _('Sensor: {} now response').format(sensor.name))
                            if sensor.send_email:
                                text = _('Now response')
                                subj = _('Sensor {}').format(sensor.name)
                                body = text
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            if sensor.log_event:                                   # event log
                                self.update_log(sensor, 'lge', _('Now response'))
                    if sensor.sens_type == 6 and sensor.multi_type == 7:
                        try:  
                            state = sensor.last_read_value[7]                 # multi Motion 
                            if state == 1:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, sensor.motion_msg, sensor.index)
                            if state == 0:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, sensor.no_motion_msg, sensor.index)
                            if state == -127:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Probe Error'), sensor.index)
                        except:
                            sensor.last_read_value[7] = -127
                            pass
                        if sensor.last_read_value[7] != sensor.prev_read_value:
                            sensor.prev_read_value = sensor.last_read_value[7]
                            changed_state = True
                        sensor.err_msg[7] = 1
                        if sensor.last_msg[7] != sensor.err_msg[7]:
                            sensor.last_msg[7] = sensor.err_msg[7]
                            log.debug('sensors.py', _('Sensor: {} now response').format(sensor.name))
                            if sensor.send_email:
                                text = _('Now response')
                                subj = _('Sensor {}').format(sensor.name)
                                body = text
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            if sensor.log_event:                                   # event log
                                self.update_log(sensor, 'lge', _('Now response'))

                    if state == 1  and changed_state:                                                    # is closed 
                        if sensor.sens_type == 1 or (sensor.sens_type == 6 and sensor.multi_type == 4):  # Dry Contact or multi Dry Contact 
                            text = _('Sensor') + ': {} ({})'.format(sensor.name, sensor.dry_clos_msg)
                            subj = _('Sensor Read Success')
                            body = _('Successfully read sensor') + ': {} ({})'.format(sensor.name, sensor.dry_clos_msg) 
                            if sensor.log_event:                                                         # sensor is enabled and enabled log
                                self.update_log(sensor, 'lge', sensor.dry_clos_msg)                      # lge is event, lgs is samples
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            self._trigger_programs(sensor, sensor.trigger_high_program)
                            self._set_stations_in_scheduler_off(sensor.used_stations_two)
                        else:                                                                            # Motion or multi Motion 
                            text = _('Sensor') + ': {} ({})'.format(sensor.name, sensor.motion_msg)
                            subj = _('Sensor Read Success')
                            body = _('Successfully read sensor') + ': {} ({})'.format(sensor.name, sensor.motion_msg)
                            if sensor.log_event:                                                         # sensor is enabled and enabled log           
                                self.update_log(sensor, 'lge', sensor.motion_msg)
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            self._trigger_programs(sensor, sensor.trigger_high_program)

                    if state == 0  and changed_state:                                                    # is open
                        if sensor.sens_type == 1 or (sensor.sens_type == 6 and sensor.multi_type == 4):  # Dry Contact or multi Dry Contact
                            text = _('Sensor') + ': {} ({})'.format(sensor.name, sensor.dry_open_msg)
                            subj = _('Sensor Read Success')
                            body = _('Successfully read sensor') + ': {} ({})'.format(sensor.name, sensor.dry_open_msg) 
                            if sensor.log_event:                                                         # sensor is enabled and enabled log 
                                self.update_log(sensor, 'lge', sensor.dry_open_msg)
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            self._trigger_programs(sensor, sensor.trigger_low_program)
                            self._set_stations_in_scheduler_off(sensor.used_stations_one) 
                        else:                                                                            # Motion or multi Motion
                            text = _('Sensor') + ': {} ({})'.format(sensor.name, sensor.no_motion_msg)
                            subj = _('Sensor Read Success')
                            body = _('Successfully read sensor') + ': {} ({})'.format(sensor.name, sensor.no_motion_msg) 
                            if sensor.log_event:                                                         # sensor is enabled and enabled log
                                self.update_log(sensor, 'lge', sensor.no_motion_msg)
                            if sensor.send_email:
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)  

                    if sensor.log_samples:                                                               # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', state, battery=sensor.last_battery, rssi=sensor.rssi)  # lge is event, lgs is samples

                else:
                    if sensor.manufacturer == 0: # pihrt.com manufacturer
                        if sensor.sens_type == 1 or (sensor.sens_type == 6 and sensor.multi_type == 4):
                            sensor.err_msg[4] = 0
                            if sensor.last_msg[4] != sensor.err_msg[4]:
                                sensor.last_msg[4] = sensor.err_msg[4]
                                if sensor.enabled:
                                    log.debug('sensors.py', _('Sensor: {} not response!').format(sensor.name))
                                if sensor.send_email:
                                    if sensor.enabled:
                                        text = _('Not response!')
                                    else:
                                        text = _('Out of order')
                                    subj = _('Sensor {}').format(sensor.name)
                                    body = text
                                    self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                                if sensor.log_event:                                   # event log
                                    self.update_log(sensor, 'lge', _('Not response!'))
                        if sensor.sens_type == 4 or (sensor.sens_type == 6 and sensor.multi_type == 7):
                            sensor.err_msg[7] = 0
                            if sensor.last_msg[7] != sensor.err_msg[7]:
                                sensor.last_msg[7] = sensor.err_msg[7]
                                if sensor.enabled:
                                    log.debug('sensors.py', _('Sensor: {} not response!').format(sensor.name))
                                if sensor.send_email:
                                    if sensor.enabled:
                                        text = _('Not response!')
                                    else:
                                        text = _('Out of order')
                                    subj = _('Sensor {}').format(sensor.name)
                                    body = text
                                    self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                                if sensor.log_event:                                   # event log
                                    self.update_log(sensor, 'lge', _('Not response!'))
                    if sensor.manufacturer == 1: # shelly manufacturer
                        sensor.err_msg[0] = 0
                        if sensor.last_msg[0] != sensor.err_msg[0]:
                            sensor.last_msg[0] = sensor.err_msg[0]
                            if sensor.enabled:
                                log.debug('sensors.py', _('Sensor: {} not response!').format(sensor.name))
                            if sensor.send_email:
                                if sensor.enabled:
                                    text = _('Not response!')
                                else:
                                    text = _('Out of order')    
                                subj = _('Sensor {}').format(sensor.name)
                                body = text
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            if sensor.log_event:                                   # event log
                                self.update_log(sensor, 'lge', _('Not response!'))

                    if sensor.show_in_footer:
                        if sensor.enabled:
                            self.start_status(sensor.name, _('Not response!'), sensor.index)
                        else:    
                            self.start_status(sensor.name, _('Out of order'), sensor.index)

            ### Moisture, Temperature, Multi Moisture, Multi Temperature ###
            if sensor.sens_type == 3 or sensor.sens_type == 5 or (sensor.sens_type == 6 and sensor.multi_type == 0) or \
                (sensor.sens_type == 6 and sensor.multi_type == 1) or (sensor.sens_type == 6 and sensor.multi_type == 2) or \
                (sensor.sens_type == 6 and sensor.multi_type == 3) or (sensor.sens_type == 6 and sensor.multi_type == 6):
                if sensor.response and sensor.enabled and sensor.manufacturer == 0:   # sensor is enabled and response is OK  
                    state = -127
                    if sensor.sens_type == 3:                                   # type is Moisture
                        try:
                            state = sensor.last_read_value[6]
                        except:
                            sensor.last_read_value[6] = -127
                            state = -127
                            pass
                        if sensor.show_in_footer:
                            if int(state) == -127:
                                self.start_status(sensor.name, _('Probe Error'), sensor.index)
                            else:
                                self.start_status(sensor.name, _('Moisture {}%').format(state), sensor.index)
                    if sensor.sens_type == 5:                                 # type is Temperature
                        try:
                            state = sensor.last_read_value[0]
                        except:
                            sensor.last_read_value[0] = -127
                            state = -127
                            pass
                        if sensor.show_in_footer:
                            if int(state) == -127:
                                self.start_status(sensor.name, _('Probe Error'), sensor.index)
                            else:
                                if options.temp_unit == 'C':
                                    self.start_status(sensor.name, _('Temperature') + ' %.1f \u2103' % state, sensor.index)
                                else:
                                    self.start_status(sensor.name, _('Temperature') + ' %.1f \u2109' % state, sensor.index)
                    if sensor.sens_type == 6 and sensor.multi_type == 0:
                        try:
                            state = sensor.last_read_value[0]                   # multi Temperature DS1  
                        except:
                            sensor.last_read_value[0] = -127
                            state = -127
                            pass   
                        if int(state) == -127:
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _('Probe Error'), sensor.index)
                        else:
                            if options.temp_unit == 'C':
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Temperature') + ' %.1f \u2103' % state, sensor.index)
                            else:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Temperature') + ' %.1f \u2109' % state, sensor.index)
                    if sensor.sens_type == 6 and sensor.multi_type == 1:
                        try:
                            state = sensor.last_read_value[1]                   # multi Temperature DS2 
                        except:
                            sensor.last_read_value[1] = -127
                            state = -127 
                            pass
                        if int(state) == -127:
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _('Probe Error'), sensor.index)
                        else:
                            if options.temp_unit == 'C':
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Temperature') + ' %.1f \u2103' % state, sensor.index)
                            else:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Temperature') + ' %.1f \u2109' % state, sensor.index)
                    if sensor.sens_type == 6 and sensor.multi_type == 2:
                        try:
                            state = sensor.last_read_value[2]                   # multi Temperature DS3
                        except:
                            sensor.last_read_value[2] = -127
                            state = -127
                            pass
                        if int(state) == -127:
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _('Probe Error'), sensor.index)
                        else:
                            if options.temp_unit == 'C':
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Temperature') + ' %.1f \u2103' % state, sensor.index)
                            else:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Temperature') + ' %.1f \u2109' % state, sensor.index)
                    if sensor.sens_type == 6 and sensor.multi_type == 3:
                        try:
                            state = sensor.last_read_value[3]                   # multi Temperature DS4 
                        except:
                            sensor.last_read_value[3] = -127
                            state = -127
                            pass
                        if int(state) == -127:
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _('Probe Error'), sensor.index)
                        else:
                            if options.temp_unit == 'C':
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Temperature') + ' %.1f \u2103' % state, sensor.index)
                            else:
                                if sensor.show_in_footer:
                                    self.start_status(sensor.name, _('Temperature') + ' %.1f \u2109' % state, sensor.index)
                    if sensor.sens_type == 6 and sensor.multi_type == 6:   
                        try:
                            state = sensor.last_read_value[6]                   # multi Moisture
                        except:
                            sensor.last_read_value[6] = -127
                            state = -127
                            pass
                        if int(state) == -127:
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _('Probe Error'), sensor.index)
                        else:
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _('Moisture {}%').format(state), sensor.index)

                    if state != sensor.prev_read_value:
                       sensor.prev_read_value = state
                       changed_state = True

                    major_change = False
                    status_update = False

                    if state > float(sensor.trigger_high_threshold) and changed_state:
                        (major_change, status_update) = self._check_high_trigger(sensor)
                        sensor.last_high_report = now()
                        action = _('High Trigger') if major_change else _('High Value')
                        if status_update:
                            if sensor.log_samples:
                                self.update_log(sensor, 'lgs', state, action, battery=sensor.last_battery, rssi=sensor.rssi)          # wait for reading to be updated
                        if major_change:
                            self._trigger_programs(sensor, sensor.trigger_high_program)

                    elif state < float(sensor.trigger_low_threshold) and changed_state:
                        (major_change, status_update) = self._check_low_trigger(sensor)
                        sensor.last_low_report = now()
                        action = _('Low Trigger') if major_change else _('Low Value')
                        if status_update:
                            if sensor.log_samples:
                                self.update_log(sensor, 'lgs', state, action, battery=sensor.last_battery, rssi=sensor.rssi)          # wait for reading to be updated
                        if major_change:
                            self._trigger_programs(sensor, sensor.trigger_low_program)
                    else:
                        if changed_state:
                            (major_change, status_update) = self._check_good_trigger(sensor)
                            sensor.last_good_report = now()
                            action = _('Normal Trigger') if major_change else _('Normal Value')
                            if status_update:
                                self.update_log(sensor, 'lgs', state, action, battery=sensor.last_battery, rssi=sensor.rssi)          # wait for reading to be updated

                    if major_change:
                        if sensor.send_email:
                            text = _('Sensor') + ': {} ({})'.format(sensor.name, self.status[sensor.index][1])
                            subj = _('Sensor Change')
                            body = _('Sensor Change') + ': {} ({})'.format(sensor.name,  self.status[sensor.index][1])
                            self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)

                    if sensor.log_samples:                                             # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', state, battery=sensor.last_battery, rssi=sensor.rssi)                      # lge is event, lgs is samples

                    if sensor.sens_type == 5:
                        sensor.err_msg[0] = 1
                    if sensor.sens_type == 6 and sensor.multi_type == 0:
                        sensor.err_msg[0] = 1
                    if sensor.sens_type == 6 and sensor.multi_type == 1:
                        sensor.err_msg[1] = 1
                    if sensor.sens_type == 6 and sensor.multi_type == 2:
                        sensor.err_msg[2] = 1
                    if sensor.sens_type == 6 and sensor.multi_type == 3:
                        sensor.err_msg[3] = 1
                    for i in range(4):
                        if sensor.last_msg[i] != sensor.err_msg[i]:
                            sensor.last_msg[i] = sensor.err_msg[i]
                            log.debug('sensors.py', _('Sensor: {} now response').format(sensor.name))
                            if sensor.send_email:
                                text = _('Now response')
                                subj = _('Sensor {}').format(sensor.name)
                                body = text
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            if sensor.log_event:
                                self.update_log(sensor, 'lge', _('Now response'))

                else:
                    if sensor.sens_type == 5:
                        sensor.err_msg[0] = 0
                    if sensor.sens_type == 6 and sensor.multi_type == 0:
                        sensor.err_msg[0] = 0
                    if sensor.sens_type == 6 and sensor.multi_type == 1:
                        sensor.err_msg[1] = 0
                    if sensor.sens_type == 6 and sensor.multi_type == 2:
                        sensor.err_msg[2] = 0
                    if sensor.sens_type == 6 and sensor.multi_type == 3:
                        sensor.err_msg[3] = 0
                    for i in range(4):
                        if sensor.last_msg[i] != sensor.err_msg[i]:
                            sensor.last_msg[i] = sensor.err_msg[i]
                            if sensor.enabled:
                                log.debug('sensors.py', _('Sensor: {} not response!').format(sensor.name))
                            if sensor.send_email:
                                if sensor.enabled:
                                    text = _('Not response!')
                                else:
                                    text = _('Out of order')
                                subj = _('Sensor {}').format(sensor.name)
                                body = text
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            if sensor.log_event:
                                if sensor.enabled:
                                    self.update_log(sensor, 'lge', _('Not response!'))
                                else:
                                    self.update_log(sensor, 'lge', _('Out of order'))
                    if sensor.show_in_footer:
                        if sensor.enabled:
                            self.start_status(sensor.name, _('Not response!'), sensor.index)
                        else:
                            self.start_status(sensor.name, _('Out of order'), sensor.index)

            ### Leak Detector, Multi Leak Detector ###
            if sensor.sens_type == 2 or (sensor.sens_type == 6 and sensor.multi_type == 5): 
                if sensor.response and sensor.enabled and sensor.manufacturer == 0: # sensor is enabled and response is OK  
                    state = -127
                    liters_per_sec = -1
                    if sensor.sens_type == 2:
                        try:
                            state = sensor.last_read_value[5]                 # type is Leak Detector 
                            liters_per_sec = float(sensor.liter_per_pulses)*state
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _('Leak {}l/s').format(liters_per_sec), sensor.index) 
                        except:
                            sensor.last_read_value[5] = -127.0
                            if sensor.show_in_footer: 
                                self.start_status(sensor.name, _('Probe Error'), sensor.index)
                            pass
                        if sensor.last_read_value[5] != sensor.prev_read_value[5]:
                            sensor.prev_read_value[5] = sensor.last_read_value[5]
                            changed_state = True
                    if sensor.sens_type == 6 and sensor.multi_type == 5:
                        try:
                            state = sensor.last_read_value[5]                # multi Leak Detector
                            liters_per_sec = float(sensor.liter_per_pulses)*state
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _('Leak {}l/s').format(liters_per_sec), sensor.index)
                        except:
                            sensor.last_read_value[5] = -127
                            if sensor.show_in_footer:
                                self.start_status(sensor.name, _('Probe Error'), sensor.index)
                            pass
                        if sensor.last_read_value[5] != sensor.prev_read_value:    
                            sensor.prev_read_value = sensor.last_read_value[5]
                            changed_state = True
                            # todo reaction Leak Detector(run progams)

                    if sensor.log_samples:                                                               # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', liters_per_sec, battery=sensor.last_battery, rssi=sensor.rssi)                               # lge is event, lgs is samples 

                    sensor.err_msg[5] = 1
                    if sensor.last_msg[5] != sensor.err_msg[5]:
                        sensor.last_msg[5] = sensor.err_msg[5]
                        log.debug('sensors.py', _('Sensor: {} now response').format(sensor.name))
                        if sensor.send_email:
                            text = _('Now response')
                            subj = _('Sensor {}').format(sensor.name)
                            body = text
                            self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                        if sensor.log_event:
                            self.update_log(sensor, 'lge', _('Now response'))
                else:
                    sensor.err_msg[5] = 0
                    if sensor.last_msg[5] != sensor.err_msg[5]:
                        sensor.last_msg[5] = sensor.err_msg[5]
                        log.debug('sensors.py', _('Sensor: {} not response!').format(sensor.name))
                        if sensor.send_email:
                            if sensor.enabled:
                                text = _('Not response!')
                            else:
                                text = _('Out of order')
                            subj = _('Sensor {}').format(sensor.name)
                            body = text
                            self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                        if sensor.log_event:
                            if sensor.enabled:
                                self.update_log(sensor, 'lge', _('Not response!'))
                            else:
                                self.update_log(sensor, 'lge', _('Out of order'))
                    if sensor.show_in_footer:
                        if sensor.enabled:
                            self.start_status(sensor.name, _('Not response!'), sensor.index)
                        else:
                            self.start_status(sensor.name, _('Out of order'), sensor.index)

            ### Multi Sonic ###
            if sensor.sens_type == 6 and sensor.multi_type == 8:
                if sensor.response and sensor.enabled and sensor.manufacturer == 0:  # sensor is enabled and response is OK
                    state = -127
                    try:
                        state = sensor.last_read_value[8]                    # multi Sonic
                    except:
                        pass
                        sensor.last_read_value[8] = -127
                        if sensor.show_in_footer:
                            self.start_status(sensor.name, _('Probe Error'), sensor.index)
                        if sensor.use_water_stop:                            # If the level sensor fails, the above selected stations in the scheduler will stop
                            self._set_stations_in_scheduler_off(sensor.used_stations)

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
                            tempText = str(volume_in_tank) + ' ' + _('liters') + ', ' + str(level_in_tank) + ' ' + _('cm') + ' (' + str(percent_in_tank) + ' ' + ('%)')
                        else:
                            # in m3
                            volume_in_tank = self.get_volume(level_in_tank, sensor.diameter, False)                     # volume in tank from tank level in m3
                            tempText = str(volume_in_tank) + ' ' + _('m3') + ', ' + str(level_in_tank) + ' ' + _('cm') + ' (' + str(percent_in_tank) + ' ' + ('%)')

                        if sensor.show_in_footer:
                            self.start_status(sensor.name,  '{}'.format(tempText), sensor.index)
                    else:
                        if sensor.show_in_footer:
                            self.start_status(sensor.name, _('Probe Error'), sensor.index)
                        if sensor.use_water_stop: # If the level sensor fails, the above selected stations in the scheduler will stop
                            if int(sensor.aux_reg_p)==1:
                                sensor.aux_reg_p = 0
                                self._set_stations_in_scheduler_off(sensor.used_stations)
                                if sensor.log_event:
                                    self.update_log(sensor, 'lge', _('Probe Error'))
                                if sensor.send_email: # Send Email?
                                    text = _('Sensor') + ': {}'.format(sensor.name)
                                    subj = _('Sensor {}').format(sensor.name)
                                    body = _('Sensor Notification') + ': ' + _('Probe Error')
                                    self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)

                    ### regulation water in tank if enable regulation ###
                    if level_in_tank > 0 and sensor.enable_reg:                           # if enable regulation "maximum water level"
                            reg_station = stations.get(int(sensor.reg_output))
                            ### level > regulation maximum ###
                            if level_in_tank > int(sensor.reg_max):                       # if actual level in tank > set maximum water level
                                if int(sensor.aux_reg_u)==1:
                                    sensor.aux_reg_u = 0
                                    sensor.aux_reg_d = 1
                                    regulation_text = _('Regulation set ON.') + ' ' + ' (' + _('Output') + ' ' +  str(reg_station.index+1) + ').'
                                   
                                    start = datetime.datetime.now()
                                    sid = reg_station.index
                                    end = datetime.datetime.now() + datetime.timedelta(seconds=int(sensor.reg_ss), minutes=int(sensor.reg_mm))
                                    new_schedule = {
                                        'active': True,
                                        'program': -1,
                                        'station': sid,
                                        'program_name': '{}'.format(sensor.name),
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
                                        self.update_log(sensor, 'lge', '{}'.format(regulation_text))
                
                            ### level < regulation minimum ### 
                            if level_in_tank < int(sensor.reg_min):
                                if int(sensor.aux_reg_d)==1:
                                    sensor.aux_reg_u = 1
                                    sensor.aux_reg_d = 0
                                    regulation_text = _('Regulation set OFF.') + ' ' + ' (' + _('Output') + ' ' +  str(reg_station.index+1) + ').'
                                    sid = reg_station.index
                                    stations.deactivate(sid)
                                    active = log.active_runs()
                                    for interval in active:
                                        if interval['station'] == sid:
                                            log.finish_run(interval)
                                    if sensor.log_event:
                                        self.update_log(sensor, 'lge', '{}'.format(regulation_text))

                    ### level in tank has minimum +5cm refresh ###
                    if level_in_tank > int(sensor.water_minimum)+5 and int(sensor.aux_mini)==0:
                        sensor.aux_mini = 1
                        action = _('Normal Trigger') 
                        if sensor.log_samples:
                            self.update_log(sensor, 'lgs', level_in_tank, action, battery=sensor.last_battery, rssi=sensor.rssi)
                        delaytime = int(sensor.delay_duration) # if the level in the tank rises above the minimum +5 cm, the delay is deactivated
                        regulation_text = _('Water in Tank') + ' > ' + str(int(sensor.water_minimum)+5) + _('cm')
                        if sensor.log_event:
                            self.update_log(sensor, 'lge', '{}'.format(regulation_text))
                        rd_text = None
                        if delaytime > 0:
                            if sensor.name in rain_blocks:
                                del rain_blocks[sensor.name]
                                rd_text = _('Removing Rain delay')
                                if sensor.log_event:
                                    self.update_log(sensor, 'lge', '{}'.format(rd_text))
                        if sensor.send_email: # Send Email?
                            text = _('Sensor') + ': {} ({})'.format(sensor.name, regulation_text)
                            subj = _('Sensor {}').format(sensor.name)
                            body = _('Sensor has water') + ': {}'.format(regulation_text)
                            if rd_text is not None:
                                body += '<br>' + rd_text
                            self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)

                    ### level in tank has minimum ### 
                    if level_in_tank <= int(sensor.water_minimum) and int(sensor.aux_mini)==1 and not options.manual_mode and level_in_tank > 1: # level value is lower
                        sensor.aux_mini = 0
                        action = _('Low Trigger') 
                        if sensor.log_samples:
                            self.update_log(sensor, 'lgs', level_in_tank, action, battery=sensor.last_battery, rssi=sensor.rssi) 
                        if sensor.use_stop:   # Stop stations if minimum water level?
                            self._set_stations_in_scheduler_off(sensor.used_stations)
                            regulation_text = _('Water in Tank') + ' < ' + str(sensor.water_minimum) + ' ' + _('cm') + _('!')
                            if sensor.log_event:
                                self.update_log(sensor, 'lge', '{}'.format(regulation_text))
                            delaytime = int(sensor.delay_duration)
                            rd_text = None
                            if delaytime > 0: # if there is no water in the tank and the stations stop, then we set the rain delay for this time for blocking
                                rain_blocks[sensor.name] = datetime.datetime.now() + datetime.timedelta(hours=float(delaytime))
                                rd_text = _('Rain delay') + ' ' + str(delaytime) + ' ' + _('hours.')
                                if sensor.log_event:
                                    self.update_log(sensor, 'lge', '{}'.format(rd_text))
                                if sensor.send_email: # Send Email?
                                    text = _('Sensor') + ': {} ({})'.format(sensor.name, regulation_text)
                                    subj = _('Sensor {}').format(sensor.name)
                                    body = _('Sensor has water minimum') + ': {}'.format(regulation_text)
                                    if rd_text is not None:
                                        body += '<br>' + rd_text
                                    self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            self._set_stations_in_scheduler_off(sensor.used_stations)

                    ### log samples ###
                    if sensor.log_samples:                                             # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', level_in_tank, battery=sensor.last_battery, rssi=sensor.rssi)              # lge is event, lgs is samples

                    sensor.err_msg[8] = 1
                    if sensor.last_msg[8] != sensor.err_msg[8]:
                        sensor.last_msg[8] = sensor.err_msg[8]
                        log.debug('sensors.py', _('Sensor: {} now response').format(sensor.name))
                        if sensor.send_email:
                            text = _('Now response')
                            subj = _('Sensor {}').format(sensor.name)
                            body = text
                            self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                        if sensor.log_event:
                            self.update_log(sensor, 'lge', _('Now response'))
                else:
                    sensor.err_msg[8] = 0
                    if sensor.last_msg[8] != sensor.err_msg[8]:
                        sensor.last_msg[8] = sensor.err_msg[8]
                        if sensor.enabled:
                            log.debug('sensors.py', _('Sensor: {} not response!').format(sensor.name))
                        if sensor.send_email:
                            if sensor.enabled:
                                text = _('Not response!')
                            else:
                                text = _('Out of order')    
                            subj = _('Sensor {}').format(sensor.name)
                            body = text
                            self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                        if sensor.log_event:
                            if sensor.enabled:
                                self.update_log(sensor, 'lge', _('Not response!'))
                            else:
                                self.update_log(sensor, 'lge', _('Out of order'))
                    if sensor.show_in_footer:
                        if sensor.enabled:
                            self.start_status(sensor.name, _('Not response!'), sensor.index)
                        else:    
                            self.start_status(sensor.name, _('Out of order'), sensor.index)

            ### Multi Soil ###
            if sensor.sens_type == 6 and sensor.multi_type == 9:
                if sensor.response and sensor.enabled and sensor.manufacturer == 0:                 # sensor is enabled and response is OK
                    state = ["-127.0"]*16
                    calculate_soil = [0.0]*16
                    tempText = ''
                    err_check = 0
                    try:
                        program = programs.get()
                        for i in range(0, 16): 
                            if type(sensor.soil_last_read_value[i]) == float:
                                state[i] = sensor.soil_last_read_value[i]                           # multi Soil probe 1 - 16
                                ### voltage from probe to humidity 0-100% with calibration range (for footer info)
                                if sensor.soil_invert_probe_in[i]:                                  # probe: rotated state 0V=100%, 3V=0% humidity
                                    calculate_soil[i] = self.maping(state[i], float(sensor.soil_calibration_max[i]), float(sensor.soil_calibration_min[i]), 0.0, 100.0)
                                    calculate_soil[i] = round(calculate_soil[i], 1)                 # round to one decimal point
                                    calculate_soil[i] = 100.0 - calculate_soil[i]                   # ex: 90% - 90% = 10%, 10% is output in invert probe mode
                                else:                                                               # probe: normal state 0V=0%, 3V=100%
                                    calculate_soil[i] = self.maping(state[i], float(sensor.soil_calibration_min[i]), float(sensor.soil_calibration_max[i]), 0.0, 100.0)
                                    calculate_soil[i] = round(calculate_soil[i], 1)                 # round to one decimal point

                                if calculate_soil[i] > 100:                                         # overflow limit > 100%
                                    calculate_soil[i] = 100
                                if calculate_soil[i] < 0:                                           # underflow limitation < 0%
                                    calculate_soil[i] = 0          

                                if sensor.soil_program[i] != "-1":                                  # the probe has a program assigned
                                    pid = u'{}'.format(program[int(sensor.soil_program[i])-1].name)
                                    program_level_adjustments[pid] = round(100.0 - calculate_soil[i], 2)
                                if state[i] >= 0:
                                    if sensor.soil_show_in_footer[i]:   
                                        tempText += '{} {}% ({}V) '.format(sensor.soil_probe_label[i], round(calculate_soil[i], 2), round(state[i], 2))
                            else:
                                err_check += 1

                        if err_check > 15:                                                          # all 16 probes has value -127 (error)
                            sensor.err_msg[9] = 2
                            if sensor.show_in_footer:
                                self.start_status(sensor.name,  _('Probe Error'), sensor.index)
                        else:
                            sensor.err_msg[9] = 1
                            if sensor.show_in_footer:
                                self.start_status(sensor.name,  '{}'.format(tempText), sensor.index)

                        if sensor.log_samples:                                                      # sensor is enabled and enabled log samples
                            if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                                sensor.last_log_samples = now()
                                self.update_log(sensor, 'lgs', state, battery=sensor.last_battery, rssi=sensor.rssi)
                                #self.update_log(sensor, 'lgs', state, msg_calculation = calculate_soil)  # show soil calculation humidity in log page

                        if sensor.last_msg[9] != sensor.err_msg[9]:
                            sensor.last_msg[9] = sensor.err_msg[9]
                            s_msg = ''
                            if sensor.err_msg[9] == 1:
                                s_msg = _('Now response')
                            if sensor.err_msg[9] == 2:
                                s_msg = _('Has Error (Probes)!')
                            log.debug('sensors.py', _('Sensor {} {}').format(sensor.name, s_msg))
                            if sensor.send_email:
                                text = s_msg
                                subj = _('Sensor {}').format(sensor.name)
                                body = text
                                self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                            if sensor.log_event:
                                self.update_log(sensor, 'lge', s_msg)
                    except:
                        log.debug('sensors.py', _('Sensor error: {}').format(traceback.format_exc()))
                        pass

                else:
                    program = programs.get()
                    for i in range(0, 16):
                        if sensor.soil_program[i] != "-1":                                  # the probe has a program assigned
                            pid = '{}'.format(program[int(sensor.soil_program[i])-1].name)
                            program_level_adjustments[pid] = 100                            # sensor not response -> set 100 (no level adjustments!)
                    sensor.err_msg[9] = 0
                    if sensor.last_msg[9] != sensor.err_msg[9]:
                        sensor.last_msg[9] = sensor.err_msg[9]
                        if sensor.enabled:
                            log.debug('sensors.py', _('Sensor: {} not response!').format(sensor.name))
                        if sensor.send_email:
                            if sensor.enabled:
                                text = _('Not response!')
                            else:
                                text = _('Out of order')
                            subj = _('Sensor {}').format(sensor.name)
                            body = text
                            self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)
                        if sensor.log_event:                                                # event log
                            if sensor.enabled:
                                self.update_log(sensor, 'lge', _('Not response!'))
                            else:
                                self.update_log(sensor, 'lge', _('Out of order'))
                    if sensor.show_in_footer:
                        if sensor.enabled:
                            self.start_status(sensor.name, _('Not response!'), sensor.index)
                        else:    
                            self.start_status(sensor.name, _('Out of order'), sensor.index)

            ### Multi Contact ###
            if sensor.sens_type == 7 and sensor.manufacturer == 0:
                if sensor.response and sensor.enabled:                                              # sensor is enabled and response is OK
                    state = [-127.0]*7
                    msg = _('Inputs state') + ' '
                    for i in range(0, 7):
                        state[i] = int(sensor.last_read_value[i])
                        
                        if state[i] == 0:
                            msg += '{}-'.format(i+1) + _('ON')
                        if state[i] == 1:
                            msg += '{}-'.format(i+1) + _('OFF')
                        if i < 6:
                            msg += ', '

                        if sensor.soil_prev_read_value[i] != state[i]:
                            sensor.soil_prev_read_value[i] = state[i]

                            clo_p = None # list with closed programs
                            ope_p = None # list with opened programs
                            clo_s = None # list with closed stations
                            ope_s = None # list with opened stations

                            if i == 0:
                                clo_p= sensor.sw0_closed_program
                                ope_p = sensor.sw0_open_program
                                clo_s = sensor.sw0_closed_stations
                                ope_s = sensor.sw0_open_stations
                            elif i == 1: 
                                clo_p= sensor.sw1_closed_program
                                ope_p = sensor.sw1_open_program
                                clo_s = sensor.sw1_closed_stations
                                ope_s = sensor.sw1_open_stations
                            elif i == 2: 
                                clo_p= sensor.sw2_closed_program
                                ope_p = sensor.sw2_open_program
                                clo_s = sensor.sw2_closed_stations
                                ope_s = sensor.sw2_open_stations
                            elif i == 3: 
                                clo_p= sensor.sw3_closed_program
                                ope_p = sensor.sw3_open_program
                                clo_s = sensor.sw3_closed_stations
                                ope_s = sensor.sw3_open_stations
                            elif i == 4: 
                                clo_p= sensor.sw4_closed_program
                                ope_p = sensor.sw4_open_program
                                clo_s = sensor.sw4_closed_stations
                                ope_s = sensor.sw4_open_stations
                            elif i == 5: 
                                clo_p= sensor.sw5_closed_program
                                ope_p = sensor.sw5_open_program
                                clo_s = sensor.sw5_closed_stations
                                ope_s = sensor.sw5_open_stations
                            elif i == 6: 
                                clo_p= sensor.sw6_closed_program
                                ope_p = sensor.sw6_open_program
                                clo_s = sensor.sw6_closed_stations
                                ope_s = sensor.sw6_open_stations                                                                                                                                                                

                            if state[i] == 0:                                                       # switch xx is closed
                                if isinstance(clo_p, list) and clo_p is not None:
                                    self._trigger_programs(sensor, clo_p)
                                if isinstance(clo_s, list) and clo_s is not None:
                                    self._set_stations_in_scheduler_off(clo_s)    
                            if state[i] == 1:                                                       # switch xx is open
                                if isinstance(ope_p, list) and ope_p is not None:
                                    self._trigger_programs(sensor, ope_p)
                                if isinstance(ope_s, list) and ope_s is not None:
                                    self._set_stations_in_scheduler_off(ope_s)

                    if sensor.show_in_footer:
                        self.start_status(sensor.name, msg , sensor.index)
                else:
                    if sensor.show_in_footer:
                        if sensor.enabled:
                            self.start_status(sensor.name, _('Not response!'), sensor.index)
                        else:
                            self.start_status(sensor.name, _('Out of order'), sensor.index)

            ### Shelly ###
            # sensor.sens_type
            # 0 = 'Voltage'
            # 1 = 'Output 1'
            # 2 = 'Output 2'
            # 3 = 'Output 3'
            # 4 = 'Output 4
            # 5 = 'Temperature 1'
            # 6 = 'Temperature 2'
            # 7 = 'Temperature 3'
            # 8 = 'Temperature 4'
            # 9 = 'Temperature 5'
            # 10 = 'Power 1'
            # 11 = 'Power 2'
            # 12 = 'Power 3'
            # 13 = 'Power 4'
            # 14 = 'Humidity'
            if sensor.manufacturer == 1:
                if sensor.response and sensor.enabled:
                    state = None
                    eml_msg = ''
                    ### Voltage ###
                    if sensor.sens_type == 0:
                        state = sensor.last_voltage
                        eml_msg = _('Voltage') + ': {} '.format(state) + _('V')
                    ### Output 1 ###
                    if sensor.sens_type == 1:
                        try:
                            state = sensor.last_read_value[0][0]
                            if state:
                                eml_msg = _('Output 1') + ': ' + _('ON')
                            else:
                                eml_msg = _('Output 1') + ': ' + _('OFF')
                        except:
                            state = None
                    ### Output 2 ###
                    if sensor.sens_type == 2:
                        try:
                            state = sensor.last_read_value[0][1]
                            if state:
                                eml_msg = _('Output 2') + ': ' + _('ON')
                            else:
                                eml_msg = _('Output 2') + ': ' + _('OFF')
                        except:
                            state = None
                    ### Output 3 ###
                    if sensor.sens_type == 3:
                        try:
                            state = sensor.last_read_value[0][2]
                            if state:
                                eml_msg = _('Output 3') + ': ' + _('ON')
                            else:
                                eml_msg = _('Output 3') + ': ' + _('OFF')
                        except:
                            state = None
                    ### Output 4 ###
                    if sensor.sens_type == 4:
                        try:
                            state = sensor.last_read_value[0][3]
                            if state:
                                eml_msg = _('Output 4') + ': ' + _('ON')
                            else:
                                eml_msg = _('Output 4') + ': ' + _('OFF')
                        except:
                            state = None
                    ### Temperature 1 ###
                    if sensor.sens_type == 5:
                        try:
                            state = sensor.last_read_value[2][0]
                            eml_msg = _('Temperature 1') + ': {} '.format(state) + _('°C')
                        except:
                            state = None
                    ### Temperature 2 ###
                    if sensor.sens_type == 6:
                        try:
                            state = sensor.last_read_value[2][1]
                            eml_msg = _('Temperature 2') + ': {} '.format(state) + _('°C')
                        except:
                            state = None
                    ### Temperature 3 ###
                    if sensor.sens_type == 7:
                        try:
                            state = sensor.last_read_value[2][2]
                            eml_msg = _('Temperature 3') + ': {} '.format(state) + _('°C')
                        except:
                            state = None
                    ### Temperature 4 ###
                    if sensor.sens_type == 8:
                        try:
                            state = sensor.last_read_value[2][3]
                            eml_msg = _('Temperature 4') + ': {} '.format(state) + _('°C')
                        except:
                            state = None
                    ### Temperature 5 ###
                    if sensor.sens_type == 9:
                        try:
                            state = sensor.last_read_value[2][4]
                            eml_msg = _('Temperature 5') + ': {} '.format(state) + _('°C')
                        except:
                            state = None
                    ### Power 1 ###
                    if sensor.sens_type == 10:
                        try:
                            state = sensor.last_read_value[1][0]
                            eml_msg = _('Power 1') + ': {} '.format(state) + _('W')
                        except:
                            state = None
                    ### Power 2 ###
                    if sensor.sens_type == 11:
                        try:
                            state = sensor.last_read_value[1][1]
                            eml_msg = _('Power 2') + ': {} '.format(state) + _('W')
                        except:
                            state = None
                    ### Power 3 ###
                    if sensor.sens_type == 12:
                        try:
                            state = sensor.last_read_value[1][2]
                            eml_msg = _('Power 3') + ': {} '.format(state) + _('W')
                        except:
                            state = None
                    ### Power 4 ###
                    if sensor.sens_type == 13:
                        try:
                            state = sensor.last_read_value[1][3]
                            eml_msg = _('Power 4') + ': {} '.format(state) + _('W')
                        except:
                            state = None
                    ### Humidity ###
                    if sensor.sens_type == 14:
                        try:
                            state = sensor.last_read_value[3][0]
                            eml_msg = _('Humidity') + ': {} '.format(state) + _('%RV')
                        except:
                            state = None

                    if state != sensor.prev_read_value:
                        sensor.prev_read_value = state
                        changed_state = True

                    if state > float(sensor.s_trigger_high_threshold) and changed_state and sensor.aux_reg_u == 1:                    # aux_reg_u is auxiliary for mutual blocking
                        sensor.aux_reg_u = 0
                        action = _('High Value')
                        if sensor.log_samples:
                            self.update_log(sensor, 'lgs', state, action, battery=sensor.last_voltage, rssi=sensor.rssi)
                        self._trigger_programs(sensor, sensor.s_trigger_high_program)
                        if sensor.send_email:
                            text = _('Sensor') + ': {}'.format(sensor.name)
                            subj = _('Sensor Change')
                            body = '{} '.format(datetime_string()) + _('Sensor Name') + ': {}'.format(sensor.name) + ' {}.'.format(eml_msg)
                            self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)

                    if state < float(sensor.s_trigger_low_threshold) and changed_state and sensor.aux_reg_u == 0:                     # aux_reg_u is auxiliary for mutual blocking
                        sensor.aux_reg_u = 1
                        action = _('Low Value')
                        if sensor.log_samples:
                            self.update_log(sensor, 'lgs', state, action, battery=sensor.last_voltage, rssi=sensor.rssi)
                        self._trigger_programs(sensor, sensor.s_trigger_low_program)
                        if sensor.send_email:
                            text = _('Sensor') + ': {}'.format(sensor.name)
                            subj = _('Sensor Change')
                            body = '{} '.format(datetime_string()) + _('Sensor Name') + ': {}'.format(sensor.name) + ' {}.'.format(eml_msg)
                            self._try_send_mail(body, text, attachment=None, subject=subj, eplug=sensor.eplug)

                    changed_state = False

                    if sensor.log_samples:                                                                                            # sensor is enabled and enabled log samples
                        if int(now() - sensor.last_log_samples) >= int(sensor.sample_rate):
                            sensor.last_log_samples = now()
                            self.update_log(sensor, 'lgs', state, battery=sensor.last_voltage, rssi=sensor.rssi)                      # lge is event, lgs is samples

                    if sensor.show_in_footer:
                        if sensor.sens_type == 0:
                            self.start_status(sensor.name, _('Voltage {} V').format(state), sensor.index)
                        if sensor.sens_type == 1 or sensor.sens_type == 2 or sensor.sens_type == 3 or sensor.sens_type == 4:
                            if state is None:
                                self.start_status(sensor.name, _('Inappropriate settings (the sensor cannot get measure this data).').format(state), sensor.index)
                            else:
                                if state:
                                    self.start_status(sensor.name, _('ON'), sensor.index)
                                else:
                                    self.start_status(sensor.name, _('OFF'), sensor.index)
                        if sensor.sens_type == 5 or sensor.sens_type == 6 or sensor.sens_type == 7 or sensor.sens_type == 8 or sensor.sens_type == 9:
                            if state is None:
                                self.start_status(sensor.name, _('Inappropriate settings (the sensor cannot get measure this data).').format(state), sensor.index)
                            else:
                                self.start_status(sensor.name, _('{} ℃').format(state), sensor.index)
                        if sensor.sens_type == 10 or sensor.sens_type == 11 or sensor.sens_type == 12 or sensor.sens_type == 13:
                            if state is None:
                                self.start_status(sensor.name, _('Inappropriate settings (the sensor cannot get measure this data).').format(state), sensor.index)
                            else:
                                self.start_status(sensor.name, _('{} W').format(state), sensor.index)
                        if sensor.sens_type == 14:
                            if state is None:
                                self.start_status(sensor.name, _('Inappropriate settings (the sensor cannot get measure this data).').format(state), sensor.index)
                            else:
                                self.start_status(sensor.name, _('{} %RV').format(state), sensor.index)
                else:
                    if sensor.show_in_footer:
                        if sensor.enabled:
                            self.start_status(sensor.name, _('Not response!'), sensor.index)
                        else:
                            self.start_status(sensor.name, _('Out of order'), sensor.index)

    def check_shellys(self):
        get_data = None
        try:
            from plugins import shelly_cloud_integrator
            get_data = shelly_cloud_integrator.shelly_devices.devices()
        except:
            log.debug('sensors.py', _('Shelly cloud integrator not installed or not enabled in plugins!'))
        try:
            if get_data is not None:
                for i in range(0, len(get_data)):                                   # we go through the list of device shelly
                    id = get_data[i]['id']                                          # we read the device parameters from the list
                    ip = get_data[i]['id']
                    label = get_data[i]['label']
                    volt = get_data[i]['voltage']
                    batt = get_data[i]['battery']
                    temp_list = get_data[i]['temperature']
                    humi_list = get_data[i]['humidity']
                    rssi = get_data[i]['rssi']
                    output_list = get_data[i]['output']
                    power_list = get_data[i]['power']
                    generation = get_data[i]['gen']
                    hardware_text = get_data[i]['hw']
                    hardware_nbr = get_data[i]['hw_nbr']
                    updated = get_data[i]['updated']
                    online = get_data[i]['online']
                    if sensors.count()>0:                                           # if there are any sensors in OSPy
                        for sensor in sensors.get():                                # we will go through all the sensors in OSPy
                            if sensor.shelly_id == id:                              # if the device ID in the shelly sensors matches the shelly sensor ID in the OSPy sensors
                                time_dif = int(now() - sensor.last_response)        # last input from sensor
                                if time_dif >= 30:                                  # save to options every 30 seconds
                                    sensor.ip = ip                                  # we load data from the device shell with this ID into the sensor shell in OSPy
                                    sensor.last_battery = batt
                                    sensor.last_voltage = volt
                                    sensor.rssi = rssi
                                    # output
                                    sensor.last_read_value[0] = output_list
                                    # power
                                    sensor.last_read_value[1] = power_list
                                    # temperature
                                    sensor.last_read_value[2] = temp_list
                                    # humidity
                                    sensor.last_read_value[3] = humi_list
                                    sensor.shelly_hw = hardware_text
                                    sensor.shelly_hw_nbr = hardware_nbr
                                    sensor.shelly_gen = generation
                                    sensor.response = 1 if online is True else 0
                                    sensor.last_response = updated
                                    sensor.last_response_datetime = datetime_string()
                                    log.debug('sensors.py', _('Sensor Shelly: {} saving every 30 seconds to sensors.').format(label))
        except Exception:
            log.debug('sensors.py', _('Sensors shelly timer loop error: {}').format(traceback.format_exc()))
            pass


    def run(self):
        self._sleep(2)
        while True:
            try:
                self.check_shellys()
                self.check_sensors()
                self._sleep(1)

            except Exception:
                log.debug('sensors.py', _('Sensors timer loop error: {}').format(traceback.format_exc()))
                pass
                self._sleep(5)  

sensors_timer = _Sensors_Timer()