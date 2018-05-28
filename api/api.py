
__author__ = 'Teodor Yantcheff'

from utils import *

from ospy import version
from ospy.stations import stations
from ospy.options import options, level_adjustments
from ospy.programs import programs, ProgramType
from ospy.log import log
from ospy import helpers


logger = logging.getLogger('OSPyAPI')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(name)s:%(levelname)s:%(message)s'))
#handler.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s'))
logger.addHandler(handler)


class Stations(object):

    def _station_to_dict(self, station):
        # This is automatic and over all the keys that a _Station has
        # return {k: getattr(station, k) for k in dir(station) if not k.startswith('_') and k is not 'SAVE_EXCLUDE'}

        return {
            'id': station.index,  # TODO: Exchange index for URI ?
            'name': station.name,
            'enabled': station.enabled,
            'ignore_rain': station.ignore_rain,
            'is_master': station.is_master,
            'activate_master': station.activate_master,
            'remaining_seconds': station.remaining_seconds,
            'running': station.active
        }

    def _dict_to_station(self, sid, data):
        for k, v in data.iteritems():
            logger.debug('stationid:{} key:\'{}\' value:\'{}\''.format(sid, k, v))
            try:
                stations[sid].__setattr__(k, v)
            except:
                logger.exception('Error setting station %d, \'%s\' to \'%s\'', sid, k, v)

    @does_json
    def GET(self, station_id=None):
        logger.debug('GET /stations/{}'.format(station_id if station_id else ''))
        if station_id:
            return self._station_to_dict(stations[int(station_id)])
        else:
            l = [self._station_to_dict(s) for s in stations]
            # stations_type = type(stations).__name__  # .strip('_')
            # return {'type': stations_type, 'stations': l}
            return l

    @auth
    @does_json
    def POST(self, station_id=None):
        logger.debug('POST /stations/{}'.format(station_id if station_id else ''))

        action = web.input().get('do', '').lower()
        station_id = int(station_id)
        if action == 'start':
            logger.debug('Starting station {id} ("{name}")'.format(id=station_id, name=stations[station_id].name))
            stations.activate(station_id)
        elif action == 'stop':
            logger.debug('Stopping station {id} ("{name}")'.format(id=station_id, name=stations[station_id].name))
            stations.deactivate(station_id)
        else:
            logger.error('Unknown station action: "%s"', action)
            raise badrequest()

        return self._station_to_dict(stations[station_id])

    @auth
    @does_json
    def PUT(self, station_id=None):
        logger.debug('PUT /stations/{}'.format(station_id if station_id else ''))
        update = json.loads(web.data())
        if station_id:
            station_id = int(station_id)
            self._dict_to_station(station_id, update)
            return self._station_to_dict(stations[station_id])
        else:
            for sid, upd in enumerate(update):
                self._dict_to_station(sid, upd)
            return [self._station_to_dict(s) for s in stations]

    @auth
    @does_json
    def DELETE(self, station_id=None):
        logger.debug('DELETE /stations/{}'.format(station_id if station_id else ''))
        raise web.nomethod()

    def OPTIONS(self, station_id=None):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')


class Programs(object):

    def _program_to_dict(self, program):
        # return {k: getattr(program, k) for k in dir(program) if not k.startswith('_') and k is not 'SAVE_EXCLUDE'}
        return {
            'id': program.index,
            'name': program.name,
            'stations': program.stations,
            'enabled': program.enabled,
            'type': program.type,
            'type_name': ProgramType.NAMES.get(program.type, ''),
            'type_data': program.type_data,
            'summary': program.summary(),
            'schedule': program.schedule,
            'modulo': program.modulo,
            'manual': program.manual,
            'start': program.start,
        }

    def _dict_to_program(self, prog, data):
        set_method_table = {
            ProgramType.DAYS_SIMPLE: prog.set_days_simple,
            ProgramType.REPEAT_SIMPLE: prog.set_repeat_simple,
            ProgramType.DAYS_ADVANCED: prog.set_days_advanced,
            ProgramType.REPEAT_ADVANCED: prog.set_repeat_advanced,
            ProgramType.WEEKLY_ADVANCED: prog.set_weekly_advanced,
            ProgramType.WEEKLY_WEATHER: prog.set_weekly_weather
        }

        for k, v in data.iteritems():
            logger.debug('Setting program property key:\'%s\' to value:\'%s\'', k, v)
            try:
                if k not in self.EXCLUDED_KEYS:
                    prog.__setattr__(k, v)
            except:
                logger.exception('Error setting program property key:\'%s\' to value:\'%s\'', k, v)

            if prog.type is ProgramType.CUSTOM:
                # CUSTOM
                prog.modulo = data['modulo']
                prog.manual = False
                try:
                    prog.start = datetime.fromtimestamp(data['start'])
                except:
                    prog.start = datetime.now()
                prog.schedule = data['schedule']
            else:
                # All other types
                program_set = set_method_table[prog.type]
                program_set(*data['type_data'])

    def __init__(self):
        self.EXCLUDED_KEYS = [
            'type_name', 'summary', 'schedule'
        ]

    @does_json
    def GET(self, program_id):
        logger.debug('GET /programs/{}'.format(program_id if program_id else ''))

        if program_id:
            program_id = int(program_id)
            return self._program_to_dict(programs[program_id])
        else:
            return [self._program_to_dict(p) for p in programs]

    @auth
    @does_json
    def POST(self, program_id):
        logger.debug('POST /programs/{}'.format(program_id if program_id else ''))

        if program_id:
            action = web.input().get('do', '').lower()
            program_id = int(program_id)
            if action == 'runnow':
                logger.debug('Starting program {id} ("{name}")'.format(id=program_id, name=programs[program_id].name))
                programs.run_now(program_id)
            elif action == 'stop':
                pass  # TODO
            else:
                logger.error('Unknown program action: "%s"', action)
                raise badrequest()
            return self._program_to_dict(programs[program_id])
        else:
            program_data = json.loads(web.data())

            p = programs.create_program()
            p.type = program_data.get('type', ProgramType.DAYS_SIMPLE)
            if p.type == ProgramType.DAYS_SIMPLE:
                p.set_days_simple(0, 30, 0, 0, [])  # some sane defaults

            self._dict_to_program(p, program_data)  # some sane defaults

            # p.enabled = False
            programs.add_program(p)
            return self._program_to_dict(programs.get(p.index))

    @auth
    @does_json
    def PUT(self, program_id):
        logger.debug('PUT /programs/{}'.format(program_id if program_id else ''))
        if program_id:
            program_id = int(program_id)
            program_data = json.loads(web.data())
            self._dict_to_program(programs[program_id], program_data)

            return self._program_to_dict(programs[program_id])
        else:
            raise badrequest()

    @auth
    @does_json
    def DELETE(self, program_id):
        logger.debug('DELETE /programs/{}'.format(program_id if program_id else ''))
        if program_id:
            programs.remove_program(int(program_id))
        else:
            while programs.count() > 0:
                programs.remove_program(programs.count()-1)

    def OPTIONS(self, program_id):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')


class Options(object):

    def __init__(self):
        """ Stuff that is not to be sent over the API, assuming it's of no interest to potential clients"""
        self.EXCLUDED_OPTIONS = [
            'password_hash', 'password_salt', 'theme', 'logged_runs', 'time_format'
        ]

        """ Options array in the format
          <option_key> : {
                            'name': OPTIONS[option_key]['name']
                            'help': OPTIONS[option_key]['help']
                            .
                            .
                         }
        """
        self.ANNOTATED_OPTIONS = {
            key: {
                opt_key: options.OPTIONS[i].get(opt_key, '')
                for opt_key in ['name', 'help', 'category', 'default', 'min', 'max']
            }
            for i, key in enumerate(options.get_options()) if key not in self.EXCLUDED_OPTIONS
        }

    @does_json
    def GET(self):
        logger.debug('GET ' + self.__class__.__name__)
        a = web.input().get('annotated', '').lower()
        if a in ['true', 'yes', 'annotated', '1']:
            opts = {o: {'value': options[o]} for o in self.ANNOTATED_OPTIONS}
            for k in opts.iterkeys():
                # "inject" current option value into the dictionary under "value"
                opts[k].update(self.ANNOTATED_OPTIONS[k])
            return opts
        else:
            return {opt: options[opt] for opt in options.get_options() if opt not in self.EXCLUDED_OPTIONS}

    @auth
    # @does_json
    def PUT(self):
        logger.debug('PUT ' + self.__class__.__name__)
        update = json.loads(web.data())
        all_options = options.get_options()
        for key, val in update.iteritems():
            if key in all_options and key not in self.EXCLUDED_OPTIONS:
                try:
                    options[key] = val
                except:
                    logger.error('Error updating \'%s\' to \'%s\'', key, val)
                    raise badrequest('{"error": "Error setting option \'{}\' to \'{}\'"}'.format(key, val))
            else:
                logger.debug('Skipping key {}'.format(key))
        return self.GET()

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS')


class Logs(object):

    def _runlog_to_dict(self, log_entry):
        return {
            'start': log_entry['start'],
            'end': log_entry['end'],
            'duration': str(log_entry['end'] - log_entry['start']).split('.')[0],  # pass it as a baked string to the client
            'manual': log_entry['manual'],
            'station': log_entry['station'],
            'station_name': stations[log_entry['station']].name,
            'program_id': log_entry['program'],
            'program_name': log_entry['program_name'],
        }

    @does_json
    def GET(self):
        logger.debug('GET logs ' + self.__class__.__name__)
        return [self._runlog_to_dict(fr) for fr in log.finished_runs()]
        # web.header('Cache-Control', 'no-cache')
        # web.header('Content-Type', 'application/json')
        # web.header('Access-Control-Allow-Origin', '*')
        # import datetime
        # return datetime.datetime.now()
        # return '[{"start": "2014-10-23T21:25:25", "station": 2, "end": "2014-10-23T21:25:30", "duration": "0:00:05", "station_name": "Station 03ttt", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": "2014-10-23T21:25:30", "station": 3, "end": "2014-10-23T21:25:35", "duration": "0:00:05", "station_name": "Station 04 dest", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": "2014-10-23T21:25:35", "station": 4, "end": "2014-10-23T21:25:40", "duration": "0:00:05", "station_name": "Station 05", "manual": true, "program_name": "Run-Once", "program_id": -1}]'
        # return '[{"start": 1414605866, "station": 0, "end": 1414605881, "duration": "0:00:15", "station_name": "Station 01", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": 1414605881, "station": 2, "end": 1414605896, "duration": "0:00:15", "station_name": "Station 03", "manual": true, "program_name": "Run-Once", "program_id": -1}, {"start": 1414605896, "station": 5, "end": 1414605911, "duration": "0:00:15", "station_name": "Station 06", "manual": true, "program_name": "Run-Once", "program_id": -1}]'

    @auth
    @does_json
    def DELETE(self):
        logger.debug('DELETE ' + self.__class__.__name__)
        log.clear_runs()

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, DELETE, OPTIONS')


class System(object):
    @does_json
    def GET(self):
        logger.debug('GET ' + self.__class__.__name__)
        return {
            'version': version.ver_str,
            'CPU_temperature': helpers.get_cpu_temp(),
            'release_date': version.ver_date,
            'uptime': helpers.uptime(),
            'platform': helpers.determine_platform(),
            'rpi_revision': helpers.get_rpi_revision(),
            'total_adjustment': level_adjustments.total_adjustment()
        }

    @auth
    @does_json
    def POST(self):
        logger.debug('POST ' + self.__class__.__name__)
        action = web.input().get('do', '').lower()

        if action == 'reboot':
            logger.info('System reboot requested via API')
            helpers.reboot()

        elif action == 'restart':
            logger.info('OSPy service restart requested via API')
            helpers.restart()

        elif action == 'poweroff':
            logger.info('System poweroff requested via API')
            helpers.poweroff()

        else:
            logger.error('Unknown system action: "%s"', action)
            raise badrequest()

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Headers', 'Content-Type')
        web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')

def get_app():
    urls = (
        # Stations
        r'/stations(?:/(?P<station_id>\d+))?/?', 'Stations',
        # Programs
        r'/programs(?:/(?P<program_id>\d+))?/?', 'Programs',
        # Options
        r'/options/?', 'Options',
        # Logs
        r'/logs/?', 'Logs',
        # System
        r'/system/?', 'System',
    )
    return web.application(urls, globals())
