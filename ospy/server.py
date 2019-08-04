#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco' # edited: 'Martin Pihrt' 

import shelve
import web
import os
import traceback

# Local imports
from ospy.options import options
from ospy.scheduler import scheduler
from ospy.reverse_proxied import reverse_proxied
from ospy.log import log

# SSL generating
from OpenSSL import crypto, SSL
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
    web.config.debug = False  # Improves page load speed', ]

    #### SSL for https #### http://webpy.org/cookbook/ssl
    ssl_patch = '././ssl/'

    if options.use_ssl:
       try:
          if not os.path.isfile(ssl_patch + 'server.crt') and not os.path.isfile(ssl_patch + 'server.key'):
             create_self_signed_cert(ssl_patch)

          if os.path.isfile(ssl_patch + 'server.crt') and os.path.isfile(ssl_patch + 'server.key'):
             log.info('server.py', 'Files: server.crt and server.key found, try starting HTTPS.')

             # web.py 0.40 version
             from cheroot.server import HTTPServer
             from cheroot.ssl.builtin import BuiltinSSLAdapter

             HTTPServer.ssl_adapter = BuiltinSSLAdapter(
             certificate= ssl_patch + 'server.crt', 
             private_key= ssl_patch + 'server.key')

             log.info('server.py', 'SSL OK.')

          else:
             log.info('server.py', 'SSL Files: server.crt and server.key nofound, starting HTTP!')

       except:
          log.info('server.py', traceback.format_exc())
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
                                               'pages': []})
    create_statistics()

    import atexit
    atexit.register(sessions.close)

    def exit_msg():
        log.info('server.py', 'OSPy is closing, saving sessions.') 
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


def create_self_signed_cert(cert_dir):
    """
    If server.crt and server.key don't exist in cert_dir, create a new
    self-signed cert and keypair and write them into that directory.
    """

    CERT_FILE = "server.crt"
    KEY_FILE = "server.key"

    if not exists(join(cert_dir, CERT_FILE)) or not exists(join(cert_dir, KEY_FILE)):
        try:
            log.info('server.py', 'SSL Creating a key pair...') 
            k = crypto.PKey()
            k.generate_key(crypto.TYPE_RSA, 2048)

            log.info('server.py', 'SSL Creating a self-signed cert...')
            cert = crypto.X509()
            cert.get_subject().C = "CR"
            cert.get_subject().ST = "PRAGUE"
            cert.get_subject().L = "PRAGUE"
            cert.get_subject().O = "OSPY-FW"
            cert.get_subject().OU = "www.pihrt.com"
            cert.get_subject().CN = gethostname()
            cert.get_subject().emailAddress = "admin@pihrt.com"
            cert.set_serial_number(1000)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(10*365*24*60*60)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(k)
            cert.sign(k, 'sha256')

            log.info('server.py', 'SSL Writing files...') 
            open(join(cert_dir, CERT_FILE), "wt").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            open(join(cert_dir, KEY_FILE), "wt").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

            log.info('server.py', 'OK')

        except Exception:
                log.error('server.py', traceback.format_exc())


def create_statistics():
    try:
        log.info('server.py', 'Creating statistics...')

        stats.enable_reporting()
        stats.note({'mode': 'compatibility'})
        ospyFW = 'version ' + str(version.ver_str) + ' date ' + str(version.ver_date)

        stats.submit(
        {'ospyfw': ospyFW},           # OSPy version
        usagestats.OPERATING_SYSTEM,  # Operating system/distribution
        usagestats.PYTHON_VERSION,    # Python version info
        usagestats.SESSION_TIME,      # Time since Stats object was created
        )

    except Exception:
        log.error('server.py', traceback.format_exc())
