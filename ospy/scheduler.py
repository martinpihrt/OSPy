#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

from blinker import signal

# System imports
from threading import Thread
import datetime
import time
import time as time_
import logging
import traceback
from . import i18n 

# Local imports
from ospy.inputs import inputs
from ospy.log import log, logEV
from ospy.options import level_adjustments, program_level_adjustments
from ospy.options import options
from ospy.options import rain_blocks
from ospy.programs import programs
from ospy.runonce import run_once
from ospy.stations import stations
from ospy.outputs import outputs
from ospy.helpers import get_external_ip

rain_active = signal('rain_active')
rain_not_active = signal('rain_not_active')
internet_available = signal('internet_available')
internet_not_available = signal('internet_not_available')
rain_delay_set = signal('rain_delay_set')
rain_delay_remove = signal('rain_delay_remove')
core_30_sec_tick = signal('core_30_sec_tick')


def report_rain_delay_set():      # send rain delay setuped signal
    remaining = abs(rain_blocks.seconds_left())
    m, s = divmod(remaining, 60)
    h, m = divmod(m, 60)
    rain_delay_set.send(txt='{}:{}:{}'.format(int(h), int(m), int(s)))
    logEV.save_events_log(_('Rain delay'), _('Rain delay has set a delay {} hours {} minutes {} seconds').format(int(h), int(m), int(s)), id='RainDelay') 

def report_rain_delay_remove():   # send rain delay removed signal
    rain_delay_remove.send() 
    logEV.save_events_log(_('Rain delay'), _('Rain delay has now been removed'), id='RainDelay')

def report_rain():
    rain_active.send()            # send rain signal
    logEV.save_events_log(_('Rain sensor'), _('Activated'), id='RainSensor')
    if options.rain_set_delay:    # if rain delay enabled set these delay
        options.rain_block = datetime.datetime.now() + datetime.timedelta(hours=options.rain_sensor_delay)
        logEV.save_events_log(_('Rain delay'), _('Rain sensor has set a delay {} hours').format(options.rain_sensor_delay), id='RainDelay')

def report_no_rain():
    rain_not_active.send()        # send not rain signal
    logEV.save_events_log(_('Rain sensor'), _('Deactivated'), id=u'RainSensor')

def report_internet_available():
    internet_available.send()     # send internet available signal
    logEV.save_events_log(_('Connection'), _('Internet is available (external IP)'), id='Internet')

def report_internet_not_available():
    internet_not_available.send() # send internet not available signal
    logEV.save_events_log(_('Connection'), _('Internet is not available (external IP)'), id='Internet')

def report_core_30_sec_tick():
    core_30_sec_tick.send()       # send core_30_sec_tick signal

pom_last_rain = False             # send signal only if rain change
pom_last_internet = False         # send signal only if internet change
pom_last_rain_delay = False       # send signal only if rain delay change
pom_last_30s_tick = 0             # helper for 30 seconds loop tick

blocking_from_pressurizer = False

### read pressurizer plugin master relay on state ###
def notify_pressurizer_master_relay_on(name, **kw):
    global blocking_from_pressurizer
    blocking_from_pressurizer = True

### read pressurizer plugin master relay off state ###
def notify_pressurizer_master_relay_off(name, **kw):
    global blocking_from_pressurizer
    blocking_from_pressurizer = False

pressurizer_master_relay_on = signal('pressurizer_master_relay_on')
pressurizer_master_relay_on.connect(notify_pressurizer_master_relay_on)
pressurizer_master_relay_off = signal('pressurizer_master_relay_off')
pressurizer_master_relay_off.connect(notify_pressurizer_master_relay_off)


### determines all schedules ###
def predicted_schedule(start_time, end_time):
    """Determines all schedules for the given time range.
    To calculate what should currently be active, a start time of some time (a day) ago should be used."""

    adjustment = level_adjustments.total_adjustment()
    max_usage = options.max_usage
    delay_delta = datetime.timedelta(seconds=options.station_delay)

    rain_block_start = datetime.datetime.now()
    rain_block_end = rain_blocks.block_end()

    skip_intervals = log.finished_runs() + log.active_runs()
    current_active = [interval for interval in skip_intervals if not interval['blocked']]

    usage_changes = {}
    for active in current_active:
        start = active['start']
        end = active['end']
        if start not in usage_changes:
            usage_changes[start] = 0
        if end not in usage_changes:
            usage_changes[end] = 0

        usage_changes[start] += active['usage']
        usage_changes[end] -= active['usage']

    station_schedules = {}

    # Get run-once information:
    for station in stations.enabled_stations():
        run_once_intervals = run_once.active_intervals(start_time, end_time, station.index)
        for interval in run_once_intervals:
            if station.index not in station_schedules:
                station_schedules[station.index] = []

            program_name = _('Run-Once')
            new_schedule = {
                'active': None,
                'program': -1,
                'program_name': program_name,
                'fixed': True,
                'cut_off': 0,
                'control_master': 0,
                'manual': True,
                'blocked': False,
                'start': interval['start'],
                'original_start': interval['start'],
                'end': interval['end'],
                'uid': '%s-%s-%d' % (str(interval['start']), program_name, station.index),
                'usage': station.usage
            }
            station_schedules[station.index].append(new_schedule)

    # Get run-now information:
    if programs.run_now_program is not None:
        program = programs.run_now_program
        for station in sorted(program.stations):
            run_now_intervals = program.active_intervals(start_time, end_time, station)
            for interval in run_now_intervals:
                if station >= stations.count() or stations.master == station or stations.master_two == station or not stations[station].enabled:
                    continue

                if station not in station_schedules:
                    station_schedules[station] = []

                program_name = _('Run-Now') + ' %s' % program.name 
                new_schedule = {
                    'active': None,
                    'program': -1,
                    'program_name': program_name,
                    'fixed': program.fixed, # True for ignore water level else program.fixed for use water level in run now-program xx
                    'cut_off': 0,
                    'control_master': program.control_master,
                    'manual': True,
                    'blocked': False,
                    'start': interval['start'],
                    'original_start': interval['start'],
                    'end': interval['end'],
                    'uid': '%s-%s-%d' % (str(interval['start']), program_name, station),
                    'usage': stations.get(station).usage
                }
                station_schedules[station].append(new_schedule)

    # Aggregate per station:
    for program in programs.get():
        if not program.enabled:
            continue

        for station in sorted(program.stations):
            program_intervals = program.active_intervals(start_time, end_time, station)
            if station >= stations.count() or stations.master == station or stations.master_two == station or not stations[station].enabled:
                continue

            if station not in station_schedules:
                station_schedules[station] = []

            for interval in program_intervals:
                if current_active and current_active[-1]['original_start'] > interval['start']:
                    continue

                new_schedule = {
                    'active': None,
                    'program': program.index,
                    'program_name': program.name, # Save it because programs can be renamed
                    'fixed': program.fixed,
                    'cut_off': program.cut_off/100.0,
                    'control_master': program.control_master,
                    'manual': program.manual,
                    'blocked': False,
                    'start': interval['start'],
                    'original_start': interval['start'],
                    'end': interval['end'],
                    'uid': '%s-%d-%d' % (str(interval['start']), program.index, station),
                    'usage': stations.get(station).usage
                }
                station_schedules[station].append(new_schedule)

    # Make lists sorted on start time, check usage
    for station in station_schedules:
        if 0 < max_usage < stations.get(station).usage:
            station_schedules[station] = []  # Impossible to schedule
        else:
            station_schedules[station].sort(key=lambda inter: inter['start'])

    all_intervals = []
    # Adjust for weather and remove overlap:
    for station, schedule in station_schedules.items():
        for interval in schedule:
            if not interval['fixed']:
                p_name = '{}'.format(interval['program_name'])
                soil_adjustment = 1.0
                if p_name in program_level_adjustments:
                    soil_adjustment = program_level_adjustments[p_name]/100
                time_delta = interval['end'] - interval['start']
                time_delta = datetime.timedelta(seconds=(time_delta.days * 24 * 3600 + time_delta.seconds) * adjustment * soil_adjustment)
                interval['end'] = interval['start'] + time_delta
                interval['adjustment'] = adjustment
            else:
                interval['adjustment'] = 1.0

        last_end = datetime.datetime(2000, 1, 1)
        for interval in schedule:
            if last_end > interval['start']:
                time_delta = last_end - interval['start']
                interval['start'] += time_delta
                interval['end'] += time_delta
            last_end = interval['end']

            new_interval = {
                'station': station
            }
            new_interval.update(interval)

            all_intervals.append(new_interval)

    # Make list of entries sorted on duration and time (stable sorted on station #)
    all_intervals.sort(key=lambda inter: inter['end'] - inter['start'])
    all_intervals.sort(key=lambda inter: inter['start'])

    # If we have processed some intervals before, we should skip all that were scheduled before them
    for to_skip in skip_intervals:
        index = 0
        while index < len(all_intervals):
            interval = all_intervals[index]

            if interval['original_start'] < to_skip['original_start']  and (not to_skip['blocked'] or interval['blocked']):
                del all_intervals[index]
            elif interval['uid'] == to_skip['uid']:
                del all_intervals[index]
                break
            else:
                index += 1

    # And make sure manual programs get priority:
    all_intervals.sort(key=lambda inter: not inter['manual'])

    # Try to add each interval
    for interval in all_intervals:
        if not interval['manual'] and not options.scheduler_enabled:
            interval['blocked'] = 'disabled scheduler'
            continue
        elif not interval['manual'] and not stations.get(interval['station']).ignore_rain and \
                rain_block_start <= interval['start'] < rain_block_end:
            interval['blocked'] = 'rain delay'
            continue
        elif not interval['manual'] and not stations.get(interval['station']).ignore_rain and inputs.rain_sensed():
            interval['blocked'] = 'rain sensor'
            continue
        elif not interval['fixed'] and interval['adjustment'] < interval['cut_off']:
            interval['blocked'] = 'cut-off'
            continue

        if max_usage > 0:
            usage_keys = sorted(usage_changes.keys())
            start_usage = 0
            start_key_index = -1

            for index, key in enumerate(usage_keys):
                if key > interval['start']:
                    break
                start_key_index = index
                start_usage += usage_changes[key]

            failed = False
            finished = False
            while not failed and not finished:
                parallel_usage = 0
                parallel_current = 0
                for index in range(start_key_index+1, len(usage_keys)):
                    key = usage_keys[index]
                    if key >= interval['end']:
                        break
                    parallel_current += usage_changes[key]
                    parallel_usage = max(parallel_usage, parallel_current)

                if start_usage + parallel_usage + interval['usage'] <= max_usage:

                    start = interval['start']
                    end = interval['end']
                    if start not in usage_changes:
                        usage_changes[start] = 0
                    if end not in usage_changes:
                        usage_changes[end] = 0

                    usage_changes[start] += interval['usage']
                    usage_changes[end] -= interval['usage']
                    finished = True
                else:
                    while not failed:
                        # Shift this interval to next possibility
                        start_key_index += 1

                        # No more options
                        if start_key_index >= len(usage_keys):
                            failed = True
                        else:
                            next_option = usage_keys[start_key_index]
                            next_change = usage_changes[next_option]
                            start_usage += next_change

                            # Lower usage at this starting point:
                            if next_change < 0:
                                skip_delay = False
                                if options.min_runtime > 0:
                                    # Try to determine how long we have been running at this point:
                                    min_runtime_delta = datetime.timedelta(seconds=options.min_runtime)
                                    temp_usage = 0
                                    running_since = next_option
                                    not_running_since = next_option
                                    for temp_index in range(0, start_key_index):
                                        temp_usage_key = usage_keys[temp_index]
                                        if temp_usage < 0.01 and usage_changes[temp_usage_key] > 0 and temp_usage_key - not_running_since > datetime.timedelta(seconds=3):
                                            running_since = temp_usage_key
                                        temp_usage += usage_changes[temp_usage_key]
                                        if temp_usage < 0.01 and usage_changes[temp_usage_key] < 0:
                                            not_running_since = temp_usage_key
                                    if next_option - running_since < min_runtime_delta:
                                        skip_delay = True

                                if skip_delay:
                                    time_to_next = next_option - interval['start']
                                else:
                                    time_to_next = next_option + delay_delta - interval['start']

                                interval['start'] += time_to_next
                                interval['end'] += time_to_next
                                break


            if failed:
                logging.warning(_('Could not schedule {}.').format(interval['uid']))
                interval['blocked'] = 'scheduler error'



    all_intervals.sort(key=lambda inter: inter['start'])

    return all_intervals


def combined_schedule(start_time, end_time):
    current_time = datetime.datetime.now()
    if current_time < start_time:
        result = predicted_schedule(start_time, end_time)
    elif current_time > end_time:
        result = [entry for entry in log.finished_runs() if start_time <= entry['start'] <= end_time or
                                                            start_time <= entry['end'] <= end_time]
    else:
        result = log.finished_runs()
        result += log.active_runs()
        predicted = predicted_schedule(start_time, end_time)
        result += [entry for entry in predicted if current_time <= entry['start'] <= end_time]

    return result


class _Scheduler(Thread):
    def __init__(self):
        super(_Scheduler, self).__init__()
        self.daemon = True
        #options.add_callback('scheduler_enabled', self._option_cb)
        options.add_callback('manual_mode', self._option_cb)
        options.add_callback('master_relay', self._option_cb)

        # If manual mode is active, finish all stale runs:
        if options.manual_mode:
            log.finish_run(None)

    def _option_cb(self, key, old, new):
        # Clear if manual mode changed:
        if key == 'manual_mode':
            programs.run_now_program = None
            run_once.clear()
            log.finish_run(None)
            stations.clear()

        # Stop relay if not used anymore:
        if key == 'master_relay' and not new and outputs.relay_output:
            outputs.relay_output = False

    def run(self):
        global pom_last_30s_tick
        
        current_time = datetime.datetime.now()
        rain = not options.manual_mode and (rain_blocks.block_end() > datetime.datetime.now() or
                                            inputs.rain_sensed())

        # Activate outputs upon start if needed:
        active = log.active_runs()
        for entry in active:
            ignore_rain = stations.get(entry['station']).ignore_rain
            if entry['end'] > current_time and (not rain or ignore_rain) and not entry['blocked']:
                stations.activate(entry['station'])

        while True:
            try:
                self._check_schedule()
                millis = int(round(time_.time() * 1000))
                if (millis - pom_last_30s_tick) >= 30000:   # always send a tick signal after 30 seconds
                    pom_last_30s_tick = millis
                    try:
                        report_core_30_sec_tick()
                    except:
                        pass 
            except Exception:
                logging.warning('Scheduler error:\n' + traceback.format_exc())
            time.sleep(1)

    @staticmethod
    def _check_schedule():
        global blocking_from_pressurizer

        current_time = datetime.datetime.now()
        check_start = current_time - datetime.timedelta(days=1)
        check_end = current_time + datetime.timedelta(days=1)

        rain = not options.manual_mode and (rain_blocks.block_end() > datetime.datetime.now() or
                                            inputs.rain_sensed())          

        global pom_last_rain, pom_last_internet, pom_last_rain_delay
        
        if inputs.rain_sensed() and not pom_last_rain:
            report_rain()
            pom_last_rain = True
        
        if not inputs.rain_sensed() and pom_last_rain:
            report_no_rain()
            pom_last_rain = False

        if get_external_ip() != '-' and not pom_last_internet:
            report_internet_available()
            pom_last_internet = True

        if get_external_ip() == '-' and pom_last_internet:
            report_internet_not_available()
            pom_last_internet = False

        if rain_blocks.seconds_left() and not pom_last_rain_delay:
            report_rain_delay_set()
            pom_last_rain_delay = True

        if not rain_blocks.seconds_left() and pom_last_rain_delay:
            report_rain_delay_remove()
            pom_last_rain_delay = False   

        active = log.active_runs()
        for entry in active:
            ignore_rain = stations.get(entry['station']).ignore_rain
            if entry['end'] <= current_time or (rain and not ignore_rain and not entry['blocked'] and not entry['manual']):
                if not rain:
                    log.finish_run(entry)
                if ignore_rain:
                    log.finish_run(entry)
                if not entry['blocked']:
                    stations.deactivate(entry['station'])

        if not options.manual_mode:
            schedule = predicted_schedule(check_start, check_end)
            for entry in schedule:
                if entry['start'] <= current_time < entry['end']: 
                    if rain and stations.get(entry['station']).ignore_rain:
                        if not entry['blocked']:
                            log.start_run(entry)
                            stations.activate(entry['station'])
                    if not rain:
                        if not entry['blocked']:
                            log.start_run(entry)
                            stations.activate(entry['station'])
               


        if stations.master is not None:
            master_on = False

            # It's easy if we don't have to use delays:
            if options.master_on_delay == options.master_off_delay == 0:
                for entry in active:
                    if not entry['blocked'] and stations.get(entry['station']).activate_master:
                        master_on = True
                        break
                    # master on by program control_master   
                    if not entry['blocked'] and stations.get(entry['station']).activate_master_by_program:
                        if 'control_master' in entry and entry['control_master'] == 1:
                            master_on = True
                            break
            else:
                # In manual mode we cannot predict, we only know what is currently running and the history
                if options.manual_mode:
                    active = log.finished_runs() + active
                else:
                    active = combined_schedule(check_start, check_end)

                for entry in active:
                    if not entry['blocked'] and stations.get(entry['station']).activate_master:
                        if entry['start'] + datetime.timedelta(seconds=options.master_on_delay) \
                                <= current_time < \
                                entry['end'] + datetime.timedelta(seconds=options.master_off_delay):
                            master_on = True
                            break
                    # master on by program control_master   
                    if not entry['blocked'] and stations.get(entry['station']).activate_master_by_program:
                        if 'control_master' in entry and entry['control_master'] == 1:
                            if entry['start'] + datetime.timedelta(seconds=options.master_on_delay) \
                                <= current_time < \
                                entry['end'] + datetime.timedelta(seconds=options.master_off_delay):
                                master_on = True
                                break                            

            if stations.master is not None:
                master_station = stations.get(stations.master)

                if master_on != master_station.active:
                    master_station.active = master_on

            if options.master_relay and not blocking_from_pressurizer: # if pressurizer plugin running blocking outputs.relay_output = master_on
               outputs.relay_output = master_on


        if stations.master_two is not None:
            master_two_on = False

            # It's easy if we don't have to use delays:
            if options.master_on_delay_two == options.master_off_delay_two == 0:
                for entry in active:
                    if not entry['blocked'] and stations.get(entry['station']).activate_master_two:
                        master_two_on = True
                        break
                    # master 2 on by program control_master   
                    if not entry['blocked'] and stations.get(entry['station']).activate_master_by_program:
                        if 'control_master' in entry and entry['control_master'] == 2:
                            master_two_on = True
                            break                        
            else:
                # In manual mode we cannot predict, we only know what is currently running and the history
                if options.manual_mode:
                    active = log.finished_runs() + active
                else:
                    active = combined_schedule(check_start, check_end)

                for entry in active:
                    if not entry['blocked'] and stations.get(entry['station']).activate_master_two:
                        if entry['start'] + datetime.timedelta(seconds=options.master_on_delay) \
                                <= current_time < \
                                entry['end'] + datetime.timedelta(seconds=options.master_off_delay):
                            master_two_on = True
                            break
                    # master on by program control_master   
                    if not entry['blocked'] and stations.get(entry['station']).activate_master_by_program:
                        if 'control_master' in entry and entry['control_master'] == 2:
                            if entry['start'] + datetime.timedelta(seconds=options.master_on_delay) \
                                <= current_time < \
                                entry['end'] + datetime.timedelta(seconds=options.master_off_delay):
                                master_two_on = True
                                break                            

            if stations.master_two is not None:
                master_station_two = stations.get(stations.master_two)

                if master_two_on != master_station_two.active:
                    master_station_two.active = master_two_on

scheduler = _Scheduler()