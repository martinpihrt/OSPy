#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco' # additional changes Martin Pihrt

# System imports
import datetime
import random
import time
import errno
import re
import subprocess
import traceback
import ast
import hmac
import os
import secrets
from threading import Lock, Thread

BRUTEFORCE_LOCK = Lock()
BRUTEFORCE_ATTEMPTS = {}
BRUTEFORCE_DELAY_AFTER = 3
BRUTEFORCE_LOCK_AFTER = 10
BRUTEFORCE_LOCK_SECONDS = 15 * 60
PASSWORD_HASH_ALGORITHM = 'pbkdf2_sha256'
PASSWORD_HASH_ITERATIONS = 200000
UPLOAD_READ_CHUNK_SIZE = 1024 * 64


def del_rw(action, name, exc):
    import os
    import stat
    if os.path.exists(name):
        os.chmod(name, stat.S_IWRITE)
    if os.path.isfile(name):
        os.remove(name)
    elif os.path.isdir(name):
        os.rmdir(name)

def remove_thing(path):
    import os, os.path
    import shutil
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except:
        pass        


def empty_directory(path):
    import os, os.path
    import glob
    for i in glob.glob(os.path.join(path, '*')):
        print_report('helpers.py', _('Deleting {}.').format(i))
        remove_thing(i)


def ospy_to_default(wait=2, del_upload=True):
    import os, os.path
    print_report('helpers.py', _('Deleting OSPy to default...'))
    time.sleep(wait)
    empty_directory(os.path.join('ospy', 'backup'))
    empty_directory(os.path.join('ssl'))
    empty_directory(os.path.join('ospy', 'images', 'stations'))
    empty_directory(os.path.join('ospy', '__pycache__'))
    empty_directory(os.path.join('ospy', 'data'))
    if del_upload:
        empty_directory(os.path.join('ospy', 'upload'))


def now():
    return time.time() + (datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds()


def try_float(val, default=0):
    try:
        return float(val)
    except ValueError:
        return default
        

def datetime_string(timestamp=None):
    if timestamp:
        if hasattr(timestamp, 'strftime'):
            return timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return time.strftime("%Y-%m-%d %H:%M:%S", timestamp)
    else:
        return time.strftime("%Y-%m-%d %H:%M:%S")


def two_digits(n):
    return u'%02d' % int(n)


def avg(lst):
    return sum(lst) / len(lst)


def program_delay(program):
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    result = (program.start - today).total_seconds()
    while result < 0:
        result += program.modulo*60
    return int(result/24/3600)


def formatTime(t):
    from . options import options
    if options.time_format:
        return t
    else:
        hour = int(t[0:2])
        newhour = hour
        if hour == 0:
            newhour = 12
        if hour > 12:
            newhour = hour-12
        return str(newhour) + t[2:] + (u" am" if hour<12 else u" pm")


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
        print_report('helpers.py', _('Rebooting...'))

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
        print_report('helpers.py', _('Powering off...'))

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


def _service_restart_command():
    if os.path.exists('/bin/systemctl') or os.path.exists('/usr/bin/systemctl'):
        return 'systemctl restart ospy || service ospy restart'
    if os.path.exists('/usr/sbin/service') or os.path.exists('/sbin/service'):
        return 'service ospy restart'
    return None


def _restart_via_service():
    command = _service_restart_command()
    if not command:
        return False

    try:
        subprocess.Popen(
            ['/bin/sh', '-c', command],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True
        )
        return True
    except Exception:
        print_report('helpers.py', _('Service restart failed, falling back to process restart.') + '\n' + traceback.format_exc())
        return False


def restart(wait=1, block=False):
    if block:
        time.sleep(wait)
        from ospy.stations import stations
        stations.clear()
        print_report('helpers.py', _('Restarting...'))

        import sys
        if determine_platform() == 'nt':
            import subprocess
            # Use this weird construction to start a separate process that is not killed when we stop the current one
            subprocess.Popen(['cmd.exe', '/c', 'start', sys.executable] + sys.argv)
        else:
            import os
            if _restart_via_service():
                return
            from ospy import server
            server.stop()
            os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        from threading import Thread
        t = Thread(target=restart, args=(wait, True))
        t.daemon = False
        t.start()


def uptime():
    """Returns UpTime for RPi"""
    try:
        with open(u'/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            seconds = int(uptime_seconds % 60)
            minutes = int(uptime_seconds /60 % 60)
            hours = int(uptime_seconds / 60 / 60 % 24)
            days = int(uptime_seconds / 60 /60 / 24)
         
        string = ''
        if days == 1 and hours < 23 and minutes < 59:
            string = '%d' % (days) + _('. day')    # 1 den
        if days >= 2 and days < 5:
            string = '%d' % (days) + _('. days')   # 2-4 dny
        if days > 4:
            string = '%d' % (days) + _('. days ')  # >5 dnu

        string += ' %s:%s' % (two_digits(hours), two_digits(minutes))

    except Exception:
       string = _('Unknown')
       print_report('helpers.py', traceback.format_exc())

    return string


def get_who_is_operator():
    try:
        from ospy import server
        logged_is = '{}: {} - {}: '.format(_('Operator'), server.session['visitor'], _('Access'))
        if server.session['category'] == 'admin':
           logged_is += '{}'.format(_('Administrator'))
        elif server.session['category'] == 'user':
           logged_is += '{}'.format(_('User'))
        elif server.session['category'] == 'public':
           logged_is += '{}'.format(_('Public'))
        else:
           logged_is += '{}'.format(_('Unknown'))                 
        return logged_is        
    except Exception:
        pass
        return ''             


def is_valid_ipv4_address(address):
    import socket
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:    # not a valid address
        return False
    return True


def is_valid_ipv6_address(address):
    import socket
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True


def valid_ip(address):
    """Return True if we have a valid IP address V4 or V6"""
    try:
        if is_valid_ipv4_address(address) or is_valid_ipv6_address(address):
            return True
        else:
            return False
    except:
        return False


def split_ip(ip):
    """If this is a valid IP address, return the 4 octets (or all zeros if a problem)"""
    octets = []
    ip += u'.'
    try:
        for i in range(4):
            dot_idx = ip.find('.')
            if dot_idx == -1:
                return ('0','0','0','0')
            octets.append(ip[0:dot_idx])
            ip = ip[dot_idx+1:]
    except:
        print_report('helpers.py', traceback.format_exc())
        return ('0','0','0','0')
    return (octets[0], octets[1], octets[2], octets[3])
        

def get_ip(net=u''):
    """Returns the IP address of 'net' if specified, otherwise 'wlan0', 'eth0', 'ppp0' whichever is found first."""
    try:
        import subprocess
        string = _('No IP Settings')
        arg = [b'/sbin/ip', b'route', b'list']
        p = subprocess.Popen(arg, stdout=subprocess.PIPE)
        data, errdata = p.communicate()
        data = data.split(b'\n')
        list = [b'wlan0', b'eth0', b'ppp0'] if net == '' else [net]
        for iface in list:
            for d in data:
                split_d = d.split()
                try:
                    idx = split_d.index(iface) # exception if not found
                    ipaddr = split_d[split_d.index(b'src') + 1]
                    return ipaddr.decode('utf-8')
                except:
                    try:
                        import socket
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.connect(("8.8.8.8",80))
                        ipaddr = s.getsockname()[0]
                        s.close()
                        return ipaddr
                    except:    
                        print_report(u'helpers.py', traceback.format_exc())
                        pass
        return string
        
    except:
        print_report('helpers.py', traceback.format_exc())
        return _('No IP Settings') 


def get_mac():
    """Return MAC from file"""
    try:
        import uuid
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
        return mac.upper()

    except Exception:
        print_report('helpers.py', traceback.format_exc())
        return _('Unknown')


def get_link_local_address(mac):
    """ get ipv6 link local address from 48bits mac address,
        details are described at the https://tools.ietf.org/html/rfc4291#section-2.5.1
        for example mac address 00:01:02:aa:bb:cc
        step 1. inverting the universal/local bit of mac address to 02:01:02:0a:0b:0c
        step 2. insert fffe in the middle of mac address to 02:01:02:ff:fe:0a:0b:0c
        step 3. convert to ip address with fe80::/64, strip the leading '0' in each sector between ':'
                fe80::201:2ff:fe0a:b0c
    """
    try:
        macs = mac.strip("\n").split(":")
        # step 1. inverting the "u" bit of mac address
        macs[0] = hex(int(macs[0], 16) ^ 2)[2:]
        # step 2, insert "fffe"
        part1 = macs[0] + macs[1] + ":"
        part2 = macs[2] + "ff" + ":"
        part3 = "fe" + macs[3] + ":"
        part4 = macs[4] + macs[5]
        #step 3
        addr = "fe80::" + part1.lstrip("0") + part2.lstrip("0") + part3.lstrip("0") + part4.lstrip("0") 
        if valid_ip(addr):
            return addr
        else:
            return _('No IP6 Settings')
    except:
        print_report('helpers.py', traceback.format_exc())
        return _('No IP6 Settings')


def get_meminfo():
    """Return the information in /proc/meminfo as a dictionary"""
    try:
        meminfo = {}
        with open('/proc/meminfo') as f:
            for line in f:
                meminfo[line.split(':')[0]] = line.split(':')[1].strip()
        return meminfo

    except Exception:
        print_report('helpers.py', traceback.format_exc())
        return {
              'MemTotal': _('Unknown'),
              'MemFree': _('Unknown')
              }
 

def get_netdevs():
    """RX and TX bytes for each of the network devices"""
    try:
        with open('/proc/net/dev') as f:
            net_dump = f.readlines()
        device_data = {}
        for line in net_dump[2:]:
            line = line.split(u':')
            if line[0].strip() != u'lo':
                device_data[line[0].strip()] = {u'rx': round(float(line[1].split()[0])/(1024.0*1024.0), 2),
                                                u'tx': round(float(line[1].split()[8])/(1024.0*1024.0), 2)}
        return device_data
    except Exception:
        print_report('helpers.py', traceback.format_exc())
        return {}


def get_cpu_temp(unit=None):
    """Returns the temperature of the CPU if available."""
    import os
    try:
        platform = determine_platform()
        if platform == 'bo':
            res = os.popen(u'cat /sys/class/hwmon/hwmon0/device/temp1_input').readline()
            temp = str(int(float(res) / 1000))
        elif platform =='pi':
            res = os.popen('vcgencmd measure_temp').readline()
            temp = res.replace("temp=", "").replace("'C\n", "")
        else:
            temp = str(0)

        if unit == 'F':
            return str(round(9.0/5.0 * float(temp) + 32, 2))
        elif unit is not None:
            return str(round(float(temp), 2))
        else:
            return round(temp, 2)
    except Exception:
        print_report('helpers.py', traceback.format_exc())
        return _('-')


prev_time_doing_things  = 0  
prev_time_doing_nothing = 0
def get_cpu_usage():
    """Return the CPU usage."""
    # Read first line from /proc/stat. It should start with "cpu" and contains times spend in various modes by all CPU's totalled.
    cpustats = ''
    global prev_time_doing_things 
    global prev_time_doing_nothing 

    try:
        import os.path
        with open("/proc/stat") as procfile:
            cpustats = procfile.readline().split()
    except Exception:
        return _('-')            

    # Sanity check
    if cpustats[0] != 'cpu':
        raise ValueError("First line of /proc/stat not recognised")

    # Refer to "man 5 proc" (search for /proc/stat) for information about which field means what.
    # Here we do calculation as simple as possible: CPU% = 100 * time-doing-things / (time_doing_things + time_doing_nothing)

    user_time = int(cpustats[1])    # time spent in user space
    nice_time = int(cpustats[2])    # 'nice' time spent in user space
    system_time = int(cpustats[3])  # time spent in kernel space

    idle_time = int(cpustats[4])    # time spent idly
    iowait_time = int(cpustats[5])  # time spent waiting is also doing nothing

    time_doing_things = user_time + nice_time + system_time
    time_doing_nothing = idle_time + iowait_time

    diff_time_doing_things = time_doing_things - prev_time_doing_things
    diff_time_doing_nothing = time_doing_nothing - prev_time_doing_nothing

    try:
       cpu_percentage = 100.0 * diff_time_doing_things/ (diff_time_doing_things + diff_time_doing_nothing)
    except:
       cpu_percentage = 0.0
       
    # remember current values to subtract next iteration of the loop
    prev_time_doing_things = time_doing_things
    prev_time_doing_nothing = time_doing_nothing

    # Output latest perccentage
    return float(round(cpu_percentage ,1))  # To one digits    


def mkdir_p(path):
    import os
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def configured_upload_limit_bytes():
    from ospy.options import options
    try:
        size_mb = float(getattr(options, 'max_upload_size_mb', 0))
    except Exception:
        size_mb = 0
    if size_mb <= 0:
        return None
    return int(size_mb * 1024 * 1024)


def read_limited_upload(file_obj, max_bytes=None):
    if max_bytes is None:
        max_bytes = configured_upload_limit_bytes()

    data = bytearray()
    while True:
        chunk = file_obj.read(UPLOAD_READ_CHUNK_SIZE)
        if not chunk:
            break
        data.extend(chunk)
        if max_bytes is not None and len(data) > max_bytes:
            raise ValueError(_('Uploaded file is larger than the configured maximum size.'))
    return bytes(data)


def safe_image_path(image_id, station_folder=False):
    import os

    if image_id is None:
        return None

    image_id = str(image_id).replace('\\', '/')
    if '/' in image_id:
        return None

    name = os.path.basename(image_id)
    if name in ('', '.', '..') or name != image_id:
        return None

    root = os.path.abspath(os.path.join('ospy', 'images', 'stations' if station_folder else ''))
    allowed_exts = ('.png', '.jpg', '.jpeg', '.gif')
    candidates = [name] if os.path.splitext(name)[1].lower() else [name + ext for ext in allowed_exts]

    root_check = os.path.normcase(root)
    for candidate in candidates:
        if os.path.splitext(candidate)[1].lower() not in allowed_exts:
            continue
        path = os.path.abspath(os.path.join(root, candidate))
        if os.path.commonpath([root_check, os.path.normcase(path)]) != root_check:
            continue
        if os.path.isfile(path):
            return path
    return None


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
    return '%02d:%02d' % (hours, minutes) + ((u':%02d' % seconds) if with_seconds else '')


def minute_time_str(minute_time, with_seconds=False):
    return timedelta_time_str(datetime.timedelta(minutes=minute_time), with_seconds)


def program_group_run_sequence(group_id, days=14, include_temporarily_blocked=False):
    """Return the next scheduled run per program in a group, ordered by scheduler output."""
    from ospy.programs import programs
    from ospy.scheduler import predicted_schedule

    now = datetime.datetime.now()
    date_time_start = datetime.datetime.combine(now.date(), datetime.time.min)
    date_time_end = date_time_start + datetime.timedelta(days=days)
    group_programs = programs.programs_in_group(group_id)
    group_indexes = set(program.index for program in group_programs)
    program_by_index = {program.index: program for program in group_programs}
    occurrences = {}

    if not group_indexes:
        return []

    for interval in predicted_schedule(date_time_start, date_time_end):
        program_index = interval.get('program')
        blocked = interval.get('blocked')
        if program_index not in group_indexes:
            continue
        if blocked and not include_temporarily_blocked:
            continue
        if blocked in ('cut-off', 'scheduler error'):
            continue

        original_start = interval.get('original_start', interval.get('start'))
        key = (program_index, original_start)
        if key not in occurrences:
            occurrences[key] = {
                'program': program_by_index[program_index],
                'start': interval['start'],
                'end': interval['end'],
                'stations': set()
            }
        else:
            occurrences[key]['start'] = min(occurrences[key]['start'], interval['start'])
            occurrences[key]['end'] = max(occurrences[key]['end'], interval['end'])
        occurrences[key]['stations'].add(interval.get('station'))

    next_by_program = {}
    for occurrence in occurrences.values():
        program = occurrence['program']
        if program.index not in next_by_program or occurrence['start'] < next_by_program[program.index]['start']:
            next_by_program[program.index] = occurrence

    result = []
    for occurrence in sorted(next_by_program.values(), key=lambda item: (item['start'], item['program'].index)):
        program = occurrence['program']
        minutes = max(1, int(round((occurrence['end'] - occurrence['start']).total_seconds() / 60)))
        station_names = []
        try:
            from ospy.stations import stations
            station_names = [stations.get(station).name for station in sorted(occurrence['stations']) if station is not None]
        except Exception:
            station_names = []
        result.append({
            'number': program.index + 1,
            'name': program.name,
            'minutes': minutes,
            'start': occurrence['start'],
            'end': occurrence['end'],
            'title': '{} {}: {} - {}, {} {}, {}'.format(
                _('Program'),
                program.index + 1,
                occurrence['start'].strftime('%Y-%m-%d %H:%M'),
                occurrence['end'].strftime('%H:%M'),
                minutes,
                _('min'),
                ', '.join(station_names)
            )
        })

    return result


def short_day(index):
    return [_('Mon'), _('Tue'), _('Wed'), _('Thu'), _('Fri'), _('Sat'), _('Sun')][index]


def long_day(index):
    return [_('Monday'),
            _('Tuesday'),
            _('Wednesday'),
            _('Thursday'),
            _('Friday'),
            _('Saturday'),
            _('Sunday')][index]


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
                allowed_values = option.get('options')
                if allowed_values is not None:
                    if hasattr(allowed_values, '__call__'):
                        allowed_values = allowed_values()
                    if value not in allowed_values:
                        continue
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

last_ip_check_time = 0
external_ip_address = '-'
external_ip_refresh_thread = None
EXTERNAL_IP_LOCK = Lock()
EXTERNAL_IP_SERVICES = (
    'https://api.ipify.org',
    'https://pihrt.com/ipbot.php',
)


def _refresh_external_ip():
    """Refresh the external IP cache without blocking request or scheduler threads."""

    global last_ip_check_time, external_ip_address, external_ip_refresh_thread

    result_address = '-'
    try:
        if net_connect():
            for service in EXTERNAL_IP_SERVICES:
                try:
                    result = subprocess.check_output(
                        ['/usr/bin/curl', '-ksS', '--max-time', '8', service],
                        stderr=subprocess.DEVNULL,
                    ).decode('utf-8').strip()
                    if valid_ip(result):
                        result_address = result
                        break
                except (OSError, subprocess.SubprocessError, UnicodeError):
                    continue
    finally:
        with EXTERNAL_IP_LOCK:
            external_ip_address = result_address
            last_ip_check_time = now()
            external_ip_refresh_thread = None


def get_external_ip():
    """Return the cached external IP and refresh stale data in the background."""

    global external_ip_refresh_thread

    with EXTERNAL_IP_LOCK:
        if (now() - last_ip_check_time > 30 and
                external_ip_refresh_thread is None):
            external_ip_refresh_thread = Thread(
                target=_refresh_external_ip,
                name='ExternalIPRefresh',
            )
            external_ip_refresh_thread.daemon = True
            try:
                external_ip_refresh_thread.start()
            except RuntimeError:
                external_ip_refresh_thread = None
        result = external_ip_address

    return '{}'.format(result) if valid_ip(result) else '-'


def external_ip_refresh_pending():
    with EXTERNAL_IP_LOCK:
        return external_ip_refresh_thread is not None


########################
#### Login Handling ####

def password_salt():
    return secrets.token_urlsafe(32)


def password_hash(password, salt):
    import hashlib
    if not salt:
        salt = password_salt()
    iterations = PASSWORD_HASH_ITERATIONS
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
    return '{}${}${}${}'.format(PASSWORD_HASH_ALGORITHM, iterations, salt, digest.hex())

def _request_ip():
    try:
        import web
        return web.ctx.env.get('REMOTE_ADDR', '-')
    except:
        return '-'

def _bruteforce_key(username):
    return '{}:{}'.format(_request_ip(), (username or '').lower())

def _bruteforce_delay(failures):
    if failures < BRUTEFORCE_DELAY_AFTER:
        return 0
    if failures < 6:
        return 2
    if failures < BRUTEFORCE_LOCK_AFTER:
        return 10
    return 0

def _bruteforce_wait(username):
    key = _bruteforce_key(username)
    with BRUTEFORCE_LOCK:
        attempt = BRUTEFORCE_ATTEMPTS.get(key, {'failures': 0, 'blocked_until': 0})
        if attempt.get('blocked_until', 0) > time.time():
            return False
        delay = _bruteforce_delay(attempt.get('failures', 0))
    if delay > 0:
        time.sleep(delay)
    return True

def _bruteforce_success(username):
    key = _bruteforce_key(username)
    with BRUTEFORCE_LOCK:
        BRUTEFORCE_ATTEMPTS.pop(key, None)

def _bruteforce_failure(username):
    key = _bruteforce_key(username)
    now_ts = time.time()
    with BRUTEFORCE_LOCK:
        attempt = BRUTEFORCE_ATTEMPTS.get(key, {'failures': 0, 'blocked_until': 0})
        attempt['failures'] = attempt.get('failures', 0) + 1
        if attempt['failures'] >= BRUTEFORCE_LOCK_AFTER:
            attempt['blocked_until'] = now_ts + BRUTEFORCE_LOCK_SECONDS
        BRUTEFORCE_ATTEMPTS[key] = attempt


def bruteforce_blocked(username):
    """Return whether the current IP and username are temporarily blocked."""
    key = _bruteforce_key(username)
    with BRUTEFORCE_LOCK:
        attempt = BRUTEFORCE_ATTEMPTS.get(key, {})
        return attempt.get('blocked_until', 0) > time.time()

def _legacy_password_hash(password, salt):
    import hashlib
    m = hashlib.sha256()
    m.update((password + salt).encode('utf-8'))
    return m.hexdigest()


def _password_matches(password, password_hash_value, salt):
    import hashlib

    if isinstance(password_hash_value, str) and password_hash_value.startswith(PASSWORD_HASH_ALGORITHM + '$'):
        try:
            algorithm, iterations, stored_salt, stored_hash = password_hash_value.split('$', 3)
            if algorithm != PASSWORD_HASH_ALGORITHM:
                return False, False
            digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), stored_salt.encode('utf-8'), int(iterations))
            return hmac.compare_digest(digest.hex(), stored_hash), False
        except Exception:
            print_report('helpers.py', traceback.format_exc())
            return False, False

    return hmac.compare_digest(_legacy_password_hash(password, salt), password_hash_value), True


def _upgrade_admin_password_hash(password):
    from ospy.options import options
    options.password_salt = password_salt()
    options.password_hash = password_hash(password, options.password_salt)


def _upgrade_user_password_hash(user, password):
    user.password_salt = password_salt()
    user.password_hash = password_hash(password, user.password_salt)

def test_password(password, username):
    from ospy.options import options
    from ospy.users import users
    from ospy import server

    if not _bruteforce_wait(username):
        print_report('helpers.py', _('Login blocked temporarily for {} from IP {}').format(username, _request_ip()))
        return False
    
    matches, legacy_hash = _password_matches(password, options.password_hash, options.password_salt)
    if matches and options.admin_user == username:     # Login for OSPy main administrator
        if legacy_hash:
            _upgrade_admin_password_hash(password)
        options.password_time = 0
        server.session['category'] = 'admin'
        server.session['visitor']  = options.admin_user
        _bruteforce_success(username)
        print_report('helpers.py', _('Logged in {}, as operator {}').format(server.session['visitor'], server.session['category']))
        return True
    else:
        for user in users.get():
            matches, legacy_hash = _password_matches(password, user.password_hash, user.password_salt)
            if matches and user.name == username:            # Login for others OSPy users
                if legacy_hash:
                    _upgrade_user_password_hash(user, password)
                options.password_time = 0 
                _bruteforce_success(username)
                if user.category == '0':   # public
                    server.session['category'] = 'public'
                    server.session['visitor']  =  user.name
                    print_report('helpers.py', _('Logged in {}, as operator {}').format(server.session['visitor'], server.session['category']))
                    return True
                elif user.category == '1': # user
                    server.session['category'] = 'user'
                    server.session['visitor']  =  user.name
                    print_report('helpers.py', _('Logged in {}, as operator {}').format(server.session['visitor'], server.session['category']))                    
                    return True
                elif user.category == '2': # admin
                    server.session['category'] = 'admin'  
                    server.session['visitor']  =  user.name
                    print_report('helpers.py', _('Logged in {}, as operator {}').format(server.session['visitor'], server.session['category']))                    
                    return True
                elif user.category == '3': # sensor
                    server.session['category'] = 'sensor'  
                    server.session['visitor']  =  user.name
                    print_report('helpers.py', _('Logged in {}, as operator {}').format(server.session['visitor'], server.session['category']))
                    return True
    _bruteforce_failure(username)
    return False


def check_login(redirect=False):
    from ospy import server
    import web
    from ospy.options import options
    qdict = web.input()

    try:
        if options.no_password:
            server.session['category'] = 'admin'
            server.session['visitor']  = _('No password')
            return True

        if hasattr(server, 'session') and hasattr(server.session, 'validated') and server.session.validated:
            return True
    except KeyError:
        print_report('helpers.py', traceback.format_exc())
        return False

    if 'pw' in qdict and 'nm' in qdict: # password and user name
        if test_password(qdict['pw'], qdict['nm']):
            if (qdict['nm'] == options.admin_user and
                    getattr(options, 'two_factor_method', 'none') != 'none'):
                server.session['category'] = 'public'
                server.session['visitor'] = 'Unknown'
                if redirect:
                    raise web.unauthorized()
                return False
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

def csrf_token():
    from ospy import server
    token = server.session.get('csrf_token')
    if not token:
        token = os.urandom(32).hex()
        server.session['csrf_token'] = token
    return token

def csrf_input():
    return '<input type="hidden" name="csrf" value="{}">'.format(csrf_token())

def csrf_query():
    from urllib.parse import quote_plus
    return 'csrf={}'.format(quote_plus(csrf_token()))

def verify_csrf(qdict=None):
    import web
    from urllib.parse import parse_qs
    if qdict is None:
        qdict = {}
    expected = csrf_token()
    supplied = ''
    query = web.ctx.env.get('QUERY_STRING', '')
    if query:
        supplied = parse_qs(query).get('csrf', [''])[0]
    supplied = supplied or qdict.get('csrf', '') or web.ctx.env.get('HTTP_X_CSRF_TOKEN', '')
    if not supplied and web.ctx.method == 'POST':
        supplied = web.input().get('csrf', '')
    if not supplied or not hmac.compare_digest(supplied, expected):
        print_report('helpers.py', _('CSRF token verification failed from IP {}.').format(_request_ip()))
        raise web.forbidden()


def template_globals():
    import json
    import plugins
    import urllib
    from urllib.request import urlopen
    from urllib.parse import quote_plus
    from web import ctx

    from ospy.inputs import inputs
    from ospy.log import log
    from ospy.options import level_adjustments, options, rain_blocks, program_level_adjustments
    from ospy.programs import programs, ProgramType
    from ospy.runonce import run_once
    from ospy.stations import stations
    from ospy import version
    from ospy.server import session
    from ospy.webpages import pluginFtr
    from ospy.webpages import pluginStn
    from ospy.webpages import pluginScripts
    from ospy.webpages import sensorSearch
    from ospy import i18n
    from ospy.users import users
    from ospy.sensors import sensors, sensors_timer
    from ospy.weather import weather

    result = {
        'str': str,
        'bool': bool,
        'int': int,
        'round': round,
        'isinstance': isinstance,
        'sorted': sorted,
        'hasattr': hasattr,
        '_': _,
        'i18n': i18n,
        'now': now,
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
    result.append((2, 'Translation Guide (i18n)', os.path.join('i18n', 'README.md')))
    result.append((2, 'Automated Tests', os.path.join('tests', 'README.md')))
    for doc in help_files_in_directory(os.path.join('ospy', 'docs')):
        result.append((2, doc[0], doc[1]))

    result.append((1, 'API'))
    result.append((2, 'Readme', os.path.join('api', 'README.md')))
    for doc in help_files_in_directory(os.path.join('api', 'docs')):
        result.append((2, doc[0], doc[1]))

    result.append((1, 'Sensors'))
    result.append((2, 'Readme', os.path.join('hardware_pcb', 'sensors_pcb_fw', 'README.md')))
    for doc in help_files_in_directory(os.path.join('hardware_pcb', 'sensors_pcb_fw', 'docs')):
        result.append((2, doc[0], doc[1]))

    result.append((1, 'Remote Controllers'))
    result.append((2, 'Readme', os.path.join('hardware_pcb', 'remote_controllers_fw', 'README.md')))
    for doc in help_files_in_directory(os.path.join('hardware_pcb', 'remote_controllers_fw', 'docs')):
        result.append((2, doc[0], doc[1]))               

    result.append((1, 'Plug-ins'))
    result.append((2, 'Readme', os.path.join('plugins', 'README.md')))
    plugin_changelog = os.path.join('plugins', 'CHANGELOG.md')
    if os.path.isfile(plugin_changelog):
        result.append((2, 'Changelog', plugin_changelog))
    from plugins import plugin_names, plugin_dir, plugin_docs_dir
    for module, name in plugin_names().items():

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
    import traceback

    try:
        id = int(id)
        docs = get_help_files()
        if 0 <= id < len(docs):
            option = docs[id]
            if len(option) > 2:
                filename = option[2]
                with open(filename, 'r', encoding='utf8', errors='ignore') as fh:
                    return gfm_str_to_html(fh.read())     
    except Exception:
        print_report('helpers.py', 'Help file error:\n' + traceback.format_exc())
        pass
    return ''


def gfm_str_to_html(input):
    import cmarkgfm
    converted = cmarkgfm.markdown_to_html(input)

    import web
    return web.template.Template(converted, globals=template_globals())()


def ASCI_convert(name):
  try:
     if name == None:
        return None
     import unicodedata    
     convert_text = unicodedata.normalize('NFKD', name).encode('ascii','ignore')
     return convert_text
  except: 
     if name == None:
        return None
     import re
     name = re.sub(r"[^A-Za-z0-9_+-.:?!/ ]+", '_', name)
     return name


def print_report(title, message=None):
    """ All prints are reported here """
    try:
        print('{}: {}'.format(title, message))
    except:
        print_report('helpers.py', traceback.format_exc())
        pass
         

def decode_B64(msg):
    try:
        import base64

        decode = base64.decodestring(msg)
        return decode    
    except:
        print_report('helpers.py', traceback.format_exc())
        return ''


def net_connect(host=None):
    from ospy.options import options
    import subprocess
    import os
    try:
        if host is None:
            host = options.ping_ip
        
        command = ['ping', '-c', '1', host]
        response = subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)    
        if response == 0:
            return True
        else:
            return False
    except:
        print_report('server.py', traceback.format_exc())
        return False


def cpu_info():
    ### Return CPU unique Serial Number ###
    try:
        import subprocess
        command = 'sudo cat /proc/cpuinfo | grep ^Serial | cut -d":" -f2'
        proc = subprocess.Popen(command, stderr=subprocess.STDOUT, # merge stdout and stderr
        stdout=subprocess.PIPE, shell=True)
        output = proc.communicate()[0].decode('utf-8') # remove byte b' 000...\n'
        output = output.replace('\n','')               # remove n ' 000...'
        output = output.strip()                        # remove spaces " " output now '000...'
        if output:
            return output
        else:
            return False
    except:
        print_report('server.py', traceback.format_exc())
        return False


def read_wifi_signal():
    # https://www.programcreek.com/python/?CodeExample=get+rssi
    import os
    try:
        dBm = os.popen("/bin/cat /proc/net/wireless | awk 'NR==3 {print $4}' | sed 's/\\.//'").readline().strip()
        if dBm=="":
            return 0
        dBm = int(dBm)

        if(dBm <= -100):
            quality = 0
        elif(dBm >= -50):
            quality = 100
        else:
            quality = 2 * (dBm + 100)
        return quality

    except:
        print_report('helpers.py', traceback.format_exc())
        return 0


def is_fqdn(hostname):
    """
    https://en.m.wikipedia.org/wiki/Fully_qualified_domain_name
    """
    if not hostname:
        return False

    if not 1 < len(hostname) < 253:
        return False

    # Remove trailing dot
    if hostname[-1] == ".":
        hostname = hostname[0:-1]

    #  Split hostname into list of DNS labels
    labels = hostname.split(".")

    #  Define pattern of DNS label
    #  Can begin and end with a number or letter only
    #  Can contain hyphens, a-z, A-Z, 0-9
    #  1 - 63 chars allowed
    fqdn = re.compile(r"^[a-z0-9]([a-z-0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)

    # Check that all labels match that pattern.
    return all(fqdn.match(label) for label in labels)


def ospy_web_url(host=None):
    """ Return OSPy web server URL """
    # First:  Valid host setting
    import socket

    if not is_fqdn(host):
        # Second: System hostname
        host = socket.getfqdn()
        if not is_fqdn(host):
            # Third : System IP used to connect with MQTT broker
            host = get_ip('eth0')
    if not host:
        return None

    return '{}'.format(host)


def get_mem_size(num):
    if num == 0:
        return _('256MB')
    if num == 1:
        return _('512MB')
    if num == 2:
        return _('1GB')
    if num == 3:
        return _('2GB')
    if num == 4:
        return _('4GB')
    if num == 5:
        return _('8GB')


def get_rpi_revision_codes():
    """https://github.com/raspberrypi/documentation/blob/develop/documentation/asciidoc/computers/raspberry-pi/revision-codes.adoc"""
    cmd = "cat /proc/cpuinfo | awk '/Revision/ {print $3}'"
    revcode = subprocess.check_output(cmd, shell=True)

    code = int(revcode, 16)
    new = (code >> 23) & 0x1
    model = (code >> 4) & 0xff
    mem = (code >> 20) & 0x7
    msg = _('Unknown')

    if new and model == 0x17:
        msg = _('Raspberry Pi 5 with at least {} RAM!').format(get_mem_size(mem))
    if new and model == 0x11:
        msg = _('Raspberry Pi 4B with at least {} RAM!').format(get_mem_size(mem))
    if new and model == 0x04: 
        msg = _('Raspberry Pi 2B with at least {} RAM!').format(get_mem_size(mem))
    if new and model == 0x0e: 
        msg = _('Raspberry Pi 3A with at least {} RAM!').format(get_mem_size(mem))
    if new and model == 0x08: 
        msg = _('Raspberry Pi 3B with at least {} RAM!').format(get_mem_size(mem))
    if new and model == 0x0d: 
        msg = _('Raspberry Pi 3B+ with at least {} RAM!').format(get_mem_size(mem))
    if new and model == 0x12: 
        msg = _('Raspberry Pi Zero 2 W at least {} RAM!').format(get_mem_size(mem))
    if new and model == 0x09: 
        msg = _('Raspberry Pi Zero at least {} RAM!').format(get_mem_size(mem))
    if new and model == 0x0c: 
        msg = _('Raspberry Pi Zero W at least {} RAM!').format(get_mem_size(mem))
    if new and model == 0x13: 
        msg = _('Raspberry Pi 400 at least {} RAM!').format(get_mem_size(mem))
    return code, new, model, mem, msg
