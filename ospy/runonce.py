#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = u'Rimco'

# System imports
import datetime

class _RunOnceProgram(object):
    def __init__(self):
        self.name = _('Run-Once')

        self._start = datetime.datetime.now()
        self._station_seconds = {}

    def clear(self):
        for station in self._station_seconds:
            self._station_seconds[station] = 0

    def set(self, station_seconds):
        """The argument should map station indices to durations in seconds."""
        self._start = datetime.datetime.now()
        self._station_seconds = station_seconds.copy()

    def is_active(self, date_time, station):
        seconds = (date_time - self._start).total_seconds()
        return self._station_seconds.get(station, 0) > seconds >= 0

    def active_intervals(self, date_time_start, date_time_end, station):
        result = []
        if station in self._station_seconds and self._station_seconds[station] > 0:
            station_start = self._start
            station_end = self._start + datetime.timedelta(seconds=self._station_seconds[station])
            if station_end > date_time_start and station_start < date_time_end:
                result.append({
                    'start': station_start,
                    'end': station_end
                })
        return result

run_once = _RunOnceProgram()