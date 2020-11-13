# -*- coding: utf-8 -*-
from __future__ import print_function
__author__ = 'Rimco' # edited: 'Martin Pihrt' 

import shelve
import web
import os
import traceback
import subprocess

# Local imports
from ospy.options import options
from ospy.scheduler import scheduler
from ospy.reverse_proxied import reverse_proxied
from ospy.log import log
from ospy.helpers import print_report
	
from socket import gethostname
from pprint import pprint
from time import gmtime, mktime
from os.path import exists, join

# statistics generating
from ospy import usagestats
from ospy import version
import sys

optin_prompt = usagestats.Prompt(enable='cool_program --enable-stats',
                                 disable='cool_program --disable-stats')

stats = usagestats.Stats('./ospy/statistics/',
                         optin_prompt,
                         'https://pihrt.com/ospystats/php_server.php',
                         unique_user_id=True,
                         version='0.1'
                         )
         
import plugins

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
            return out

        return self.app(environ, xstart_response)

    def log(self, status, environ):
        import logging

        req = environ.get('PATH_INFO', '_')
        protocol = environ.get('ACTUAL_SERVER_PROTOCOL', '-')
        method = environ.get('REQUEST_METHOD', '-')
        host = "%s:%s" % (environ.get('REMOTE_ADDR', '-'),
                          environ.get('REMOTE_PORT', '-'))

        msg = self.format % (host, protocol, method, req, status)
        logging.debug(web.utils.safestr(msg))


class PluginStaticMiddleware(web.httpserver.StaticMiddleware):
    """WSGI middleware for serving static plugin files.
    This ensures all URLs starting with /plugins/static/plugin_name are mapped correctly."""

    def __call__(self, environ, start_response):
        upath = environ.get('PATH_INFO', '')
        upath = self.normpath(upath)
        words = upath.split('/')

        if len(words) >= 4 and words[1] == 'plugins' and words[3] == 'static':
            return web.httpserver.StaticApp(environ, start_response)
        else:
            return self.app(environ, start_response)


def start():
    global __server
    global session

    ##############################
    #### web.py setup         ####
    ##############################
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
               log.info('server.py', _(u'Files: fullchain.pem and privkey.pem found, try starting HTTPS.'))
               print_report('server.py', _(u'Files: fullchain.pem and privkey.pem found, try starting HTTPS.'))

               # web.py 0.40 version
               from cheroot.server import HTTPServer
               from cheroot.ssl.builtin import BuiltinSSLAdapter

               HTTPServer.ssl_adapter = BuiltinSSLAdapter(
               certificate = ssl_patch_fullchain,  
               private_key = ssl_patch_privkey)   

               log.info('server.py', _(u'SSL OK.'))
               print_report('server.py', _(u'SSL OK.'))

           else:
               log.info('server.py', _(u'SSL Files: fullchain.pem and privkey.pem not found, starting only HTTP!'))
               print_report('server.py', _(u'SSL Files: fullchain.pem and privkey.pem not found, starting only HTTP!'))

       except:
           log.info('server.py', traceback.format_exc())
           print_report('server.py', traceback.format_exc())
           pass       
    
    if options.use_own_ssl and not options.use_ssl:
       try:
           if os.path.isfile(ssl_own_patch_fullchain) and os.path.isfile(ssl_own_patch_privkey):
               log.info('server.py', _(u'Own SSL Files: fullchain.pem and privkey.pem found, try starting HTTPS.'))
               print_report('server.py', _(u'Own SSL Files: fullchain.pem and privkey.pem found, try starting HTTPS.'))

               # web.py 0.40 version
               from cheroot.server import HTTPServer
               from cheroot.ssl.builtin import BuiltinSSLAdapter

               HTTPServer.ssl_adapter = BuiltinSSLAdapter(
               certificate = ssl_own_patch_fullchain,  
               private_key = ssl_own_patch_privkey)   

               log.info('server.py', _(u'Own SSL OK.'))
               print_report('server.py', _(u'Own SSL OK.'))

           else:
               log.info('server.py', _(u'Own SSL Files: fullchain.pem and privkey.pem not found, starting only HTTP!'))
               print_report('server.py', _(u'Own SSL Files: fullchain.pem and privkey.pem not found, starting only HTTP!'))

       except:
           log.info('server.py', traceback.format_exc())
           print_report('server.py', traceback.format_exc())
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

    sessions = shelve.open(os.path.join('ospy', 'data', 'sessions.db'))
    session = web.session.Session(app, web.session.ShelfStore(sessions),
                                  initializer={'validated': False,
                                               'pages': [],
                                               'category': u'public',
                                               'visitor': _(u'Unknown operator')})
    try:
        if not session['category']:
            session['category'] = 'public'
            print_report('server.py', _(u'Category is not in session, adding to sessions.'))
        if not session['visitor']:
            session['visitor'] = _(u'Unknown visitor')
            print_report('server.py', _(u'Visitor-operator is not in session, adding to sessions.'))            
    except:
        session['category'] = 'public'
        session['visitor'] = _(u'Unknown visitor')
        pass
                                               
    import atexit
    atexit.register(sessions.close)

    def exit_msg():
        log.info('server.py', _(u'OSPy is closing, saving sessions.')) 
        print_report('server.py', _(u'OSPy is closing, saving sessions.'))
    atexit.register(exit_msg)

    print_report('server.py', _(u'Starting scheduler and plugins...'))
    scheduler.start()
    plugins.start_enabled_plugins()

    create_statistics()
    print_report('server.py', _(u'Ready'))

    try:
        __server.start()
    except (KeyboardInterrupt, SystemExit):
        stop()   

   
def stop():
    global __server
    if __server is not None:
        __server.stop()
        __server = None


def create_statistics():
    try:
        log.info('server.py', _(u'Creating statistics...'))
        print_report('server.py', _(u'Creating statistics...'))

        stats.enable_reporting()
        stats.note({'mode': 'compatibility'})
        ospyFW = 'version ' + str(version.ver_str) + ' date ' + str(version.ver_date)
        ospyNUM = version.ver_str

        stats.submit(
        {'ospyfw': ospyFW,            # OSPy version
         'ospynum': ospyNUM           # OSPy version only numeric ver
        },          
        usagestats.OPERATING_SYSTEM,  # Operating system/distribution
        usagestats.PYTHON_VERSION,    # Python version info
        usagestats.SESSION_TIME,      # Time since Stats object was created
        )

    except Exception:
        log.error('server.py', traceback.format_exc())
        print_report('server.py', traceback.format_exc())
        