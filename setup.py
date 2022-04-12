#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = u'Rimco'

import sys
import os
import subprocess
import shutil

from ospy import i18n
from ospy.helpers import print_report, is_python2


def yes_no(msg):
    response = u''
    while response.lower().strip() not in ['y', 'yes', 'n', 'no']:
        if is_python2():
            response = raw_input('{} [y/yes/n/no]\n'.format(msg.encode('utf-8')))
        else:
            response = input('{} [y/yes/n/no]\n'.format(msg))
    return response.lower().strip() in ['y', 'yes']


def install_package(module, easy_install=None, package=None, pip=None, git=None, git_execs=None, zipfile=None, zip_cwd=None, zip_execs=None):
    from ospy.helpers import del_rw
    try:
        print_report('setup.py', _('Checking {}').format(module))
        __import__(module)
        print_report('setup.py', _('{} is available').format(module))
        return
    except Exception:
        if not yes_no(_('{} not available, do you want to install it?').format(module)):
            return

    done = False
    if not done and easy_install is not None:
        try:
            subprocess.check_call([sys.executable, '-m', 'easy_install', easy_install])
            done = True
        except Exception as err:
            print_report('setup.py', _('Failed to use easy_install:') + '{}'.format(err))

    if sys.platform.startswith('linux'):
        if not done and package is not None:
            try:
                subprocess.check_call(['apt-get', 'install', package])
                done = True
            except Exception as err:
                print_report('setup.py', _('Failed to use apt-get:') + u'{}'.format(err))

        if not done and package is not None:
            try:
                subprocess.check_call(['yum', 'install', package])
                done = True
            except Exception as err:
                print_report('setup.py', _('Failed to use yum:') + u'{}'.format(err))

    if not done and pip is not None:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pip])
            done = True
        except Exception as err:
            print_report('setup.py', _('Failed to use pip:') + u'{}'.format(err))

    if not done and git is not None and git_execs is not None:
        try:
            shutil.rmtree('tmp', onerror=del_rw)
            subprocess.check_call(['git', 'clone', git, 'tmp'])
            for exc in git_execs:
                subprocess.check_call(exc, cwd='tmp')
            shutil.rmtree('tmp', onerror=del_rw)
            done = True
        except Exception as err:
            print_report('setup.py', _(u'Failed to use git:') + '{}'.format(err))

    if not done and zipfile is not None and zip_cwd is not None and zip_execs is not None:
        try:
            del_rw(None, 'tmp.zip', None)
            shutil.rmtree('tmp', onerror=del_rw)
            if is_python2():
                from urllib import urlretrieve
            else:
                from urllib.request import urlretrieve
            urlretrieve(zipfile, 'tmp.zip')

            import zipfile
            zipfile.ZipFile('tmp.zip').extractall('tmp')
            del_rw(None, 'tmp.zip', None)

            for exc in zip_execs:
                subprocess.check_call(exc, cwd=os.path.join('tmp', zip_cwd))

            shutil.rmtree('tmp', onerror=del_rw)
            done = True
        except Exception as err:
            print_report('setup.py', _('Failed to use zip file:') + u'{}'.format(err))

    if not done:
        print_report('setup.py', _('Failed to install {}.').format(module))


def install_service():
    my_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join('/etc', 'init.d', 'ospy')
    if sys.platform.startswith('linux'):
        if yes_no(_('Do you want to install OSPy as a service?')):
            with open(os.path.join(my_dir, 'service', 'ospy.sh')) as source:
                with open(path, 'w') as target:
                    target.write(source.read().replace('{{OSPY_DIR}}', my_dir))       
            os.chmod(path, 0o755)
            subprocess.check_call(['update-rc.d', 'ospy', 'defaults'])
            print_report('setup.py', _('Done installing service.'))

    else:
        print_report('setup.py', _('Service installation is only possible on unix systems.'))


def uninstall_service():
    if sys.platform.startswith('linux'):
        if os.path.exists(os.path.join('/var', 'run', 'ospy.pid')):
            try:
                subprocess.Popen(['service', 'ospy', 'stop'])
            except Exception:
                print_report('setup.py', _('Could not stop service.'))
        else:
            print_report('setup.py', _('OSPy was not running.'))

        try:
            subprocess.Popen(['systemctl', 'daemon-reload'])
        except Exception:
            print_report('setup.py', _('Could not reload systemctl daemon.'))            

        try:
            subprocess.check_call(['update-rc.d', '-f', 'ospy', 'remove'])
        except Exception:
            print_report('setup.py', _('Could not remove service using update-rc.d'))

        import glob
        old_paths = glob.glob(os.path.join('/etc', 'init.d', '*ospy*'))
        for old_path in old_paths:
            os.unlink(old_path)

        if old_paths:
            print_report('setup.py', _('Service removed.'))            
        else:
            print_report('setup.py', _('Service not found.'))
    else:
        print_report('setup.py', _('Service uninstall is only possible on unix systems.'))


def start():
    if yes_no(_('Do you want to start OSPy now?')):
        if sys.platform.startswith('linux'):
            try:
                subprocess.Popen(['service', 'ospy', 'restart'])
            except Exception:
                subprocess.Popen([sys.executable, 'run.py'])

        else:
            subprocess.check_call(['cmd.exe', '/c', 'start', sys.executable, 'run.py'])


if __name__ == '__main__':
    # On unix systems we need to be root:
    if sys.platform.startswith('linux'):
        if not os.getuid() == 0:
            sys.exit(_('This script needs to be run as root.'))

    if len(sys.argv) == 2 and sys.argv[1] == 'install':
        pkg = False
        try:
            import setuptools
            pkg = True
        except ImportError:
            if yes_no(_('Could not find setuptools which is needed to install packages, do you want to install it now?')):
                if is_python2():
                    from urllib import urlretrieve
                else:
                    from urllib.request import urlretrieve
                from ospy.helpers import del_rw
                shutil.rmtree('tmp', onerror=del_rw)
                os.mkdir('tmp')
                urlretrieve('https://bootstrap.pypa.io/ez_setup.py', 'tmp/ez_setup.py')
                import subprocess
                subprocess.check_call([sys.executable, 'ez_setup.py'], cwd='tmp')
                shutil.rmtree('tmp', onerror=del_rw)
                pkg = True

        if not pkg:
            print_report('setup.py', _('Cannot install packages without setuptools.'))
        
        else:           
            # Check if packages are available:
            #               module, easy_install=None, package=None, pip=None, git=None, git_execs=None, zipfile=None, zip_cwd=None, zip_execs=None

            install_package('web', 'web.py==0.51', 'python-webpy', 'web.py==0.51',
                            'https://github.com/webpy/webpy.git',
                            [[sys.executable, 'setup.py', 'install']],
                            'https://github.com/webpy/webpy/archive/master.zip', 'webpy-master',
                            [[sys.executable, 'setup.py', 'install']])

            if is_python2():
                install_package('mdx_partial_gfm', None, None, 'py-gfm==0.1.1',
                                'https://github.com/Zopieux/py-gfm.git',
                                [[sys.executable, 'setup.py', 'install']],
                                'https://github.com/Zopieux/py-gfm/archive/master.zip', 'py-gfm-master',
                                [[sys.executable, 'setup.py', 'install']])

                install_package('pygments', 'pygments==2.5.2', 'python-pygments', 'pygments==2.5.2',
                                'http://bitbucket.org/birkenfeld/pygments-main',
                                [[sys.executable, 'setup.py', 'install']],
                                'https://bitbucket.org/birkenfeld/pygments-main/get/0fb2b54a6e10.zip', 'birkenfeld-pygments-main-0fb2b54a6e10',
                                [[sys.executable, 'setup.py', 'install']])
            else:
                install_package('cmarkgfm', None, None, 'cmarkgfm',
                                'https://github.com/theacodes/cmarkgfm',
                                [[sys.executable, 'setup.py', 'install']],
                                'https://github.com/Zopieux/cmarkgfm/archive/master.zip', 'cmarkgfm-master',
                                [[sys.executable, 'setup.py', 'install']])

        install_service()
        start()
        print_report('setup.py', _('Done.'))

    elif len(sys.argv) == 2 and sys.argv[1] == 'uninstall':
        uninstall_service()

    else:
        sys.exit("Usage:\n"
                 "setup.py install:   Interactive install.\n"
                 "setup.py uninstall: Removes the service if installed.")
