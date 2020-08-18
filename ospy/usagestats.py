# -*- coding: utf-8 -*-
from __future__ import print_function
__author__ = 'remram44' # https://github.com/remram44/usagestats

# usagestats = Anonymous usage statistics collector

import logging
import os
import platform
import time
import sys
import subprocess
from ospy.helpers import print_report

try:
    import requests

except ImportError:
    print_report('usagestats.py', _('Requests not found, installing. Please wait...'))
    cmd = "sudo apt-get install python-requests"
    proc = subprocess.Popen(cmd,stderr=subprocess.STDOUT,stdout=subprocess.PIPE,shell=True)
    output = proc.communicate()[0]
    print_report('usagestats.py', output)
       
    try: 
        import requests
    except:
        pass

__version__ = '0.7'


logger = logging.getLogger('usagestats')


class Prompt(object):
    """The reporting prompt, asking the user to enable or disable the system.
    """
    def __init__(self, prompt=None, enable=None, disable=None):
        if prompt is not None:
            if enable is not None or disable is not None:
                raise TypeError("Expects either 'prompt' or both 'enable' and "
                                "'disable'")
            self.prompt = prompt
        else:
            if enable is None or disable is None:
                raise TypeError("Expects either 'prompt' or both 'enable' and "
                                "'disable'")
            self.prompt = (
                    "\nUploading usage statistics is currently disabled\n"
                    "Please help us by providing anonymous usage statistics; "
                    "you can enable this\nby running:\n"
                    "    {enable}\n"
                    "If you do not want to see this message again, you can "
                    "run:\n"
                    "    {disable}\n"
                    "Nothing will be uploaded before you opt in.\n".format(
                        enable=enable,
                        disable=disable))


def OPERATING_SYSTEM(stats, info):
    """General information about the operating system.

    This is a flag you can pass to `Stats.submit()`.
    """
    info.append(('architecture', platform.machine().lower()))
    info.append(('distribution',
                 "%s;%s" % (platform.linux_distribution()[0:2])))
    info.append(('system',
                 "%s;%s" % (platform.system(), platform.release())))


def SESSION_TIME(stats, info):
    """Total time of this session.

    Reports the time elapsed from the construction of the `Stats` object to
    this `submit()` call.

    This is a flag you can pass to `Stats.submit()`.
    """
    duration = time.time() - stats.started_time
    secs = int(duration)
    msecs = int((duration - secs) * 1000)
    info.append(('session_time', '%d.%d' % (secs, msecs)))


def PYTHON_VERSION(stats, info):
    """Python interpreter version.

    This is a flag you can pass to `Stats.submit()`.
    """
    # Some versions of Python have a \n in sys.version!
    #version = sys.version.replace(' \n', ' ').replace('\n', ' ')
    #python = ';'.join([str(c) for c in sys.version_info] + [version])
    python = platform.python_version()
    info.append(('python', python))


def _encode(s):
    if not isinstance(s, bytes):
        if str == bytes:  # Python 2
            if isinstance(s, unicode):
                s = s.encode('utf-8')
            else:
                s = str(s)
        else:  # Python 3
            if isinstance(s, str):
                s = s.encode('utf-8')
            else:
                s = str(s).encode('utf-8')
    if b'\n' in s:
        s = s.replace(b'\n', b' ')
    return s


class Stats(object):
    """Usage statistics collection and reporting.

    Create an object of this class when your application starts, collect
    information using `note()` from all around your codebase, then call
    `submit()` to generate a report and upload it to your drop point for
    analysis.
    """
    ERRORED, DISABLED_ENV, DISABLED, UNSET, ENABLED = range(5)

    @property
    def enabled(self):
        return self.status in (Stats.UNSET, Stats.ENABLED)

    @property
    def enableable(self):
        return self.status not in (Stats.ERRORED, Stats.ENABLED)

    @property
    def disableable(self):
        return self.status not in (Stats.ERRORED, Stats.DISABLED)

    @property
    def recording(self):
        return self.status in (Stats.UNSET, Stats.ENABLED)

    @property
    def sending(self):
        return self.status is Stats.ENABLED

    def __init__(self, location, prompt, drop_point,
                 version, unique_user_id=False,
                 env_var='PYTHON_USAGE_STATS',
                 ssl_verify=None):
        """Start a report for later submission.

        This creates a report object that you can fill with data using
        `note()`, until you finally upload it (or not, depending on
        configuration) using `submit()`.
        """
        self.started_time = time.time()

        if ssl_verify is None or isinstance(ssl_verify, str):
            self.ssl_verify = ssl_verify
        elif isinstance(ssl_verify, bytes):  # bytes on PY3
            self.ssl_verify = ssl_verify.decode('utf-8')
        else:  # unicode on PY2
            self.ssl_verify = ssl_verify.encode('utf-8')

        self.env_var = env_var
        env_val = os.environ.get(env_var, '').lower()
        if env_val not in (None, '', '1', 'on', 'enabled', 'yes', 'true'):
            self.status = Stats.DISABLED_ENV
        else:
            self.status = Stats.UNSET
        self.location = os.path.expanduser(location)
        self.drop_point = drop_point
        self.version = version

        if isinstance(prompt, Prompt):
            self.prompt = prompt
        elif isinstance(prompt, basestring):
            self.prompt = Prompt(prompt)
        else:
            raise TypeError("'prompt' should either a Prompt or a string")

        self.read_config()

        if self.enabled and unique_user_id:
            user_id_file = os.path.join(self.location, 'user_id')
            if os.path.exists(user_id_file):
                with open(user_id_file, 'r') as fp:
                    self.user_id = fp.read().strip()
            else:
                import uuid
                self.user_id = str(uuid.uuid4())
                with open(user_id_file, 'w') as fp:
                    fp.write(self.user_id)
        else:
            self.user_id = None

        self.notes = []

        self.note([('version', self.version)])

    def read_config(self):
        """Reads the configuration.

        This method can be overloaded to integrate with your application's own
        configuration mechanism. By default, a single 'status' file is read
        from the reports' directory.

        This should set `self.status` to one of the state constants, and make
        sure `self.location` points to a writable directory where the reports
        will be written.

        The possible values for `self.status` are:

        - `UNSET`: nothing has been selected and the user should be prompted
        - `ENABLED`: collect and upload reports
        - `DISABLED`: don't collect or upload anything, stop prompting
        - `ERRORED`: something is broken, and we can't do anything in this
          session (for example, the configuration directory is not writable)
        """
        if self.enabled and not os.path.isdir(self.location):
            try:
                os.makedirs(self.location, 0o700)
            except OSError:
                logger.warning(_('Could not create %s, usage statistics won not be collected'), self.location)
                self.status = Stats.ERRORED

        status_file = os.path.join(self.location, 'status')
        if self.enabled and os.path.exists(status_file):
            with open(status_file, 'r') as fp:
                status = fp.read().strip()
            if status == 'ENABLED':
                self.status = Stats.ENABLED
            elif status == 'DISABLED':
                self.status = Stats.DISABLED

    def write_config(self, enabled):
        """Writes the configuration.

        This method can be overloaded to integrate with your application's own
        configuration mechanism. By default, a single 'status' file is written
        in the reports' directory, containing either ``ENABLED`` or
        ``DISABLED``; if the file doesn't exist, `UNSET` is assumed.

        :param enabled: Either `Stats.UNSET`, `Stats.DISABLED` or
        `Stats.ENABLED`.
        """
        status_file = os.path.join(self.location, 'status')
        with open(status_file, 'w') as fp:
            if enabled is Stats.ENABLED:
                fp.write('ENABLED')
            elif enabled is Stats.DISABLED:
                fp.write('DISABLED')
            else:
                raise ValueError(_('Unknown reporting state %r') % enabled)

    def enable_reporting(self):
        """Call this method to explicitly enable reporting.

        The current report will be uploaded, plus the previously recorded ones,
        and the configuration will be updated so that future runs also upload
        automatically.
        """
        if self.status == Stats.ENABLED:
            return
        if not self.enableable:
            logger.critical(_('Can not enable reporting'))
            return
        self.status = Stats.ENABLED
        self.write_config(self.status)

    def disable_reporting(self):
        """Call this method to explicitly disable reporting.

        The current report will be discarded, along with the previously
        recorded ones that haven't been uploaded. The configuration is updated
        so that future runs do not record or upload reports.
        """
        if self.status == Stats.DISABLED:
            return
        if not self.disableable:
            logger.critical(_('Can not disable reporting'))
            return
        self.status = Stats.DISABLED
        self.write_config(self.status)
        if os.path.exists(self.location):
            old_reports = [f for f in os.listdir(self.location)
                           if f.startswith('report_')]
            for old_filename in old_reports:
                fullname = os.path.join(self.location, old_filename)
                os.remove(fullname)
            logger.info(_('Deleted %d pending reports'), len(old_reports))

    @staticmethod
    def _to_notes(info):
        if hasattr(info, 'iteritems'):
            return info.iteritems()
        elif hasattr(info, 'items'):
            return info.items()
        else:
            return info

    def note(self, info):
        """Record some info to the report.

        :param info: Dictionary of info to record. Note that previous info
        recorded under the same keys will not be overwritten.
        """
        if self.recording:
            if self.notes is None:
                raise ValueError(_('This report has already been submitted'))
            self.notes.extend(self._to_notes(info))

    def submit(self, info, *flags):
        """Finish recording and upload or save the report.

        This closes the `Stats` object, no further methods should be called.
        The report is either saved, uploaded or discarded, depending on
        configuration. If uploading is enabled, previous reports might be
        uploaded too. If uploading is not explicitly enabled or disabled, the
        prompt will be shown, to ask the user to enable or disable it.
        """
        if not self.recording:
            return
        env_val = os.environ.get(self.env_var, '').lower()
        if env_val not in (None, '', '1', 'on', 'enabled', 'yes', 'true'):
            self.status = Stats.DISABLED_ENV
            self.notes = None
            return

        if self.notes is None:
            raise ValueError(_('This report has already been submitted'))

        all_info, self.notes = self.notes, None
        all_info.extend(self._to_notes(info))
        for flag in flags:
            flag(self, all_info)

        now = time.time()
        secs = int(now)
        msecs = int((now - secs) * 1000)
        all_info.insert(0, ('date', '%d.%d' % (secs, msecs)))

        if self.user_id:
            all_info.insert(1, ('user', self.user_id))

        logger.debug(_('Generated report:\n%r'), (all_info,))

        # Current report
        def generator():
            for key, value in all_info:
                yield _encode(key) + b':' + _encode(value) + b'\n'
        filename = 'report_%d_%d.txt' % (secs, msecs)

        # Save current report and exit, unless user has opted in
        if not self.sending:
            fullname = os.path.join(self.location, filename)
            with open(fullname, 'wb') as fp:
                for l in generator():
                    fp.write(l)

            # Show prompt
            sys.stderr.write(self.prompt.prompt)
            return

        # Post previous reports
        old_reports = [f for f in os.listdir(self.location)
                       if f.startswith('report_')]
        old_reports.sort()
        old_reports = old_reports[:4]  # Only upload 5 at a time
        for old_filename in old_reports:
            fullname = os.path.join(self.location, old_filename)
            try:
                with open(fullname, 'rb') as fp:
                    # `data=fp` would make requests stream, which is currently
                    # not a good idea (WSGI chokes on it)
                    r = requests.post(self.drop_point, data=fp.read(),
                                      timeout=1, verify=self.ssl_verify)
                    r.raise_for_status()
            except Exception as e:
                logger.warning(_('Could not upload %s: %s'), old_filename, str(e))
                break
            else:
                logger.info(_('Submitted report %s'), old_filename)
                os.remove(fullname)

        # Post current report
        try:
            # `data=generator()` would make requests stream, which is currently
            # not a good idea (WSGI chokes on it)
            r = requests.post(self.drop_point, data=b''.join(generator()),
                              timeout=1, verify=self.ssl_verify)
        except requests.RequestException as e:
            logger.warning(_('Could not upload report: %s'), str(e))
            fullname = os.path.join(self.location, filename)
            with open(fullname, 'wb') as fp:
                for l in generator():
                    fp.write(l)
        else:
            try:
                r.raise_for_status()
                logger.info(_('Submitted report'))
            except requests.RequestException as e:
                logger.warning(_('Server rejected report: %s'), str(e))
