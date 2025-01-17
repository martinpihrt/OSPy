#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

# System imports
import datetime
import logging

# Local imports
from ospy.options import options

from blinker import signal

zone_change = signal('zone_change')
master_one_on = signal('master_one_on')
master_one_off = signal('master_one_off')
master_two_on = signal('master_two_on')
master_two_off = signal('master_two_off')
station_off = signal('station_off')
station_on = signal('station_on')
station_clear = signal('station_clear')


class _Station(object):
    SAVE_EXCLUDE = ['SAVE_EXCLUDE', 'index', 'is_master', 'is_master_two', 'is_master_by_program', 'active', 'remaining_seconds']

    def __init__(self, stations_instance, index):
        self._stations = stations_instance
        self.activate_master = False              # this station activate master 1
        self.activate_master_two = False          # this station activate master 2
        self.activate_master_by_program = False   # this station activate master 1 or 2 by program
        self.master_type = 0                      # selector in stations page (0=none, 1=master 1, 2=master 2, 3=master 1/2 by program)

        self.name = "Station %02d" % (index+1)
        self.enabled = True
        self.ignore_rain = False
        self.usage = 1.0
        self.precipitation = 10.0
        self.capacity = 10.0
        self.eto_factor = 1.0
        self.balance = {}
        self.notes = " "

        # Remove (old) balance info:
        if options.cls_name(self, index) in options:
            opts = options[options.cls_name(self, index)]
            if 'last_balance_date' in opts and 'last_balance' in opts:
                self.balance[opts['last_balance_date']] = {
                    'eto': 0.0,
                    'rain': 0.0,
                    'intervals': [],
                    'total': opts['last_balance'],
                    'valid': True
                }

            if 'last_balance_date' in opts:
                del opts['last_balance_date']
            if 'last_balance' in opts:
                del opts['last_balance']
            options[options.cls_name(self, index)] = opts                

        options.load(self, index)

    @property
    def index(self):
        return self._stations.get().index(self)

    @property
    def is_master(self):
        return self.index == self._stations.master

    @property
    def is_master_two(self):
        return self.index == self._stations.master_two

    @property
    def is_master_by_program(self):
        return self.index == self._stations.master_by_program        

    @is_master.setter
    def is_master(self, value):
        if value:
            self._stations.master = self.index
        elif self.is_master:
            self._stations.master = None
    
    @is_master_two.setter
    def is_master_two(self, value):
        if value:
            self._stations.master_two = self.index
        elif self.is_master_two:
            self._stations.master_two = None

    @is_master_by_program.setter
    def is_master_by_program(self, value):
        if value:
            self._stations.master_by_program = self.index
        elif self.is_master_by_program:
            self._stations.master_by_program = None            

    @property
    def active(self):
        return self._stations.active(self.index)

    @active.setter
    def active(self, value):
        if value:
            self._stations.activate(self.index)
        else:
            self._stations.deactivate(self.index)

    @property
    def remaining_seconds(self):
        """Tries to figure out how long this output will be active.
        Returns 0 if no corresponding interval was found.
        Returns -1 if it should be considered infinite."""
        from ospy.log import log
        active = log.active_runs()
        index = self.index
        result = 0
        for interval in active:
            if not interval['blocked'] and interval['station'] == index:
                result = max(0, (interval['end'] - datetime.datetime.now()).total_seconds())
                if result > datetime.timedelta(days=356).total_seconds():
                    result = -1
                break
        return result

    def __setattr__(self, key, value):
        try:
            super(_Station, self).__setattr__(key, value)
            if not key.startswith('_') and key not in self.SAVE_EXCLUDE:
                options.save(self, self.index)
        except ValueError:  # No index available yet
            pass

        if key == 'usage' and value > options.max_usage:
            logging.warning(_('The usage of') + ' %s ' + _('is more than the maximum allowed usage. Scheduling it will be impossible.'), self.name)


class _BaseStations(object):
    def __init__(self, count):
        self._loading = True
        self.master = None
        self.master_two = None
        self.master_by_program = None
        options.load(self)
        self._loading = False

        self._stations = []
        self._state = [False] * count
        for i in range(count):
            self._stations.append(_Station(self, i))
        self.clear()

        options.add_callback('output_count', self._resize_cb)

    def _activate(self):
        """This function should be used to update real outputs according to self._state."""
        logging.debug(_('Activated outputs'))

    def _resize_cb(self, key, old, new):
        self.resize(new)

    def resize(self, count):
        while len(self._stations) < count:
            self._stations.append(_Station(self, len(self._stations)))
            self._state.append(False)

        if count < len(self._stations):
            if self.master is not None:
                if self.master >= count:
                    self.master = None

            if self.master_two is not None:
                if self.master_two >= count:
                    self.master_two = None

            if self.master_by_program is not None:
                if self.master_by_program >= count:
                    self.master_by_program = None

            # Make sure we turn them off before they become unreachable
            for index in range(count, len(self._stations)):
                self._state[index] = False
            self._activate()

            while len(self._stations) > count:
                del self._stations[-1]
                del self._state[-1]

        logging.debug(_('Resized to') + ' %d', count)

    def count(self):
        return len(self._stations)

    def enabled_stations(self):
        return [s for s in self._stations if s.enabled and not s.is_master and not s.is_master_two and not s.is_master_by_program]

    def get(self, index=None):
        if index is None:
            result = self._stations[:]
        else:
            result = self._stations[index]
        return result

    __getitem__ = get


    def activate(self, index):
        if not isinstance(index, list):
            index = [index]
        for i in index:
            if i < len(self._state):
                self._state[i] = True
                logging.debug(_('Activated output') + ' %d', i)
                if self._stations[i].is_master:
                    logging.debug(_('Activated master one'))
                    master_one_on.send()                   # send signal master ON
                if self._stations[i].is_master_two:
                    logging.debug(_('Activated master two'))    
                    master_two_on.send()                   # send signal master 2 ON                            
                 
    def deactivate(self, index):
        if not isinstance(index, list):
            index = [index]
        for i in index:
            if i < len(self._state):
                self._state[i] = False
                logging.debug(_('Deactivated output') + ' %d', i)
                if self._stations[i].is_master:
                    logging.debug(_('Deactivated master one'))
                    master_one_off.send()                   # send signal master OFF
                if self._stations[i].is_master_two:
                    logging.debug(_('Deactivated master two'))    
                    master_two_off.send()                   # send signal master 2 OFF                                    

    def active(self, index=None):
        if index is None:
            result = self._state[:]
        else:
            result = self._state[index] if index < len(self._state) else False
        return result

    def clear(self):
        for i in range(len(self._state)):
            self._state[i] = False
        logging.debug(_('Cleared all outputs'))

    def __setattr__(self, key, value):
        super(_BaseStations, self).__setattr__(key, value)
        if not key.startswith('_') and not self._loading:
            options.save(self)


class _ShiftStations(_BaseStations):

    # All these class variables should be initialized by the subclass before calling init of this class
    _io = None
    _sr_dat = 0
    _sr_clk = 0
    _sr_noe = 0
    _sr_lat = 0

    def __init__(self, count):
        self._io.setup(self._sr_noe, self._io.OUT)
        self._io.output(self._sr_noe, self._io.HIGH)
        self._io.setup(self._sr_clk, self._io.OUT)
        self._io.output(self._sr_clk, self._io.LOW)
        self._io.setup(self._sr_dat, self._io.OUT)
        self._io.output(self._sr_dat, self._io.LOW)
        self._io.setup(self._sr_lat, self._io.OUT)
        self._io.output(self._sr_lat, self._io.LOW)

        super(_ShiftStations, self).__init__(count)

    def _activate(self):
        """Set the state of each output pin on the shift register from the internal state."""
        self._io.output(self._sr_noe, self._io.HIGH)
        self._io.output(self._sr_clk, self._io.LOW)
        self._io.output(self._sr_lat, self._io.LOW)
        for state in reversed(self._state):
            self._io.output(self._sr_clk, self._io.LOW)
            self._io.output(self._sr_dat, self._io.HIGH if state else self._io.LOW)
            self._io.output(self._sr_clk, self._io.HIGH)
        self._io.output(self._sr_lat, self._io.HIGH)
        self._io.output(self._sr_noe, self._io.LOW)
        logging.debug(_('Activated shift outputs'))
        zone_change.send()

    def resize(self, count):
        super(_ShiftStations, self).resize(count)
        self._activate()

    def activate(self, index):
        super(_ShiftStations, self).activate(index)
        self._activate()
        station_on.send("Signaling stations ON", txt=index)

    def deactivate(self, index):
        super(_ShiftStations, self).deactivate(index)
        self._activate()
        station_off.send("Signaling stations OFF", txt=index)

    def clear(self):
        super(_ShiftStations, self).clear()
        self._activate()
        station_clear.send("Signaling stations clear")        


class _RPiStations(_ShiftStations):
    def __init__(self, count):
        import RPi.GPIO as GPIO  # RPi hardware
        self._io = GPIO
        self._io.setwarnings(False)
        self._io.setmode(self._io.BOARD)  # IO channels are identified by header connector pin numbers. Pin numbers are always the same regardless of Raspberry Pi board revision.

        self._sr_dat = 13
        self._sr_clk = 7
        self._sr_noe = 11
        self._sr_lat = 15

        super(_RPiStations, self).__init__(count)


class _BBBStations(_ShiftStations):
    def __init__(self, count):
        import Adafruit_BBIO.GPIO as GPIO  # Beagle Bone Black hardware
        self._io = GPIO
        self._io.setwarnings(False)

        self._sr_dat = "P9_11"
        self._sr_clk = "P9_13"
        self._sr_noe = "P9_14"
        self._sr_lat = "P9_12"

        super(_BBBStations, self).__init__(count)

try:
    stations = _RPiStations(options.output_count)
except Exception as err:
    logging.debug(err)
    try:
        stations = _BBBStations(options.output_count)
    except Exception as err:
        logging.debug(err)
        stations = _BaseStations(options.output_count)