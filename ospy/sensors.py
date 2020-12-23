# -*- coding: utf-8 -*-
__author__ = 'Martin Pihrt'

# System imports
from threading import Thread
import traceback
import logging
import traceback
import time
import datetime

# Local imports
from ospy.options import options
from ospy.helpers import now, password_hash

### Sensors ###
class _Sensor(object):
    SAVE_EXCLUDE = ['SAVE_EXCLUDE', 'index', '_sensors']

    def __init__(self, sensors_instance, index):
        self._sensors = sensors_instance
        self.name = ""                  # sensor name        
        self.encrypt = password_hash(str(now()), 'notarandomstring')[:16] # sensor security encrypted code
        self.enabled = 0                # sensor enable or disable
        self.sens_type = 0              # selector sensor type: 0-5 'None', 'Dry Contact', 'Leak Detector', 'Moisture', 'Motion', 'Temperature'
        self.com_type = 0               # selector sensor communication type 0-1: 'Wi-Fi/LAN', 'Radio'
        self.notes = ""                 # notes for sensor
        self.log_samples = 0            # log samples
        self.log_event = 0              # log event
        self.send_email  = 0            # send e-mail  
        self.sample_rate = 60           # sample rate 
        self.last_read_value = ""       # last read value
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
        self.daemon = True

    def run(self):
        while True:
            try:
                self._check_sensors()
            except Exception:
                logging.warning(_(u'Sensors timer loop error: {}').format(traceback.format_exc()))
            time.sleep(1)


    @staticmethod
    def _check_sensors():
        for sensor in sensors.get():
            time_dif = int(now() - sensor.last_response)                      # last input from sensor
            if time_dif >= 120:                                               # timeout 120 seconds
                if sensor.response != 0:
                    sensor.response = 0                                       # reseting status green circle to red (on sensors page)
            
            #if sensor.enabled:                                                    # if sensor is enabled
            #    if sensor.sens_type == 1:                                         # sensor type 1 (Dry Contact)
            #        print "1"
            #    elif sensor.sens_type == 2:                                       # sensor type 2 (Leak Detector)
            #        print "2"
            #    elif sensor.sens_type == 3:                                       # sensor type 3 (Moisture)
            #        print "3"
            #    elif sensor.sens_type == 4:                                       # sensor type 4 (Motion)
            #        print "4"
            #    elif sensor.sens_type == 5:                                       # sensor type 5 (Temperature)
            #        print "5" 

                #if sensor.log_samples:                                                # if sensor logging samples enabled 
                #if sensor.log_event:                                                  # if sensor logging event enabled
                #if sensor.send_email:                                                 # if sensor sending e-mail enabled


sensors_timer = _Sensors_Timer()

