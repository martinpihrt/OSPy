import pkgutil
import traceback
import re
import sys
from os import path
import types
import threading
import importlib

__running = {}
REPOS = ['https://github.com/martinpihrt/OSPy-plugins/archive/master.zip'] # repository with plugins


def _plugin_import_name(module):
    return __name__ + '.' + module


def _clear_plugin_caches(module):
    """Clear cached plugin metadata and route mappings after an install/update."""
    __name_cache.pop(module, None)
    __name_cache_menu.pop(module, None)

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

            if install_updates:
                status = options.plugin_status
                for plugin in available():
                    update = self.available_version(plugin)
                    if update is not None and plugin in status and status[plugin]['hash'] != update['hash']:
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

                # Version information:
                plugin_hash = ''
                plugin_date = datetime.datetime(1970, 1, 1)

                if init_dir + '/README.md' in files:

                    # Check all files:
                    for zip_info in infos:
                        zip_name = zip_info.filename
                        if zip_name.startswith(init_dir):
                            relative_name = zip_name[len(init_dir):].lstrip('/')
                            if relative_name and not relative_name.endswith('/'):
                                plugin_date = max(plugin_date, datetime.datetime(*zip_info.date_time))
                                plugin_hash += hex(zip_info.CRC)

                    if load_read_me:
                        from ospy.helpers import gfm_str_to_html
                        read_me = gfm_str_to_html(zip_file.read(init_dir + '/README.md').decode('utf-8'))

                    result[plugin_id] = {
                        'name': _plugin_name(zip_file.read(init).decode('utf-8').splitlines()),
                        'hash': hashlib.md5(plugin_hash.encode("utf-8")).hexdigest(),
                        'date': plugin_date,
                        'read_me': read_me,
                        'dir': init_dir
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

        options.plugin_status[plugin] = {
            'hash': hashlib.md5(plugin_hash.encode('utf-8')).hexdigest(),
            'date': plugin_date
        }
        options.plugin_status = options.plugin_status
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
        __name_cache[plugin] = None
        filename = path.join(path.dirname(__file__), plugin, '__init__.py')
        try:
            with open(filename) as fh:
                __name_cache[plugin] = _plugin_name(fh)
        except Exception:
            pass
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
        __name_cache_menu[plugin] = None
        filename = path.join(path.dirname(__file__), plugin, '__init__.py')
        try:
            with open(filename) as fh:
                __name_cache_menu[plugin] = _plugin_name_menu(fh)
        except Exception:
            pass
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
            logging.error(_('Failed to stop the') + ': {} {}'.format(plugin_n, traceback.format_exc()))
        finally:
            __running.pop(module, None)

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
        plugin_n = plugin.NAME

        mkdir_p(plugin_data_dir(module))
        mkdir_p(plugin_docs_dir(module))

        plugin.start()
        __running[module] = plugin
        logging.info(_('Started the') + ': {}'.format(plugin_n))

        if plugin.LINK is not None and not (plugin.LINK.startswith(module) or plugin.LINK.startswith(__name__)):
            plugin.LINK = module + '.' + plugin.LINK

        return True

    except Exception:
        logging.error(_('Failed to load the') + ' {} {}'.format(plugin_n, traceback.format_exc()))
        if module in options.enabled_plugins:
            options.enabled_plugins.remove(module)
            options.enabled_plugins = options.enabled_plugins
        _clear_plugin_caches(module)
        _unload_plugin_modules(module)
        _protect(module)
        return False


def reload_plugin(module):
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
