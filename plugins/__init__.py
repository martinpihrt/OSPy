import pkgutil
import traceback
import re
import sys
from os import path
import types
import threading

__running = {}
REPOS = ['https://github.com/martinpihrt/OSPy-plugins/archive/master.zip']

################################################################################
# Plugin Options                                                               #
################################################################################
class PluginOptions(dict):
    def __init__(self, plugin, defaults):
        super(PluginOptions, self).__init__(defaults.iteritems())
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
            for key, value in options[plugin].iteritems():
                if key in self:
                    value_type = type(value)
                    if value_type == unicode:
                        value_type = str
                    default_type = type(self[key])
                    if default_type == unicode:
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
        for key in self.keys():
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
                elif isinstance(default_value, str) or isinstance(old_value, unicode):
                    self[key] = qdict.get(key, old_value)
                elif isinstance(default_value, list):
                    self[key] = [int(x) for x in qdict.get(key, old_value)]           
            except ValueError:
                import web
                raise web.badrequest('Invalid value for \'%s\': \'%s\'' % (key, qdict.get(key)))


################################################################################
# Plugin Repositories                                                          #
################################################################################
class _PluginChecker(threading.Thread):
    def __init__(self):
        super(_PluginChecker, self).__init__()
        self.daemon = True
        self._sleep_time = 0

        self._repo_data = {}
        self._repo_contents = {}

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
                    for repo in REPOS:
                        self._repo_data[repo] = self._download_zip(repo)
                        self._repo_contents[repo] = self.zip_contents(self._get_zip(repo))

                status = options.plugin_status
                if options.auto_plugin_update and options.use_plugin_update and not log.active_runs():
                    for plugin in available():
                        update = self.available_version(plugin)
                        if update is not None and plugin in status and status[plugin]['hash'] != update['hash']:
                            logging.info('Updating the {} plug-in.'.format(plugin))
                            self.install_repo_plugin(update['repo'], plugin)

            except Exception:
                logging.error('Failed to update the plug-ins information:\n' + traceback.format_exc())
            finally:
                self._sleep(3600)

    def available_version(self, plugin):
        result = None
        for repo_index, repo in enumerate(REPOS):
            repo_contents = self.get_repo_contents(repo)
            if plugin in repo_contents:
                result = repo_contents[plugin]
                result['repo_index'] = repo_index
                result['repo'] = repo
                break
        return result

    @staticmethod
    def _download_zip(repo):
        import urllib2
        import logging
        import io

        response = urllib2.urlopen(repo)
        zip_data = response.read()
        logging.debug('Downloaded ' + repo)

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
                        import web
                        import markdown
                        from ospy.helpers import template_globals
                        converted = markdown.markdown(zip_file.read(init_dir + '/README.md'),
                                                      extensions=['partial_gfm', 'markdown.extensions.codehilite'])
                        read_me = web.template.Template(converted, globals=template_globals())()

                    result[plugin_id] = {
                        'name': _plugin_name(zip_file.read(init).splitlines()),
                        'hash': hashlib.md5(plugin_hash).hexdigest(),
                        'date': plugin_date,
                        'read_me': read_me,
                        'dir': init_dir
                    }

        except Exception:
            logging.error('Failed to read a plug-in zip file:\n' + traceback.format_exc())

        return result

    def get_repo_contents(self, repo):
        import logging
        try:
            if repo not in self._repo_contents:
                self._repo_contents[repo] = self.zip_contents(self._get_zip(repo))
        except Exception:
            logging.error('Failed to get contents of {}:'.format(repo) + '\n' + traceback.format_exc())
            return {}

        return self._repo_contents[repo]

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
            options.enabled_plugins.remove(plugin)
            start_enabled_plugins()

        # Clean the target directory and create it if needed:
        target_dir = plugin_dir(plugin)
        if os.path.exists(target_dir):
            old_files = os.listdir(target_dir)
            for old_file in old_files:
                if old_file != 'data':
                    shutil.rmtree(os.path.join(target_dir, old_file), onerror=del_rw)
        else:
            mkdir_p(target_dir)

        # Load the zip file:
        zip_file = zipfile.ZipFile(zip_file_data)
        infos = zip_file.infolist()

        # Version information:
        plugin_hash = ''
        plugin_date = datetime.datetime(1970, 1, 1)

        # Extract all files:
        for zip_info in infos:
            zip_name = zip_info.filename
            if zip_name.startswith(p_dir):
                relative_name = zip_name[len(p_dir):].lstrip('/')
                target_name = os.path.join(target_dir, relative_name)
                if relative_name:
                    if relative_name.endswith('/'):
                        mkdir_p(target_name)
                    else:
                        plugin_date = max(plugin_date, datetime.datetime(*zip_info.date_time))
                        plugin_hash += hex(zip_info.CRC)
                        contents = zip_file.read(zip_name)
                        with open(target_name, 'wb') as fh:
                            fh.write(contents)

        options.plugin_status[plugin] = {
            'hash': hashlib.md5(plugin_hash).hexdigest(),
            'date': plugin_date
        }
        options.plugin_status = options.plugin_status

        # Start again if needed:
        if enabled:
            options.enabled_plugins.append(plugin)
            start_enabled_plugins()

    def install_repo_plugin(self, repo, plugin_filter):
        self.install_custom_plugin(self._get_zip(repo), plugin_filter)

    def install_custom_plugin(self, zip_file_data, plugin_filter=None):
        contents = self.zip_contents(zip_file_data, False)
        for plugin, info in contents.iteritems():
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
            mapping = []
            for module in running():
                import_name = __name__ + '.' + module
                plugin = get(module)
                mapping += _get_urls(import_name, plugin)
            fn, args = self._match(mapping, web.ctx.path)
            return self._delegate(fn, self.fvars, args)

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
    if plugin not in __name_cache:
        __name_cache[plugin] = None
        filename = path.join(path.dirname(__file__), plugin, '__init__.py')
        try:
            with open(filename) as fh:
                __name_cache[plugin] = _plugin_name(fh)
        except Exception:
            pass
    return __name_cache[plugin]


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
def start_enabled_plugins():
    from ospy.helpers import mkdir_p
    from ospy.options import options
    import logging
    import time
    
    for module in available():
        if module in options.enabled_plugins and module not in __running:
            plugin_n = module
            import_name = __name__ + '.' + module
            try:
                time.sleep(0.1)
                plugin = getattr(__import__(import_name), module)
                plugin = reload(plugin)
                plugin_n = plugin.NAME
                mkdir_p(plugin_data_dir(module))
                mkdir_p(plugin_docs_dir(module))

                plugin.start()
                __running[module] = plugin
                logging.info('Started the {} plug-in.'.format(plugin_n))

                if plugin.LINK is not None and not (plugin.LINK.startswith(module) or plugin.LINK.startswith(__name__)):
                    plugin.LINK = module + '.' + plugin.LINK

            except Exception:
                logging.error('Failed to load the {} plug-in:'.format(plugin_n) + '\n' + traceback.format_exc())
                options.enabled_plugins.remove(module)

    for module, plugin in __running.copy().iteritems():
        if module not in options.enabled_plugins:
            plugin_n = plugin.NAME
            try:
                plugin.stop()
                del __running[module]
                logging.info('Stopped the {} plug-in.'.format(plugin_n))
            except Exception:
                logging.error('Failed to stop the {} plug-in:'.format(plugin_n) + '\n' + traceback.format_exc())


def running():
    return __running.keys()


def get(name):
    if name not in __running:
        raise Exception('The %s plug-in is not running.' % name)
    return __running[name]


# The following (cryptic) functionality ensures disabled plug-ins will not be loaded by other parts of the code.
# Only enabled plug-ins will be allowed to be imported.
class _PluginWrapper(types.ModuleType):
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def __getattr__(self, name):
        return getattr(get(self._wrapped), name)


def _protect(module):
    if __name__ not in sys.modules:
        import_name = __name__ + '.' + module
        sys.modules[import_name] = _PluginWrapper(module)
        setattr(sys.modules[__name__], module, _PluginWrapper(module))
