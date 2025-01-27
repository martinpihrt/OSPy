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

stats = usagestats.Stats('./ospy/statistics/',
                         optin_prompt,
                         'https://pihrt.com/ospystats/php_server.php',
                         unique_user_id=True,
                         version='0.1'
                         )

__server = None
session = None


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
    ssl_patch_fullchain = '/etc/letsencrypt/live/' + options.domain_ssl + '/fullchain.pem' 
    ssl_patch_privkey   = '/etc/letsencrypt/live/' + options.domain_ssl + '/privkey.pem'   

    # for own SSL certificate in OSPy folder
    ssl_own_patch_fullchain =  '././ssl/fullchain.pem'
    ssl_own_patch_privkey   =  '././ssl/privkey.pem'

    if options.use_ssl and not options.use_own_ssl:
       try:
           if os.path.isfile(ssl_patch_fullchain) and os.path.isfile(ssl_patch_privkey):
               log.debug('server.py', _('Files: fullchain.pem and privkey.pem found, try starting HTTPS.'))

               # web.py 0.40 version
               from cheroot.server import HTTPServer
               from cheroot.ssl.builtin import BuiltinSSLAdapter

               HTTPServer.ssl_adapter = BuiltinSSLAdapter(
               certificate = ssl_patch_fullchain,  
               private_key = ssl_patch_privkey)   

               log.debug('server.py', _('SSL OK.'))
           else:
               log.debug('server.py', _('SSL Files: fullchain.pem and privkey.pem not found, starting only HTTP!'))

       except:
           log.debug('server.py', traceback.format_exc())
           pass
    
    if options.use_own_ssl and not options.use_ssl:
       try:
           if os.path.isfile(ssl_own_patch_fullchain) and os.path.isfile(ssl_own_patch_privkey):
                log.debug('server.py', _('Own SSL Files: fullchain.pem and privkey.pem found, try starting HTTPS.'))

                from cheroot.server import HTTPServer
                from cheroot.ssl.builtin import BuiltinSSLAdapter

                HTTPServer.ssl_adapter = BuiltinSSLAdapter(
                certificate = ssl_own_patch_fullchain,  
                private_key = ssl_own_patch_privkey)   

                log.debug('server.py', _('Own SSL OK.'))
           else:
               log.debug('server.py', _('Own SSL Files: fullchain.pem and privkey.pem not found, starting only HTTP!'))

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
    
    log.debug('server.py', _('Starting sensors timer...'))
    sensors_timer.start()    

    if net_connect():
        create_statistics()

    print_report('server.py', _('OSPy is ready'))
    log.debug('server.py', _('OSPy is ready'))
    logEV.save_events_log( _('Server'), _('Starting'), id='Server')

    try:
        __server.start()
    except (KeyboardInterrupt, SystemExit):
        stop()


def close_sessions():
    global sessions
    if sessions is not None:
        try:
            log.debug('server.py', _('OSPy is closing, saving sessions.'))
            logEV.save_events_log(_('Server'), _('Stopping'), id='Server')
            log.debug('server.py', _('Closing shelve database.'))

            # Check if shelve database is corrupted
            def is_shelve_corrupted(file_path):
                try:
                    with shelve.open(file_path) as test_shelve:
                        pass
                    return False
                except Exception:
                    return True

            session_file = os.path.join('ospy', 'data', 'sessions.db')
            if is_shelve_corrupted(session_file):
                log.error('server.py', _('Shelve database is corrupted. Removing...'))
                for db_file in glob.glob(session_file + '*'):
                    try:
                        os.remove(db_file)
                        log.debug('server.py', _('Removed corrupted session file: {}').format(db_file))
                    except Exception as rm_e:
                        log.error('server.py', _('Error removing corrupted session file {}: {}').format(db_file, rm_e))

            sessions.close()
            log.debug('server.py', _('Shelve database closed successfully.'))
        except Exception as e:
            log.error('server.py', _('Error closing shelve database: {}').format(e))
   
def stop():
    global __server
    if __server is not None:
        logEV.save_events_log( _('Server'), _('Stopping'), id='Server')
        __server.stop()
        __server = None
        close_sessions()


def create_statistics():
    try:
        log.debug('server.py', _('Creating statistics...'))

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
        )

    except:
        log.debug('server.py', traceback.format_exc())
        pass