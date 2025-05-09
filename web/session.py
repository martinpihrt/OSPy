"""
Session Management
(from web.py)
modify: Martin Pihrt
date: 13.01.2025
"""

import datetime
import os
import os.path
import shutil
import threading
import time
from copy import deepcopy
from hashlib import sha1

from . import utils
from . import webapi as web
from .py3helpers import iteritems

try:
    import cPickle as pickle
except ImportError:
    import pickle


from base64 import encodebytes, decodebytes

from .utils import ThreadedDict

from ospy.log import log


__all__ = ["Session", "SessionExpired", "Store", "DiskStore", "DBStore", "MemoryStore"]

web.config.session_parameters = utils.storage(
    {
        "cookie_name": "webpy_session_id",
        "cookie_domain": None,
        "cookie_path": None,
        "samesite": 'Lax',
        "timeout": 604800,  # 24 * 60 * 60 * 7 -> # one week
        "ignore_expiry": True,
        "ignore_change_ip": True,
        "secret_key": "fLjUfxqXtfNoIldA0Aed",
        "expired_message": "Session expired",
        "httponly": True,
        "secure": False,
    }
)


class SessionExpired(web.HTTPError):
    def __init__(self, message):
        web.HTTPError.__init__(self, "200 OK", {}, data=message)


class Session(object):
    """Session management for web.py"""

    __slots__ = [
        "store",
        "_initializer",
        "_last_cleanup_time",
        "_config",
        "_data",
        "__getitem__",
        "__setitem__",
        "__delitem__",
    ]

    def __init__(self, app, store, initializer=None):
        self.store = store
        self._initializer = initializer
        self._last_cleanup_time = 0
        self._config = utils.storage(web.config.session_parameters)
        self._data = utils.threadeddict()

        self.__getitem__ = self._data.__getitem__
        self.__setitem__ = self._data.__setitem__
        self.__delitem__ = self._data.__delitem__

        if app:
            app.add_processor(self._processor)

    def __contains__(self, name):
        return name in self._data

    def __getattr__(self, name):
        return getattr(self._data, name)

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            setattr(self._data, name, value)

    def __delattr__(self, name):
        delattr(self._data, name)

    def _processor(self, handler):
        """Application processor to setup session for every request"""

        self._cleanup()
        self._load()

        try:
            return handler()
        finally:
            self._save()

    def _load(self):
        """Load the session from the store, by the id from cookie"""
        cookie_name = self._config.cookie_name
        self.session_id = web.cookies().get(cookie_name)

        # protection against session_id tampering
        if self.session_id and not self._valid_session_id(self.session_id):
            self.session_id = None

        self._check_expiry()
        if self.session_id:
            d = self.store[self.session_id]
            self.update(d)
            self._validate_ip()

        if not self.session_id:
            self.session_id = self._generate_session_id()

            if self._initializer:
                if isinstance(self._initializer, dict):
                    self.update(deepcopy(self._initializer))
                elif hasattr(self._initializer, "__call__"):
                    self._initializer()

        self.ip = web.ctx.ip

    def _check_expiry(self):
        # check for expiry
        if self.session_id and self.session_id not in self.store:
            if self._config.ignore_expiry:
                self.session_id = None
            else:
                return self.expired()

    def _validate_ip(self):
        # check for change of IP
        if self.session_id and self.get("ip", None) != web.ctx.ip:
            if not self._config.ignore_change_ip:
                return self.expired()

    def _save(self):
        try:
            current_values = dict(self._data)

            # Deleting keys we don't want to store
            if "session_id" in current_values:
                del current_values["session_id"]
            if "ip" in current_values:
                del current_values["ip"]

            # Verifying that session_id is a valid string
            if not isinstance(self.session_id, str) or not self.session_id:
                log.error('web', _('Session ID must be a valid non-empty string.'))
                pass

            if not self.get("_killed"):
                self._setcookie(self.session_id)

                # Convert to a regular dictionary if _data is of type ThreadedDict
                if isinstance(self._data, ThreadedDict):
                    data_to_save = dict(self._data)
                else:
                    data_to_save = self._data

                # Checking if data can be serialized before saving
                pickle.dumps(data_to_save)

                # Saving to a store (e.g. shelve)
                self.store[self.session_id] = data_to_save
            else:
                if web.cookies().get(self._config.cookie_name):
                    self._setcookie(self.session_id, expires=-1)
        except pickle.PicklingError:
            log.error('web', _('Unable to serialize session data for storage.'))
            pass
        except Exception as e:
            log.error('web', _('Error saving to database: {}').format(e))
            pass


    def _setcookie(self, session_id, expires="", **kw):
        cookie_name = self._config.cookie_name
        cookie_domain = self._config.cookie_domain
        cookie_path = self._config.cookie_path
        httponly = self._config.httponly
        secure = self._config.secure
        samesite = kw.get("samesite", self._config.get("samesite", 'Lax'))
        web.setcookie(
            cookie_name,
            session_id,
            expires=expires,
            domain=cookie_domain,
            httponly=httponly,
            secure=secure,
            path=cookie_path,
            samesite=samesite,
        )

    def _generate_session_id(self):
        """Generate a random id for session"""

        while True:
            rand = os.urandom(16)
            now = time.time()
            secret_key = self._config.secret_key

            hashable = "{}{}{}{}".format(rand, now, utils.safestr(web.ctx.ip), secret_key)
            session_id = sha1(hashable.encode("utf-8")).hexdigest()
            if session_id not in self.store:
                break
        return session_id

    def _valid_session_id(self, session_id):
        rx = utils.re_compile("^[0-9a-fA-F]+$")
        return rx.match(session_id)

    def _cleanup(self):
        """Cleanup the stored sessions"""
        current_time = time.time()
        timeout = self._config.timeout
        if current_time - self._last_cleanup_time > timeout:
            self.store.cleanup(timeout)
            self._last_cleanup_time = current_time

    def expired(self):
        """Called when an expired session is atime"""
        self._killed = True
        self._save()
        raise SessionExpired(self._config.expired_message)

    def kill(self):
        """Kill the session, make it no longer available"""
        del self.store[self.session_id]
        self._killed = True


class Store:
    """Base class for session stores"""

    def __contains__(self, key):
        raise NotImplementedError()

    def __getitem__(self, key):
        raise NotImplementedError()

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def cleanup(self, timeout):
        """removes all the expired sessions"""
        raise NotImplementedError()

    def encode(self, session_dict):
        """encodes session dict as a string"""
        pickled = pickle.dumps(session_dict)
        return encodebytes(pickled)

    def decode(self, session_data):
        """decodes the data to get back the session dict """
        if isinstance(session_data, str):
            session_data = session_data.encode()

        pickled = decodebytes(session_data)
        return pickle.loads(pickled)


class DiskStore(Store):
    """
    Store for saving a session on disk.

        >>> import tempfile
        >>> root = tempfile.mkdtemp()
        >>> s = DiskStore(root)
        >>> s['a'] = 'foo'
        >>> s['a']
        'foo'
        >>> time.sleep(0.01)
        >>> s.cleanup(0.01)
        >>> s['a']
        Traceback (most recent call last):
            ...
        KeyError: 'a'
    """

    def __init__(self, root):
        # if the storage root doesn't exists, create it.
        if not os.path.exists(root):
            os.makedirs(os.path.abspath(root))
        self.root = root

    def _get_path(self, key):
        if os.path.sep in key:
            raise ValueError("Bad key: %s" % repr(key))
        return os.path.join(self.root, key)

    def __contains__(self, key):
        path = self._get_path(key)
        return os.path.exists(path)

    def __getitem__(self, key):
        path = self._get_path(key)

        if os.path.exists(path):
            with open(path, "rb") as fh:
                pickled = fh.read()
            return self.decode(pickled)
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        path = self._get_path(key)
        pickled = self.encode(value)
        try:
            tname = path + "." + threading.current_thread().getName()
            f = open(tname, "wb")
            try:
                f.write(pickled)
            finally:
                f.close()
                shutil.move(tname, path)  # atomary operation
        except IOError:
            pass

    def __delitem__(self, key):
        path = self._get_path(key)
        if os.path.exists(path):
            os.remove(path)

    def cleanup(self, timeout):
        if not os.path.isdir(self.root):
            return

        now = time.time()
        for f in os.listdir(self.root):
            path = self._get_path(f)
            atime = os.stat(path).st_atime
            if now - atime > timeout:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)


class DBStore(Store):
    """Store for saving a session in database
    Needs a table with the following columns:

        session_id CHAR(128) UNIQUE NOT NULL,
        atime DATETIME NOT NULL default current_timestamp,
        data TEXT
    """

    def __init__(self, db, table_name):
        self.db = db
        self.table = table_name

    def __contains__(self, key):
        data = self.db.select(self.table, where="session_id=$key", vars=locals())
        return bool(list(data))

    def __getitem__(self, key):
        now = datetime.datetime.now()
        try:
            s = self.db.select(self.table, where="session_id=$key", vars=locals())[0]
            self.db.update(
                self.table, where="session_id=$key", atime=now, vars=locals()
            )
        except IndexError:
            raise KeyError(key)
        else:
            return self.decode(s.data)

    def __setitem__(self, key, value):
        try:
            pickle.dumps(value)
            if not isinstance(key, str) or not key:
                log.error('web', _('The key must be a non-empty string.'))
                pass
            self.shelf[key] = time.time(), value
        except pickle.PicklingError:
            log.error('web', _('Unable to serialize value: {}').format(value))
            pass
        except Exception as e:
            log.error('web', _('Error saving to database: {}').format(e))
            pass

    def __delitem__(self, key):
        try:
            del self.shelf[key]
        except KeyError:
            pass
        except Exception as e:
            log.error('web', _('Error while deleting from database: {}').format(e))
            pass

    def cleanup(self, timeout):
        timeout = datetime.timedelta(
            timeout / (24.0 * 60 * 60)
        )  # timedelta takes numdays as arg
        last_allowed_time = datetime.datetime.now() - timeout
        self.db.delete(self.table, where="$last_allowed_time > atime", vars=locals())


class ShelfStore:
    """Store for saving session using `shelve` module.

        import shelve
        store = ShelfStore(shelve.open('session.shelf'))

    XXX: is shelve thread-safe?
    """

    def __init__(self, shelf):
        self.shelf = shelf
        self.lock = threading.Lock()

    def __contains__(self, key):
        return key in self.shelf

    def __getitem__(self, key):
        atime, v = self.shelf[key]
        self[key] = v  # update atime
        return v

    def __setitem__(self, key, value):
        with self.lock:
            try:
                if not isinstance(key, str) or not key:
                    log.error('web', _('The key must be a non-empty string.'))
                else:
                    self.shelf[key] = time.time(), value
            except pickle.PicklingError:
                pass
                log.error('web', _('Unable to serialize value: {}').format(value))
            except Exception as e:
                pass
                log.error('web', _('Error saving to database key: {} error: {}').format(e, key))
            

    def __delitem__(self, key):
        try:
            del self.shelf[key]
        except KeyError:
            pass
        except Exception as e:
            pass
            log.error('web', _('Error while deleting from database: {}').format(e))


    def cleanup(self, timeout):
        now = time.time()
        for k in self.shelf:
            atime, v = self.shelf[k]
            if now - atime > timeout:
                try:
                    del self[k]
                except Exception as e:
                    pass
                    log.error('web', _('Error while cleaning: {}').format(e))


class MemoryStore(Store):
    """Store for saving a session in memory.
    Useful where there is limited fs writes on the disk, like
    flash memories

    Data will be saved into a dict:
    k: (time, pydata)
    """

    def __init__(self, d_store=None):
        if d_store is None:
            d_store = {}
        self.d_store = d_store

    def __contains__(self, key):
        return key in self.d_store

    def __getitem__(self, key):
        """Return the value and update the last seen value"""
        t, value = self.d_store[key]
        self.d_store[key] = (time.time(), value)
        return value

    def __setitem__(self, key, value):
        self.d_store[key] = (time.time(), value)

    def __delitem__(self, key):
        del self.d_store[key]

    def cleanup(self, timeout):
        now = time.time()
        to_del = []
        for k, (atime, value) in iteritems(self.d_store):
            if now - atime > timeout:
                to_del.append(k)

        # to avoid exception on "dict change during iterations"
        for k in to_del:
            del self.d_store[k]


if __name__ == "__main__":
    import doctest

    doctest.testmod()