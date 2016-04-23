#!/usr/bin/env python
# -*- coding: utf-8 -*-

# System imports
import os
import datetime
import json
import web

# Local imports
from ospy.helpers import test_password, template_globals, check_login, save_to_options, \
    password_hash, password_salt, get_input, get_help_files, get_help_file, restart
from ospy.inputs import inputs
from ospy.log import log
from ospy.options import options
from ospy.options import rain_blocks
from ospy.programs import programs
from ospy.programs import ProgramType
from ospy.runonce import run_once
from ospy.stations import stations
from ospy import scheduler
import plugins

from web import form


signin_form = form.Form(
    form.Password('password', description='Password:'),
    validators=[
        form.Validator(
            "Incorrect password, please try again",
            lambda x: test_password(x["password"])
        )
    ]
)


class InstantCacheRender(web.template.render):
    '''This class immediately starts caching all templates in the given location.'''
    def __init__(self, loc='templates', cache=None, base=None, limit=None, exclude=None, **keywords):
        web.template.render.__init__(self, loc, cache, base, **keywords)

        self._limit = limit
        self._exclude = exclude

        from threading import Thread
        t = Thread(target=self._fill_cache)
        t.daemon = True
        t.start()

    def _fill_cache(self):
        import time
        if os.path.isdir(self._loc):
            for name in os.listdir(self._loc):
                if name.endswith('.html') and \
                        (self._limit is None or name[:-5] in self._limit) and \
                        (self._exclude is None or name[:-5] not in self._exclude):
                    self._template(name[:-5])
                    time.sleep(0.1)


class WebPage(object):
    base_render = InstantCacheRender(os.path.join('ospy', 'templates'),
                                     globals=template_globals(), limit=['base']).base
    core_render = InstantCacheRender(os.path.join('ospy', 'templates'),
                                     globals=template_globals(), exclude=['base'], base=base_render)

    def __init__(self):
        cls = self.__class__

        from ospy.server import session
        if not cls.__name__.endswith('json') and (not session.pages or session.pages[-1] != web.ctx.fullpath):
            session.pages.append(web.ctx.fullpath)
        while len(session.pages) > 5:
            del session.pages[0]

        if self.__module__.startswith('plugins') and 'plugin_render' not in cls.__dict__:
            cls.plugin_render = InstantCacheRender(os.path.join(os.path.join(*self.__module__.split('.')), 'templates'), globals=template_globals(), base=self.base_render)

    @staticmethod
    def _redirect_back():
        from ospy.server import session
        for page in reversed(session.pages):
            if page != web.ctx.fullpath:
                raise web.seeother(page)
        raise web.seeother('/')


class ProtectedPage(WebPage):
    def __init__(self):
        WebPage.__init__(self)
        try:
            check_login(True)
        except web.seeother:
            raise


class login_page(WebPage):
    """Login page"""

    def GET(self):
        if check_login(False):
            raise web.seeother('/')
        else:
            return self.core_render.login(signin_form())

    def POST(self):
        my_signin = signin_form()

        if not my_signin.validates():
            return self.core_render.login(my_signin)
        else:
            from ospy import server
            server.session.validated = True
            self._redirect_back()


class logout_page(WebPage):
    def GET(self):
        from ospy import server
        server.session.kill()
        raise web.seeother('/')


class home_page(ProtectedPage):
    """Open Home page."""

    def GET(self):
        return self.core_render.home()


class action_page(ProtectedPage):
    """Page to perform some simple actions (mainly from the homepage)."""

    def GET(self):
        from ospy import server
        qdict = web.input()

        stop_all = get_input(qdict, 'stop_all', False, lambda x: True)
        scheduler_enabled = get_input(qdict, 'scheduler_enabled', None, lambda x: x == '1')
        manual_mode = get_input(qdict, 'manual_mode', None, lambda x: x == '1')
        rain_block = get_input(qdict, 'rain_block', None, float)
        level_adjustment = get_input(qdict, 'level_adjustment', None, float)
        toggle_temp = get_input(qdict, 'toggle_temp', False, lambda x: True)

        if stop_all:
            if not options.manual_mode:
                options.scheduler_enabled = False
                programs.run_now_program = None
                run_once.clear()
            log.finish_run(None)
            stations.clear()

        if scheduler_enabled is not None:
            options.scheduler_enabled = scheduler_enabled

        if manual_mode is not None:
            options.manual_mode = manual_mode

        if rain_block is not None:
            options.rain_block = datetime.datetime.now() + datetime.timedelta(hours=rain_block)

        if level_adjustment is not None:
            options.level_adjustment = level_adjustment / 100

        if toggle_temp:
            options.temp_unit = "F" if options.temp_unit == "C" else "C"

        set_to = get_input(qdict, 'set_to', None, int)
        sid = get_input(qdict, 'sid', 0, int) - 1
        set_time = get_input(qdict, 'set_time', 0, int)

        if set_to is not None and 0 <= sid < stations.count() and options.manual_mode:
            if set_to:  # if status is on
                start = datetime.datetime.now()
                new_schedule = {
                    'active': True,
                    'program': -1,
                    'station': sid,
                    'program_name': "Manual",
                    'fixed': True,
                    'cut_off': 0,
                    'manual': True,
                    'blocked': False,
                    'start': start,
                    'original_start': start,
                    'end': start + datetime.timedelta(days=3650),
                    'uid': '%s-%s-%d' % (str(start), "Manual", sid),
                    'usage': stations.get(sid).usage
                }
                if set_time > 0:  # if an optional duration time is given
                    new_schedule['end'] = datetime.datetime.now() + datetime.timedelta(seconds=set_time)

                log.start_run(new_schedule)
                stations.activate(new_schedule['station'])

            else:  # If status is off
                stations.deactivate(sid)
                active = log.active_runs()
                for interval in active:
                    if interval['station'] == sid:
                        log.finish_run(interval)

        self._redirect_back()

class programs_page(ProtectedPage):
    """Open programs page."""

    def GET(self):
        qdict = web.input()
        delete_all = get_input(qdict, 'delete_all', False, lambda x: True)
        if delete_all:
            while programs.count() > 0:
                programs.remove_program(programs.count()-1)
        return self.core_render.programs()


class program_page(ProtectedPage):
    """Open page to allow program modification."""

    def GET(self, index):
        qdict = web.input()
        try:
            index = int(index)
            delete = get_input(qdict, 'delete', False, lambda x: True)
            runnow = get_input(qdict, 'runnow', False, lambda x: True)
            enable = get_input(qdict, 'enable', None, lambda x: x == '1')
            if delete:
                programs.remove_program(index)
                raise web.seeother('/programs')
            elif runnow:
                programs.run_now(index)
                raise web.seeother('/programs')
            elif enable is not None:
                programs[index].enabled = enable
                raise web.seeother('/programs')
        except ValueError:
            pass

        if isinstance(index, int):
            program = programs.get(index)
        else:
            program = programs.create_program()
            program.set_days_simple(6*60, 30, 30, 0, [])

        return self.core_render.program(program)

    def POST(self, index):
        qdict = web.input()
        try:
            index = int(index)
            program = programs.get(index)
        except ValueError:
            program = programs.create_program()

        qdict['schedule_type'] = int(qdict['schedule_type'])

        program.name = qdict['name']
        program.stations = json.loads(qdict['stations'])
        program.enabled = True if qdict.get('enabled', 'off') == 'on' else False
        program.cut_off = int(qdict['cut_off'])
        program.fixed = True if qdict.get('fixed', 'off') == 'on' else False

        simple = [int(qdict['simple_hour']) * 60 + int(qdict['simple_minute']),
                  int(qdict['simple_duration']),
                  int(qdict['simple_pause']),
                  int(qdict['simple_rcount']) if qdict.get('simple_repeat', 'off') == 'on' else 0]

        repeat_start_date = datetime.datetime.combine(datetime.date.today(), datetime.time.min) + \
                            datetime.timedelta(days=int(qdict['interval_delay']))

        if qdict['schedule_type'] == ProgramType.DAYS_SIMPLE:
            program.set_days_simple(*(simple + [
                                    json.loads(qdict['days'])]))

        elif qdict['schedule_type'] == ProgramType.DAYS_ADVANCED:
            program.set_days_advanced(json.loads(qdict['advanced_schedule_data']),
                                      json.loads(qdict['days']))

        elif qdict['schedule_type'] == ProgramType.REPEAT_SIMPLE:
            program.set_repeat_simple(*(simple + [
                                      int(qdict['interval']),
                                      repeat_start_date]))

        elif qdict['schedule_type'] == ProgramType.REPEAT_ADVANCED:
            program.set_repeat_advanced(json.loads(qdict['advanced_schedule_data']),
                                        int(qdict['interval']),
                                        repeat_start_date)

        elif qdict['schedule_type'] == ProgramType.WEEKLY_ADVANCED:
            program.set_weekly_advanced(json.loads(qdict['weekly_schedule_data']))

        elif qdict['schedule_type'] == ProgramType.CUSTOM:
            program.modulo = int(qdict['interval'])*1440
            program.manual = False
            program.start = repeat_start_date
            program.schedule = json.loads(qdict['custom_schedule_data'])

        if program.index < 0:
            programs.add_program(program)

        raise web.seeother('/programs')


class runonce_page(ProtectedPage):
    """Open a page to view and edit a run once program."""

    def GET(self):
        return self.core_render.runonce()

    def POST(self):
        qdict = web.input()
        station_seconds = {}
        for station in stations.enabled_stations():
            mm_str = "mm" + str(station.index)
            ss_str = "ss" + str(station.index)
            if mm_str in qdict and ss_str in qdict:
                seconds = int(qdict[mm_str] or 0) * 60 + int(qdict[ss_str] or 0)
                station_seconds[station.index] = seconds

        run_once.set(station_seconds)
        raise web.seeother('/')


class plugins_manage_page(ProtectedPage):
    """Manage plugins page."""

    def GET(self):
        qdict = web.input()
        plugin = get_input(qdict, 'plugin', None)
        delete = get_input(qdict, 'delete', False, lambda x: True)
        enable = get_input(qdict, 'enable', None, lambda x: x == '1')
        disable_all = get_input(qdict, 'disable_all', False, lambda x: True)
        auto_update = get_input(qdict, 'auto', None, lambda x: x == '1')
        use_update = get_input(qdict, 'use', None, lambda x: x == '1')

        if disable_all:
            options.enabled_plugins = []
            plugins.start_enabled_plugins()

        if plugin is not None and plugin in plugins.available():
            if delete:
                enable = False

            if enable is not None:
                if not enable and plugin in options.enabled_plugins:
                    options.enabled_plugins.remove(plugin)
                elif enable and plugin not in options.enabled_plugins:
                    options.enabled_plugins.append(plugin)
                options.enabled_plugins = options.enabled_plugins  # Explicit write to save to file
                plugins.start_enabled_plugins()

            if delete:
                from ospy.helpers import del_rw
                import shutil
                shutil.rmtree(os.path.join('plugins', plugin), onerror=del_rw)

            raise web.seeother('/plugins_manage')

        if auto_update is not None:
            options.auto_plugin_update = auto_update
            raise web.seeother('/plugins_manage')
        
        if use_update is not None:
            options.use_plugin_update = use_update
            raise web.seeother('/plugins_manage')    

        return self.core_render.plugins_manage()


class plugins_install_page(ProtectedPage):
    """Manage plugins page."""

    def GET(self):
        qdict = web.input()
        repo = get_input(qdict, 'repo', None, int)
        plugin = get_input(qdict, 'plugin', None)
        install = get_input(qdict, 'install', False, lambda x: True)

        if install and repo is not None:
            plugins.checker.install_repo_plugin(plugins.REPOS[repo], plugin)
            self._redirect_back()

        plugins.checker.update()
        return self.core_render.plugins_install()

    def POST(self):
        qdict = web.input(zipfile={})

        zip_file_data = qdict['zipfile'].file
        plugins.checker.install_custom_plugin(zip_file_data)

        self._redirect_back()


class log_page(ProtectedPage):
    """View Log"""

    def GET(self):
        qdict = web.input()
        if 'clear' in qdict:
            log.clear_runs()
            raise web.seeother('/log')

        if 'csv' in qdict:
            events = log.finished_runs() + log.active_runs()
            data = "Date, Start Time, Zone, Duration, Program\n"
            for interval in events:
                # return only records that are visible on this day:
                duration = (interval['end'] - interval['start']).total_seconds()
                minutes, seconds = divmod(duration, 60)

                data += ', '.join([
                    interval['start'].strftime("%Y-%m-%d"),
                    interval['start'].strftime("%H:%M:%S"),
                    str(interval['station']),
                    "%02d:%02d" % (minutes, seconds),
                    interval['program_name']
                ]) + '\n'

            web.header('Content-Type', 'text/csv')
            web.header('Content-Disposition', 'attachment; filename="log.csv"')
            return data

        return self.core_render.log()


class options_page(ProtectedPage):
    """Open the options page for viewing and editing."""

    def GET(self):
        qdict = web.input()
        errorCode = qdict.get('errorCode', 'none')

        return self.core_render.options(errorCode)

    def POST(self):
        qdict = web.input()

        save_to_options(qdict)

        if 'master' in qdict:
            m = int(qdict['master'])
            if m < 0:
                stations.master = None
            elif m < stations.count():
                stations.master = m

        if 'old_password' in qdict and qdict['old_password'] != "":
            try:
                if test_password(qdict['old_password']):
                    if qdict['new_password'] == "":
                        raise web.seeother('/options?errorCode=pw_blank')
                    elif qdict['new_password'] == qdict['check_password']:
                        options.password_salt = password_salt()  # Make a new salt
                        options.password_hash = password_hash(qdict['new_password'], options.password_salt)
                    else:
                        raise web.seeother('/options?errorCode=pw_mismatch')
                else:
                    raise web.seeother('/options?errorCode=pw_wrong')
            except KeyError:
                pass

        raise web.seeother('/')


class stations_page(ProtectedPage):
    """Stations page"""

    def GET(self):
        return self.core_render.stations()

    def POST(self):
        qdict = web.input()

        for s in xrange(0, stations.count()):
            stations[s].name = qdict["%d_name" % s]
            stations[s].usage = float(qdict.get("%d_usage" % s, 1.0))
            stations[s].enabled = True if qdict.get("%d_enabled" % s, 'off') == 'on' else False
            stations[s].ignore_rain = True if qdict.get("%d_ignore_rain" % s, 'off') == 'on' else False
            if stations.master is not None or options.master_relay:
                stations[s].activate_master = True if qdict.get("%d_activate_master" % s, 'off') == 'on' else False

        raise web.seeother('/')

class help_page(ProtectedPage):
    """Stations page"""

    def GET(self):
        qdict = web.input()
        id = get_input(qdict, 'id')
        if id is not None:
            web.header('Content-Type', 'text/html')
            return get_help_file(id)

        docs = get_help_files()
        return self.core_render.help(docs)

class download_page(ProtectedPage):
    """Download OSPy DB file with settings"""
    def GET(self):
       OPTIONS_FILE = './ospy/data/options.db'

       def _read_log():
          """Read OSPy DB file"""
          try:                
             logf = open(OPTIONS_FILE,'r')
             return logf.read()
          except IOError:
             return []

       try:
          import mimetypes
         
          download_name = 'options.db'
          content = mimetypes.guess_type(OPTIONS_FILE)[0]
          web.header('Content-type', content)
          web.header('Content-Length', os.path.getsize(OPTIONS_FILE))    
          web.header('Content-Disposition', 'attachment; filename=%s'%download_name)
          return _read_log()
          raise web.seeother('/')

       except Exception:
          return self.core_render.home()


class upload_page(ProtectedPage):
    """Upload OSPy DB file with settings"""
    
    def GET(self):
        raise web.seeother('/')

    def POST(self):
        OPTIONS_FILE = './ospy/data/options.db'
        i = web.input(uploadfile={})
        if i.uploadfile.filename == 'options.db':
            fout = open(OPTIONS_FILE,'w') 
            fout.write(i.uploadfile.file.read()) 
            fout.close() 
            log.debug('webpages.py', 'Uploading and saving options.db file sucesfully, now restarting OSPy...')
            restart(3)
            return self.core_render.restarting(home_page)
        self._redirect_back()
        
################################################################################
# APIs                                                                         #
################################################################################
class api_status_json(ProtectedPage):
    """Simple Status API"""

    def GET(self):
        statuslist = []
        for station in stations.get():
            if station.enabled or station.is_master:
                status = {
                    'station': station.index,
                    'status': 'on' if station.active else 'off',
                    'reason': 'master' if station.is_master else '',
                    'master': 1 if station.is_master else 0,
                    'programName': '',
                    'remaining': 0}

                if not station.is_master:
                    if options.manual_mode:
                        status['programName'] = 'Manual Mode'
                    else:
                        if station.active:
                            active = log.active_runs()
                            for interval in active:
                                if not interval['blocked'] and interval['station'] == station.index:
                                    status['programName'] = interval['program_name']

                                    status['reason'] = 'program'
                                    status['remaining'] = max(0, (interval['end'] -
                                                                  datetime.datetime.now()).total_seconds())
                        elif not options.scheduler_enabled:
                            status['reason'] = 'system_off'
                        elif not station.ignore_rain and inputs.rain_sensed():
                            status['reason'] = 'rain_sensed'
                        elif not station.ignore_rain and rain_blocks.seconds_left():
                            status['reason'] = 'rain_delay'

                statuslist.append(status)

        web.header('Content-Type', 'application/json')
        return json.dumps(statuslist)


class api_log_json(ProtectedPage):
    """Simple Log API"""

    def GET(self):
        qdict = web.input()
        data = []
        if 'date' in qdict:
            # date parameter filters the log values returned; "yyyy-mm-dd" format
            date = datetime.datetime.strptime(qdict['date'], "%Y-%m-%d").date()
            check_start = datetime.datetime.combine(date, datetime.time.min)
            check_end = datetime.datetime.combine(date, datetime.time.max)
            log_start = check_start - datetime.timedelta(days=1)
            log_end = check_end + datetime.timedelta(days=1)

            events = scheduler.combined_schedule(log_start, log_end)
            for interval in events:
                # Return only records that are visible on this day:
                if check_start <= interval['start'] <= check_end or check_start <= interval['end'] <= check_end:
                    data.append(self._convert(interval))

        web.header('Content-Type', 'application/json')
        return json.dumps(data)

    def _convert(self, interval):
            duration = (interval['end'] - interval['start']).total_seconds()
            minutes, seconds = divmod(duration, 60)
            return {
                'program': interval['program'],
                'program_name': interval['program_name'],
                'active': interval['active'],
                'manual': interval.get('manual', False),
                'fixed': True,
                'cut_off': interval['cut_off'],
                'blocked': interval.get('blocked', False),
                'station': interval['station'],
                'date': interval['start'].strftime("%Y-%m-%d"),
                'start': interval['start'].strftime("%H:%M:%S"),
                'duration': "%02d:%02d" % (minutes, seconds)
            }
