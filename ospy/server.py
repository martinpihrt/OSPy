#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = 'Rimco' # modify: Martin Pihrt

import shelve
import web
import os
import glob
import traceback
import subprocess
import time as time_module
from threading import Timer, Lock
from blinker import signal

# Local imports
from ospy.options import options
from ospy.scheduler import scheduler

import plugins

from ospy.reverse_proxied import reverse_proxied
from ospy.log import log, logEV
from ospy.helpers import print_report, net_connect

from socket import gethostname
from pprint import pprint
from time import gmtime, mktime
from os.path import exists, join

# statistics generating
from ospy import usagestats
from ospy import version
import sys

# sensors
from ospy.sensors import sensors_timer

optin_prompt = usagestats.Prompt(enable='cool_program --enable-stats',
                                 disable='cool_program --disable-stats')

STATS_LOCATION = './ospy/statistics/'
STATS_DROP_POINT = 'https://pihrt.com/ospystats/php_server.php'
STATS_VERSION = '0.1'
STATS_RETRY_INTERVAL = 6 * 60 * 60
SESSION_SECRET_FILE = os.path.join('ospy', 'data', 'session_secret')
SESSION_SECRET_LENGTH = 64

__server = None
session = None
sessions = None
statistics_timer = None
statistics_lock = Lock()
sessions_lock = Lock()
shutdown_lock = Lock()
_stopping = False
CORE_STOP_TIMEOUT = 5.0
PLUGIN_STOP_TIMEOUT = 10.0


def _new_stats():
    return usagestats.Stats(STATS_LOCATION,
                            optin_prompt,
                            STATS_DROP_POINT,
                            unique_user_id=True,
                            version=STATS_VERSION
                            )


def configure_session_secret():
    try:
        secret_dir = os.path.dirname(SESSION_SECRET_FILE)
        if not os.path.isdir(secret_dir):
            os.makedirs(secret_dir)

        if os.path.isfile(SESSION_SECRET_FILE):
            with open(SESSION_SECRET_FILE, 'r') as secret_file:
                secret = secret_file.read().strip()
            if len(secret) >= 32:
                web.config.session_parameters.secret_key = secret
                return

            log.error('server.py', _('Session secret file is invalid, generating a new one.'))

        secret = os.urandom(SESSION_SECRET_LENGTH).hex()
        with open(SESSION_SECRET_FILE, 'w') as secret_file:
            secret_file.write(secret)
        try:
            os.chmod(SESSION_SECRET_FILE, 0o600)
        except Exception:
            log.debug('server.py', _('Could not set permissions on session secret file.'))

        web.config.session_parameters.secret_key = secret
        log.debug('server.py', _('Generated a new installation-specific session secret.'))
    except Exception:
        log.error('server.py', _('Could not load or create session secret, using default fallback.'))
        log.debug('server.py', traceback.format_exc())


class DebugLogMiddleware:
    """WSGI middleware for logging the status."""
    def __init__(self, app):
        self.app = app
        self.format = '%s "%s %s %s" - %s'

    def __call__(self, environ, start_response):
        def xstart_response(status, response_headers, *args):
            out = start_response(status, response_headers, *args)
            self.log(status, environ)
            try:
                return out
            except:
                log.error('server.py', _('An error occurred') + ':\n' + traceback.format_exc())
                start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
                msg = _('An internal error was found in the system, see the error log for more information. The error is called in part:') + ' '
                msg += _('server.py -> DebugLogMiddleware')
                return msg

        return self.app(environ, xstart_response)

    def log(self, status, environ):
        req = environ.get('PATH_INFO', '_')
        protocol = environ.get('ACTUAL_SERVER_PROTOCOL', '-')
        method = environ.get('REQUEST_METHOD', '-')
        host = "%s:%s" % (environ.get('REMOTE_ADDR', '-'),
                          environ.get('REMOTE_PORT', '-'))

        msg = self.format % (host, protocol, method, req, status)
        log.debug('server.py', web.utils.safestr(msg))


class PluginStaticMiddleware(web.httpserver.StaticMiddleware):
    """WSGI middleware for serving static plugin files.
    This ensures all URLs starting with /plugins/static/plugin_name or /plugins/script/plugin_name are mapped correctly."""

    def __call__(self, environ, start_response):
        upath = environ.get('PATH_INFO', '')
        upath = self.normpath(upath)
        words = upath.split('/')

        try:
            if len(words) >= 4 and words[1] == 'plugins' and words[3] == 'static':
                return web.httpserver.StaticApp(environ, start_response)
            elif len(words) >= 4 and words[1] == 'plugins' and words[3] == 'script':
                return web.httpserver.StaticApp(environ, start_response)
            else:
                return self.app(environ, start_response)
        except:
            log.error('server.py', _('An error occurred') + ':\n' + traceback.format_exc())
            start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
            msg = _('An internal error was found in the system, see the error log for more information. The error is called in part:') + ' '
            msg += _('server.py -> PluginStaticMiddleware')
            return msg


def start():
    global __server
    global session
    global sessions

    import time
    
    if net_connect():
        log.debug('server.py', _('Network connection is available, Im skipping waiting.'))
    else:
        log.debug('server.py', _('Network connection not available, waiting 20 seconds.'))
        wait = 20
        while(wait > 0):
            wait = wait-1
            time.sleep(1)
            if net_connect():
                break
                log.debug('server.py', _('Network connection is available.'))

    ##############################
    #### web.py setup         ####
    ##############################
    if options.web_log:
        web.config.debug = True   # Deteriorates page loading speed
    else:
        web.config.debug = False  # Improves page load speed

    #### SSL for https #### http://webpy.org/cookbook/ssl  

    # for SSL certificate via letsencrypt
    ssl_patch_fullchain = None
    ssl_patch_privkey = None
    if options.domain_ssl:
        configured_domain_ssl = str(options.domain_ssl).strip()
        domain_ssl = os.path.basename(configured_domain_ssl)
        if domain_ssl == configured_domain_ssl and '/' not in domain_ssl and '\\' not in domain_ssl:
            ssl_patch_fullchain = os.path.join('/etc', 'letsencrypt', 'live', domain_ssl, 'fullchain.pem')
            ssl_patch_privkey = os.path.join('/etc', 'letsencrypt', 'live', domain_ssl, 'privkey.pem')
        else:
            log.error('server.py', _('Invalid SSL domain name, starting only HTTP.'))

    # for own SSL certificate in OSPy folder
    ssl_own_patch_fullchain = os.path.join('.', 'ssl', 'fullchain.pem')
    ssl_own_patch_privkey = os.path.join('.', 'ssl', 'privkey.pem')

    web.config.session_parameters.secure = False

    if options.use_own_ssl:
       try:
           if os.path.isfile(ssl_own_patch_fullchain) and os.path.isfile(ssl_own_patch_privkey):
                log.debug('server.py', _('Own SSL Files: fullchain.pem and privkey.pem found, try starting HTTPS.'))

                from cheroot.server import HTTPServer
                from cheroot.ssl.builtin import BuiltinSSLAdapter

                HTTPServer.ssl_adapter = BuiltinSSLAdapter(
                certificate = ssl_own_patch_fullchain,
                private_key = ssl_own_patch_privkey)
                web.config.session_parameters.secure = True

                log.debug('server.py', _('Own SSL OK.'))
           else:
               log.debug('server.py', _('Own SSL Files: fullchain.pem and privkey.pem not found, starting only HTTP!'))

       except:
           log.debug('server.py', traceback.format_exc())
           pass

    elif options.use_ssl:
       try:
           if ssl_patch_fullchain and ssl_patch_privkey and os.path.isfile(ssl_patch_fullchain) and os.path.isfile(ssl_patch_privkey):
               log.debug('server.py', _('Files: fullchain.pem and privkey.pem found, try starting HTTPS.'))

               # web.py 0.40 version
               from cheroot.server import HTTPServer
               from cheroot.ssl.builtin import BuiltinSSLAdapter

               HTTPServer.ssl_adapter = BuiltinSSLAdapter(
               certificate = ssl_patch_fullchain,  
               private_key = ssl_patch_privkey)   
               web.config.session_parameters.secure = True

               log.debug('server.py', _('SSL OK.'))
           else:
               log.debug('server.py', _('SSL Files: fullchain.pem and privkey.pem not found, starting only HTTP!'))

       except:
           log.debug('server.py', traceback.format_exc())
           pass

    #############################

    from ospy.urls import urls
    app = web.application(urls, globals())
    app.notfound = lambda: web.seeother('/', True)

    wsgifunc = app.wsgifunc()
    wsgifunc = web.httpserver.StaticMiddleware(wsgifunc)
    wsgifunc = PluginStaticMiddleware(wsgifunc)
    wsgifunc = DebugLogMiddleware(wsgifunc)
    wsgifunc = reverse_proxied(wsgifunc)

    __server = web.httpserver.WSGIServer((options.HTTP_web_ip, options.web_port), wsgifunc)
    __server.timeout = 1  # Speed-up restarting

    sessions = None
    session_file = os.path.join('ospy', 'data', 'sessions.db')
    log.debug('server.py', _('Opening shelve database at {}').format(session_file))

    try:
        sessions = shelve.open(session_file)
        log.debug('server.py', _('Successfully opened shelve database.'))

        # Test to see if we can read the data
        for s in sessions:
            try:
                str(sessions[s])
            except Exception as e:
                log.error('server.py', _('Error reading session data for key {}: {}').format(s, e))

    except Exception as e:
        log.error('server.py', _('Exception occurred while opening or reading shelve database: {}').format(e))
        if sessions is not None:
            try:
                sessions.close()
            except Exception as close_e:
                log.error('server.py', _('Error closing shelve database: {}').format(close_e))

        # Remove corrupted session files
        for db_file in glob.glob(session_file + '*'):
            try:
                log.debug('server.py', _('Remove corrupted session files') + ': {}'.format(db_file))
                os.remove(db_file)
            except Exception as rm_e:
                log.error('server.py', _('Error removing corrupted session file {}: {}').format(db_file, rm_e))
    
        # Re-attempt to open the shelve database
        try:    
            sessions = shelve.open(session_file)
            log.debug('server.py', _('Re-opened shelve database after cleanup.'))
        except Exception as re_open_e:
            log.error('server.py', _('Exception occurred while re-opening shelve database: {}').format(re_open_e))
    
    configure_session_secret()

    session = web.session.Session(app, web.session.ShelfStore(sessions),
                                  initializer={'validated': False,
                                               'pages': [],
                                               'category': 'public',
                                               'visitor': 'Unknown'
                                               })
    try:         
        if 'category' not in session:
            session['category'] = 'public'
            log.debug('server.py', _('Category is not in session, initializing it.'))
        if not session['category']:
            session['category'] = 'public'
            log.debug('server.py', _('Category is empty, setting it to public.'))

        if 'visitor' not in session:
            session['visitor'] = 'Unknown'
            log.debug('server.py', _('Visitor-operator is not in session, initializing it.'))
        if not session['visitor']:
            session['visitor'] = 'Unknown'
            log.debug('server.py', _('Visitor is empty, setting it to Unknown visitor.'))
    except Exception as e:
        log.error('server.py', traceback.format_exc())
        session['category'] = 'public'
        session['visitor'] = 'Unknown'

    log.debug('server.py', _('Starting scheduler and plugins...'))
    scheduler.start()
    plugins.start_enabled_plugins()
    from ospy import webpages
    webpages.start_diagnostics_history()
    
    log.debug('server.py', _('Starting sensors timer...'))
    sensors_timer.start()    

    create_statistics(upload=net_connect())
    schedule_statistics_retry()

    print_report('server.py', _('OSPy is ready'))
    log.debug('server.py', _('OSPy is ready'))
    logEV.save_events_log(_('Server'), _('Starting'), id='Server', level='success', category='system')

    try:
        __server.start()
    except (KeyboardInterrupt, SystemExit):
        stop()


def close_sessions():
    global sessions
    with sessions_lock:
        if sessions is not None:
            try:
                log.debug('server.py', _('OSPy is closing, saving sessions.'))
                logEV.save_events_log(_('Server'), _('Stopping'), id='Server', level='info', category='system')
                log.debug('server.py', _('Closing shelve database.'))
                sessions.close()
                sessions = None
                log.debug('server.py', _('Shelve database closed successfully.'))
            except Exception as e:
                log.error('server.py', _('Error closing shelve database: {}').format(e))


def reset_session_store(remove_files=False):
    """Close and re-open the session store while OSPy keeps running."""
    global sessions

    session_file = os.path.join('ospy', 'data', 'sessions.db')
    with sessions_lock:
        if sessions is not None:
            try:
                sessions.close()
            except Exception as e:
                log.error('server.py', _('Error closing session database before reset: {}').format(e))
            sessions = None

        if remove_files:
            for db_file in glob.glob(session_file + '*'):
                try:
                    os.remove(db_file)
                    log.debug('server.py', _('Removed session file: {}').format(db_file))
                except Exception as e:
                    log.error('server.py', _('Error removing session file {}: {}').format(db_file, e))

        sessions = shelve.open(session_file)
        if session is not None:
            session.store = web.session.ShelfStore(sessions)
        log.info('server.py', _('Session database has been reset.'))
   
def _safe_stop_outputs():
    """Clear scheduled runs and force every physical output to its safe state."""
    try:
        from ospy.programs import programs
        programs.run_now_program = None
    except Exception:
        log.error('server.py', traceback.format_exc())
    try:
        from ospy.runonce import run_once
        run_once.clear()
    except Exception:
        log.error('server.py', traceback.format_exc())
    try:
        from ospy.log import log as run_log
        run_log.finish_run(None)
    except Exception:
        log.error('server.py', traceback.format_exc())
    try:
        from ospy.stations import stations
        stations.clear()
    except Exception:
        log.error('server.py', traceback.format_exc())
    try:
        from ospy.outputs import outputs
        outputs.relay_output = False
    except Exception:
        log.error('server.py', traceback.format_exc())


def _core_workers():
    from ospy.weather import weather
    return (scheduler, sensors_timer, weather, plugins.checker)


def _request_core_stop():
    for worker in _core_workers():
        try:
            worker.request_stop()
        except Exception:
            log.error('server.py', traceback.format_exc())


def _wait_for_core_stop(timeout=CORE_STOP_TIMEOUT):
    deadline = time_module.time() + max(0.0, float(timeout))
    failed = []
    for worker in _core_workers():
        try:
            remaining = max(0.0, deadline - time_module.time())
            if not worker.wait_stopped(remaining):
                failed.append(worker.name or worker.__class__.__name__)
        except Exception:
            failed.append(getattr(worker, 'name', worker.__class__.__name__))
            log.error('server.py', traceback.format_exc())
    return failed


def stop():
    global __server
    global statistics_timer
    global _stopping

    with shutdown_lock:
        if _stopping:
            return
        _stopping = True

    try:
        if statistics_timer is not None:
            statistics_timer.cancel()
            statistics_timer = None

        try:
            from ospy import webpages
            webpages.stop_diagnostics_history()
        except Exception:
            log.debug('server.py', traceback.format_exc())

        # Stop accepting web work before shutting down its dependencies.
        if __server is not None:
            logEV.save_events_log(_('Server'), _('Stopping'), id='Server', level='info', category='system')
            try:
                __server.stop()
            except Exception:
                log.error('server.py', traceback.format_exc())
            __server = None

        # Signal all core loops together, then make outputs safe immediately.
        _request_core_stop()
        _safe_stop_outputs()

        try:
            failed_plugins = plugins.stop_all_plugins(PLUGIN_STOP_TIMEOUT)
            if failed_plugins:
                log.error(
                    'server.py',
                    _('Plug-in threads did not stop in time') + ': ' +
                    ', '.join(failed_plugins)
                )
        except Exception:
            log.error('server.py', traceback.format_exc())

        # A plug-in stop function may have touched an output; enforce the safe
        # state once more after all plug-in callbacks have returned.
        _safe_stop_outputs()
        failed_workers = _wait_for_core_stop(CORE_STOP_TIMEOUT)
        if failed_workers:
            log.error(
                'server.py',
                _('Background threads did not stop in time') + ': ' +
                ', '.join(failed_workers)
            )
        _safe_stop_outputs()

        try:
            options.flush()
        except Exception:
            log.error('server.py', traceback.format_exc())
        close_sessions()
    finally:
        # Keep stop idempotent for the lifetime of this process. Core Thread
        # instances cannot be started for a second time; restart creates a new
        # process through helpers.restart().
        _stopping = True


def flush_statistics_queue():
    try:
        if not net_connect():
            return

        with statistics_lock:
            stats = _new_stats()
            stats.enable_reporting()
            stats.flush_pending()
    except:
        log.debug('server.py', traceback.format_exc())
        pass


def schedule_statistics_retry():
    global statistics_timer
    try:
        if statistics_timer is not None:
            statistics_timer.cancel()

        statistics_timer = Timer(STATS_RETRY_INTERVAL, statistics_retry)
        statistics_timer.daemon = True
        statistics_timer.start()
    except:
        log.debug('server.py', traceback.format_exc())
        pass


def statistics_retry():
    flush_statistics_queue()
    schedule_statistics_retry()


def notify_statistics_internet_available(name=None, **kw):
    flush_statistics_queue()


signal('internet_available').connect(notify_statistics_internet_available)


def create_statistics(upload=True):
    try:
        log.debug('server.py', _('Creating statistics...'))

        stats = _new_stats()
        stats.enable_reporting()
        stats.note({'mode': 'compatibility'})
        ospyFW = 'version ' + str(version.ver_str) + ' date ' + str(version.ver_date)
        ospyNUM = version.ver_str

        stats.submit(
        {'ospyfw': ospyFW,           # OSPy version
         'ospynum': ospyNUM          # OSPy version only numeric ver
        },          
        usagestats.OPERATING_SYSTEM,  # Operating system/distribution
        usagestats.PYTHON_VERSION,    # Python version info
        usagestats.SESSION_TIME,      # Time since Stats object was created
        upload=upload
        )

    except:
        log.debug('server.py', traceback.format_exc())
        pass
