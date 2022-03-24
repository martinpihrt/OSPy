#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = u'Rimco'


class _RainSensorMixIn(object):
    def rain_sensed(self):
        from ospy.options import options
        return options.rain_sensor_enabled and (options.rain_sensor_no == self.rain_input)


class _DummyInputs(_RainSensorMixIn):
    def __init__(self):
        self.rain_input = False


class _IOInputs(_RainSensorMixIn):
    def __init__(self):
        self._mapping = {}
        self._initialized = False

    def __getattr__(self, item):
        if not self._initialized:
            self._initialized = True
            for pin in self._mapping.values():
                self._io.setup(pin, self._io.IN)

        if item.startswith(u'_'):
            return super(_IOInputs, self).__getattribute__(item)
        else:
            return self._io.input(self._mapping[item])


class _RPiInputs(_IOInputs, _RainSensorMixIn):
    def __init__(self):
        import RPi.GPIO as GPIO  # RPi hardware

        super(_RPiInputs, self).__init__()
        self._io = GPIO
        self._io.setwarnings(False)
        self._io.setmode(self._io.BOARD)

        self._mapping = {
            'rain_input': 8
        }


class _BBBInputs(_IOInputs, _RainSensorMixIn):
    def __init__(self):
        import Adafruit_BBIO.GPIO as GPIO  # Beagle Bone Black hardware

        super(_BBBInputs, self).__init__()
        self._io = GPIO
        self._io.setwarnings(False)

        self._mapping = {
            'rain_input': "P9_15"
        }


try:
    inputs = _RPiInputs()
except Exception:
    try:
        inputs = _BBBInputs()
    except Exception:
        inputs = _DummyInputs()