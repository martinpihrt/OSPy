# -*- coding: utf-8 -*-
from __future__ import absolute_import

__author__ = 'Rimco' # additional changes Martin Pihrt

# System imports
import datetime
import logging
import random
import time
import errno
import re
import subprocess
import traceback
import ast
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
    return '%02d' % int(n)


def program_delay(program):
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    result = (program.start - today).total_seconds()
    while result < 0:
        result += program.modulo*60
    return int(result/24/3600)


def formatTime(t):
    from .options import options
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
        logging.info(_(u'Rebooting...'))

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
        logging.info(_(u'Powering off...'))

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
        logging.info(_(u'Restarting...'))

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
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            seconds = int(uptime_seconds % 60)
            minutes = int(uptime_seconds /60 % 60)
            hours = int(uptime_seconds / 60 / 60 % 24)
            days = int(uptime_seconds / 60 /60 / 24)
         
        string = ''
        if days == 1 and hours < 23 and minutes < 59:
            string = u'%d' % (days) + _(u'. day')    # den
        if days >= 2 and days < 5:
            string = u'%d' % (days) + _(u'. days')   # dny 
        if days > 4:
            string = u'%d' % (days) + _(u'. days ')  # dnu  

        string += u' %s:%s' % (two_digits(hours), two_digits(minutes))

    except Exception:
       string = _(u'Unknown')
       print_report('helpers.py', traceback.format_exc())

    return string  

    
def valid_ip(ip):
    """Return True if we have a valid IP address"""
    try:
        octets = ip.split('.')
        if len(octets) != 4:
            return False
        for o in octets:
            if int(o) < 0 or int(o) > 255:
                return False
    except:
        return False
    return True


def split_ip(ip):
    """If this is a valid IP address, return the 4 octets (or all zeros if a problem)"""
    octets = []
    ip += '.'
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
        

def get_ip(net=''):
    """Returns the IP address of 'net' if specified, otherwise 'wlan0', 'eth0', 'ppp0' whichever is found first."""
    try:
        import subprocess
        from ospy.options import options
        arg = ['/sbin/ip', 'route', 'list']
        p = subprocess.Popen(arg, stdout=subprocess.PIPE)
        data,errdata = p.communicate()
        data = data.split('\n')
        list = ['wlan0', 'eth0', 'ppp0'] if net == '' else [net]
        for iface in list:
            for d in data:
                split_d = d.split()
                try:
                    idx = split_d.index(iface) # exception if not found
                    ipaddr = split_d[split_d.index('src') + 1]
                    return ipaddr
                except:
                    pass
        
            string = _(u'No IP Settings')
        return string
        
    except:
        print_report('helpers.py', traceback.format_exc())
        return _('No IP Settings') 


def get_mac():
    """Return MAC from file"""
    try:
        return str(open('/sys/class/net/eth0/address').read())

    except Exception:
        print_report('helpers.py', traceback.format_exc())
        return _(u'Unknown')


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
              'MemTotal': _(u'Unknown'),
              'MemFree': _(u'Unknown')
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
        print_report('helpers.py', traceback.format_exc())
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
        print_report('helpers.py', traceback.format_exc())
        return _(u'-')


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
        return _(u'-')            

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
    return [_(u'Mon'), _(u'Tue'), _(u'Wed'), _(u'Thu'), _(u'Fri'), _(u'Sat'), _(u'Sun')][index]


def long_day(index):
    return [_(u'Monday'),
            _(u'Tuesday'),
            _(u'Wednesday'),
            _(u'Thursday'),
            _(u'Friday'),
            _(u'Saturday'),
            _(u'Sunday')][index]


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

last_ip_check_time = 0
external_ip_address = '-'
def get_external_ip():
    """Return the externally visible IP address for this OSPy system."""

    global last_ip_check_time, external_ip_address

    check_time = 0
    if external_ip_address is '-':
        check_time = 10
    else:
        check_time = 5*60   

    if now() - last_ip_check_time > check_time:
        last_ip_check_time = now()
        try:
            external_ip_address = subprocess.check_output(['/usr/bin/curl', '-ks', 'https://pihrt.com/ipbot.php'])
        except:
            print_report('helpers.py', traceback.format_exc())
            external_ip_address = '-'

    return str(external_ip_address)


########################
#### Login Handling ####

def password_salt():
    return "".join(chr(random.randint(33, 127)) for _ in range(64))


def password_hash(password, salt):
    import hashlib
    m = hashlib.sha256() 
    m.update((password+salt).encode('utf-8')) 
    return m.hexdigest()


def test_password(password, username):
    from ospy.options import options
    from ospy.users import users
    from ospy import server

    result_admin = False
    result_users = False

    # Brute-force protection:
    with BRUTEFORCE_LOCK: 
        if options.password_time > 0:                                           # for OSPY main administrator
            time.sleep(options.password_time)

        for user in users.get():                                                # for others OSPy users
            if user.password_time > 0:
                time.sleep(user.password_time)            

    if options.password_hash == password_hash(password, options.password_salt) and options.admin_user == username: # for OSPY main administrator
        result_admin = True
        try:
            server.session['category'] = 'admin'
            server.session['visitor']  = _(u'%s') % options.admin_user
        except:
            pass    

    if result_admin:
        options.password_time = 0
    else:
        if options.password_time < 30:
            options.password_time += 1        

    for user in users.get():
        if user.password_hash == password_hash(password, user.password_salt) and user.name == username:            # for others OSPy users
            result_users = True  
            if user.category == '0': # public
                try:
                    server.session['category'] = 'public'
                    server.session['visitor']  =  user.name
                except:
                    pass    
            elif user.category == '1': # user
                try:
                    server.session['category'] = 'user'
                    server.session['visitor']  =  user.name
                except:
                    pass                     
            elif user.category == '2': # admin
                try:
                    server.session['category'] = 'admin'  
                    server.session['visitor']  =  user.name
                except:
                    pass                                                                         

        if result_users:
            user.password_time = 0
            break
        else:
            if user.password_time < 30:
                user.password_time += 1          

    if result_admin or result_users: 
        try:
            if user.category != '3': # no info for sensors input
                print_report('helpers.py', _(u'Logged in %s, as operator %s') % (server.session['visitor'], server.session['category']))
        except:
            pass    
        return True

    try:
        server.session['category'] = 'public'
        server.session['visitor']  = _(u'Unknown operator')
        print_report('helpers.py', _(u'Unauthorised operator') + ': ' + _(u'%s') % username)        
    except:
        pass

    return False    


def check_login(redirect=False):
    from ospy import server
    import web
    from ospy.options import options
    qdict = web.input()

    try:
        if options.no_password:
            server.session['category'] = 'admin'
            server.session['visitor']  = _(u'No password')
            return True

        if server.session.validated:
            return True
    except KeyError:
        pass

    if 'pw' and 'nm'in qdict: # password and user name
        if test_password(qdict['pw'], qdict['nm']):
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
    import ast
    from web import ctx

    from ospy.inputs import inputs
    from ospy.log import log
    from ospy.options import level_adjustments, options, rain_blocks
    from ospy.programs import programs, ProgramType
    from ospy.runonce import run_once
    from ospy.stations import stations
    from ospy import version
    from ospy.server import session
    from ospy.webpages import pluginFtr
    from ospy.webpages import pluginStn
    from ospy.webpages import sensorSearch
    from ospy import i18n
    from ospy.users import users
    from ospy.sensors import sensors

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
        'ast': ast
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
    from ospy.options import options

    has_error = False

    try:
        id = int(id)
        docs = get_help_files()
        if 0 <= id < len(docs):
            option = docs[id]
            if len(option) > 2:
                filename = option[2]

                import io

                ### Usually non-ASCII data is received from a file. The io module provides a TextWrapper that decodes your file on the fly, using a given encoding.                    ###
                ### You must use the correct encoding for the file - it can't be easily guessed. For example, for a UTF-8 file:                                                        ###  
                ### my_unicode_string would then be suitable for passing to Markdown. If a UnicodeDecodeError from the read() line, then you've probably used the wrong encoding value.###
                ### https://stackoverflow.com/questions/21129020/how-to-fix-unicodedecodeerror-ascii-codec-cant-decode-byte                                                            ###
  
                with io.open(filename, "r", encoding="utf-8") as fh: 
                    my_unicode_string = fh.read() 

                    import markdown

                    try: 
                        converted = markdown.markdown(my_unicode_string, extensions=['partial_gfm', 'markdown.extensions.codehilite'])
                        return web.template.Template(converted, globals=template_globals())()

                    except:    
                        has_error = True
                        options.ospy_readme_error = has_error
                        return web.template.Template(my_unicode_string, globals=template_globals())()   
   
    except Exception:
        return ''                          


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
        print('{}: {}'.format(title.encode('ascii', 'replace'), message.encode('ascii', 'replace')))  
    return
        

def encrypt_data(aes_key, plain_msg, iv_mode = None): # if iv_mode is None aes mode is ECB else CBC with IV 16 bytes
    try:
        from Crypto.Cipher import AES
        import binascii

        if iv_mode is None:
            encryption_suite = AES.new(aes_key, AES.MODE_ECB)
        else:
            encryption_suite = AES.new(aes_key, AES.MODE_CBC, aes_iv)

        pad = len(plain_msg) % 16
        if pad > 0:
            for i in range(16-pad):
                plain_msg += ' '
        enc_msg = binascii.hexlify(encryption_suite.encrypt(plain_msg))
        return enc_msg
    except:
        print_report('helpers.py', traceback.format_exc())
        return ''
        

def decrypt_data(aes_key, enc_msg, iv_mode = None):    # if iv_mode is None aes mode is ECB else CBC with IV 16 bytes
    try:
        from Crypto.Cipher import AES
        import binascii

        if iv_mode is None:
            decryption_suite = AES.new(aes_key, AES.MODE_ECB)
        else:
            decryption_suite = AES.new(aes_key, AES.MODE_CBC, iv_mode)

        sec_str = str(binascii.unhexlify(enc_msg))
        plain_msg = decryption_suite.decrypt(sec_str)
        return plain_msg    
    except:
        print_report('helpers.py', traceback.format_exc())
        return ''


def decode_B64(msg):
    try:
        import base64

        decode = base64.decodestring(msg)
        return decode    
    except:
        print_report('helpers.py', traceback.format_exc())
        return ''         