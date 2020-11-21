# -*- coding: utf-8 -*-
__author__ = 'Martin Pihrt'

# Local imports
from ospy.options import options
import logging
import traceback


class _Sensor(object):
    SAVE_EXCLUDE = ['SAVE_EXCLUDE', 'index', '_sensors']

    def __init__(self, sensors_instance, index):
        self._sensors = sensors_instance
 
        self.name = ""                  # sensor name
        self.enabled = 0                # sensor enable or disable
        self.token_aes = ""             # aes sensor token
        self.sens_type = 0              # selector 0-5 'None', 'Dry Contact', 'Leak Detector', 'Moisture', 'Motion', 'Temperature'
        self.notes = ""                 # notes for sensor
        self.log_samples = 0            # log samples
        self.log_event = 0              # log event
        self.send_email  = 0            # send e-mail  
        self.normal_trigger = 0         # normal trigger
        self.sensor_position = 0        # sensor position
        self.sensor_board = 0           # sensor board 0-2 'None', 'Wi-Fi', 'Radio'  
        self.sample_rate = 60           # sample rate 
        self.last_read_value = ""       # last read value
        self.sensitivity = 100          # sensitivity
        self.stabilization_time = 0     # stabilization time
        self.trigger_low_program = 0    # open program
        self.trigger_high_program = 0   # close Program
        self.trigger_low_threshold = 0  # low threshold
        self.trigger_high_threshold = 0 # high threshold
        self.ip_address = ""            # ip address for sensor 
        self.last_battery = ""          # battery voltage  
        self.rssi = 0                   # rssi signal

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
