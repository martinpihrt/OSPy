#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

import shelve
import web
import os

# Local imports
from ospy.options import options
from ospy.scheduler import scheduler
from ospy.reverse_proxied import reverse_proxied

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
    web.config.debug = False  # Improves page load speed', ]

    #### SSL for https #### http://www.8bitavenue.com/2015/05/webpy-ssl-support/
    ssl_patch = '././ssl/'
    if options.use_ssl:
       try:
          if os.path.isfile(ssl_patch + 'server.crt') and os.path.isfile(ssl_patch + 'server.key') :
             print 'SSL certificate OK starting HTTPS.'
             from web.wsgiserver import CherryPyWSGIServer
             CherryPyWSGIServer.ssl_certificate = "././ssl/server.crt"
             CherryPyWSGIServer.ssl_private_key = "././ssl/server.key"

       except:
          print 'SSL certificate not found.'
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

    __server = web.httpserver.WSGIServer(("0.0.0.0", options.web_port), wsgifunc)
    __server.timeout = 1  # Speed-up restarting

    sessions = shelve.open(os.path.join('ospy', 'data', 'sessions.db'))
    session = web.session.Session(app, web.session.ShelfStore(sessions),
                                  initializer={'validated': False,
                                               'pages': []})

    import atexit
    atexit.register(sessions.close)

    def exit_msg():
        print 'OSPy is closing, saving sessions.'
    atexit.register(exit_msg)

    scheduler.start()
    plugins.start_enabled_plugins()

    try:
        __server.start()
    except (KeyboardInterrupt, SystemExit):
        stop()


def stop():
    global __server
    if __server is not None:
        __server.stop()
        __server = None
