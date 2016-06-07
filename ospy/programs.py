#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Add i18n Martin Pihrt
__author__ = 'Rimco'

# System imports
import datetime

# Local imports
from ospy.helpers import minute_time_str, short_day
from ospy.options import options
import i18n

class ProgramType(object):
    DAYS_SIMPLE = 0
    DAYS_ADVANCED = 1
    REPEAT_SIMPLE = 2
    REPEAT_ADVANCED = 3
    WEEKLY_ADVANCED = 4
    CUSTOM = 5

    FRIENDLY_NAMES = {
        DAYS_SIMPLE: _('Selected days (Simple)'), 
        DAYS_ADVANCED: _('Selected days (Advanced)'),
        REPEAT_SIMPLE: _('Repeating (Simple)'),
        REPEAT_ADVANCED: _('Repeating (Advanced)'),
        WEEKLY_ADVANCED: _('Weekly (Advanced)'),
        CUSTOM: _('Custom'),
    }

ProgramType.NAMES = {getattr(ProgramType, x): x for x in dir(ProgramType) if not x.startswith('_') and
                                                                             isinstance(getattr(ProgramType, x), int)}

class _Program(object):
    SAVE_EXCLUDE = ['SAVE_EXCLUDE', 'index', '_programs', '_loading']

    def __init__(self, programs_instance, index):
        self._programs = programs_instance
        self._loading = True

        self.name =  _('Program') + " %02d" % (index+1 if index >= 0 else abs(index))
        self.stations = []
        self.enabled = True

        self.fixed = 0
        self.cut_off = 0

        self._schedule = []
        self._modulo = 24*60
        self._manual = False  # Non-repetitive (run-once) if True
        self._start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

        self.type = ProgramType.CUSTOM
        self.type_data = [[]]
        if index >= 0:
            options.load(self, index)
        self._loading = False

    @property
    def index(self):
        try:
            return self._programs.get().index(self)
        except ValueError:
            return -1

    @property
    def schedule(self):
        return [interval[:] for interval in self._schedule]

    @schedule.setter
    def schedule(self, value):
        new_schedule = []
        for interval in value:
            new_schedule = self._update_schedule(new_schedule, self.modulo, interval[0], interval[1])

        self._schedule = new_schedule
        self.type = ProgramType.CUSTOM
        self.type_data = [value]

    @property
    def modulo(self):
        return self._modulo

    @property
    def manual(self):
        return self._manual

    @property
    def start(self):
        return self._start

    def start_now(self):
        first_offset = datetime.timedelta(minutes=self._schedule[0][0])
        self._manual = True
        self._schedule = [interval for interval in self.typed_schedule() if interval[1] <= 1440]
        self._start = datetime.datetime.now() - first_offset  # Make sure the first interval starts now

    def _day_str(self, index):
        if self.type != ProgramType.CUSTOM and self.type != ProgramType.REPEAT_ADVANCED:
            return short_day(index)
        else:
            return _('Day') + " %d" % (index + 1)

    def summary(self):
        result = _('Unknown schedule')
        if self.type == ProgramType.CUSTOM:
            if self.manual:
                result = _('Custom schedule running once on') + " %s" % self.start.strftime("%Y-%m-%d")
            else:
                if self._modulo % 1440 == 0 and self._modulo > 0:
                    days = (self._modulo / 1440)
                    if days == 1:
                        result = _('Custom schedule repeating daily')
                    else:
                        result = _('Custom schedule repeating every') + " %d " % (self._modulo / 1440) + _('days')
                else:
                    result = _('Custom schedule repeating every') + " %d " % self._modulo + _('minutes')
        elif self.type == ProgramType.REPEAT_SIMPLE:
            if self.type_data[4] == 1:
                result = _('Simple daily schedule')
            else:
                result = _('Simple schedule repeating every') + " %d " % self.type_data[4] +  _('days') 
        elif self.type == ProgramType.REPEAT_ADVANCED:
            if self.type_data[1] == 1:
                result = _('Advanced daily schedule')
            else:
                result = _('Advanced schedule repeating every') + " %d " % self.type_data[1] + _('days') 
        elif self.type == ProgramType.DAYS_SIMPLE:
            result = _('Simple schedule on') + " " + ' '.join([self._day_str(x) for x in self.type_data[4]])
        elif self.type == ProgramType.DAYS_ADVANCED:
            result = _('Advanced schedule on') + " " + ' '.join([self._day_str(x) for x in self.type_data[1]])
        elif self.type == ProgramType.WEEKLY_ADVANCED:
            result = _('Advanced weekly schedule')
        return result

    def details(self):
        result = _('Unknown schedule')

        if len(self._schedule) == 0:
            result = _('Empty schedule')
        elif self.type == ProgramType.REPEAT_SIMPLE or self.type == ProgramType.DAYS_SIMPLE:
            start_time = minute_time_str(self.type_data[0])
            duration = self.type_data[1]
            pause = self.type_data[2]
            repeat = self.type_data[3]
            result = _('Starting:') + " <span class='val'>%s</span>" % start_time + " " + _('For') + " <span class='val'>%d</span>" % duration + " " + _('minutes') + "<br>" 
            if repeat:
                result += (_('Repeat:') + " <span class='val'>%s</span> "  % repeat + (_('times') if repeat > 1 else _('time')) +
                           " " + _('with a') + " <span class='val'>%d</span> " % pause + _('minute delay') + "<br>") 

        elif self.type == ProgramType.CUSTOM or \
                self.type == ProgramType.REPEAT_ADVANCED or \
                self.type == ProgramType.WEEKLY_ADVANCED:
            if self.type == ProgramType.CUSTOM:
                days = self._modulo / 1440
                intervals = self.schedule
            elif self.type == ProgramType.WEEKLY_ADVANCED:
                days = self._modulo / 1440
                intervals = self.type_data[0]
            else:
                days = self.type_data[1]
                intervals = self.type_data[0]

            if days == 1:
                result = _('Intervals:') + " "
                for interval in intervals:
                    result += "<span class='val'>%s-%s</span> " % (minute_time_str(interval[0]),
                                                                   minute_time_str(interval[1]))
            else:
                day_strs = {}
                for interval in intervals:
                    day_start = int(interval[0] / 1440)
                    day_end = int(interval[1] / 1440)
                    if day_start == day_end:
                        if day_start not in day_strs:
                            day_strs[day_start] = "%s: " % self._day_str(day_start)
                        day_strs[day_start] += "<span class='val'>%s-%s</span> " % (minute_time_str(interval[0]),
                                                                                    minute_time_str(interval[1]))
                    else:
                        if day_start not in day_strs:
                            day_strs[day_start] = "%s: " % self._day_str(day_start)
                        if day_end not in day_strs:
                            day_strs[day_end] = "%s: " % self._day_str(day_end)
                        day_strs[day_start] += "<span class='val'>%s-%s</span> " % (minute_time_str(interval[0]),
                                                                                    minute_time_str(1440))
                        day_strs[day_end] += "<span class='val'>%s-%s</span> " % (minute_time_str(1440),
                                                                                  minute_time_str(interval[1]))
                result = '<br>'.join(day_strs.values())

        elif self.type == ProgramType.DAYS_ADVANCED:
            result = _('Intervals:') + " "
            for interval in self.type_data[0]:
                result += "<span class='val'>%s-%s</span> " % (minute_time_str(interval[0]),
                                                               minute_time_str(interval[1]))
        return result

    def clear(self):
        self._schedule = []

    def set_days_simple(self, start_min, duration_min, pause_min, repeat_times, days):
        new_schedule = []
        for day in days:
            day_start_min = start_min + 1440 * day
            for i in range(repeat_times+1):
                new_schedule = self._update_schedule(new_schedule, 7*1440, day_start_min, day_start_min + duration_min)
                day_start_min += pause_min + duration_min

        self._modulo = 7*1440
        self._manual = False
        self._start = datetime.datetime.combine(datetime.date.today() -
                                                datetime.timedelta(days=datetime.date.today().weekday()),
                                                datetime.time.min)  # First day of current week
        self._schedule = new_schedule

        self.type = ProgramType.DAYS_SIMPLE
        self.type_data = [start_min, duration_min, pause_min, repeat_times, days[:]]

    def set_days_advanced(self, schedule, days):
        new_schedule = []
        for day in days:
            offset = 1440 * day
            for interval in schedule:
                new_schedule = self._update_schedule(new_schedule, 7*1440, interval[0] + offset, interval[1] + offset)

        self._modulo = 7*1440
        self._manual = False
        self._start = datetime.datetime.combine(datetime.date.today() -
                                                datetime.timedelta(days=datetime.date.today().weekday()),
                                                datetime.time.min)  # First day of current week
        self._schedule = new_schedule

        self.type = ProgramType.DAYS_ADVANCED
        self.type_data = [schedule, days[:]]

    def set_repeat_simple(self, start_min, duration_min, pause_min, repeat_times, repeat_days, start_date):
        new_schedule = []
        day_start_min = start_min
        for i in range(repeat_times+1):
            new_schedule = self._update_schedule(new_schedule, repeat_days*1440, day_start_min, day_start_min + duration_min)
            day_start_min += pause_min + duration_min

        self._modulo = repeat_days*1440
        self._manual = False
        self._start = datetime.datetime.combine(start_date, datetime.time.min)
        self._schedule = new_schedule

        self.type = ProgramType.REPEAT_SIMPLE
        self.type_data = [start_min, duration_min, pause_min, repeat_times, repeat_days, start_date]

    def set_repeat_advanced(self, schedule, repeat_days, start_date):
        new_schedule = []
        for interval in schedule:
            new_schedule = self._update_schedule(new_schedule, repeat_days*1440, interval[0], interval[1])

        self._schedule = new_schedule
        self._modulo = repeat_days*1440
        self._manual = False
        self._start = datetime.datetime.combine(start_date, datetime.time.min)

        self.type = ProgramType.REPEAT_ADVANCED
        self.type_data = [schedule, repeat_days, start_date]

    def set_weekly_advanced(self, schedule):
        new_schedule = []
        for interval in schedule:
            new_schedule = self._update_schedule(new_schedule, 7*1440, interval[0], interval[1])

        self._modulo = 7*1440
        self._manual = False
        self._start = datetime.datetime.combine(datetime.date.today() -
                                                datetime.timedelta(days=datetime.date.today().weekday()),
                                                datetime.time.min)  # First day of current week
        self._schedule = new_schedule

        self.type = ProgramType.WEEKLY_ADVANCED
        self.type_data = [schedule]

    # The following functions provide easy access to data of different types, returns default if not available

    def start_min(self):
        if self.type == ProgramType.DAYS_SIMPLE or self.type == ProgramType.REPEAT_SIMPLE:
            return self.type_data[0]
        else:
            return 6*60

    def duration_min(self):
        if self.type == ProgramType.DAYS_SIMPLE or self.type == ProgramType.REPEAT_SIMPLE:
            return self.type_data[1]
        else:
            return 30

    def pause_min(self):
        if self.type == ProgramType.DAYS_SIMPLE or self.type == ProgramType.REPEAT_SIMPLE:
            return self.type_data[2]
        else:
            return 30

    def repeat_times(self):
        if self.type == ProgramType.DAYS_SIMPLE or self.type == ProgramType.REPEAT_SIMPLE:
            return self.type_data[3]
        else:
            return 0

    def days(self):
        if self.type == ProgramType.DAYS_SIMPLE:
            return self.type_data[4]
        elif self.type == ProgramType.DAYS_ADVANCED:
            return self.type_data[1]
        else:
            return []

    def repeat_days(self):
        if self.type == ProgramType.REPEAT_SIMPLE:
            return self.type_data[4]
        elif self.type == ProgramType.REPEAT_ADVANCED:
            return self.type_data[1]
        elif self.type == ProgramType.WEEKLY_ADVANCED:
            return 7
        else:
            return max(1, int(self._modulo / 1440))

    def start_date(self):
        if self.type == ProgramType.REPEAT_SIMPLE:
            return self.type_data[5]
        elif self.type == ProgramType.REPEAT_ADVANCED:
            return self.type_data[2]
        else:
            return self._start

    def typed_schedule(self):
        if self.type == ProgramType.DAYS_ADVANCED:
            return self.type_data[0]
        elif self.type == ProgramType.REPEAT_ADVANCED:
            return self.type_data[0]
        elif self.type == ProgramType.WEEKLY_ADVANCED:
            return self.type_data[0]
        else:
            return self.schedule

    @staticmethod
    def _update_schedule(schedule, modulo, start_minute, end_minute):
        start_minute %= modulo
        end_minute %= modulo

        if end_minute < start_minute:
            end_minute += modulo

        if end_minute > modulo:
            new_entries = [
                [0, end_minute % modulo],
                [start_minute, modulo]
            ]
        else:
            new_entries = [[start_minute, end_minute]]

        new_schedule = schedule[:]

        while new_entries:
            entry = new_entries.pop(0)
            for existing in new_schedule:
                if existing[0] <= entry[0] < existing[1]:
                    entry[0] = existing[1]
                if existing[0] < entry[1] <= existing[1]:
                    entry[1] = existing[0]
                if entry[0] < existing[0] <= existing[1] < entry[1]:
                    new_entries.append([existing[1], entry[1]])
                    entry[1] = existing[0]

                if entry[1] - entry[0] <= 0:
                    break

            if entry[1] - entry[0] > 0:
                new_schedule.append(entry)
                new_schedule.sort(key=lambda ent: ent[0])

        return new_schedule

    def is_active(self, date_time):
        time_delta = date_time - self.start
        minute_delta = time_delta.days*24*60 + int(time_delta.seconds/60)

        if self.manual and minute_delta >= self.modulo:
            return False

        current_minute = minute_delta % self.modulo

        result = False
        for entry in self.schedule:
            if entry[0] <= current_minute < entry[1]:
                result = True
                break
            elif entry[0] <= current_minute+self.modulo < entry[1]:
                result = True
                break
            elif entry[0] > current_minute:
                break

        return result

    def active_intervals(self, date_time_start, date_time_end):
        result = []
        if self.manual:
            current_date_time = self.start
        else:
            start_delta = date_time_start - self.start
            start_minutes = (start_delta.days*24*60 + int(start_delta.seconds/60)) % self.modulo
            current_date_time = date_time_start - datetime.timedelta(minutes=start_minutes,
                                                                     seconds=date_time_start.second,
                                                                     microseconds=date_time_start.microsecond)

        while current_date_time < date_time_end:
            for entry in self.schedule:
                start = current_date_time + datetime.timedelta(minutes=entry[0])
                end = current_date_time + datetime.timedelta(minutes=entry[1])

                if end <= date_time_start:
                    continue

                if start >= date_time_end:
                    break

                result.append({
                    'start': start,
                    'end': end
                })

            if self.manual:
                break

            current_date_time += datetime.timedelta(minutes=self.modulo)

        return result

    def __setattr__(self, key, value):
        if key == 'modulo':
            self._modulo = value
            if not self._loading:
                self.schedule = self._schedule  # Convert to custom sequence
        elif key == 'manual':
            self._manual = value
            if not self._loading and value:
                self.schedule = self._schedule  # Convert to custom sequence
        elif key == 'start':
            if self._loading:  # Update start date to most recent possible
                while value <= datetime.datetime.today():
                    value += datetime.timedelta(minutes=self._modulo)
                self._start = value
            else:
                self._start = value
                self.schedule = self._schedule  # Convert to custom sequence
        else:
            super(_Program, self).__setattr__(key, value)
            if key not in self.SAVE_EXCLUDE:
                if not self._loading and self.index >= 0:
                    options.save(self, self.index)


class _Programs(object):
    def __init__(self):
        self._programs = []
        self.run_now_program = None

        i = 0
        while options.available(_Program, i):
            self._programs.append(_Program(self, i))
            i += 1

        options.add_callback('output_count', self._option_cb)

    def _option_cb(self, key, old, new):
        # Remove all stations that do not exist anymore
        for program in self._programs:
            program.stations = [station for station in program.stations if 0 <= station < new]

    def add_program(self, program=None):
        if program is None:
            program = _Program(self, len(self._programs))
        self._programs.append(program)
        options.save(program, program.index)

    def create_program(self):
        """Returns a new program, but doesn't add it to the list."""
        return _Program(self, -1-len(self._programs))

    def remove_program(self, index):
        if 0 <= index < len(self._programs):
            del self._programs[index]

        for i in range(index, len(self._programs)):
            options.save(self._programs[i], i)  # Save programs using new indices

        options.erase(_Program, len(self._programs))  # Remove info in last index

    def run_now(self, index):
        if 0 <= index < len(self._programs):
            program = self._programs[index]
            if program.type != ProgramType.WEEKLY_ADVANCED and program.type != ProgramType.CUSTOM:
                if len(program.schedule) > 0:
                    run_now_p = _Program(self, index)  # Create a copy using the information saved in options
                    run_now_p.start_now()
                    self.run_now_program = run_now_p

    def count(self):
        return len(self._programs)

    def get(self, index=None):
        if index is None:
            result = self._programs[:]
        else:
            result = self._programs[index]
        return result

    __getitem__ = get

programs = _Programs()