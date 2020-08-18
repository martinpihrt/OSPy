# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = 'Rimco'

# System imports
import datetime
import logging
import traceback
from os import path
import threading
import time
import sys
import codecs

# Local imports
from ospy.options import options
from ospy.helpers import print_report

EVENT_FILE = './ospy/data/events.log'
EVENT_FORMAT = "%(asctime)s [%(levelname)s %(event_type)s] %(filename)s:%(lineno)d: %(message)s"
RUN_START_FORMAT = "%(asctime)s [START  Run] Program %(program)d - Station %(station)d: From %(start)s to %(end)s"
RUN_FINISH_FORMAT = "%(asctime)s [FINISH Run] Program %(program)d - Station %(station)d: From %(start)s to %(end)s"


class _Log(logging.Handler):
    def __init__(self):
        super(_Log, self).__init__()
        self._log = {
            'Run': options.logged_runs[:]
        }
        self._lock = threading.RLock()
        self._plugin_time = time.time() + 3

    @property
    def level(self):
        return logging.DEBUG if options.debug_log else logging.INFO

    @level.setter
    def level(self, value):
        pass  # Override level using options

    def _save_logs(self):
        from ospy.programs import programs, ProgramType
        result = []
        if options.run_log or any(program.type == ProgramType.WEEKLY_WEATHER for program in programs.get()):
            result = self._log['Run']
        options.logged_runs = result


    @staticmethod
    def _save_log(msg, level, event_type):
        
        msg_print = msg.encode('ascii', 'replace')
       
        # Print if it is important:
        if level >= logging.WARNING:
            print(msg_print, file=sys.stderr)

        # Or print it we are debugging or if it is general information
        elif options.debug_log or (event_type == 'Event' and level >= logging.INFO):
            print(msg_print)

        # Save it if we are debugging
        if options.debug_log:
            with codecs.open(EVENT_FILE, 'a', encoding='utf-8') as fh:
                fh.write(msg + '\n')


    def _prune(self, event_type):
        if event_type not in self._log:
            return  # We cannot prune

        if event_type == 'Run':
            self.clear_runs(False)
        else:
            # Delete everything older than 1 day
            current_time = datetime.datetime.now()
            while len(self._log[event_type]) > 0 and \
                    current_time - self._log[event_type][0]['time'] > datetime.timedelta(days=1):
                del self._log[event_type][0]

    def start_run(self, interval):
        """Indicates a certain run has been started. The start time will be updated."""
        with self._lock:
            # Update time with current time
            interval = interval.copy()
            interval['start'] = datetime.datetime.now()
            interval['active'] = True

            self._log['Run'].append({
                'time': datetime.datetime.now(),
                'level': logging.INFO,
                'data': interval
            })

            fmt_dict = interval.copy()
            fmt_dict['asctime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            fmt_dict['start'] = fmt_dict['start'].strftime("%Y-%m-%d %H:%M:%S")
            fmt_dict['end'] = fmt_dict['end'].strftime("%Y-%m-%d %H:%M:%S")

            self._save_log(RUN_START_FORMAT % fmt_dict, logging.DEBUG, 'Run')
            self._prune('Run')

    def finish_run(self, interval):
        """Indicates a certain run has been stopped. Use interval=None to stop all active runs.
        The stop time(s) will be updated with the current time."""
        with self._lock:
            if isinstance(interval, str) or interval is None:
                uid = interval
            elif isinstance(interval, dict) and 'uid' in interval:
                uid = interval['uid']
            else:
                raise ValueError

            for entry in self._log['Run']:
                if (uid is None or entry['data']['uid'] == uid) and entry['data']['active']:
                    entry['data']['end'] = datetime.datetime.now()
                    entry['data']['active'] = False

                    fmt_dict = entry['data'].copy()
                    fmt_dict['asctime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
                    fmt_dict['start'] = fmt_dict['start'].strftime("%Y-%m-%d %H:%M:%S")
                    fmt_dict['end'] = fmt_dict['end'].strftime("%Y-%m-%d %H:%M:%S")

                    self._save_log(RUN_FINISH_FORMAT % fmt_dict, logging.DEBUG, 'Run')
                    if uid is not None:
                        break

            self._prune('Run')

    def active_runs(self):
        return [run['data'].copy() for run in self._log['Run'] if run['data']['active']]

    def finished_runs(self):
        return [run['data'].copy() for run in self._log['Run'] if not run['data']['active']]

    def log_event(self, event_type, message, level=logging.INFO, format_msg=True):
        if threading.current_thread().__class__.__name__ != '_MainThread' and time.time() < self._plugin_time:
            time.sleep(self._plugin_time - time.time())
        with self._lock:
            if level >= self.level:
                if event_type not in self._log:
                    self._log[event_type] = []

                self._log[event_type].append({
                    'time': datetime.datetime.now(),
                    'level': level,
                    'data': message
                })
                if options.debug_log and format_msg:
                    stack = traceback.extract_stack()
                    filename = ''
                    lineno = 0
                    for tb in reversed(stack):
                        filename = path.basename(tb[0])
                        lineno = tb[1]
                        if path.abspath(tb[0]) != path.abspath(__file__):
                            break

                    fmt_dict = {
                        'asctime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3],
                        'levelname': logging.getLevelName(level),
                        'event_type': event_type,
                        'filename': filename,
                        'lineno': lineno,
                        'message': message
                    }

                    message = EVENT_FORMAT % fmt_dict

                self._save_log(message, level, event_type)
                self._prune(event_type)

    def debug(self, event_type, message):
        self.log_event(event_type, message, logging.DEBUG)

    def info(self, event_type, message):
        self.log_event(event_type, message, logging.INFO)

    def warning(self, event_type, message):
        self.log_event(event_type, message, logging.WARNING)

    def error(self, event_type, message):
        self.log_event(event_type, message, logging.ERROR)

    def clear_runs(self, all_entries=True):
        from ospy.programs import programs, ProgramType
        from ospy.stations import stations
        if all_entries or not options.run_log:  # User request or logging is disabled
            minimum = 0
        elif options.run_entries > 0:
            minimum = options.run_entries
        else:
            return  # We should not prune in this case

        # determine the start of the first active run:
        first_start = min([datetime.datetime.now()] + [interval['start'] for interval in self.active_runs()])
        min_eto = datetime.date.today() + datetime.timedelta(days=1)
        for program in programs.get():
            if program.type == ProgramType.WEEKLY_WEATHER:
                for station in program.stations:
                    min_eto = min(min_eto, min([datetime.date.today() - datetime.timedelta(days=7)] + stations.get(station).balance.keys()))

        # Now try to remove as much as we can
        for index in reversed(xrange(len(self._log['Run']) - minimum)):
            interval = self._log['Run'][index]['data']

            delete = True
            # If this entry cannot have influence on the current state anymore:
            if (first_start - interval['end']).total_seconds() <= max(options.station_delay + options.min_runtime,
                                                                      options.master_off_delay,
                                                                      60):
                delete = False
            elif interval['end'].date() >= min_eto:
                delete = False

            if delete:
                del self._log['Run'][index]

        self._save_logs()

    def clear(self, event_type):
        if event_type != 'Run':
            self._log[event_type] = []

    def event_types(self):
        return self._log.keys()

    def events(self, event_type):
        return [evt['data'] for evt in self._log.get(event_type, [])]

    def emit(self, record):
        if not hasattr(record, 'event_type'):
            record.event_type = 'Event'

        txt = self.format(record) if options.debug_log else record.getMessage()
        self.log_event(record.event_type, txt, record.levelno, False)


class _LogEM():
    def __init__(self):
        self._logEM = {
            'RunEM': options.logged_email[:]
        }
        self._lock = threading.RLock()


    def finished_email(self):
        try:
            for option in options.OPTIONS:
                if 'key' in option:
                   name = option['key']
                   if name == 'logged_email':
                      value = options[option['key']]
                      return(value)

        except Exception:
            print_report('log.py', traceback.format_exc())
            pass
            return []

    def _save_logsEM(self):
        result = []
        if options.run_logEM:
            result = self._logEM['RunEM']
        options.logged_email = result

    def clear_email(self, all_entries=True):
        if all_entries or not options.run_logEM:  # User request or logging is disabled
            minimum = 0
        elif options.run_entriesEM > 0:
            minimum = options.run_entriesEM
        else:
            return  # We should not prune in this case

        for index in reversed(xrange(len(self._logEM['RunEM']) - minimum)):
            interval = self._logEM['RunEM'][index]
            del self._logEM['RunEM'][index]

        self._save_logsEM()

    def save_email_log(self, subject, body, status):  
        subject_print = subject.encode('utf-8')
        body_print = body.encode('utf-8')
        status_print = status.encode('utf-8')

        with self._lock:
            self._logEM['RunEM'].append({
                'time': datetime.datetime.now().strftime("%H:%M:%S"),
                'date': datetime.datetime.now().strftime("%Y-%m-%d"),
                'subject': subject_print,
                'body': body_print,
                'status': status_print
            })
        
            self._save_logsEM()     # save email
            self.clear_email(False) # count only options.run_entriesEM


log = _Log()
logEM = _LogEM()

log.setFormatter(logging.Formatter(EVENT_FORMAT))


def hook_logging():
    _logger = logging.getLogger()
    _logger.setLevel(logging.DEBUG)
    _logger.propagate = False
    _logger.handlers = [log]

    # Don't care about debug and info messages of markdown:
    _markdown_logger = logging.getLogger('MARKDOWN')
    _markdown_logger.setLevel(logging.WARNING)
