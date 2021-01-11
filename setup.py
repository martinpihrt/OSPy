# -*- coding: utf-8 -*-
__author__ = 'Rimco'

import sys
import os
import subprocess
import shutil

from ospy import i18n
from ospy.helpers import print_report


def yes_no(msg):
    response = ''
    while response.lower().strip() not in ['y', 'yes', 'n', 'no']:
        response = raw_input('%s [y/yes/n/no]\n' % msg.encode('ascii', 'replace'))
    return response.lower().strip() in ['y', 'yes']


def install_package(module, easy_install=None, package=None, git=None, git_execs=None, zipfile=None, zip_cwd=None, zip_execs=None):
    from ospy.helpers import del_rw
    try:
        print_report('setup.py', _(u'Checking %s') % module)
        __import__(module)
        print_report('setup.py', _(u'%s is available') % module)
        return
    except Exception:
        if not yes_no(_(u'%s not available, do you want to install it?') % module):
            return

    done = False
    if not done and easy_install is not None:
        try:
            subprocess.check_call(['easy_install', easy_install])
            done = True
        except Exception as err:
            print_report('setup.py', _(u'Failed to use easy_install:') + u'{}'.format(err))

    if sys.platform.startswith('linux'):
        if not done and package is not None:
            try:
                subprocess.check_call('apt-get install'.split() + [package])
                done = True
            except Exception as err:
                print_report('setup.py', _(u'Failed to use apt-get:') + u'{}'.format(err))

        if not done and package is not None:
            try:
                subprocess.check_call('yum install'.split() + [package])
                done = True
            except Exception as err:
                print_report('setup.py', _(u'Failed to use yum:') + u'{}'.format(err))

    if not done and git is not None and git_execs is not None:
        try:
            shutil.rmtree('tmp', onerror=del_rw)
            subprocess.check_call(['git', 'clone', git, 'tmp'])
            for exc in git_execs:
                subprocess.check_call(exc, cwd='tmp')
            shutil.rmtree('tmp', onerror=del_rw)
            done = True
        except Exception as err:
            print_report('setup.py', _(u'Failed to use git:') + u'{}'.format(err))

    if not done and zipfile is not None and zip_cwd is not None and zip_execs is not None:
        try:
            del_rw(None, 'tmp.zip', None)
            shutil.rmtree('tmp', onerror=del_rw)
            import urllib
            urllib.urlretrieve(zipfile, 'tmp.zip')

            import zipfile
            zipfile.ZipFile('tmp.zip').extractall('tmp')
            del_rw(None, 'tmp.zip', None)

            for exc in zip_execs:
                subprocess.check_call(exc, cwd=os.path.join('tmp', zip_cwd))

            shutil.rmtree('tmp', onerror=del_rw)
            done = True
        except Exception as err:
            print_report('setup.py', _(u'Failed to use zip file:') + u'{}'.format(err))

    if not done:
        print_report('setup.py', _(u'Failed to install %s.') % module)


def install_service():
    my_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join('/etc', 'init.d', 'ospy')
    if sys.platform.startswith('linux'):
        if yes_no(_(u'Do you want to install OSPy as a service?')):
            with open(os.path.join(my_dir, 'service', 'ospy.sh')) as source:
                with open(path, 'w') as target:
                    target.write(source.read().replace('/home/pi/OSPy', my_dir))
            os.chmod(path, 0o755)
            subprocess.check_call(['update-rc.d', 'ospy', 'defaults'])
            print_report('setup.py', _(u'Done installing service.'))

    else:
        print_report('setup.py', _(u'Service installation is only possible on unix systems.'))


def uninstall_service():
    if sys.platform.startswith('linux'):
        if os.path.exists(os.path.join('/var', 'run', 'ospy.pid')):
            try:
                subprocess.Popen(['service', 'ospy', 'stop'])
            except Exception:
                print_report('setup.py', _(u'Could not stop service.'))
        else:
            print_report('setup.py', _(u'OSPy was not running.'))

        try:
            subprocess.check_call(['update-rc.d', '-f', 'ospy', 'remove'])
        except Exception:
            print_report('setup.py', _(u'Could not remove service using update-rc.d'))

        import glob
        old_paths = glob.glob(os.path.join('/etc', 'init.d', '*ospy*'))
        for old_path in old_paths:
            os.unlink(old_path)

        if old_paths:
            print_report('setup.py', _(u'Service removed.'))
        else:
            print_report('setup.py', _(u'Service not found.'))
    else:
        print_report('setup.py', _(u'Service uninstall is only possible on unix systems.'))


def check_password():
    from ospy.options import options
    from ospy.helpers import test_password, password_hash, password_salt
    
    if not options.no_password and test_password('opendoor', 'admin'):
        if yes_no(_(u'You are still using the default password and name, you should change it! Do you want to change it now?')):
            from getpass import getpass
            pw1 = pw2 = name = ''
            while True:
                name = getpass(_(u'New administrator name: '))
                print_report('setup.py', _(u'Inputted name is: %s') % name)
                pw1 = getpass(_(u'New administrator password: '))
                print_report('setup.py', _(u'Inputted password is: %s') % pw1)
                pw2 = getpass(_(u'Repeat administrator password: '))
                print_report('setup.py', _(u'Inputted password is: %s') % pw2)
                if pw1 != '' and pw1 == pw2 and name != '':
                    print_report('setup.py', _(u'Correctly.'))
                    break
                print_report('setup.py', _(u'Invalid input!'))

            options.admin_user = name
            salt = password_salt()
            options.password_salt = salt
            options.password_hash = password_hash(pw1, salt)
            options.password_time = 0


def start():
    if yes_no(_(u'Do you want to start OSPy now?')):
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
            sys.exit(_(u'This script needs to be run as root.'))

    if len(sys.argv) == 2 and sys.argv[1] == 'install':
        pkg = False
        try:
            import setuptools
            pkg = True
        except ImportError:
            if yes_no(_(u'Could not find setuptools which is needed to install packages, do you want to install it now?')):
                import urllib
                from ospy.helpers import del_rw
                shutil.rmtree('tmp', onerror=del_rw)
                os.mkdir('tmp')
                urllib.urlretrieve('https://bootstrap.pypa.io/ez_setup.py', 'tmp/ez_setup.py')
                subprocess.check_call([sys.executable, 'ez_setup.py'], cwd='tmp')
                shutil.rmtree('tmp', onerror=del_rw)
                pkg = True

        if not pkg:
            print_report('setup.py', _(u'Cannot install packages without setuptools.'))
        else:
            # Check if packages are available:
            install_package('gfm', None, None,
                            'https://github.com/martinpihrt/py-gfm.git',
                            [[sys.executable, 'setup.py', 'install']],
                            'https://github.com/martinpihrt/py-gfm/archive/master.zip', 'py-gfm-master',
                            [[sys.executable, 'setup.py', 'install']])

            install_package('pygments', 'pygments', 'python-pygments',
                            'https://github.com/martinpihrt/pygments', #'http://bitbucket.org/birkenfeld/pygments-main',
                            [[sys.executable, 'setup.py', 'install']],
                            'https://github.com/martinpihrt/pygments/archive/master.zip', 'pygments-master', # 'https://bitbucket.org/birkenfeld/pygments-main/get/0fb2b54a6e10.zip', 'birkenfeld-pygments-main-0fb2b54a6e10',
                            [[sys.executable, 'setup.py', 'install']])

        install_service()
        check_password()
        start()
        print_report('setup.py', _(u'Done.'))

    elif len(sys.argv) == 2 and sys.argv[1] == 'uninstall':
        uninstall_service()

    else:
        sys.exit("Usage:\n"
                 "setup.py install:   Interactive install.\n"
                 "setup.py uninstall: Removes the service if installed.")
