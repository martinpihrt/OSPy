from __future__ import absolute_import
__author__ = 'Teodor Yantcheff' # Changed: Martin Pihrt (Fixed for logging. Added support for sensors.)


import base64
from functools import wraps, partial
from datetime import datetime
import time
import json
import re

import web

from .errors import badrequest, unauthorized

from ospy.helpers import test_password
from ospy.options import options
from ospy.log import log


# datetime to timestamp conversion function
def to_timestamp(dt):
    try:
        return int(time.mktime(dt.timetuple()))
    except:
        return 0


#  Converts local time to UTC time
def local_to_utc(dt):
    try:
        TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        local = dt.strftime(TIME_FORMAT)
        # print "local_to_utc: before convert:", local
        timestamp = str(time.mktime(datetime.strptime(local, TIME_FORMAT).timetuple()))[:-2]
        utc = datetime.utcfromtimestamp(int(timestamp))
        # print "local_to_utc: after convert:", utc
        return utc
    except:
        return dt


# jsonify dates
_json_dumps = partial(json.dumps,
                      # default=lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x),
                      # default=lambda x: local_to_utc(x).isoformat() if hasattr(x, 'isoformat') else str(x),
                      default=lambda x: to_timestamp(x) if hasattr(x, 'isoformat') else str(x),
                      sort_keys=False)


def does_json(func):
    """
    api function jsonificator
    Takes care of IndexError and ValueError so that the decorated code can igrnore those
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Set headers
        web.header('Cache-Control', 'no-cache')
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin', '*')

        # This calls the decorated method
        try:
            r = func(*args, **kwargs)
            if r:
                # Take care of JSONP
                params = web.input(callback=None)
                if params.callback:
                    # Wrap the response in JSONP format
                    r = "{callback}({json});".format(callback=params.callback,
                                                     json=_json_dumps(r))
                    return r
                else:
                    # Just jsonify the response
                    return _json_dumps(r)
            else:
                return ''

        except IndexError as e:  # No such item
            log.error('utils.py',  _(u'Error: (IndexError) Index out of bounds {}').format(e.message))
            raise badrequest('{"error": "(IndexError) Index out of bounds - ' + e.message + '"}')

        except ValueError as e:  # json errors
            log.error('utils.py',  _(u'Error: (ValueError) Inappropriate argument value {}').format(e.message))
            raise badrequest('{"error": "(ValueError) Inappropriate argument value - ' + e.message + '"}')
            # raise badrequest(format(e.message))

        except KeyError as e:  # missing attribute names
            log.error('utils.py',  _(u'Error: (KeyError) Missing key {}').format(e.message))
            raise badrequest('{"error": "(KeyError) Missing key - ' + e.message + '"}')
            # raise badrequest(format(e.message))

    return wrapper


def auth(func):
    """
    HTTP Basic authentication wrapper
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not options.no_password:
            username = password = ''
            try:
                auth_data = web.ctx.env.get('HTTP_AUTHORIZATION')
                assert auth_data, 'No authentication data provided'

                http_auth = re.sub('^Basic ', '', auth_data)
                username, password = base64.decodestring(http_auth).split(':')
                log.debug('utils.py',  _(u'API Auth Attempt with: user: {} password: {}').format(username, password))
                assert test_password(password, username), 'Wrong password'
                # if (username, password) not in dummy_users:
                #     raise  # essentially a goto :P
            except:
                # no or wrong auth provided
                log.debug('utils.py',  _(u'API Unauthorized attempt user: {} password: {}').format(username, password))
                web.header('WWW-Authenticate', 'Basic realm="OSPy"')
                raise unauthorized()

        return func(*args, **kwargs)
        
    return wrapper


# class JSONAppBrowser(web.browser.AppBrowser):
#     """
#     JSON-ified AppBrowser
#     """
#     # TODO: tests
#
#     headers = {'Accept': 'application/json'}
#
#     def json_open(self, url, data=None, headers={}, method='GET'):
#         headers = headers or self.headers
#         url = urllib.basejoin(self.url, url)
#         req = urllib2.Request(url, json.dumps(data), headers)
#         req.get_method = lambda: method  # Fake urllub's get_method
#         return self.do_request(req)
#
#     @property
#     def json_data(self):
#         return json.loads(self.data)