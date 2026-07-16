import pkgutil
import traceback
import re
import sys
import json
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
PLUGIN_HEALTH_TIMEOUT = 1.0
PLUGIN_MANIFEST_FILE = 'plugin.json'
PLUGIN_MANIFEST_MAX_BYTES = 64 * 1024
PLUGIN_MANIFEST_SCHEMA_VERSION = 1
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
            'last_error': '',
            'last_restart': '',
        })


def _now_string():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def _register_plugin_thread(module, thread):
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


def plugin_diagnostics():
    data = []
    running_modules = running()
    available_modules = available()
    now = time.time()
    from ospy.options import options
    health_results = {
        module: plugin_health(module) for module in available_modules
    }

    with __profile_lock:
        for module in available_modules:
            plugin = __running.get(module)
            entry = __plugin_runtime.get(module, {})
            manifest = plugin_manifest(module)
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
                'running': module in running_modules,
                'enabled': module in options.enabled_plugins,
                'link': link,
                'started': entry.get('started', 0),
                'started_text': entry.get('started_text', ''),
                'restarts': entry.get('restarts', 0),
                'last_restart': entry.get('last_restart', ''),
                'last_error': entry.get('last_error', ''),
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
        self._lock = threading.RLock()

        self._repo_data = {}
        self._repo_contents = {}
        self._changes_cache = {}

        self.start()

    def update(self):
        self._sleep_time = 10

    def _sleep(self, secs):
        import time
        self._sleep_time = secs
        while self._sleep_time > 0:
            time.sleep(1)
            self._sleep_time -= 1

    def run(self):
        from ospy.options import options
        from ospy.log import log
        import logging
        while True:
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
        from urllib.parse import quote_plus
        import logging
        import io

        response = urlopen(repo, timeout=30)
        zip_data = response.read()
        logging.debug(_('Downloaded {}').format(repo))

        return io.BytesIO(zip_data)

    def _get_zip(self, repo):
        if repo not in self._repo_data:
            self._repo_data[repo] = self._download_zip(repo)
        return self._repo_data[repo]

    @staticmethod
    def zip_contents(zip_file_data, load_read_me=True):
        import zipfile
        import os
        import datetime
        import hashlib
        import logging
        result = {}

        try:

            zip_file = zipfile.ZipFile(zip_file_data)

            infos = zip_file.infolist()
            files = zip_file.namelist()
            inits = [f for f in files if f.endswith('__init__.py')]

            for init in inits:
                init_dir = os.path.dirname(init)
                plugin_id = os.path.basename(init_dir)
                read_me = ''
                manifest = {}
                manifest_name = init_dir + '/' + PLUGIN_MANIFEST_FILE
                if manifest_name in files:
                    manifest = _manifest_from_bytes(
                        zip_file.read(manifest_name), plugin_id
                    )

                # Version information:
                plugin_hash = ''
                plugin_date = datetime.datetime(1970, 1, 1)
                plugin_files = {}
                plugin_zip_prefix = init_dir.rstrip('/\\') + '/'

                if init_dir + '/README.md' in files or manifest:

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

                    result[plugin_id] = {
                        'name': (
                            manifest.get('name') or
                            _plugin_name(zip_file.read(init).decode('utf-8').splitlines())
                        ),
                        'manifest': manifest,
                        'version': manifest.get('version', ''),
                        'hash': hashlib.md5(plugin_hash.encode("utf-8")).hexdigest(),
                        'date': plugin_date,
                        'read_me': read_me,
                        'dir': init_dir,
                        'files': plugin_files
                    }

        except Exception: 
            logging.error(_('Failed to read a plug-in zip file') + ': {}'.format(traceback.format_exc()))
            pass

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

            return self._repo_contents[repo]

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
        import zipfile
        from ospy.helpers import mkdir_p

        allowed_docs = {'README.md', 'CHANGELOG.md'}
        target_dir = plugin_dir()
        target_dir_abs = os.path.abspath(target_dir)

        zip_file = zipfile.ZipFile(zip_file_data)
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
            if len(parts) != 2 or parts[1] not in allowed_docs or parts[0] not in repo_roots:
                continue
            is_directory = zip_info.is_dir() if hasattr(zip_info, 'is_dir') else zip_name.endswith('/')
            if is_directory:
                continue

            target_name = os.path.abspath(os.path.join(target_dir, parts[1]))
            if os.path.commonpath([target_dir_abs, target_name]) != target_dir_abs:
                raise ValueError(_('Unsafe plug-in ZIP path: {}').format(zip_info.filename))

            mkdir_p(os.path.dirname(target_name))
            with open(target_name, 'wb') as fh:
                fh.write(zip_file.read(zip_info.filename))

    @staticmethod
    def _install_plugin(zip_file_data, plugin, p_dir):
        import os
        import shutil
        import zipfile
        import datetime
        import hashlib
        from ospy.helpers import mkdir_p
        from ospy.helpers import del_rw
        from ospy.options import options

        # First stop it if it is running:
        enabled = plugin in options.enabled_plugins
        if enabled:
            stop_plugin(plugin)

        # Clean the target directory and create it if needed:
        target_dir = plugin_dir(plugin)
        if os.path.exists(target_dir):
            old_files = os.listdir(target_dir)
            for old_file in old_files:
                if old_file != 'data':
                    old_path = os.path.join(target_dir, old_file)
                    if os.path.isdir(old_path):
                        shutil.rmtree(old_path, onerror=del_rw)
                    else:
                        del_rw(None, old_path, None)
        else:
            mkdir_p(target_dir)

        # Load the zip file:
        zip_file = zipfile.ZipFile(zip_file_data)
        infos = zip_file.infolist()
        target_dir_abs = os.path.abspath(target_dir)

        # Version information:
        plugin_hash = ''
        plugin_date = datetime.datetime(1970, 1, 1)
        plugin_zip_prefix = p_dir.rstrip('/\\') + '/'

        # Extract all files:
        for zip_info in infos:
            zip_name = zip_info.filename
            if zip_name.startswith(plugin_zip_prefix):
                is_directory = zip_info.is_dir() if hasattr(zip_info, 'is_dir') else zip_name.endswith('/')
                relative_name = zip_name[len(plugin_zip_prefix):].lstrip('/\\')
                relative_name = os.path.normpath(relative_name)
                if not relative_name or relative_name == '.':
                    continue
                if os.path.isabs(relative_name) or relative_name.startswith('..' + os.path.sep) or relative_name == '..':
                    raise ValueError(_('Unsafe plug-in ZIP path: {}').format(zip_name))
                target_name = os.path.abspath(os.path.join(target_dir, relative_name))
                if os.path.commonpath([target_dir_abs, target_name]) != target_dir_abs:
                    raise ValueError(_('Unsafe plug-in ZIP path: {}').format(zip_name))
                if relative_name:
                    if is_directory:
                        mkdir_p(target_name)
                    else:
                        plugin_date = max(plugin_date, datetime.datetime(*zip_info.date_time))
                        plugin_hash += hex(zip_info.CRC)
                        contents = zip_file.read(zip_name)
                        mkdir_p(os.path.dirname(target_name))
                        with open(target_name, 'wb') as fh:
                            fh.write(contents)

        plugin_status = dict(options.plugin_status)
        plugin_status[plugin] = {
            'hash': hashlib.md5(plugin_hash.encode('utf-8')).hexdigest(),
            'date': plugin_date
        }
        options.plugin_status = plugin_status
        _clear_plugin_caches(plugin)
        _unload_plugin_modules(plugin)

        # Start again if needed:
        if enabled:
            reload_plugin(plugin)

    def install_repo_plugin(self, repo, plugin_filter):
        import logging
        logging.info(_('Installing plug-in from repository {} plugin {}').format(repo, plugin_filter if plugin_filter else _('all plugins')))
        self.install_custom_plugin(self._get_zip(repo), plugin_filter)

    def install_custom_plugin(self, zip_file_data, plugin_filter=None):
        self._install_repo_docs(zip_file_data)
        contents = self.zip_contents(zip_file_data, False)
        for plugin, info in contents.items():
            if plugin_filter is None or plugin == plugin_filter:
                self._install_plugin(zip_file_data, plugin, info['dir'])

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
def stop_plugin(module):
    from ospy.options import options
    import logging

    plugin = __running.get(module)
    if plugin is not None:
        plugin_n = getattr(plugin, 'NAME', module)
        try:
            plugin.stop()
            logging.info(_('Stopped the') + ': {}'.format(plugin_n))
        except Exception:
            _runtime_entry(module)['last_error'] = traceback.format_exc()
            logging.error(_('Failed to stop the') + ': {} {}'.format(plugin_n, traceback.format_exc()))
        finally:
            __running.pop(module, None)
            with __profile_lock:
                for ident in list(__thread_plugin.keys()):
                    if __thread_plugin.get(ident) == module:
                        __thread_plugin.pop(ident, None)

    try:
        from ospy.webpages import clear_plugin_runtime_data
        clear_plugin_runtime_data(module)
    except Exception:
        logging.error(_('Failed to clear runtime data for the plug-in') + ': {} {}'.format(module, traceback.format_exc()))

    _clear_plugin_caches(module)
    _unload_plugin_modules(module)

    if module not in options.enabled_plugins:
        _protect(module)


def start_plugin(module):
    from ospy.helpers import mkdir_p
    from ospy.options import options
    import logging

    if module not in options.enabled_plugins or module in __running:
        return module in __running

    plugin_n = module
    try:
        _clear_plugin_caches(module)
        _unload_plugin_modules(module)

        import_name = _plugin_import_name(module)
        plugin = importlib.import_module(import_name)
        manifest = plugin_manifest(module)
        plugin_n = getattr(plugin, 'NAME', None) or manifest.get('name') or module
        if not getattr(plugin, 'NAME', None):
            plugin.NAME = plugin_n
        if not getattr(plugin, 'MENU', None) and manifest.get('menu'):
            plugin.MENU = manifest['menu']
        if not hasattr(plugin, 'LINK'):
            plugin.LINK = None

        mkdir_p(plugin_data_dir(module))
        mkdir_p(plugin_docs_dir(module))

        entry = _runtime_entry(module)
        entry['started'] = time.time()
        entry['started_text'] = _now_string()
        entry['threads'] = {}
        entry['last_error'] = ''

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
