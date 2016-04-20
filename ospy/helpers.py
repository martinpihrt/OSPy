#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Rimco'

# System imports
import datetime
import logging
import random
import time
import errno
import re
from threading import Lock

BRUTEFORCE_LOCK = Lock()


def del_rw(action, name, exc):
    import os
    import stat
    if os.path.exists(name):
        os.chmod(name, stat.S_IWRITE)
    if os.path.isfile(name):
        os.remove(name)
    elif os.path.isdir(name):
        os.rmdir(name)


def now():
    return time.time() + (datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds()


def datetime_string(timestamp=None):
    if timestamp:
        if hasattr(timestamp, 'strftime'):
            return timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return time.strftime("%Y-%m-%d %H:%M:%S", timestamp)
    else:
        return time.strftime("%Y-%m-%d %H:%M:%S")


def two_digits(n):
    return '%02d' % int(n)


def program_delay(program):
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    result = (program.start - today).total_seconds()
    while result < 0:
        result += program.modulo*60
    return int(result/24/3600)


def formatTime(t):
    from options import options
    if options.time_format:
        return t
    else:
        hour = int(t[0:2])
        newhour = hour
        if hour == 0:
            newhour = 12
        if hour > 12:
            newhour = hour-12
        return str(newhour) + t[2:] + (" am" if hour<12 else " pm")


def themes():
    import os
    return os.listdir(os.path.join('static', 'themes'))


def determine_platform():
    import os
    try:
        import RPi.GPIO
        return 'pi'
    except Exception:
        pass
    try:
        import Adafruit_BBIO.GPIO
        return 'bo'
    except Exception:
        pass

    if os.name == 'nt':
        return 'nt'

    return ''


def get_rpi_revision():
    try:
        import RPi.GPIO as GPIO
        return GPIO.RPI_REVISION
    except ImportError:
        return 0


def reboot(wait=1, block=False):
    if block:
        # Stop the web server first:
        from ospy import server
        server.stop()

        from ospy.stations import stations
        stations.clear()
        time.sleep(wait)
        logging.info("Rebooting...")

        import subprocess
        if determine_platform() == 'nt':
            subprocess.Popen('shutdown /r /t 0'.split())
        else:
            subprocess.Popen(['reboot'])
    else:
        from threading import Thread
        t = Thread(target=reboot, args=(wait, True))
        t.daemon = False
        t.start()


def poweroff(wait=1, block=False):
    if block:
        # Stop the web server first:
        from ospy import server
        server.stop()

        from ospy.stations import stations
        stations.clear()
        time.sleep(wait)
        logging.info("Powering off...")

        import subprocess
        if determine_platform() == 'nt':
            subprocess.Popen('shutdown /t 0'.split())
        else:
            subprocess.Popen(['poweroff'])
    else:
        from threading import Thread
        t = Thread(target=poweroff, args=(wait, True))
        t.daemon = False
        t.start()


def restart(wait=1, block=False):
    if block:
        # Stop the web server first:
        from ospy import server
        server.stop()

        from ospy.stations import stations
        stations.clear()
        time.sleep(wait)
        logging.info("Restarting...")

        import sys
        if determine_platform() == 'nt':
            import subprocess
            # Use this weird construction to start a separate process that is not killed when we stop the current one
            subprocess.Popen(['cmd.exe', '/c', 'start', sys.executable] + sys.argv)
        else:
            import os
            os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        from threading import Thread
        t = Thread(target=restart, args=(wait, True))
        t.daemon = False
        t.start()


def uptime():
    """Returns UpTime for RPi"""
    try:
        with open("/proc/uptime") as f:
            total_sec = float(f.read().split()[0])
            string = str(datetime.timedelta(seconds=total_sec)).split('.')[0]
    except Exception:
        string = 'Unknown'

    return string


def get_ip():
    """Returns the IP adress if available."""
    try:
        import subprocess
        arg = 'ip route list'
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        data = p.communicate()
        split_data = data[0].split()
        ipaddr = split_data[split_data.index('src') + 1]
        return ipaddr
    except Exception:
        return 'Unknown'


def get_mac():
    """Retrun MAC from file"""
    try:
        return str(open('/sys/class/net/eth0/address').read())
    except Exception:
        return 'Unknown'


def get_meminfo():
    """Return the information in /proc/meminfo as a dictionary"""
    try:
        meminfo = {}
        with open('/proc/meminfo') as f:
            for line in f:
                meminfo[line.split(':')[0]] = line.split(':')[1].strip()
        return meminfo
    except Exception:
        return {
            'MemTotal': 'Unknown',
            'MemFree': 'Unknown'
        }


def get_netdevs():
    """RX and TX bytes for each of the network devices"""
    try:
        with open('/proc/net/dev') as f:
            net_dump = f.readlines()
        device_data = {}
        for line in net_dump[2:]:
            line = line.split(':')
            if line[0].strip() != 'lo':
                device_data[line[0].strip()] = {'rx': float(line[1].split()[0])/(1024.0*1024.0),
                                                'tx': float(line[1].split()[8])/(1024.0*1024.0)}
        return device_data
    except Exception:
        return {}


def get_cpu_temp(unit=None):
    """Returns the temperature of the CPU if available."""
    import os
    try:
        platform = determine_platform()
        if platform == 'bo':
            res = os.popen('cat /sys/class/hwmon/hwmon0/device/temp1_input').readline()
            temp = str(int(float(res) / 1000))
        elif platform == 'pi':
            res = os.popen('vcgencmd measure_temp').readline()
            temp = res.replace("temp=", "").replace("'C\n", "")
        else:
            temp = str(0)

        if unit == 'F':
            return str(9.0 / 5.0 * float(temp) + 32)
        elif unit is not None:
            return str(float(temp))
        else:
            return temp
    except Exception:
        return '!!'


def mkdir_p(path):
    import os
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def duration_str(total_seconds):
    minutes, seconds = divmod(total_seconds, 60)
    return '%02d:%02d' % (minutes, seconds)


def timedelta_duration_str(time_delta):
    return duration_str(time_delta.total_seconds())


def timedelta_time_str(time_delta, with_seconds=False):
    days, remainder = divmod(time_delta.total_seconds(), 24*3600)
    hours, remainder = divmod(remainder, 3600)
    if hours == 24:
        hours = 0
    minutes, seconds = divmod(remainder, 60)
    return '%02d:%02d' % (hours, minutes) + ((':%02d' % seconds) if with_seconds else '')


def minute_time_str(minute_time, with_seconds=False):
    return timedelta_time_str(datetime.timedelta(minutes=minute_time), with_seconds)


def short_day(index):
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][index]


def long_day(index):
    return ["Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"][index]


def stop_onrain():
    """Stop stations that do not ignore rain."""
    from ospy.stations import stations
    for station in stations.get():
        if not station.ignore_rain:
            station.activated = False


def save_to_options(qdict):
    from ospy.options import options

    for option in options.OPTIONS:
        key = option['key']
        multi_enum = option.get('multi_options')
        if 'category' in option:
            if key in qdict:
                value = qdict[key]
                if isinstance(option['default'], bool):
                    options[key] = True if value and value != "off" else False
                elif isinstance(option['default'], int) or isinstance(option['default'], float):
                    if 'min' in option and float(qdict[key]) < option['min']:
                        continue
                    if 'max' in option and float(qdict[key]) > option['max']:
                        continue
                    options[key] = type(option['default'])(qdict[key])
                else:
                    options[key] = qdict[key]
            elif multi_enum:
                if hasattr(multi_enum, '__call__'):
                    multi_enum = multi_enum()

                value = []
                for name in multi_enum:
                    v_name = key + '_' + name
                    if v_name in qdict and qdict[v_name] and qdict[v_name] != "off":
                        value.append(name)
                options[key] = value
            else:
                if isinstance(option['default'], bool):
                    options[key] = False


########################
#### Login Handling ####

def password_salt():
    return "".join(chr(random.randint(33, 127)) for _ in xrange(64))


def password_hash(password, salt):
    import hashlib
    m = hashlib.sha1()
    m.update(password + salt)
    return m.hexdigest()


def test_password(password):
    from ospy.options import options

    # Brute-force protection:
    with BRUTEFORCE_LOCK:
        if options.password_time > 0:
            time.sleep(options.password_time)

    result = options.password_hash == password_hash(password, options.password_salt)

    if result:
        options.password_time = 0
    else:
        if options.password_time < 30:
            options.password_time += 1

    return result


def check_login(redirect=False):
    from ospy import server
    import web
    from ospy.options import options
    qdict = web.input()

    try:
        if options.no_password:
            return True

        if server.session.validated:
            return True
    except KeyError:
        pass

    if 'pw' in qdict:
        if test_password(qdict['pw']):
            return True
        if redirect:
            raise web.unauthorized()
        return False

    if redirect:
        raise web.seeother('/login', True)
    return False


def get_input(qdict, key, default=None, cast=None):
    result = default
    if key in qdict:
        result = qdict[key]
        if cast is not None:
            result = cast(result)
    return result


def template_globals():
    import json
    import plugins
    import urllib
    from web import ctx

    from ospy.inputs import inputs
    from ospy.log import log
    from ospy.options import level_adjustments, options, rain_blocks
    from ospy.programs import programs, ProgramType
    from ospy.runonce import run_once
    from ospy.stations import stations
    from ospy import version
    from ospy.server import session

    result = {
        'str': str,
        'bool': bool,
        'int': int,
        'round': round,
        'isinstance': isinstance,
        'sorted': sorted,
        'hasattr': hasattr,

        'now': now
    }

    result.update(globals()) # Everything in the global scope of this file will be available
    result.update(locals())  # Everything imported in this function will be available

    return result


def help_files_in_directory(docs_dir):
    import os
    result = []
    if os.path.isdir(docs_dir):
        for filename in sorted(os.listdir(docs_dir)):
            if filename.endswith('.md'):
                name = os.path.splitext(os.path.basename(filename))[0]
                name = name.replace('.', ' ').replace('_', ' ').title()
                filename = os.path.relpath(os.path.join(docs_dir, filename))
                result.append((name, filename))
    return result


def get_help_files():
    import os
    result = []

    result.append((1, 'OSPy'))
    result.append((2, 'Readme', 'README.md'))
    for doc in help_files_in_directory(os.path.join('ospy', 'docs')):
        result.append((2, doc[0], doc[1]))

    result.append((1, 'API'))
    result.append((2, 'Readme', os.path.join('api', 'README.md')))
    for doc in help_files_in_directory(os.path.join('api', 'docs')):
        result.append((2, doc[0], doc[1]))

    result.append((1, 'Plug-ins'))
    result.append((2, 'Readme', os.path.join('plugins', 'README.md')))
    from plugins import plugin_names, plugin_dir, plugin_docs_dir
    for module, name in plugin_names().iteritems():

        readme_file = os.path.join(os.path.relpath(plugin_dir(module)), 'README.md')
        readme_exists = os.path.isfile(readme_file)

        docs = help_files_in_directory(plugin_docs_dir(module))
        if readme_exists or docs:
            if readme_exists:
                result.append((2, name, readme_file))
            else:
                result.append((2, name))

            for doc in docs:
                result.append((3, doc[0], doc[1]))
    return result


def get_help_file(id):
    import web

    try:
        id = int(id)
        docs = get_help_files()
        if 0 <= id < len(docs):
            option = docs[id]
            if len(option) > 2:
                filename = option[2]
                with open(filename) as fh:
                    import markdown
                    converted = markdown.markdown(fh.read(), extensions=['partial_gfm', 'markdown.extensions.codehilite'])
                    return web.template.Template(converted, globals=template_globals())()
    except Exception:
        pass
    return ''

def ASCI_convert(name):
  if re.search(r"[^\x00-\x7F]", name):
     # digraphs.  May be culturally sensitive
     name=re.sub(r"\xc3\x9f", 'ss', name)
     name=re.sub(r"\xc3\xa4|a\xcc\x88", 'ae', name)
     name=re.sub(r"\xc3\xa5|a\xcc\x8a", 'aa', name)
     name=re.sub(r"\xc3\xa6", 'ae', name)
     name=re.sub(r"\xc3\xb1|n\xcc\x83", 'ny', name)
     name=re.sub(r"\xc3\xb6|o\xcc\x88", 'oe', name)
     name=re.sub(r"\xc3\xbc|u\xcc\x88", 'ue', name)
     # latin 1
     name=re.sub(r"\xc3[\xa0-\xa5]", 'a', name)
     name=re.sub(r"\xc3\xa7", 'c', name)
     name=re.sub(r"\xc3[\xa8-\xab]", 'e', name)
     name=re.sub(r"\xc3[\xac-\xaf]", 'i', name)
     name=re.sub(r"\xc3[\xb2-\xb6]|\xc3\xb8", 'o', name)
     name=re.sub(r"\xc3[\xb9-\xbc]", 'u', name)
     name=re.sub(r"\xc3[\xbd\xbf]", 'y', name)
     # Latin Extended-A
     name=re.sub(r"\xc4[\x80-\x85]", 'a', name)
     name=re.sub(r"\xc4[\x86-\x8d]", 'c', name)
     name=re.sub(r"\xc4[\x8e-\x91]", 'd', name)
     name=re.sub(r"\xc4[\x92-\x9b]", 'e', name)
     name=re.sub(r"\xc4[\x9c-\xa3]", 'g', name)
     name=re.sub(r"\xc4[\xa4-\xa7]", 'h', name)
     name=re.sub(r"\xc4[\xa8-\xb1]", 'i', name)
     name=re.sub(r"\xc4[\xb2-\xb3]", 'ij', name)
     name=re.sub(r"\xc4[\xb4-\xb5]", 'j', name)
     name=re.sub(r"\xc4[\xb6-\xb8]", 'k', name)
     name=re.sub(r"\xc4[\xb9-\xff]|\xc5[\x80-\x82]", 'l', name)
     name=re.sub(r"\xc5[\x83-\x8b]", 'n', name)
     name=re.sub(r"\xc5[\x8c-\x91]", 'o', name)
     name=re.sub(r"\xc5[\x92-\x93]", 'oe', name)
     name=re.sub(r"\xc5[\x94-\x99]", 'r', name)
     name=re.sub(r"\xc5[\x9a-\xa2]", 's', name)
     name=re.sub(r"\xc5[\xa2-\xa7]", 't', name)
     name=re.sub(r"\xc5[\xa8-\xb3]", 'u', name)
     name=re.sub(r"\xc5[\xb4-\xb5]", 'w', name)
     name=re.sub(r"\xc5[\xb6-\xb8]", 'y', name)
     name=re.sub(r"\xc5[\xb9-\xbe]", 'z', name)
     # denormalized diacritics
     name=re.sub(r"\xcc[\x80-\xff]|\xcd[\x80-\xaf]", '', name)
  return re.sub(r"[^.\w]+", '-', name)
