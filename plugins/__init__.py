import pkgutil
import traceback
import re
import sys
import json
import importlib.util
import ast
import tokenize
from os import path
import types
import threading
import importlib
import os
import time

__running = {}
__plugin_runtime = {}
__thread_plugin = {}
__diagnostic_sample = {}
__plugin_health_workers = {}
__manifest_cache = {}
__profile_lock = threading.RLock()
__plugin_health_lock = threading.RLock()
__plugin_diagnostics_lock = threading.RLock()
__plugin_diagnostics_cache = {'time': 0, 'data': None}
PLUGIN_HEALTH_TIMEOUT = 1.0
PLUGIN_THREAD_STOP_TIMEOUT = 5.0
PLUGIN_MANIFEST_FILE = 'plugin.json'
PLUGIN_MANIFEST_MAX_BYTES = 64 * 1024
PLUGIN_MANIFEST_SCHEMA_VERSION = 1
PLUGIN_PREFLIGHT_MAX_FILES = 512
PLUGIN_PREFLIGHT_MAX_FILE_BYTES = 2 * 1024 * 1024
PLUGIN_PREFLIGHT_MAX_TOTAL_BYTES = 16 * 1024 * 1024
PLUGIN_ZIP_MAX_DOWNLOAD_BYTES = 64 * 1024 * 1024
PLUGIN_ZIP_MAX_FILES = 4096
PLUGIN_ZIP_MAX_FILE_BYTES = 32 * 1024 * 1024
PLUGIN_ZIP_MAX_TOTAL_BYTES = 128 * 1024 * 1024
PLUGIN_ZIP_MAX_RATIO = 200
PLUGIN_ZIP_MAX_PLUGINS = 256
PLUGIN_PERMISSIONS = {
    'network', 'files', 'i2c', 'gpio', 'email', 'subprocess', 'system'
}
REPOS = ['https://github.com/martinpihrt/OSPy-plugins/archive/master.zip'] # repository with plugins


def _plugin_import_name(module):
    return __name__ + '.' + module


def _clear_plugin_caches(module):
    """Clear cached plugin metadata and route mappings after an install/update."""
    __name_cache.pop(module, None)
    __name_cache_menu.pop(module, None)
    __manifest_cache.pop(module, None)

    for key in list(__urls_cache.keys()):
        if key == module or getattr(key, '__name__', '').endswith('.' + module):
            __urls_cache.pop(key, None)


def _unload_plugin_modules(module):
    """Remove a plugin package and its submodules so the next import reads disk."""
    import_name = _plugin_import_name(module)
    for name in list(sys.modules.keys()):
        if name == import_name or name.startswith(import_name + '.'):
            del sys.modules[name]

    if hasattr(sys.modules.get(__name__), module):
        delattr(sys.modules[__name__], module)

    importlib.invalidate_caches()


def _runtime_entry(module):
    with __profile_lock:
        return __plugin_runtime.setdefault(module, {
            'started': 0,
            'restarts': 0,
            'threads': {},
            'runtime': None,
            'last_error': '',
            'last_restart': '',
        })


def _now_string():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def _register_plugin_thread(module, thread, managed=False):
    ident = getattr(thread, 'ident', None)
    if ident is None:
        return
    native_id = getattr(thread, 'native_id', None)
    with __profile_lock:
        __thread_plugin[ident] = module
        entry = _runtime_entry(module)
        entry['threads'][ident] = {
            'name': getattr(thread, 'name', ''),
            'native_id': native_id,
            'started': time.time(),
            'managed': bool(managed),
            'thread': thread,
        }


def _thread_cpu_seconds(native_id):
    if native_id is None or os.name != 'posix':
        return None
    try:
        clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
        with open('/proc/{}/task/{}/stat'.format(os.getpid(), native_id), 'r') as fh:
            stat = fh.read()
        end = stat.rfind(')')
        fields = stat[end + 2:].split()
        return (float(fields[11]) + float(fields[12])) / float(clk_tck)
    except Exception:
        return None


def _track_threads_started_by(module, start_callable):
    before = {thread.ident for thread in threading.enumerate() if thread.ident is not None}
    result = start_callable()
    after_threads = [thread for thread in threading.enumerate() if thread.ident is not None and thread.ident not in before]
    for thread in after_threads:
        _register_plugin_thread(module, thread)
    return result


def _caller_plugin_module():
    my_dir = path.dirname(path.abspath(__file__))
    for frame in reversed(traceback.extract_stack()):
        frame_path = path.abspath(frame.filename)
        frame_dir = path.dirname(frame_path)
        if frame_dir.startswith(my_dir + path.sep):
            relative = frame_dir[len(my_dir) + 1:]
            module = relative.split(path.sep)[0]
            if module:
                return module
    return None


class PluginRuntime(object):
    """Cooperative lifecycle helper for plug-in background threads."""

    def __init__(self, module):
        self.module = module
        self.stop_event = threading.Event()
        self._threads = []
        self._lock = threading.RLock()

    def register_thread(self, thread):
        if not isinstance(thread, threading.Thread):
            raise TypeError(_('A threading.Thread instance is required.'))
        with self._lock:
            if thread not in self._threads:
                self._threads.append(thread)
        if thread.ident is not None:
            _register_plugin_thread(self.module, thread, managed=True)
        return thread

    def start_thread(self, target, name=None, args=(), kwargs=None, daemon=True):
        if not callable(target):
            raise TypeError(_('Thread target must be callable.'))
        thread = threading.Thread(
            target=target,
            name=name or '{} worker'.format(self.module),
            args=tuple(args or ()),
            kwargs=dict(kwargs or {}),
        )
        thread.daemon = bool(daemon)
        with self._lock:
            self._threads.append(thread)
        thread.start()
        _register_plugin_thread(self.module, thread, managed=True)
        return thread

    def request_stop(self):
        self.stop_event.set()

    def join(self, timeout=PLUGIN_THREAD_STOP_TIMEOUT):
        deadline = time.time() + max(0.0, float(timeout))
        alive = []
        with self._lock:
            threads = list(self._threads)
        for thread in threads:
            if thread is threading.current_thread() or not thread.is_alive():
                continue
            remaining = max(0.0, deadline - time.time())
            if remaining:
                thread.join(remaining)
            if thread.is_alive():
                alive.append(thread)
        return alive

    def threads(self):
        with self._lock:
            return list(self._threads)


def get_runtime(module=None):
    """Return the cooperative runtime for the calling plug-in."""
    module = module or _caller_plugin_module()
    if not module:
        raise RuntimeError(_('Plug-in module could not be determined.'))
    entry = _runtime_entry(module)
    runtime = entry.get('runtime')
    if runtime is None:
        runtime = PluginRuntime(module)
        entry['runtime'] = runtime
    return runtime


def register_thread(thread, module=None):
    """Register an existing plug-in thread for cooperative shutdown."""
    return get_runtime(module).register_thread(thread)


def _plugin_health_result(value):
    """Normalize the optional plug-in health() result for diagnostics."""
    if isinstance(value, dict):
        result = dict(value)
        status = str(result.get('status', 'unknown')).lower()
        aliases = {
            'healthy': 'ok',
            'good': 'ok',
            'running': 'ok',
            'warn': 'warning',
            'degraded': 'warning',
            'failed': 'error',
            'unhealthy': 'error',
            'disabled': 'unknown',
            'not_configured': 'unknown',
            'unavailable': 'unknown',
        }
        status = aliases.get(status, status)
        if status not in ('ok', 'warning', 'error', 'unknown'):
            status = 'unknown'
        details = result.get('details', '')
        if isinstance(details, dict):
            details = '; '.join(
                '{}: {}'.format(key, value)
                for key, value in sorted(details.items(), key=lambda item: str(item[0]))
            )
        updated = result.get('updated', time.time())
        if not isinstance(updated, (int, float, str)):
            updated = time.time()
        return {
            'supported': True,
            'status': status,
            'summary': str(result.get('summary', result.get('message', '')) or ''),
            'details': str(details or ''),
            'updated': updated,
        }

    if isinstance(value, bool):
        return {
            'supported': True,
            'status': 'ok' if value else 'error',
            'summary': '',
            'details': '',
            'updated': time.time(),
        }

    if value is not None:
        return {
            'supported': True,
            'status': 'unknown',
            'summary': str(value),
            'details': '',
            'updated': time.time(),
        }

    return {
        'supported': True,
        'status': 'unknown',
        'summary': _('Not reported'),
        'details': '',
        'updated': time.time(),
    }


def plugin_health(module):
    """Read the optional health() report of a running plug-in safely."""
    plugin = __running.get(module)
    if plugin is None:
        return {
            'supported': False,
            'status': 'unknown',
            'summary': _('Not running'),
            'details': '',
            'updated': 0,
        }

    health_check = getattr(plugin, 'health', None)
    if not callable(health_check):
        return {
            'supported': False,
            'status': 'unknown',
            'summary': _('Not reported'),
            'details': '',
            'updated': 0,
        }

    with __plugin_health_lock:
        worker = __plugin_health_workers.get(module)
        if worker is not None and worker['plugin'] is not plugin:
            __plugin_health_workers.pop(module, None)
            worker = None
        if worker is None:
            worker = {
                'plugin': plugin,
                'result': None,
                'started': time.time(),
            }

            def run_health_check():
                try:
                    worker['result'] = _plugin_health_result(health_check())
                except Exception:
                    worker['result'] = {
                        'supported': True,
                        'status': 'error',
                        'summary': _('Health check failed.'),
                        'details': traceback.format_exc(),
                        'updated': time.time(),
                    }

            thread = threading.Thread(
                target=run_health_check,
                name='OSPy plug-in health {}'.format(module),
            )
            thread.daemon = True
            worker['thread'] = thread
            __plugin_health_workers[module] = worker
            thread.start()

    worker['thread'].join(PLUGIN_HEALTH_TIMEOUT)
    if worker['thread'].is_alive():
        return {
            'supported': True,
            'status': 'warning',
            'summary': _('Health check timed out.'),
            'details': '',
            'updated': worker['started'],
        }

    with __plugin_health_lock:
        if __plugin_health_workers.get(module) is worker:
            __plugin_health_workers.pop(module, None)
    return worker['result']


def _parallel_plugin_health(available_modules, running_modules):
    """Collect running plug-in health checks within one shared timeout window."""
    results = {}
    workers = []

    def collect(module):
        results[module] = plugin_health(module)

    for module in available_modules:
        if module not in running_modules:
            results[module] = plugin_health(module)
            continue
        worker = threading.Thread(
            target=collect,
            args=(module,),
            name='OSPy diagnostics health {}'.format(module),
        )
        worker.daemon = True
        workers.append((module, worker))
        worker.start()

    deadline = time.time() + PLUGIN_HEALTH_TIMEOUT + 0.25
    for module, worker in workers:
        worker.join(max(0.0, deadline - time.time()))
        if worker.is_alive() or module not in results:
            results[module] = {
                'supported': True,
                'status': 'warning',
                'summary': _('Health check timed out.'),
                'details': '',
                'updated': time.time(),
            }
    return results


def plugin_diagnostics(force=False):
    global __plugin_diagnostics_cache
    with __plugin_diagnostics_lock:
        now = time.time()
        cached = __plugin_diagnostics_cache
        if (not force and cached.get('data') is not None and
                now - cached.get('time', 0) < 2.0):
            return cached['data']

        data = _plugin_diagnostics_uncached()
        __plugin_diagnostics_cache = {'time': time.time(), 'data': data}
        return data


def _plugin_diagnostics_uncached():
    data = []
    running_modules = running()
    available_modules = available()
    now = time.time()
    from ospy.options import options
    health_results = _parallel_plugin_health(available_modules, running_modules)

    with __profile_lock:
        for module in available_modules:
            plugin = __running.get(module)
            entry = __plugin_runtime.get(module, {})
            manifest = plugin_manifest(module)
            compatibility = plugin_compatibility(module)
            preflight = plugin_preflight(module)
            threads = []
            total_cpu = 0.0
            cpu_known = False

            for ident, thread_info in entry.get('threads', {}).items():
                native_id = thread_info.get('native_id')
                cpu_seconds = _thread_cpu_seconds(native_id)
                alive = any(thread.ident == ident and thread.is_alive() for thread in threading.enumerate())
                if cpu_seconds is not None:
                    total_cpu += cpu_seconds
                    cpu_known = True
                threads.append({
                    'name': thread_info.get('name', ''),
                    'ident': ident,
                    'native_id': native_id,
                    'alive': alive,
                    'managed': thread_info.get('managed', False),
                    'age_seconds': max(0, int(now - thread_info.get('started', now))),
                    'cpu_seconds': round(cpu_seconds, 3) if cpu_seconds is not None else None,
                })

            link = None
            if plugin is not None and getattr(plugin, 'LINK', None):
                link = plugin_url(plugin.LINK)

            cpu_seconds_value = round(total_cpu, 3) if cpu_known else None
            cpu_percent = None
            previous = __diagnostic_sample.get(module)
            if cpu_known and previous:
                elapsed = max(0.001, now - previous.get('time', now))
                cpu_delta = max(0.0, total_cpu - previous.get('cpu', total_cpu))
                cpu_percent = round((cpu_delta / elapsed) * 100.0, 1)
            if cpu_known:
                __diagnostic_sample[module] = {'time': now, 'cpu': total_cpu}

            data.append({
                'module': module,
                'name': getattr(plugin, 'NAME', None) if plugin is not None else plugin_name(module) or module,
                'menu': getattr(plugin, 'MENU', None) if plugin is not None else plugin_name_menu(module),
                'manifest': manifest,
                'version': manifest.get('version', ''),
                'compatibility': compatibility,
                'preflight': preflight,
                'running': module in running_modules,
                'enabled': module in options.enabled_plugins,
                'link': link,
                'started': entry.get('started', 0),
                'started_text': entry.get('started_text', ''),
                'restarts': entry.get('restarts', 0),
                'last_restart': entry.get('last_restart', ''),
                'last_error': entry.get('last_error', ''),
                'stop_requested': bool(
                    entry.get('runtime') and entry['runtime'].stop_event.is_set()
                ),
                'threads': threads,
                'thread_count': len([thread for thread in threads if thread['alive']]),
                'cpu_seconds': cpu_seconds_value,
                'cpu_percent': cpu_percent,
                'health': health_results[module],
            })

    data.sort(key=lambda item: (item['cpu_percent'] if item['cpu_percent'] is not None else -1, item['cpu_seconds'] if item['cpu_seconds'] is not None else -1), reverse=True)
    return data

################################################################################
# Plugin Options                                                               #
################################################################################
class PluginOptions(dict):
    def __init__(self, plugin, defaults):
        super(PluginOptions, self).__init__(iter(defaults.items()))
        self._defaults = defaults.copy()

        from ospy.options import options

        my_dir = path.dirname(path.abspath(__file__))
        plugin = 'plugin_unknown'
        stack = traceback.extract_stack()
        for tb in reversed(stack):
            abspath = path.dirname(path.abspath(tb[0]))
            if abspath.startswith(my_dir) and abspath != path.abspath(__file__):
                parts = abspath[len(my_dir):].split(path.sep)
                while parts and not parts[0]:
                    del parts[0]
                if parts:
                    plugin = 'plugin_' + parts[0]
                    break

        if plugin in options:
            for key, value in options[plugin].items():
                if key in self:
                    value_type = type(value)
                    if value_type == str:
                        value_type = str
                    default_type = type(self[key])
                    if default_type == str:
                        default_type = str

                    if value_type == default_type:
                        self[key] = value

        self._plugin = plugin

    def __setitem__(self, key, value):
        try:
            super(PluginOptions, self).__setitem__(key, value)
            if hasattr(self, '_plugin'):
                from ospy.options import options

                options[self._plugin] = self.copy()
        except ValueError:  # No index available yet
            pass

    def web_update(self, qdict, skipped=None):
        for key in list(self.keys()):
            try:
                if skipped is not None and key in skipped:
                    continue
                default_value = self._defaults[key]
                old_value = self[key]
                if isinstance(default_value, bool):
                    self[key] = True if qdict.get(key, 'off') == 'on' else False
                elif isinstance(default_value, int):
                    self[key] = int(qdict.get(key, old_value))
                elif isinstance(default_value, float):
                    self[key] = float(qdict.get(key, old_value))
                elif isinstance(default_value, str) or isinstance(old_value, str):
                    self[key] = qdict.get(key, old_value)
                elif isinstance(default_value, list):
                    self[key] = [int(x) for x in qdict.get(key, old_value)]           
            except ValueError:
                import web
                raise web.badrequest(_('Invalid value for') + ' ' + '%s:%s' % (key, qdict.get(key)))


################################################################################
# Plugin Repositories                                                          #
################################################################################
class _PluginChecker(threading.Thread):
    def __init__(self):
        super(_PluginChecker, self).__init__()
        self.daemon = True
        self._sleep_time = 0
        self._stop_event = threading.Event()
        self._lock = threading.RLock()

        self._repo_data = {}
        self._repo_contents = {}
        self._changes_cache = {}

        if os.environ.get('OSPY_DISABLE_BACKGROUND_THREADS') != '1':
            self.start()

    def update(self):
        self._sleep_time = 10

    def request_stop(self):
        """Ask the repository checker to stop without waiting for it."""
        self._stop_event.set()
        self.update()

    def wait_stopped(self, timeout=5.0):
        if self.is_alive() and self is not threading.current_thread():
            self.join(max(0.0, float(timeout)))
        return not self.is_alive()

    def _sleep(self, secs):
        import time
        self._sleep_time = secs
        while self._sleep_time > 0 and not self._stop_event.is_set():
            wait_time = min(1, self._sleep_time)
            if self._stop_event.wait(wait_time):
                break
            self._sleep_time -= wait_time
        return not self._stop_event.is_set()

    def run(self):
        from ospy.options import options
        from ospy.log import log
        import logging
        while not self._stop_event.is_set():
            try:
                if options.use_plugin_update:
                    self.refresh(install_updates=options.auto_plugin_update and not log.active_runs())

            except Exception:
                logging.error(_('Failed to update the plug-ins information') + ': {}'.format(traceback.format_exc()))
            finally:
                self._sleep(3600)

    def refresh(self, install_updates=False):
        from ospy.options import options
        import logging

        with self._lock:
            self._changes_cache.clear()
            for repo in REPOS:
                self._repo_data[repo] = self._download_zip(repo)
                self._repo_contents[repo] = self.zip_contents(self._get_zip(repo))

            status = options.plugin_status
            for plugin in available():
                update = self.available_version(plugin)
                if update is None:
                    continue
                current_hash = status.get(plugin, {}).get('hash') if isinstance(status.get(plugin), dict) else None
                if current_hash == update['hash']:
                    continue
                if self.sync_installed_status(plugin, update):
                    continue
                if install_updates:
                    compatibility = update.get('compatibility', {})
                    if not compatibility.get('compatible', False):
                        logging.warning(
                            _('Automatic update skipped for incompatible plug-in {}').format(
                                plugin
                            ) + ': ' +
                            '; '.join(compatibility.get('errors', []))
                        )
                        continue
                    logging.info(_('Updating the {} plug-in.').format(plugin))
                    self.install_repo_plugin(update['repo'], plugin)

    def available_version(self, plugin):
        with self._lock:
            result = None
            for repo_index, repo in enumerate(REPOS):
                repo_contents = self.get_repo_contents(repo)
                if plugin in repo_contents:
                    result = repo_contents[plugin].copy()
                    result['repo_index'] = repo_index
                    result['repo'] = repo
                    break
            return result

    @staticmethod
    def _download_zip(repo):
        from urllib.request import urlopen
        from contextlib import closing
        import logging
        import io

        with closing(urlopen(repo, timeout=30)) as response:
            content_length = response.headers.get('Content-Length')
            if content_length:
                try:
                    content_length = int(content_length)
                except (TypeError, ValueError):
                    content_length = None
            if (content_length is not None and
                    content_length > PLUGIN_ZIP_MAX_DOWNLOAD_BYTES):
                raise ValueError(_('Plug-in ZIP download is too large.'))
            zip_data = response.read(PLUGIN_ZIP_MAX_DOWNLOAD_BYTES + 1)
        if len(zip_data) > PLUGIN_ZIP_MAX_DOWNLOAD_BYTES:
            raise ValueError(_('Plug-in ZIP download is too large.'))
        logging.debug(_('Downloaded {}').format(repo))

        return io.BytesIO(zip_data)

    def _get_zip(self, repo):
        if repo not in self._repo_data:
            self._repo_data[repo] = self._download_zip(repo)
        return self._repo_data[repo]

    @staticmethod
    def _validated_zip(zip_file_data):
        """Open and fully validate a bounded, portable plug-in ZIP archive."""
        import stat
        import unicodedata
        import zipfile

        try:
            zip_file = zipfile.ZipFile(zip_file_data)
        except (zipfile.BadZipFile, OSError, ValueError):
            raise ValueError(_('Invalid plug-in ZIP archive.'))

        try:
            infos = zip_file.infolist()
            if len(infos) > PLUGIN_ZIP_MAX_FILES:
                raise ValueError(_('Plug-in ZIP contains too many files.'))

            seen_paths = set()
            total_size = 0
            reserved_names = {
                'con', 'prn', 'aux', 'nul',
                'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
                'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9',
            }
            for info in infos:
                original_name = info.filename
                name = original_name.replace('\\', '/')
                is_directory = (
                    info.is_dir() if hasattr(info, 'is_dir') else name.endswith('/')
                )
                path_name = name[:-1] if is_directory and name.endswith('/') else name
                parts = path_name.split('/')
                unsafe = (
                    not path_name or original_name != name or
                    '\x00' in path_name or name.startswith('/') or
                    re.match(r'^[A-Za-z]:', name) or
                    any(part in ('', '.', '..') for part in parts) or
                    len(path_name) > 1024 or
                    any(len(part) > 255 or part.endswith((' ', '.')) or ':' in part
                        for part in parts) or
                    any(part.split('.')[0].lower() in reserved_names for part in parts)
                )
                if unsafe:
                    raise ValueError(
                        _('Unsafe plug-in ZIP path: {}').format(original_name)
                    )

                normalized = unicodedata.normalize('NFC', '/'.join(parts)).casefold()
                if normalized in seen_paths:
                    raise ValueError(
                        _('Duplicate plug-in ZIP path: {}').format(original_name)
                    )
                seen_paths.add(normalized)

                mode = (info.external_attr >> 16) & 0xffff
                if stat.S_ISLNK(mode):
                    raise ValueError(
                        _('Symbolic links are not allowed in plug-in ZIP files.')
                    )
                file_type = stat.S_IFMT(mode)
                if file_type and not (
                        stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                    raise ValueError(
                        _('Special files are not allowed in plug-in ZIP files.')
                    )
                if info.flag_bits & 0x1:
                    raise ValueError(_('Encrypted plug-in ZIP files are not supported.'))
                if is_directory:
                    continue
                if info.file_size > PLUGIN_ZIP_MAX_FILE_BYTES:
                    raise ValueError(
                        _('A file in the plug-in ZIP is too large: {}').format(original_name)
                    )
                total_size += info.file_size
                if total_size > PLUGIN_ZIP_MAX_TOTAL_BYTES:
                    raise ValueError(_('Plug-in ZIP expands to too much data.'))
                if info.file_size and (
                        info.compress_size == 0 or
                        info.file_size > info.compress_size * PLUGIN_ZIP_MAX_RATIO):
                    raise ValueError(
                        _('Suspicious compression ratio in plug-in ZIP: {}').format(
                            original_name
                        )
                    )

            damaged = zip_file.testzip()
            if damaged:
                raise ValueError(
                    _('Damaged file in plug-in ZIP: {}').format(damaged)
                )
            return zip_file
        except Exception:
            zip_file.close()
            raise

    @staticmethod
    def zip_contents(zip_file_data, load_read_me=True):
        import os
        import datetime
        import hashlib
        import logging
        result = {}
        zip_file = None

        try:
            zip_file = _PluginChecker._validated_zip(zip_file_data)

            infos = zip_file.infolist()
            files = zip_file.namelist()
            inits = [f for f in files if f.endswith('__init__.py')]

            for init in inits:
                init_dir = os.path.dirname(init)
                plugin_id = os.path.basename(init_dir)
                read_me = ''
                manifest = {}
                manifest_name = init_dir + '/' + PLUGIN_MANIFEST_FILE
                manifest_present = manifest_name in files
                manifest_error = ''
                if manifest_name in files:
                    manifest_info = zip_file.getinfo(manifest_name)
                    if manifest_info.file_size > PLUGIN_MANIFEST_MAX_BYTES:
                        manifest_error = _('Plug-in manifest is too large.')
                    else:
                        manifest = _manifest_from_bytes(
                            zip_file.read(manifest_name), plugin_id
                        )
                        if not manifest:
                            manifest_error = _('Plug-in manifest is invalid.')
                else:
                    manifest_error = _('Plug-in manifest is missing.')

                compatibility = plugin_manifest_compatibility(
                    plugin_id,
                    manifest,
                    require_manifest=True,
                    manifest_error=manifest_error,
                )

                # Version information:
                plugin_hash = ''
                plugin_date = datetime.datetime(1970, 1, 1)
                plugin_files = {}
                plugin_zip_prefix = init_dir.rstrip('/\\') + '/'
                init_parts = [
                    part for part in init.replace('\\', '/').split('/') if part
                ]
                is_repository_plugin = (
                    len(init_parts) >= 3 and init_parts[-3] == 'plugins'
                )
                is_top_level_plugin = len(init_parts) == 2

                if is_repository_plugin or is_top_level_plugin:

                    # Check all files:
                    for zip_info in infos:
                        zip_name = zip_info.filename
                        if zip_name.startswith(plugin_zip_prefix):
                            relative_name = zip_name[len(plugin_zip_prefix):].lstrip('/\\')
                            if relative_name and not relative_name.endswith('/'):
                                plugin_date = max(plugin_date, datetime.datetime(*zip_info.date_time))
                                plugin_hash += hex(zip_info.CRC)
                                plugin_files[relative_name.replace('\\', '/')] = zip_info.CRC

                    if load_read_me:
                        try:
                            from ospy.helpers import gfm_str_to_html
                            if init_dir + '/README.md' in files:
                                read_me = gfm_str_to_html(
                                    zip_file.read(init_dir + '/README.md').decode('utf-8')
                                )
                            elif manifest.get('description'):
                                read_me = gfm_str_to_html(manifest['description'])
                        except Exception:
                            logging.error(_('Failed to read plug-in README') + ': {}'.format(traceback.format_exc()))
                            read_me = ''

                    if plugin_id in result:
                        raise ValueError(
                            _('Duplicate plug-in identifier in ZIP: {}').format(plugin_id)
                        )
                    if len(result) >= PLUGIN_ZIP_MAX_PLUGINS:
                        raise ValueError(_('Plug-in ZIP contains too many plug-ins.'))
                    result[plugin_id] = {
                        'name': (
                            manifest.get('name') or
                            _plugin_name(zip_file.read(init).decode('utf-8').splitlines())
                        ),
                        'manifest': manifest,
                        'manifest_present': manifest_present,
                        'manifest_valid': bool(manifest),
                        'manifest_error': manifest_error,
                        'compatibility': compatibility,
                        'version': manifest.get('version', ''),
                        'hash': hashlib.md5(plugin_hash.encode("utf-8")).hexdigest(),
                        'date': plugin_date,
                        'read_me': read_me,
                        'dir': init_dir,
                        'files': plugin_files
                    }

        except ValueError:
            raise
        except Exception:
            logging.error(_('Failed to read a plug-in zip file') + ': {}'.format(traceback.format_exc()))
            raise ValueError(_('Invalid plug-in ZIP archive.'))
        finally:
            if zip_file is not None:
                zip_file.close()

        return result

    def get_repo_contents(self, repo):
        import logging
        with self._lock:
            try:
                if repo not in self._repo_contents:
                    self._repo_contents[repo] = self.zip_contents(self._get_zip(repo))
            except Exception:
                logging.error(_('Failed to get contents of {}:').format(repo) + '\n' + traceback.format_exc())
                pass
                return {}

            result = {}
            for plugin, info in self._repo_contents[repo].items():
                current_info = info.copy()
                current_info['compatibility'] = plugin_manifest_compatibility(
                    plugin,
                    current_info.get('manifest', {}),
                    require_manifest=True,
                    manifest_error=current_info.get('manifest_error', ''),
                )
                result[plugin] = current_info
            return result

    @staticmethod
    def _local_file_crc(filename):
        import zlib

        crc = 0
        with open(filename, 'rb') as fh:
            for data in iter(lambda: fh.read(1024 * 64), b''):
                crc = zlib.crc32(data, crc)
        return crc & 0xffffffff

    def local_plugin_matches(self, plugin, repo_info):
        import os
        import logging

        repo_files = repo_info.get('files') if isinstance(repo_info, dict) else None
        if not repo_files:
            return False

        base_dir = plugin_dir(plugin)
        if not os.path.isdir(base_dir):
            return False

        try:
            for relative_name, repo_crc in repo_files.items():
                relative_path = os.path.normpath(relative_name)
                if os.path.isabs(relative_path) or relative_path.startswith('..' + os.path.sep) or relative_path == '..':
                    return False
                local_name = os.path.join(base_dir, relative_path)
                if not os.path.isfile(local_name):
                    return False
                if self._local_file_crc(local_name) != repo_crc:
                    return False
        except Exception:
            logging.error(_('Failed to check local plug-in status') + ': {}'.format(traceback.format_exc()))
            return False

        return True

    def sync_installed_status(self, plugin, repo_info=None):
        from ospy.options import options

        if repo_info is None:
            repo_info = self.available_version(plugin)
        if repo_info is None or not self.local_plugin_matches(plugin, repo_info):
            return False

        current_info = options.plugin_status.get(plugin)
        if isinstance(current_info, dict) and current_info.get('hash') == repo_info['hash']:
            return False

        plugin_status = dict(options.plugin_status)
        plugin_status[plugin] = {
            'hash': repo_info['hash'],
            'date': repo_info['date']
        }
        options.plugin_status = plugin_status
        return True

    def sync_installed_statuses(self):
        changed = False
        for plugin in available():
            if self.sync_installed_status(plugin):
                changed = True
        return changed

    @staticmethod
    def _github_repo_info(repo):
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)/archive/([^/]+)\.zip', repo)
        if not match:
            return None
        owner, name, branch = match.groups()
        return owner, name, branch

    def plugin_changes(self, plugin, repo_index=0, limit=20, force=False):
        import datetime
        import json
        import logging
        import time
        from urllib.parse import urlencode
        from urllib.request import Request, urlopen
        from ospy.options import options

        repo = REPOS[repo_index]
        repo_info = self._github_repo_info(repo)
        if repo_info is None:
            return []

        status = options.plugin_status
        since = None
        if plugin in status and isinstance(status[plugin], dict):
            installed_date = status[plugin].get('date')
            if isinstance(installed_date, datetime.datetime):
                since = installed_date.isoformat() + 'Z'

        cache_key = (plugin, repo_index, since, limit)
        cached = self._changes_cache.get(cache_key)
        if not force and cached is not None and time.time() - cached['time'] < 600:
            return cached['changes']

        owner, name, branch = repo_info
        params = {
            'sha': branch,
            'path': 'plugins/{}'.format(plugin),
            'per_page': limit
        }
        if since:
            params['since'] = since

        url = 'https://api.github.com/repos/{}/{}/commits?{}'.format(owner, name, urlencode(params))
        changes = []

        try:
            request = Request(url, headers={'User-Agent': 'OSPy plugin manager'})
            response = urlopen(request, timeout=20)
            data = json.loads(response.read().decode('utf-8'))
            for item in data:
                commit = item.get('commit', {})
                author = commit.get('author') or {}
                message = (commit.get('message') or '').splitlines()[0]
                sha = item.get('sha', '')
                changes.append({
                    'sha': sha[:7],
                    'date': author.get('date', ''),
                    'message': message,
                    'url': item.get('html_url', '')
                })
        except Exception:
            logging.error(_('Failed to get plug-in changes') + ': {}'.format(traceback.format_exc()))

        self._changes_cache[cache_key] = {'time': time.time(), 'changes': changes}
        return changes

    @staticmethod
    def _install_repo_docs(zip_file_data):
        import os
        from ospy.helpers import mkdir_p

        allowed_docs = {'README.md', 'CHANGELOG.md'}
        target_dir = plugin_dir()
        target_dir_abs = os.path.abspath(target_dir)

        zip_file = _PluginChecker._validated_zip(zip_file_data)
        try:
            files = zip_file.namelist()
            repo_roots = set()
            for filename in files:
                zip_name = filename.replace('\\', '/')
                if not zip_name.endswith('/__init__.py'):
                    continue
                parts = [part for part in zip_name.split('/') if part]
                if len(parts) >= 4 and parts[1] == 'plugins':
                    repo_roots.add(parts[0])

            for zip_info in zip_file.infolist():
                zip_name = zip_info.filename.replace('\\', '/')
                parts = [part for part in zip_name.split('/') if part]
                if (len(parts) != 2 or parts[1] not in allowed_docs or
                        parts[0] not in repo_roots):
                    continue
                is_directory = (
                    zip_info.is_dir() if hasattr(zip_info, 'is_dir')
                    else zip_name.endswith('/')
                )
                if is_directory:
                    continue

                target_name = os.path.abspath(os.path.join(target_dir, parts[1]))
                if os.path.commonpath([target_dir_abs, target_name]) != target_dir_abs:
                    raise ValueError(
                        _('Unsafe plug-in ZIP path: {}').format(zip_info.filename)
                    )

                mkdir_p(os.path.dirname(target_name))
                with open(target_name, 'wb') as fh:
                    fh.write(zip_file.read(zip_info.filename))
        finally:
            zip_file.close()

    @staticmethod
    def _install_plugin(zip_file_data, plugin, p_dir):
        import os
        import shutil
        import tempfile
        import datetime
        import hashlib
        from ospy.helpers import mkdir_p
        from ospy.helpers import del_rw
        from ospy.options import options

        enabled = plugin in options.enabled_plugins
        target_dir = plugin_dir(plugin)
        plugins_dir = plugin_dir()
        mkdir_p(plugins_dir)
        transaction_dir = tempfile.mkdtemp(
            prefix='.ospy-plugin-install-', dir=plugins_dir
        )
        staged_dir = os.path.join(transaction_dir, 'new')
        backup_dir = os.path.join(transaction_dir, 'old')
        failed_dir = os.path.join(transaction_dir, 'failed')
        mkdir_p(staged_dir)

        old_status = dict(options.plugin_status)
        had_old_plugin = os.path.exists(target_dir)
        swapped = False
        plugin_hash = ''
        plugin_date = datetime.datetime(1970, 1, 1)
        plugin_zip_prefix = p_dir.rstrip('/\\').replace('\\', '/') + '/'

        try:
            old_data = os.path.join(target_dir, 'data')
            staged_data = os.path.join(staged_dir, 'data')
            if os.path.isdir(old_data):
                shutil.copytree(
                    old_data, staged_data, symlinks=True, dirs_exist_ok=True
                )

            zip_file = _PluginChecker._validated_zip(zip_file_data)
            try:
                for zip_info in zip_file.infolist():
                    zip_name = zip_info.filename.replace('\\', '/')
                    if not zip_name.startswith(plugin_zip_prefix):
                        continue
                    is_directory = (
                        zip_info.is_dir() if hasattr(zip_info, 'is_dir')
                        else zip_name.endswith('/')
                    )
                    relative_name = zip_name[len(plugin_zip_prefix):].rstrip('/')
                    if not relative_name:
                        continue
                    target_name = os.path.join(
                        staged_dir, *relative_name.split('/')
                    )
                    if is_directory:
                        mkdir_p(target_name)
                        continue
                    plugin_date = max(
                        plugin_date, datetime.datetime(*zip_info.date_time)
                    )
                    plugin_hash += hex(zip_info.CRC)
                    mkdir_p(os.path.dirname(target_name))
                    with zip_file.open(zip_info, 'r') as source, \
                            open(target_name, 'wb') as target:
                        shutil.copyfileobj(source, target, 1024 * 64)
            finally:
                zip_file.close()

            if not os.path.isfile(os.path.join(staged_dir, '__init__.py')):
                raise ValueError(_('Plug-in ZIP does not contain __init__.py.'))

            if enabled:
                stop_plugin(plugin)
            if had_old_plugin:
                os.replace(target_dir, backup_dir)
            os.replace(staged_dir, target_dir)
            swapped = True

            plugin_status = dict(options.plugin_status)
            plugin_status[plugin] = {
                'hash': hashlib.md5(plugin_hash.encode('utf-8')).hexdigest(),
                'date': plugin_date
            }
            options.plugin_status = plugin_status
            _clear_plugin_caches(plugin)
            _unload_plugin_modules(plugin)

            if enabled and not reload_plugin(plugin):
                raise RuntimeError(
                    _('Updated plug-in failed to start; the previous version was restored.')
                )
        except Exception:
            if swapped and os.path.exists(target_dir):
                os.replace(target_dir, failed_dir)
            if had_old_plugin and os.path.exists(backup_dir):
                os.replace(backup_dir, target_dir)
            options.plugin_status = old_status
            enabled_plugins = list(options.enabled_plugins)
            if enabled and plugin not in enabled_plugins:
                enabled_plugins.append(plugin)
                options.enabled_plugins = enabled_plugins
            elif not enabled and plugin in enabled_plugins:
                enabled_plugins.remove(plugin)
                options.enabled_plugins = enabled_plugins
            _clear_plugin_caches(plugin)
            _unload_plugin_modules(plugin)
            if enabled and had_old_plugin:
                try:
                    reload_plugin(plugin)
                except Exception:
                    pass
            raise
        finally:
            if os.path.isdir(transaction_dir):
                shutil.rmtree(transaction_dir, onerror=del_rw)

    def install_repo_plugin(self, repo, plugin_filter):
        import logging
        logging.info(_('Installing plug-in from repository {} plugin {}').format(repo, plugin_filter if plugin_filter else _('all plugins')))
        return self.install_custom_plugin(self._get_zip(repo), plugin_filter)

    def install_custom_plugin(self, zip_file_data, plugin_filter=None):
        contents = self.zip_contents(zip_file_data, False)
        if not contents:
            raise ValueError(_('No installable plug-ins were found in the ZIP file.'))
        if plugin_filter is not None and plugin_filter not in contents:
            raise ValueError(
                _('Requested plug-in was not found in the ZIP file') +
                ': ' + str(plugin_filter)
            )

        selected = {
            plugin: info for plugin, info in contents.items()
            if plugin_filter is None or plugin == plugin_filter
        }
        result = {
            'installed': [],
            'blocked': {},
            'warnings': {},
        }
        for plugin, info in selected.items():
            compatibility = plugin_manifest_compatibility(
                plugin,
                info.get('manifest', {}),
                require_manifest=True,
                manifest_error=info.get('manifest_error', ''),
            )
            info['compatibility'] = compatibility
            if not compatibility.get('compatible', False):
                result['blocked'][plugin] = list(
                    compatibility.get('errors') or
                    [_('Plug-in is incompatible with this OSPy installation.')]
                )
            elif compatibility.get('warnings'):
                result['warnings'][plugin] = list(compatibility['warnings'])

        if plugin_filter is not None and result['blocked']:
            reasons = result['blocked'][plugin_filter]
            raise ValueError(
                _('Plug-in cannot be installed') + ': ' +
                '; '.join(reasons)
            )

        installable = [
            (plugin, info) for plugin, info in selected.items()
            if plugin not in result['blocked']
        ]
        if not installable:
            blocked_details = []
            for plugin, reasons in sorted(result['blocked'].items()):
                blocked_details.append(
                    '{}: {}'.format(plugin, '; '.join(reasons))
                )
            raise ValueError(
                _('No compatible plug-ins are available for installation.') +
                (' ' + ' | '.join(blocked_details) if blocked_details else '')
            )

        for plugin, info in installable:
            self._install_plugin(zip_file_data, plugin, info['dir'])
            result['installed'].append(plugin)
        self._install_repo_docs(zip_file_data)
        return result

checker = _PluginChecker()


################################################################################
# Plugin App                                                                   #
################################################################################
def get_app():
    import web

    class PluginApp(web.application):
        def handle(self):
            from ospy.server import session

            mapping = []
            for module in running():
                import_name = __name__ + '.' + module
                plugin = get(module)
                mapping += _get_urls(import_name, plugin)
            fn, args = self._match(mapping, web.ctx.path)
            
            if session['category'] == 'admin':
                return self._delegate(fn, self.fvars, args)
            else:
                return ''    
    
    return PluginApp(fvars=locals())


################################################################################
# Plugin directories                                                           #
################################################################################
def plugin_dir(module=None):
    my_dir = path.dirname(path.abspath(__file__))

    if module is not None:
        if module.startswith('plugins.'):
            module = module[8:]
    else:
        stack = traceback.extract_stack()
        module = ''
        for tb in reversed(stack):
            tb_dir = path.dirname(path.abspath(tb[0]))
            if 'plugins' in tb_dir and tb_dir != my_dir:
                module = path.basename(tb_dir)
                break

    return path.join(my_dir, module)


def plugin_data_dir(module=None):
    return path.join(plugin_dir(module), 'data')


def plugin_docs_dir(module=None):
    return path.join(plugin_dir(module), 'docs')


################################################################################
# Plugin information + urls                                                    #
################################################################################
def _normalize_plugin_manifest(data, module=None):
    """Return a safe copy of a plug-in manifest or an empty dictionary."""
    if not isinstance(data, dict):
        return {}

    manifest = dict(data)
    schema_version = manifest.get('schema_version', PLUGIN_MANIFEST_SCHEMA_VERSION)
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or schema_version < 1:
        return {}
    manifest['schema_version'] = schema_version

    for key in ('id', 'name', 'menu', 'version', 'description', 'author',
                'homepage', 'license'):
        value = manifest.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            return {}
        manifest[key] = value.strip()
        if len(manifest[key]) > (4096 if key == 'description' else 255):
            return {}

    if module and manifest.get('id') and manifest['id'] != module:
        return {}
    if manifest.get('id') and not re.match(r'^[a-z0-9][a-z0-9_]*$', manifest['id']):
        return {}
    if module and not manifest.get('id'):
        manifest['id'] = module
    if manifest.get('homepage') and not manifest['homepage'].lower().startswith(
            ('https://', 'http://')):
        return {}

    for key in ('ospy', 'python', 'requirements', 'hardware', 'permissions',
                'conflicts'):
        value = manifest.get(key)
        if value is not None and not isinstance(value, (dict, list)):
            return {}

    return manifest


def _manifest_from_bytes(contents, module=None):
    if not isinstance(contents, bytes) or len(contents) > PLUGIN_MANIFEST_MAX_BYTES:
        return {}
    try:
        data = json.loads(contents.decode('utf-8-sig'))
    except (UnicodeDecodeError, ValueError):
        return {}
    return _normalize_plugin_manifest(data, module)


def plugin_manifest(plugin):
    """Read optional plugin.json metadata without importing the plug-in."""
    import logging

    if plugin not in __manifest_cache:
        __manifest_cache[plugin] = {}
        filename = path.join(plugin_dir(plugin), PLUGIN_MANIFEST_FILE)
        if path.isfile(filename):
            try:
                if path.getsize(filename) > PLUGIN_MANIFEST_MAX_BYTES:
                    raise ValueError(_('Plug-in manifest is too large.'))
                with open(filename, 'rb') as fh:
                    manifest = _manifest_from_bytes(fh.read(), plugin)
                if not manifest:
                    raise ValueError(_('Plug-in manifest is invalid.'))
                __manifest_cache[plugin] = manifest
            except Exception:
                logging.error(
                    _('Failed to read plug-in manifest') +
                    ': {} {}'.format(plugin, traceback.format_exc())
                )
    return dict(__manifest_cache[plugin])


def _version_parts(value):
    """Return a comparison-friendly numeric version tuple."""
    if value is None:
        return ()
    parts = re.findall(r'\d+', str(value))
    return tuple(int(part) for part in parts[:4])


def _version_in_range(current, constraints):
    if not isinstance(constraints, dict):
        return True
    current_parts = _version_parts(current)
    minimum = _version_parts(constraints.get('min'))
    maximum = _version_parts(constraints.get('max'))
    if minimum and current_parts[:len(minimum)] < minimum:
        return False
    if maximum and current_parts[:len(maximum)] > maximum:
        return False
    return True


def _manifest_list(value):
    if isinstance(value, list):
        return value
    return []


def _hardware_manifest(manifest):
    hardware = manifest.get('hardware', {})
    if isinstance(hardware, list):
        return {'requires': hardware}
    return hardware if isinstance(hardware, dict) else {}


def _normalized_resource(value):
    if isinstance(value, int):
        return str(value)
    return str(value).strip().lower()


def plugin_manifest_compatibility(module, manifest, enabled_modules=None,
                                  require_manifest=False, manifest_error=''):
    """Validate supplied manifest data against this OSPy installation."""
    if not manifest:
        if require_manifest:
            error = manifest_error or _(
                'A valid plugin.json manifest is required for installation.'
            )
            return {
                'status': 'error',
                'compatible': False,
                'summary': _('Cannot be installed.'),
                'errors': [error],
                'warnings': [],
                'permissions': [],
            }
        return {
            'status': 'legacy',
            'compatible': True,
            'summary': _('Legacy, without manifest.'),
            'errors': [],
            'warnings': [],
            'permissions': [],
        }

    from ospy import version
    from ospy.helpers import determine_platform

    errors = []
    warnings = []
    if not _version_in_range(version.ver_str, manifest.get('ospy')):
        errors.append(
            _('OSPy version {} is outside the supported range.').format(
                version.ver_str
            )
        )
    python_version = '.'.join(str(part) for part in sys.version_info[:3])
    if not _version_in_range(python_version, manifest.get('python')):
        errors.append(
            _('Python version {} is outside the supported range.').format(
                python_version
            )
        )

    for requirement in _manifest_list(manifest.get('requirements')):
        if isinstance(requirement, str):
            module_name = requirement
            required = True
        elif isinstance(requirement, dict):
            module_name = requirement.get('module') or requirement.get('name')
            required = requirement.get('required', True) is not False
        else:
            warnings.append(_('Invalid Python requirement declaration.'))
            continue
        if not module_name or not isinstance(module_name, str):
            warnings.append(_('Invalid Python requirement declaration.'))
            continue
        try:
            available_module = importlib.util.find_spec(module_name) is not None
        except (ImportError, AttributeError, ValueError):
            available_module = False
        if not available_module:
            message = _('Python module {} is not installed.').format(module_name)
            (errors if required else warnings).append(message)

    hardware = _hardware_manifest(manifest)
    platform_name = determine_platform() or ('windows' if os.name == 'nt' else 'linux')
    allowed_platforms = [
        _normalized_resource(item)
        for item in _manifest_list(hardware.get('platforms'))
    ]
    platform_aliases = {
        'pi': {'pi', 'raspberry_pi', 'raspberry-pi', 'linux'},
        'bo': {'bo', 'beaglebone', 'beaglebone_black', 'linux'},
        'nt': {'nt', 'windows'},
        'windows': {'nt', 'windows'},
        'linux': {'linux'},
    }
    current_platforms = platform_aliases.get(platform_name, {platform_name})
    if allowed_platforms and not current_platforms.intersection(allowed_platforms):
        errors.append(
            _('This plug-in does not support platform {}.').format(platform_name)
        )

    hardware_requirements = {
        _normalized_resource(item)
        for item in _manifest_list(hardware.get('requires'))
    }
    if 'gpio' in hardware_requirements and platform_name not in ('pi', 'bo'):
        errors.append(_('Required GPIO hardware is not available.'))
    if 'i2c' in hardware_requirements:
        i2c_available = (
            importlib.util.find_spec('smbus') is not None or
            importlib.util.find_spec('smbus2') is not None or
            (os.name == 'posix' and os.path.exists('/dev/i2c-1'))
        )
        if not i2c_available:
            errors.append(_('Required I2C support is not available.'))

    permissions = [
        _normalized_resource(item)
        for item in _manifest_list(manifest.get('permissions'))
    ]
    unknown_permissions = sorted(set(permissions) - PLUGIN_PERMISSIONS)
    if unknown_permissions:
        warnings.append(
            _('Unknown plug-in permissions') + ': ' + ', '.join(unknown_permissions)
        )

    if enabled_modules is None:
        from ospy.options import options
        enabled_modules = list(options.enabled_plugins)
    enabled_modules = set(enabled_modules)
    conflicts = manifest.get('conflicts', {})
    if isinstance(conflicts, list):
        conflicts = {'plugins': conflicts}
    explicit_conflicts = {
        str(item) for item in _manifest_list(conflicts.get('plugins'))
    } if isinstance(conflicts, dict) else set()
    active_conflicts = sorted(explicit_conflicts.intersection(enabled_modules) - {module})
    if active_conflicts:
        errors.append(
            _('Conflicting plug-ins are enabled') + ': ' + ', '.join(active_conflicts)
        )

    gpio = {
        _normalized_resource(item)
        for item in _manifest_list(hardware.get('gpio'))
    }
    i2c = {
        _normalized_resource(item)
        for item in _manifest_list(hardware.get('i2c'))
    }
    for other in sorted(enabled_modules - {module}):
        other_manifest = plugin_manifest(other)
        if not other_manifest:
            continue
        other_conflicts = other_manifest.get('conflicts', {})
        if isinstance(other_conflicts, list):
            other_conflicts = {'plugins': other_conflicts}
        other_plugin_conflicts = {
            str(item) for item in _manifest_list(other_conflicts.get('plugins'))
        } if isinstance(other_conflicts, dict) else set()
        if module in other_plugin_conflicts:
            errors.append(_('Conflicting plug-in is enabled') + ': ' + other)
        other_hardware = _hardware_manifest(other_manifest)
        other_gpio = {
            _normalized_resource(item)
            for item in _manifest_list(other_hardware.get('gpio'))
        }
        other_i2c = {
            _normalized_resource(item)
            for item in _manifest_list(other_hardware.get('i2c'))
        }
        shared_gpio = sorted(gpio.intersection(other_gpio))
        shared_i2c = sorted(i2c.intersection(other_i2c))
        if shared_gpio:
            errors.append(
                _('GPIO conflict with {}').format(other) + ': ' + ', '.join(shared_gpio)
            )
        if shared_i2c:
            errors.append(
                _('I2C conflict with {}').format(other) + ': ' + ', '.join(shared_i2c)
            )

    status = 'error' if errors else ('warning' if warnings else 'ok')
    return {
        'status': status,
        'compatible': not errors,
        'summary': (
            _('Compatibility problems found.')
            if errors else (
                _('Compatible with warnings.') if warnings else _('Compatible.')
            )
        ),
        'errors': errors,
        'warnings': warnings,
        'permissions': permissions,
    }


def plugin_compatibility(module, enabled_modules=None):
    """Validate an installed plug-in without importing it."""
    return plugin_manifest_compatibility(
        module, plugin_manifest(module), enabled_modules=enabled_modules
    )


def plugin_preflight(module):
    """Statically validate a plug-in without importing or executing its code."""
    base_dir = os.path.realpath(plugin_dir(module))
    plugin_root = os.path.realpath(plugin_dir())
    errors = []
    warnings = []
    checked_files = 0
    total_bytes = 0
    entry_ast = None

    try:
        if os.path.commonpath([plugin_root, base_dir]) != plugin_root:
            errors.append(_('Plug-in directory is outside the plug-in root.'))
        elif not os.path.isdir(base_dir):
            errors.append(_('Plug-in directory does not exist.'))
    except (OSError, ValueError):
        errors.append(_('Plug-in directory is invalid.'))

    init_file = os.path.join(base_dir, '__init__.py')
    if not os.path.isfile(init_file):
        errors.append(_('Plug-in entry file __init__.py is missing.'))

    if not errors:
        for root, dirs, files in os.walk(base_dir, followlinks=False):
            safe_dirs = []
            for directory in dirs:
                directory_path = os.path.join(root, directory)
                if os.path.islink(directory_path):
                    warnings.append(
                        _('Symbolic link directory was not checked') + ': ' +
                        os.path.relpath(directory_path, base_dir)
                    )
                else:
                    safe_dirs.append(directory)
            dirs[:] = safe_dirs

            for filename in files:
                if not filename.endswith('.py'):
                    continue
                checked_files += 1
                if checked_files > PLUGIN_PREFLIGHT_MAX_FILES:
                    errors.append(_('Plug-in contains too many Python files.'))
                    break
                file_path = os.path.join(root, filename)
                if os.path.islink(file_path):
                    warnings.append(
                        _('Symbolic link file was not checked') + ': ' +
                        os.path.relpath(file_path, base_dir)
                    )
                    continue
                try:
                    size = os.path.getsize(file_path)
                    total_bytes += size
                    if size > PLUGIN_PREFLIGHT_MAX_FILE_BYTES:
                        errors.append(
                            _('Python file is too large') + ': ' +
                            os.path.relpath(file_path, base_dir)
                        )
                        continue
                    if total_bytes > PLUGIN_PREFLIGHT_MAX_TOTAL_BYTES:
                        errors.append(_('Plug-in Python sources are too large.'))
                        break
                    with tokenize.open(file_path) as source_file:
                        source = source_file.read()
                    parsed = ast.parse(source, filename=file_path)
                    compile(parsed, file_path, 'exec')
                    if os.path.realpath(file_path) == os.path.realpath(init_file):
                        entry_ast = parsed
                except (OSError, SyntaxError, UnicodeError) as err:
                    errors.append(
                        _('Python source check failed') + ': {} ({})'.format(
                            os.path.relpath(file_path, base_dir), err
                        )
                    )
            if errors and (
                    checked_files > PLUGIN_PREFLIGHT_MAX_FILES or
                    total_bytes > PLUGIN_PREFLIGHT_MAX_TOTAL_BYTES):
                break

    if entry_ast is not None and plugin_manifest(module):
        functions = {
            node.name for node in entry_ast.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for function_name in ('start', 'stop'):
            if function_name not in functions:
                errors.append(
                    _('Required plug-in function is missing') + ': ' +
                    function_name + '()'
                )

    manifest_file = os.path.join(base_dir, PLUGIN_MANIFEST_FILE)
    if os.path.isfile(manifest_file) and not plugin_manifest(module):
        errors.append(_('Plug-in manifest is invalid.'))

    status = 'error' if errors else ('warning' if warnings else 'ok')
    return {
        'status': status,
        'passed': not errors,
        'summary': (
            _('Failed.')
            if errors else (
                _('Passed with warnings.')
                if warnings else _('Passed.')
            )
        ),
        'errors': errors,
        'warnings': warnings,
        'checked_files': checked_files,
        'total_bytes': total_bytes,
    }


def available():
    plugins = []
    for imp, module, is_pkg in pkgutil.iter_modules(['plugins']):
        _protect(module)
        if plugin_name(module) is not None:
            plugins.append(module)
    return plugins


def _plugin_name(lines):
    result = None
    for line in lines:
        if 'NAME' in line:
            match = re.search('NAME\\s=\\s("|\')([^"\']+)("|\')', line)
            if match is not None:
                result = match.group(2)
    return result


__name_cache = {}
def plugin_name(plugin):
    """Tries to find the name of the given plugin without importing it yet."""
    import logging
    if plugin not in __name_cache:
        manifest_name = plugin_manifest(plugin).get('name')
        __name_cache[plugin] = manifest_name or None
        filename = path.join(path.dirname(__file__), plugin, '__init__.py')
        if not __name_cache[plugin]:
            try:
                with open(filename, encoding='utf-8') as fh:
                    __name_cache[plugin] = _plugin_name(fh)
            except Exception:
                logging.error(_('Failed to read in NAME plugin') + ': {} {}'.format(plugin, traceback.format_exc()))
    return __name_cache[plugin]


def _plugin_name_menu(lines):
    result = None
    for line in lines:
        if 'MENU' in line:
#TODO translation and re
            match = re.search('MENU\\s=\\s("|\')([^"\']+)("|\')', line)
            if match is not None:
                result = match.group(2)
    return result


__name_cache_menu = {}
def plugin_name_menu(plugin):
    """Tries to find the menu translated name of the given plugin without importing it yet."""
    import logging
    if plugin not in __name_cache_menu:
        manifest_menu = plugin_manifest(plugin).get('menu')
        __name_cache_menu[plugin] = manifest_menu or None
        filename = path.join(path.dirname(__file__), plugin, '__init__.py')
        if not __name_cache_menu[plugin]:
            try:
                with open(filename, encoding='utf-8') as fh:
                    __name_cache_menu[plugin] = _plugin_name_menu(fh)
            except Exception:
                logging.error(_('Failed to read in MENU name plugin') + ': {} {}'.format(plugin, traceback.format_exc()))
    return __name_cache_menu[plugin]    


def plugin_names():
    return {plugin: (plugin_name(plugin)) for plugin in available() if plugin_name(plugin)}


def plugin_url(cls, prefix='/plugins/'):
    from ospy.webpages import WebPage
    import inspect

    if cls is None:
        result = cls
    else:
        if inspect.isclass(cls) and issubclass(cls, WebPage):
            cls = cls.__module__ + '.' + cls.__name__

        parts = cls.split('.')
        if len(parts) >= 3:
            result = prefix + '/'.join(parts[1:])
        elif len(parts) >= 2:
            result = prefix + '/'.join(parts)
        else:
            result = prefix + cls

        if result.endswith('_page'):
            result = result[:-5]

        if result.endswith('_json'):
            result = result[:-5] + '.json'

        if result.endswith('_csv'):
            result = result[:-4] + '.csv'

        return result


__urls_cache = {}
def _get_urls(import_name, plugin):
    if plugin not in __urls_cache:
        from ospy.webpages import WebPage
        import inspect

        result = []
        for element in dir(plugin):
            if inspect.isclass(getattr(plugin, element)) and issubclass(getattr(plugin, element), WebPage):
                if import_name == getattr(plugin, element).__module__:
                    classname = import_name + '.' + element
                    result.append((plugin_url(classname, '/'), classname))
        __urls_cache[plugin] = result

    return __urls_cache[plugin]


################################################################################
# Plugin start/stop                                                            #
################################################################################
def stop_plugin(module, timeout=PLUGIN_THREAD_STOP_TIMEOUT):
    from ospy.options import options
    import logging

    plugin = __running.get(module)
    alive_threads = []
    if plugin is not None:
        plugin_n = getattr(plugin, 'NAME', module)
        entry = _runtime_entry(module)
        runtime = entry.get('runtime')
        if runtime is not None:
            runtime.request_stop()
        stop_deadline = time.time() + max(0.0, float(timeout))
        stop_result = {'error': ''}

        def call_plugin_stop():
            try:
                plugin.stop()
            except Exception:
                stop_result['error'] = traceback.format_exc()

        stop_worker = threading.Thread(
            target=call_plugin_stop,
            name='OSPy plug-in stop {}'.format(module),
        )
        stop_worker.daemon = True
        stop_worker.start()
        _register_plugin_thread(module, stop_worker, managed=True)
        stop_worker.join(max(0.0, stop_deadline - time.time()))
        if stop_worker.is_alive():
            entry['last_error'] = _('Plug-in stop function timed out.')
            logging.error(
                _('Failed to stop the') + ': {} {}'.format(
                    plugin_n, entry['last_error']
                )
            )
        elif stop_result['error']:
            entry['last_error'] = stop_result['error']
            logging.error(
                _('Failed to stop the') + ': {} {}'.format(
                    plugin_n, stop_result['error']
                )
            )

        try:
            alive_threads = (
                runtime.join(max(0.0, stop_deadline - time.time()))
                if runtime is not None else []
            )
            if stop_worker.is_alive():
                alive_threads.append(stop_worker)
            tracked_threads = [
                info.get('thread') for info in entry.get('threads', {}).values()
                if info.get('thread') is not None
            ]
            for thread in tracked_threads:
                if (thread is threading.current_thread() or
                        not thread.is_alive() or thread in alive_threads):
                    continue
                remaining = max(0.0, stop_deadline - time.time())
                if remaining:
                    thread.join(remaining)
                if thread.is_alive():
                    alive_threads.append(thread)
            if alive_threads:
                thread_names = ', '.join(
                    thread.name or str(thread.ident) for thread in alive_threads
                )
                entry['last_error'] = (
                    _('Plug-in threads did not stop in time') + ': ' + thread_names
                )
                logging.error(entry['last_error'])
            elif not entry.get('last_error'):
                logging.info(_('Stopped the') + ': {}'.format(plugin_n))
        finally:
            __running.pop(module, None)
            with __profile_lock:
                for ident in list(__thread_plugin.keys()):
                    thread_info = entry.get('threads', {}).get(ident, {})
                    thread = thread_info.get('thread')
                    if (__thread_plugin.get(ident) == module and
                            (thread is None or not thread.is_alive())):
                        __thread_plugin.pop(ident, None)

    try:
        from ospy.webpages import clear_plugin_runtime_data
        clear_plugin_runtime_data(module)
    except Exception:
        logging.error(_('Failed to clear runtime data for the plug-in') + ': {} {}'.format(module, traceback.format_exc()))

    if not alive_threads:
        _clear_plugin_caches(module)
        _unload_plugin_modules(module)

    if module not in options.enabled_plugins and not alive_threads:
        _protect(module)

    return not alive_threads


def start_plugin(module):
    from ospy.helpers import mkdir_p
    from ospy.options import options
    import logging

    if module not in options.enabled_plugins or module in __running:
        return module in __running

    plugin_n = module
    try:
        previous_entry = _runtime_entry(module)
        lingering_threads = [
            info.get('thread')
            for info in previous_entry.get('threads', {}).values()
            if info.get('thread') is not None and info['thread'].is_alive()
        ]
        if lingering_threads:
            raise RuntimeError(
                _('Plug-in still has running threads') + ': ' +
                ', '.join(thread.name for thread in lingering_threads)
            )

        preflight = plugin_preflight(module)
        if not preflight['passed']:
            raise RuntimeError(
                _('Plug-in pre-activation test failed') + ': ' +
                '; '.join(preflight['errors'])
            )

        compatibility = plugin_compatibility(module)
        if not compatibility['compatible']:
            raise RuntimeError(
                _('Plug-in compatibility check failed') + ': ' +
                '; '.join(compatibility['errors'])
            )

        _clear_plugin_caches(module)
        _unload_plugin_modules(module)

        import_name = _plugin_import_name(module)
        entry = _runtime_entry(module)
        entry['threads'] = {}
        entry['runtime'] = PluginRuntime(module)
        entry['last_error'] = ''
        plugin = importlib.import_module(import_name)
        manifest = plugin_manifest(module)
        plugin_n = getattr(plugin, 'NAME', None) or manifest.get('name') or module
        if not getattr(plugin, 'NAME', None):
            plugin.NAME = plugin_n
        if not getattr(plugin, 'MENU', None) and manifest.get('menu'):
            plugin.MENU = manifest['menu']
        if not hasattr(plugin, 'LINK'):
            plugin.LINK = None
        plugin.RUNTIME = entry['runtime']

        mkdir_p(plugin_data_dir(module))
        mkdir_p(plugin_docs_dir(module))

        entry['started'] = time.time()
        entry['started_text'] = _now_string()

        _track_threads_started_by(module, plugin.start)
        __running[module] = plugin
        logging.info(_('Started the') + ': {}'.format(plugin_n))

        if (isinstance(plugin.LINK, str) and
                not (plugin.LINK.startswith(module) or plugin.LINK.startswith(__name__))):
            plugin.LINK = module + '.' + plugin.LINK

        return True

    except Exception:
        _runtime_entry(module)['last_error'] = traceback.format_exc()
        logging.error(_('Failed to load the') + ' {} {}'.format(plugin_n, traceback.format_exc()))
        if module in options.enabled_plugins:
            options.enabled_plugins.remove(module)
            options.enabled_plugins = options.enabled_plugins
        _clear_plugin_caches(module)
        _unload_plugin_modules(module)
        _protect(module)
        return False


def reload_plugin(module):
    entry = _runtime_entry(module)
    entry['restarts'] = entry.get('restarts', 0) + 1
    entry['last_restart'] = _now_string()
    stop_plugin(module)
    return start_plugin(module)


def start_enabled_plugins():
    from ospy.options import options
    
    for module in available():
        if module in options.enabled_plugins and module not in __running:
            start_plugin(module)

    for module in list(__running.keys()):
        if module not in options.enabled_plugins:
            stop_plugin(module)


def stop_all_plugins(timeout=10.0):
    """Stop every running plug-in within one shared shutdown window."""
    modules = list(running())
    deadline = time.time() + max(0.0, float(timeout))

    # Signal all cooperative workers first so they can stop concurrently while
    # plug-in stop() functions are called in their established order.
    for module in modules:
        entry = _runtime_entry(module)
        runtime = entry.get('runtime')
        if runtime is not None:
            runtime.request_stop()

    failed = []
    for module in modules:
        remaining = max(0.0, deadline - time.time())
        if not stop_plugin(module, timeout=remaining):
            failed.append(module)
    return failed


def running():
    return list(__running.keys())


def get(name):
    if name not in __running:
        raise Exception(_('The plug-in') + ': {} '.format(name) + _('is not running.'))
    return __running[name]


# The following (cryptic) functionality ensures disabled plug-ins will not be loaded by other parts of the code.
# Only enabled plug-ins will be allowed to be imported.
class _PluginWrapper(types.ModuleType):
    def __init__(self, wrapped):
        super(_PluginWrapper, self).__init__(_plugin_import_name(wrapped))
        self._wrapped = wrapped
        self.__file__ = None
        self.__package__ = __name__

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        return getattr(get(self._wrapped), name)


def _protect(module):
    import_name = _plugin_import_name(module)
    if import_name not in sys.modules:
        sys.modules[import_name] = _PluginWrapper(module)
        setattr(sys.modules[__name__], module, _PluginWrapper(module))
