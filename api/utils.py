__author__ = 'Teodor Yantcheff' 


import base64
from functools import wraps, partial
import datetime
import time
import json
import re
import traceback
from threading import Lock

import web

from .errors import badrequest, unauthorized

from ospy.helpers import bruteforce_blocked, test_password, print_report
from ospy.helpers import verify_csrf
from ospy.options import options
from ospy.log import log, logEV
from ospy import server


_API_AUTH_EVENT_LOCK = Lock()
_API_AUTH_EVENT_TIMES = {}


def _api_request_ip():
    try:
        return web.ctx.env.get('REMOTE_ADDR', '-')
    except Exception:
        return '-'


def _save_api_security_event(key, subject, status, level='warning'):
    """Write an API security event at most once per key and minute."""
    current_time = time.time()
    with _API_AUTH_EVENT_LOCK:
        if current_time - _API_AUTH_EVENT_TIMES.get(key, 0) < 60:
            return
        _API_AUTH_EVENT_TIMES[key] = current_time
        if len(_API_AUTH_EVENT_TIMES) > 500:
            stale = [item for item, saved in _API_AUTH_EVENT_TIMES.items()
                     if current_time - saved > 3600]
            for item in stale:
                del _API_AUTH_EVENT_TIMES[item]
    logEV.save_events_log(
        subject,
        status,
        id='Login',
        level=level,
        category='security'
    )



# datetime to timestamp conversion function
def to_timestamp(dt):
    try:
        if isinstance(dt, datetime.date):
            dt = datetime.datetime.combine(dt, datetime.datetime.min.time())
        return int(dt.timestamp())
    except:
        print_report('utils.py', traceback.format_exc())
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
        print_report('utils.py', traceback.format_exc())
        return dt


# jsonify dates
_json_dumps = partial(json.dumps,
                      # default=lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x),
                      # default=lambda x: local_to_utc(x).isoformat() if hasattr(x, 'isoformat') else str(x),
                      default=lambda x: to_timestamp(x) if hasattr(x, 'isoformat') else str(x),
                      sort_keys=False)


def _api_cors_origin():
    configured = getattr(options, 'api_cors_allowed_origin', '*')
    configured = configured.strip() if isinstance(configured, str) else '*'
    if not configured:
        return None
    if configured == '*':
        return '*'

    request_origin = web.ctx.env.get('HTTP_ORIGIN', '') if hasattr(web.ctx, 'env') else ''
    allowed_origins = [origin.strip() for origin in configured.split(',') if origin.strip()]
    if request_origin and request_origin in allowed_origins:
        return request_origin
    if request_origin:
        return None
    return allowed_origins[0] if allowed_origins else None


def set_api_headers(methods=None):
    origin = _api_cors_origin()
    if origin:
        web.header('Access-Control-Allow-Origin', origin)
        if origin != '*':
            web.header('Vary', 'Origin')
    if methods:
        web.header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        web.header('Access-Control-Allow-Methods', methods)


def _valid_jsonp_callback(callback):
    return re.match(r'^[A-Za-z_$][0-9A-Za-z_$]*(\.[A-Za-z_$][0-9A-Za-z_$]*)*$', callback)


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
        set_api_headers()

        # This calls the decorated method
        try:
            r = func(*args, **kwargs)
            if r:
                # Take care of JSONP
                params = web.input(callback=None)
                if params.callback:
                    if getattr(options, 'api_jsonp_enabled', False):
                        if not _valid_jsonp_callback(params.callback):
                            raise badrequest('{"error": "Invalid JSONP callback"}')
                        # Wrap the response in JSONP format
                        r = "{callback}({json});".format(callback=params.callback,
                                                         json=_json_dumps(r))
                        return r
                else:
                    # Just jsonify the response
                    return _json_dumps(r)
                return _json_dumps(r)
            else:
                return ''

        except IndexError as e:  # No such item
            log.error('utils.py',  _('Error: (IndexError) Index out of bounds {}').format(e.message))
            raise badrequest('{"error": "(IndexError) Index out of bounds - ' + e.message + '"}')

        except ValueError as e:  # json errors
            log.error('utils.py',  _('Error: (ValueError) Inappropriate argument value {}').format(e.message))
            raise badrequest('{"error": "(ValueError) Inappropriate argument value - ' + e.message + '"}')
            # raise badrequest(format(e.message))

        except KeyError as e:  # missing attribute names
            log.error('utils.py',  _('Error: (KeyError) Missing key {}').format(e.message))
            raise badrequest('{"error": "(KeyError) Missing key - ' + e.message + '"}')
            # raise badrequest(format(e.message))

    return wrapper


def authenticate_basic():
    username = password = ''
    failure_logged = False
    try:
        auth_data = web.ctx.env.get('HTTP_AUTHORIZATION')
        assert auth_data, 'No authentication data provided'

        http_auth = re.sub('^Basic ', '', auth_data)
        base64_bytes = http_auth.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        message = message_bytes.decode('ascii')
        username, password = message.split(':', 1)
        log.debug('utils.py',  _('API Auth Attempt with user: {}').format(username))
        if not test_password(password, username):
            blocked = bruteforce_blocked(username)
            if blocked:
                _save_api_security_event(
                    'blocked:{}:{}'.format(_api_request_ip(), username.lower()),
                    _('API authentication blocked'),
                    _('API authentication for user {} from IP {} was temporarily blocked.').format(
                        username, _api_request_ip()),
                    level='error'
                )
            else:
                _save_api_security_event(
                    'failed:{}:{}'.format(_api_request_ip(), username.lower()),
                    _('API authentication failed'),
                    _('API authentication failed for user {} from IP {}.').format(
                        username, _api_request_ip())
                )
            failure_logged = True
            raise AssertionError('Wrong password')
        return True
    except:
        if not failure_logged:
            _save_api_security_event(
                'invalid:{}:{}'.format(_api_request_ip(), username.lower()),
                _('API authentication failed'),
                _('Invalid API authentication request from IP {}.').format(_api_request_ip())
            )
        log.debug('utils.py',  _('API Unauthorized attempt user: {}').format(username))
        web.header('WWW-Authenticate', 'Basic realm="OSPy"')
        print_report('utils.py', traceback.format_exc())
        raise unauthorized()


def verify_api_csrf_if_required():
    if not getattr(options, 'api_csrf_required', False):
        return
    method = getattr(web.ctx, 'method', '').upper()
    if method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        verify_csrf()


def auth(func):
    """
    HTTP Basic authentication wrapper
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not options.no_password:
            authenticate_basic()

        verify_api_csrf_if_required()

        return func(*args, **kwargs)
        
    return wrapper


def permission(func):
    """
    user authentication wrapper
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not options.no_password:
            try:

                log.debug('utils.py',  _('API permission granted.'))
                print(server.session['category'])
                assert server.session['category']!='public' ,'Bad permission'
            except:
                # no or wrong auth provided
                try:
                    denied_user = server.session.get('visitor', '-')
                except Exception:
                    denied_user = '-'
                _save_api_security_event(
                    'denied:{}:{}'.format(_api_request_ip(), denied_user),
                    _('API authorization denied'),
                    _('API access was denied for user {} from IP {}.').format(
                        denied_user, _api_request_ip())
                )
                log.debug('utils.py',  _('API permission block.'))
                print_report('utils.py', traceback.format_exc())
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
