# -*- coding: utf-8 -*-

# System imports
from __future__ import absolute_import
import os
from shutil import copyfile
import datetime
import json
import web
from threading import Timer
import traceback

# Local imports
from ospy.helpers import test_password, template_globals, check_login, save_to_options, \
    password_hash, password_salt, get_input, get_help_files, get_help_file, restart, reboot, poweroff, print_report
from ospy.inputs import inputs
from ospy.log import log, logEM
from ospy.options import options
from ospy.options import rain_blocks
from ospy.programs import programs
from ospy.programs import ProgramType
from ospy.runonce import run_once
from ospy.stations import stations
from ospy import scheduler
import plugins
from blinker import signal
from ospy.users import users
from ospy.sensors import sensors

plugin_data = {}  # Empty dictionary to hold plugin based global data
pluginFtr = []    # Empty list of dicts to hold plugin data for display in footer
pluginStn = []    # Empty list of dicts to hold plugin data for display on timeline
sensorSearch = [] # Empty list of dicts to hold sensors data for display on sensor search page

loggedin = signal('loggedin')
def report_login():
    loggedin.send()

value_change = signal('value_change')
def report_value_change():
    value_change.send()

option_change = signal('option_change')
def report_option_change():
    option_change.send()

rebooted = signal('rebooted')
def report_rebooted():
    rebooted.send()

restarted = signal('restarted')
def report_restarted():
    restarted.send()

station_names = signal('station_names')
def report_station_names():
    station_names.send()

program_change = signal('program_change')
def report_program_change():
    program_change.send()

program_deleted = signal('program_deleted')
def report_program_deleted():
    program_deleted.send()

program_toggled = signal('program_toggled')
def report_program_toggle():
    program_toggled.send()

program_runnow = signal('program_runnow')
def report_program_runnow():
    program_runnow.send()


from web import form

signin_form = form.Form(
    form.Textbox('username', description=_('Username:')),
    form.Password('password', description=_('Password:')),
    validators=[
        form.Validator(
            _('Incorrect username or password, please try again...'),
            lambda x: test_password(x["password"], x["username"])
        )  
    ]

)


class InstantCacheRender(web.template.render):
    '''This class immediately starts caching all templates in the given location.'''
    def __init__(self, loc='templates', cache=None, base=None, limit=None, exclude=None, **keywords):
        web.template.render.__init__(self, loc, cache, base, **keywords)

        self._limit = limit
        self._exclude = exclude

        from threading import Thread
        t = Thread(target=self._fill_cache)
        t.daemon = True
        t.start()

    def _fill_cache(self):
        import time
        if os.path.isdir(self._loc):
            for name in os.listdir(self._loc):
                if name.endswith('.html') and \
                        (self._limit is None or name[:-5] in self._limit) and \
                        (self._exclude is None or name[:-5] not in self._exclude):
                    self._template(name[:-5])
                    time.sleep(0.1)


class WebPage(object):
    base_render = InstantCacheRender(os.path.join('ospy', 'templates'),
                                     globals=template_globals(), limit=['base']).base
    core_render = InstantCacheRender(os.path.join('ospy', 'templates'),
                                     globals=template_globals(), exclude=['base'], base=base_render)

    def __init__(self):
        cls = self.__class__

        from ospy.server import session
        if not cls.__name__.endswith('json') and (not session.pages or session.pages[-1] != web.ctx.fullpath):
            session.pages.append(web.ctx.fullpath)
        while len(session.pages) > 5:
            del session.pages[0]

        if self.__module__.startswith('plugins') and 'plugin_render' not in cls.__dict__:
            cls.plugin_render = InstantCacheRender(os.path.join(os.path.join(*self.__module__.split('.')), 'templates'), globals=template_globals(), base=self.base_render)

    @staticmethod
    def _redirect_back():
        from ospy.server import session
        for page in reversed(session.pages):
            if page != web.ctx.fullpath:
                raise web.seeother(page)
        raise web.seeother(u'/')


class ProtectedPage(WebPage):
    def __init__(self):
        WebPage.__init__(self)
        try:
            check_login(True)
        except web.seeother:
            raise
            

class sensors_page(ProtectedPage):
    """Open all sensors page. /sensors"""

    def GET(self):
        from ospy.server import session
        global searchData

        if session['category'] != 'admin':
            raise web.seeother(u'/')

        qdict = web.input()

        delete_all = get_input(qdict, 'delete_all', False, lambda x: True)
        search = get_input(qdict, 'search', False, lambda x: True) 
        clean_all = get_input(qdict, 'clean_all', False, lambda x: True)

        if clean_all:
            for i in range(0, len(sensorSearch)):
                try:
                    del sensorSearch[int(i)]            
                except:
                    pass    
            return self.core_render.sensors_search()
          
        if delete_all:
            while sensors.count() > 0:
                sensors.remove_sensors(sensors.count()-1)
            try:
                import shutil
                shutil.rmtree(os.path.join('.', 'ospy', 'data', 'sensors'))
            except:
                pass    

        if search:
            return self.core_render.sensors_search()                

        return self.core_render.sensors()


class sensor_page(ProtectedPage):
    """Open page to allow sensor modification. /sensor """
    def GET(self, index):
        from ospy.server import session
        import shutil

        qdict = web.input()
        try:
            index = int(index)
            delete = get_input(qdict, 'delete', False, lambda x: True)
            enable = get_input(qdict, 'enable', None, lambda x: x == '1')
            log = get_input(qdict, 'log', False, lambda x: True)       # return web page sensor log
            glog = get_input(qdict, 'glog', False, lambda x: True)     # return log json for graph
            graph = get_input(qdict, 'graph', False, lambda x: True)   # return web page sensor graph
            csvE = get_input(qdict, 'csvE', False, lambda x: True)     # return event csv file
            csvS = get_input(qdict, 'csvS', False, lambda x: True)     # return samples csv file
            clear = get_input(qdict, 'clear', False, lambda x: True)   # clear event and samples

            if session['category'] != 'admin':
                raise web.seeother(u'/') 

            if 'history' in qdict:
                options.sensor_graph_histories = int(qdict['history'])
                raise web.seeother(u'/sensor/{}?graph'.format(index))

            if delete:
                sensors.remove_sensors(index)
                try:
                    shutil.rmtree(os.path.join('.', 'ospy', 'data', 'sensors', str(index)))
                except:
                    pass
                raise web.seeother(u'/sensors')
            
            elif enable is not None:
                sensors[index].enabled = enable
                raise web.seeother(u'/sensors') 

            elif log:
                dir_name_slog = os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs', 'slog.json')
                try:
                    with open(dir_name_slog) as logf:
                        slog_file =  json.load(logf)
                except IOError:
                    slog_file = []

                dir_name_elog = os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs', 'elog.json')
                try:
                    with open(dir_name_elog) as logf:
                        elog_file =  json.load(logf)
                except IOError:
                    elog_file = []    

                try:
                    name = sensors[index].name
                    stype = sensors[index].sens_type
                    mtype = sensors[index].multi_type
                    return self.core_render.log_sensor(index, name, stype, mtype, slog_file, elog_file) 
                except:    
                    print_report('webpages.py', traceback.format_exc())

            elif glog:
                dir_name_glog = os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs', 'graph', 'graph.json')
                try:
                    with open(dir_name_glog) as logf:
                        glog_file =  json.load(logf)
                except IOError:
                    glog_file = []
   
                try:
                    data = []
                    epoch = datetime.date(1970, 1, 1)                                      # first date
                    current_time  = datetime.date.today()                                  # actual date

                    if options.sensor_graph_histories == 0:                                # without filtering
                        web.header('Access-Control-Allow-Origin', '*')
                        web.header('Content-Type', 'application/json')
                        return json.dumps(glog_file)

                    if options.sensor_graph_histories == 1:
                        check_start  = current_time - datetime.timedelta(days=1)           # actual date - 1 day
                    if options.sensor_graph_histories == 2:
                        check_start  = current_time - datetime.timedelta(days=7)           # actual date - 7 day (week)
                    if options.sensor_graph_histories == 3:
                        check_start  = current_time - datetime.timedelta(days=30)          # actual date - 30 day (month)
                    if options.sensor_graph_histories == 4:
                        check_start  = current_time - datetime.timedelta(days=365)         # actual date - 365 day (year)                       

                    log_start = int((check_start - epoch).total_seconds())                 # start date for log in second (timestamp)
                
                    temp_balances = {}
                    for key in glog_file[0]['balances']:
                        find_key =  int(key.encode('utf8'))                                # key is in unicode ex: u'1601347000' -> find_key is int number
                        if find_key >= log_start:                                          # timestamp interval 
                            temp_balances[key] = glog_file[0]['balances'][key]
                    data.append({ 'sname': glog_file[0]['sname'], 'balances': temp_balances })

                    web.header('Access-Control-Allow-Origin', '*')
                    web.header('Content-Type', 'application/json')
                    return json.dumps(data)
                except:    
                    #print_report('webpages.py', traceback.format_exc())
                    pass

            elif graph:
                try:
                    name = sensors[index].name
                    stype = sensors[index].sens_type
                    mtype = sensors[index].multi_type
                    return self.core_render.graph_sensor(index, name, stype, mtype) 
                except:    
                    print_report('webpages.py', traceback.format_exc())                    

            elif csvE:
                dir_name_elog = os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs', 'elog.json')
                try:
                    with open(dir_name_elog) as logf:
                        slog_file =  json.load(logf)
                except IOError:
                    slog_file = []
                data = "Date; Time; Event\n"
                for interval in slog_file:
                    data += '; '.join([
                        interval['date'],
                        interval['time'],
                        u'{}'.format(interval['event']),
                    ]) + '\n'

                web.header('Content-Type', 'text/csv')
                web.header('Content-Disposition', 'attachment; filename="event.csv"')
                return data 

            elif csvS:
                dir_name_slog = os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs', 'slog.json')
                try:
                    with open(dir_name_slog) as logf:
                        slog_file =  json.load(logf)
                except IOError:
                    slog_file = []
                data = "Date; Time; Value; Action\n"
                for interval in slog_file:
                    data += '; '.join([
                        interval['date'],
                        interval['time'],
                        u'{}'.format(interval['value']),
                        u'{}'.format(interval['action']),
                    ]) + '\n'

                web.header('Content-Type', 'text/csv')
                web.header('Content-Disposition', 'attachment; filename="sample.csv"')
                return data   

            elif clear:
                try:
                    shutil.rmtree(os.path.join('.', 'ospy', 'data', 'sensors', str(index), 'logs'))
                except:
                    pass
                raise web.seeother(u'/sensors')                                                                    

        except ValueError:
            pass        

        if isinstance(index, int):
            sensor = sensors.get(index)
        else:
            sensor = sensors.create_sensors()       

        errorCode = qdict.get('errorCode', 'None')
        return self.core_render.sensor(sensor, errorCode)


    def POST(self, index):
        from ospy.server import session

        qdict = web.input(AL=[], AH=[], BL=[], BH=[], CL=[], CH=[], DL=[], DH=[]) # A-D for multiple select LO/HI programs
        multi_type = -1
        sen_type = -1

        try:
            index = int(index)
            sensor = sensors.get(index)

        except ValueError:
            sensor = sensors.create_sensors()         

        if session['category'] == 'admin':
            if 'name' in qdict:
                sensor.name = qdict['name']

            if 'notes' in qdict:    
                sensor.notes = qdict['notes']

            if 'enable' in qdict and qdict['enable'] == 'on':    
                sensor.enabled = 1
            else:    
                sensor.enabled = 0

            if 'senscode' in qdict: 
                if len(qdict['senscode'])>16 or len(qdict['senscode'])<16:
                    errorCode = qdict.get('errorCode', 'ucode')
                    return self.core_render.sensor(sensor, errorCode)
                else:    
                    sensor.encrypt = qdict['senscode']

            if 'sens_type' in qdict:
                sensor.sens_type = int(qdict['sens_type']) 
                sen_type = int(qdict['sens_type'])  

            if 'com_type' in qdict:
                sensor.com_type = int(qdict['com_type'])

            if 'multi_type' in qdict:
                sensor.multi_type = int(qdict['multi_type'])
                multi_type = int(qdict['multi_type'])            

            if 'log_samples' in qdict and qdict['log_samples'] == 'on':
                sensor.log_samples = 1
            else:                                  
                sensor.log_samples = 0

            if 'log_event' in qdict and qdict['log_event'] == 'on':
                sensor.log_event = 1
            else:                                  
                sensor.log_event = 0 

            if 'send_email' in qdict and qdict['send_email'] == 'on':
                sensor.send_email = 1
            else:                                  
                sensor.send_email = 0 

            if 'sample_rate_min' in qdict and 'sample_rate_sec' in qdict:
                try:
                    sensor.sample_rate = int(qdict['sample_rate_min'])*60 + int(qdict['sample_rate_sec'])
                except:
                    sensor.sample_rate = 60    
                    pass

            if 'sensitivity' in qdict:
                sensor.sensitivity = int(qdict['sensitivity'])

            if 'stabilization_time_min' in qdict and 'stabilization_time_sec' in qdict:
                sensor.stabilization_time = int(qdict['stabilization_time_min'])*60 + int(qdict['stabilization_time_sec'])

            if 'trigger_low_threshold' in qdict:
                sensor.trigger_low_threshold = qdict['trigger_low_threshold'] 

            if 'trigger_high_threshold' in qdict:
                sensor.trigger_high_threshold = qdict['trigger_high_threshold']

            if  sen_type == 1:                           # dry contact
                sensor.trigger_low_program = qdict['AL']           
                sensor.trigger_high_program = qdict['AH']

            elif sen_type == 2:                          # leak detector
                sensor.trigger_low_program = qdict['BL']
                sensor.trigger_high_program = qdict['BH']  

            elif sen_type == 4:                          # motion
                sensor.trigger_low_program = ""
                sensor.trigger_high_program = qdict['CH'] 

            elif sen_type == 3 or sen_type == 5:         # moisture / temperature
                sensor.trigger_low_program = qdict['DL']
                sensor.trigger_high_program = qdict['DH'] 

            elif sen_type == 6 and (multi_type == 0 or multi_type == 1 or multi_type == 2 or multi_type == 3): # multi temperature 0-3
                sensor.trigger_low_program = qdict['DL']
                sensor.trigger_high_program = qdict['DH']                    

            elif sen_type == 6 and multi_type == 4:      # multi dry contact
                sensor.trigger_low_program = qdict['AL']           
                sensor.trigger_high_program = qdict['AH'] 

            elif sen_type == 6 and multi_type == 5:      # multi leak detector
                sensor.trigger_low_program = qdict['BL']
                sensor.trigger_high_program = qdict['BH']   

            elif sen_type == 6 and multi_type == 6:      # multi moisture
                sensor.trigger_low_program = qdict['DL']
                sensor.trigger_high_program = qdict['DH']                 

            elif sen_type == 6 and multi_type == 7:      # multi motion
                sensor.trigger_low_program = ""
                sensor.trigger_high_program = qdict['CH']                                                      

            if 'ip_address' in qdict:
                from ospy.helpers import split_ip
                ip = split_ip(qdict['ip_address'])
                sensor.ip_address = ip                                               
                             
            if 'mac_address' in qdict:
                sensor.mac_address = qdict['mac_address'].upper()

            if 'radio_id' in qdict:
                if qdict['radio_id'] != '-':
                    sensor.radio_id = int(qdict['radio_id'])

            if 'name' in qdict and qdict['name'] == '' and sensor.index < 0:
                errorCode = qdict.get('errorCode', 'uname')
                return self.core_render.sensor(sensor, errorCode) 

            try:
                if 'name' in qdict and sensor.index < 0:
                    for sens in sensors.get():
                        if sens.name == qdict['name']:
                            errorCode = qdict.get('errorCode', 'unameis')
                            return self.core_render.sensor(sensor, errorCode) 
            except:
                print_report('webpages.py', traceback.format_exc())                

        if sensor.index < 0 and session['category'] == 'admin':
            sensors.add_sensors(sensor)    

        raise web.seeother(u'/sensors')


class users_page(ProtectedPage):
    """Open all users page. /users"""

    def GET(self):
        from ospy.server import session

        if session['category'] != 'admin':
            raise web.seeother(u'/')

        qdict = web.input()
        delete_all = get_input(qdict, 'delete_all', False, lambda x: True)
        if delete_all:
            while users.count() > 0:
                users.remove_users(users.count()-1)
  
        return self.core_render.users()


class user_page(ProtectedPage):
    """Open page to allow user modification. /user """
    def GET(self, index):
        from ospy.server import session

        qdict = web.input()
        try:
            index = int(index)
            delete = get_input(qdict, 'delete', False, lambda x: True)
            if delete and session['category'] == 'admin':
                users.remove_users(index)
                raise web.seeother(u'/users')

        except ValueError:
            pass        

        if isinstance(index, int):
            user = users.get(index)
        else:
            user = users.create_users()       

        errorCode = qdict.get('errorCode', 'None')
        return self.core_render.user(user, errorCode)


    def POST(self, index):
        from ospy.server import session

        qdict = web.input()
        try:
            index = int(index)
            user = users.get(index)

        except ValueError:
            user = users.create_users()

        user.name = ''
        password = ''

        if session['category'] == 'admin':
            user.name = qdict['name']
            password = qdict['password']
            user.category = qdict['category']    
            user.notes = qdict['notes']   

        if user.name == '' and user.index < 0:
            errorCode = qdict.get('errorCode', 'uname')
            return self.core_render.user(user, errorCode) 

        if len(user.name) < 5:
            errorCode = qdict.get('errorCode', 'unamelen')
            return self.core_render.user(user, errorCode)             
        
        if password == user.name:
            errorCode = qdict.get('errorCode', 'upassuname')
            return self.core_render.user(user, errorCode) 

        if password == '':
            errorCode = qdict.get('errorCode', 'upass')
            return self.core_render.user(user, errorCode)   

        if len(password) < 5:
            errorCode = qdict.get('errorCode', 'unamepass')
            return self.core_render.user(user, errorCode)            

        if user.name == options.admin_user:
            errorCode = qdict.get('errorCode', 'unameis')
            return self.core_render.user(user, errorCode)            
        
        for x in range(users.count()):
            isuser = users.get(x)
            if user.name == isuser.name and user.index < 0:
                errorCode = qdict.get('errorCode', 'unameis')
                return self.core_render.user(user, errorCode)            

        if user.index < 0 and session['category'] == 'admin':
            salt = password_salt()
            user.password_salt = salt
            user.password_hash = password_hash(password, salt) # actual user hash+salt for saving           
            users.add_users(user)    

        raise web.seeother(u'/users')        


class image_edit_page(ProtectedPage):
    """Open page to edit images for station."""
    def GET(self, index):
        from ospy.server import session
        import os
        
        qdict = web.input() 
        errorCode = qdict.get('errorCode', 'None')
        delete = get_input(qdict, 'delete', False, lambda x: True)

        img_path    = './ospy/images/stations/station%s.png' % str(index)
        img_path_th = './ospy/images/stations/station%s_thumbnail.png' % str(index)

        if delete and session['category'] == 'admin':
            try:
                if os.path.isfile(img_path):
                    os.remove(img_path)
                if os.path.isfile(img_path_th):    
                    os.remove(img_path_th)
                log.debug('webpages.py', _(u'Files %s and %s has sucesfully deleted...') % ('station%s.png' % str(index),'station%s_thumbnail.png' % str(index)))
            except:
                pass    

        if not os.path.isfile(img_path) or not os.path.isfile(img_path_th): 
            img_url = '/images?id=no_image'                           # fake default img
            errorCode = qdict.get('errorCode', 'noex')   
        else:
            img_url = '/images?sf=1&id=station%s' % str(index)        # station img            

        return self.core_render.edit(index, img_url, errorCode)


    def POST(self, index):
        from ospy.server import session

        qdict = web.input()

        img_path      = './ospy/images/stations/station%s.png' % str(index)
        img_path_th   = './ospy/images/stations/station%s_thumbnail.png' % str(index)
        img_path_temp = './ospy/images/stations/temp%s.png' % str(index)

        if session['category'] == 'admin':
            if 'enabled' in qdict and qdict['enabled']== u'on':
                options.high_resolution_mode = True
            else:
                options.high_resolution_mode = False 
                   
            i = web.input(uploadfile={})
            #web.debug(i['uploadfile'].filename)    # This is the filename
            #web.debug(i['uploadfile'].value)       # This is the file contents
            #web.debug(i['uploadfile'].file.read()) # Or use a file(-like) object
            upload_type = i.uploadfile.filename[-4:len(i.uploadfile.filename)] # only .png file accepted
            if upload_type != '.png': # check file type
                if not os.path.isfile(img_path) or not os.path.isfile(img_path_th): 
                    img_url = '/images?id=no_image'                            # fake default img
                else:
                    img_url = '/images?sf=1&id=station%s' % str(index)         # station img 
            
                errorCode = qdict.get('errorCode', 'uplname') 
                return self.core_render.edit(index, img_url, errorCode)
            else:                     # file is png continue        
                if not os.path.isfile(img_path_temp):
                    fout = open(img_path_temp,'w') 
                    fout.write(i.uploadfile.file.read()) 
                    fout.close()
                    log.debug('webpages.py', _(u'File %s has sucesfully uploaded...') % i.uploadfile.filename)
                else:
                    os.remove(img_path_temp) 
                    fout = open(img_path_temp,'w')  # temporary file after uploading
                    fout.write(i.uploadfile.file.read()) 
                    fout.close()         
                    log.debug('webpages.py', _(u'File %s has sucesfully uploaded...') % i.uploadfile.filename)           

                try:
                    from PIL import Image
                    if os.path.isfile(img_path_temp):
                        im = Image.open(img_path_temp)
                        size = 50,50                # resize to thumbnail               
                        im.thumbnail(size)
                        im.save(img_path_th, "PNG")
                        im = Image.open(img_path_temp)
                        if options.high_resolution_mode:
                            size = 1024,768         # resize original (high quality)
                        else:
                            size = 640,480          # resize original (low quality)
                        im.thumbnail(size)
                        im.save(img_path, "PNG")
                        os.remove(img_path_temp)
                        log.debug('webpages.py', _(u'Files has sucesfully resized to max 60x60/640x480...'))
 
                except:
                    pass
                    log.error('webpages.py', _(u'Cannot create resized files!'))

        raise web.seeother(u'/stations')   

 
class image_view_page(ProtectedPage):
    """Open page to view images for station."""
    def GET(self, index):
        import os

        img_path    = './ospy/images/stations/station%s.png' % str(index)   
        if not os.path.isfile(img_path): 
            img_url = '/images?id=no_image'                           # fake default img
        else:
            img_url = '/images?sf=1&id=station%s' % str(index)        # station img            

        return self.core_render.view(img_url)            


class login_page(WebPage):
    """Login page"""

    def GET(self):
        if check_login(False):
            raise web.seeother(u'/')
        else:
            return self.core_render.login(signin_form())

    def POST(self):
        my_signin = signin_form()

        if not my_signin.validates():
            return self.core_render.login(my_signin)
        else:
            from ospy import server
            server.session.validated = True
            report_login()
            self._redirect_back()


class logout_page(WebPage):
    def GET(self):
        from ospy.server import session
        session.kill()
        raise web.seeother(u'/')


class home_page(ProtectedPage):
    """Open Home page."""

    def GET(self):
        from ospy.server import session

        if session['category'] == 'public':
            return self.core_render.home_public()
        elif session['category'] == 'user': 
            return self.core_render.home_user()
        elif session['category'] == 'admin':  
            return self.core_render.home_admin()  


class action_page(ProtectedPage):
    """Page to perform some simple actions (mainly from the homepage)."""

    def GET(self):
        from ospy.server import session

        qdict = web.input()

        stop_all = get_input(qdict, 'stop_all', False, lambda x: True)
        scheduler_enabled = get_input(qdict, 'scheduler_enabled', None, lambda x: x == '1')
        manual_mode = get_input(qdict, 'manual_mode', None, lambda x: x == '1')
        rain_block = get_input(qdict, 'rain_block', None, float)
        level_adjustment = get_input(qdict, 'level_adjustment', None, float)
        toggle_temp = get_input(qdict, 'toggle_temp', False, lambda x: True)

        if stop_all:
            if session['category'] == 'admin' or session['category'] == 'user':
                if not options.manual_mode:
                    options.scheduler_enabled = False
                    programs.run_now_program = None
                    run_once.clear()
                log.finish_run(None)
                stations.clear()

        if scheduler_enabled is not None:
            if session['category'] == 'admin' or session['category'] == 'user':
                options.scheduler_enabled = scheduler_enabled

        if manual_mode is not None:
            if session['category'] == 'admin' or session['category'] == 'user':
                options.manual_mode = manual_mode

        if rain_block is not None:
            if session['category'] == 'admin' or session['category'] == 'user':
                options.rain_block = datetime.datetime.now() + datetime.timedelta(hours=rain_block)

        if level_adjustment is not None:
            if session['category'] == 'admin' or session['category'] == 'user':
                options.level_adjustment = level_adjustment / 100

        if toggle_temp:
            if session['category'] == 'admin' or session['category'] == 'user':
                options.temp_unit = "F" if options.temp_unit == "C" else "C"

        set_to = get_input(qdict, 'set_to', None, int)
        sid = get_input(qdict, 'sid', 0, int) - 1
        set_time = get_input(qdict, 'set_time', 0, int)

        if set_to is not None and 0 <= sid < stations.count() and options.manual_mode:
          if session['category'] == 'admin' or session['category'] == 'user':
            if set_to:  # if status is on
                start = datetime.datetime.now()
                new_schedule = {
                    'active': True,
                    'program': -1,
                    'station': sid,
                    'program_name': _('Manual'),
                    'fixed': True,
                    'cut_off': 0,
                    'manual': True,
                    'blocked': False,
                    'start': start,
                    'original_start': start,
                    'end': start + datetime.timedelta(days=3650),
                    'uid': '%s-%s-%d' % (str(start), "Manual", sid),
                    'usage': stations.get(sid).usage
                }
                if set_time > 0:  # if an optional duration time is given
                    new_schedule['end'] = datetime.datetime.now() + datetime.timedelta(seconds=set_time)

                log.start_run(new_schedule)
                stations.activate(new_schedule['station'])

            else:  # If status is off
                stations.deactivate(sid)
                active = log.active_runs()
                for interval in active:
                    if interval['station'] == sid:
                        log.finish_run(interval)

        report_value_change()
        raise web.seeother(u'/')  # Send browser back to home page


class programs_page(ProtectedPage):
    """Open programs page."""

    def GET(self):
        from ospy.server import session

        qdict = web.input()
        delete_all = get_input(qdict, 'delete_all', False, lambda x: True)
        if delete_all and session['category'] == 'admin':
            while programs.count() > 0:
                programs.remove_program(programs.count()-1)
            report_program_deleted()

        if session['category'] == 'admin':
            return self.core_render.programs()
        if session['category'] == 'user': 
            return self.core_render.programs_user()
        
        raise web.seeother(u'/')
   

class program_page(ProtectedPage):
    """Open page to allow program modification."""

    def GET(self, index):
    	from ospy.server import session

        qdict = web.input()
        try:
            index = int(index)
            delete = get_input(qdict, 'delete', False, lambda x: True)
            runnow = get_input(qdict, 'runnow', False, lambda x: True)
            enable = get_input(qdict, 'enable', None, lambda x: x == '1')
            if delete and session['category'] == 'admin':
                programs.remove_program(index)
                Timer(0.1, programs.calculate_balances).start()
                report_program_deleted()
                raise web.seeother(u'/programs')
            elif runnow:
                programs.run_now(index)
                Timer(0.1, programs.calculate_balances).start()
                report_program_runnow()
                raise web.seeother(u'/')
            elif enable is not None:
                programs[index].enabled = enable
                Timer(0.1, programs.calculate_balances).start()
                report_program_toggle()
                raise web.seeother(u'/programs')
        except ValueError:
            pass

        if isinstance(index, int):
            program = programs.get(index)
        else:
            program = programs.create_program()
            program.set_days_simple(6*60, 30, 30, 0, [])

        report_program_change()
        return self.core_render.program(program)

    def POST(self, index):
        from ospy.server import session

        if session['category'] != 'admin':
            raise web.seeother(u'/')

        qdict = web.input()
        try:
            index = int(index)
            program = programs.get(index)
        except ValueError:
            program = programs.create_program()

        qdict['schedule_type'] = int(qdict['schedule_type'])

        program.name = qdict['name']
        program.stations = json.loads(qdict['stations'])
        program.enabled = True if qdict.get('enabled', 'off') == 'on' else False

        if qdict['schedule_type'] == ProgramType.WEEKLY_WEATHER:
            program.cut_off = 0
            program.fixed = True
        else:
            program.cut_off = int(qdict['cut_off'])
            program.fixed = True if qdict.get('fixed', 'off') == 'on' else False

        simple = [int(qdict['simple_hour']) * 60 + int(qdict['simple_minute']),
                  int(qdict['simple_duration']),
                  int(qdict['simple_pause']),
                  int(qdict['simple_rcount']) if qdict.get('simple_repeat', 'off') == 'on' else 0]

        repeat_start_date = datetime.datetime.combine(datetime.date.today(), datetime.time.min) + \
                            datetime.timedelta(days=int(qdict['interval_delay']))

        if qdict['schedule_type'] == ProgramType.DAYS_SIMPLE:
            program.set_days_simple(*(simple + [
                                    json.loads(qdict['days'])]))

        elif qdict['schedule_type'] == ProgramType.DAYS_ADVANCED:
            program.set_days_advanced(json.loads(qdict['advanced_schedule_data']),
                                      json.loads(qdict['days']))

        elif qdict['schedule_type'] == ProgramType.REPEAT_SIMPLE:
            program.set_repeat_simple(*(simple + [
                                      int(qdict['interval']),
                                      repeat_start_date]))

        elif qdict['schedule_type'] == ProgramType.REPEAT_ADVANCED:
            program.set_repeat_advanced(json.loads(qdict['advanced_schedule_data']),
                                        int(qdict['interval']),
                                        repeat_start_date)

        elif qdict['schedule_type'] == ProgramType.WEEKLY_ADVANCED:
            program.set_weekly_advanced(json.loads(qdict['weekly_schedule_data']))

        elif qdict['schedule_type'] == ProgramType.WEEKLY_WEATHER:
            program.set_weekly_weather(int(qdict['weather_irrigation_min']),
                                       int(qdict['weather_irrigation_max']),
                                       int(qdict['weather_run_max']),
                                       int(qdict['weather_pause_ratio'])/100.0,
                                       json.loads(qdict['weather_pems_data']),
                                       )

        elif qdict['schedule_type'] == ProgramType.CUSTOM:
            program.modulo = int(qdict['interval'])*1440
            program.manual = False
            program.start = repeat_start_date
            program.schedule = json.loads(qdict['custom_schedule_data'])

        if program.index < 0:
            programs.add_program(program)

        Timer(0.1, programs.calculate_balances).start()
        report_program_toggle()
        raise web.seeother(u'/programs')


class runonce_page(ProtectedPage):
    """Open a page to view and edit a run once program."""

    def GET(self):
        return self.core_render.runonce()

    def POST(self):
        from ospy.server import session

        qdict = web.input()
        station_seconds = {}
        for station in stations.enabled_stations():
            mm_str = "mm" + str(station.index)
            ss_str = "ss" + str(station.index)
            if mm_str in qdict and ss_str in qdict:
                seconds = int(qdict[mm_str] or 0) * 60 + int(qdict[ss_str] or 0)
                station_seconds[station.index] = seconds

        if session['category'] == 'admin' or session['category'] != 'user':
            run_once.set(station_seconds)
            report_program_toggle()
        raise web.seeother(u'/')


class plugins_manage_page(ProtectedPage):
    """Manage plugins page."""

    def GET(self):
        from ospy.server import session

        qdict = web.input()
        plugin = get_input(qdict, 'plugin', None)
        delete = get_input(qdict, 'delete', False, lambda x: True)
        enable = get_input(qdict, 'enable', None, lambda x: x == '1')
        disable_all = get_input(qdict, 'disable_all', False, lambda x: True)
        enable_all = get_input(qdict, 'enable_all', False, lambda x: True)
        delete_all = get_input(qdict, 'delete_all', False, lambda x: True)
        auto_update = get_input(qdict, 'auto', None, lambda x: x == '1')
        use_update = get_input(qdict, 'use', None, lambda x: x == '1')

        if disable_all and session['category'] == 'admin':
            options.enabled_plugins = []
            plugins.start_enabled_plugins()

        if enable_all and session['category'] == 'admin':
            for plugin in plugins.available():
               if plugin not in options.enabled_plugins:
                  options.enabled_plugins.append(plugin)
            plugins.start_enabled_plugins()

        if delete_all and session['category'] == 'admin':
            from ospy.helpers import del_rw
            import shutil
            for plugin in plugins.available():
            	if plugin in options.enabled_plugins:
            		options.enabled_plugins.remove(plugin)
                shutil.rmtree(os.path.join('plugins', plugin), onerror=del_rw)  
            options.enabled_plugins = options.enabled_plugins  # Explicit write to save to file
            plugins.start_enabled_plugins()              
            raise web.seeother(u'/plugins_manage')        

        if plugin is not None and plugin in plugins.available():
            if delete:
                enable = False

            if enable is not None and session['category'] == 'admin':
                if not enable and plugin in options.enabled_plugins:
                    options.enabled_plugins.remove(plugin)
                elif enable and plugin not in options.enabled_plugins:
                    options.enabled_plugins.append(plugin)
                options.enabled_plugins = options.enabled_plugins  # Explicit write to save to file
                plugins.start_enabled_plugins()

            if delete and session['category'] == 'admin':
                from ospy.helpers import del_rw
                import shutil
                shutil.rmtree(os.path.join('plugins', plugin), onerror=del_rw)

            raise web.seeother(u'/plugins_manage')

        if auto_update is not None and session['category'] == 'admin':
            options.auto_plugin_update = auto_update
            raise web.seeother(u'/plugins_manage')
        
        if use_update is not None and session['category'] == 'admin':
            options.use_plugin_update = use_update
            raise web.seeother(u'/plugins_manage')    

        return self.core_render.plugins_manage()


class plugins_install_page(ProtectedPage):
    """Manage plugins page."""

    def GET(self):
        from ospy.server import session

        qdict = web.input()
        repo = get_input(qdict, 'repo', None, int)
        plugin = get_input(qdict, 'plugin', None)
        install = get_input(qdict, 'install', False, lambda x: True)

        if install and repo is not None and session['category'] == 'admin':
            plugins.checker.install_repo_plugin(plugins.REPOS[repo], plugin)
            self._redirect_back()

        plugins.checker.update()

        if options.plugin_readme_error: # true if is ImportError: Failed loading extension partial_gfm               
            errorCode = qdict.get('errorCode', 'gfm')
        else:    
            errorCode = qdict.get('errorCode', 'none')    
        return self.core_render.plugins_install(errorCode)


    def POST(self):
        from ospy.server import session

        qdict = web.input(zipfile={})

        if session['category'] == 'admin':
            zip_file_data = qdict['zipfile'].file
            plugins.checker.install_custom_plugin(zip_file_data)

        self._redirect_back()


class log_page(ProtectedPage):
    """View Log"""

    def GET(self):
        from ospy.server import session

        qdict = web.input()
        if 'clear' in qdict and session['category'] == 'admin':
            log.clear_runs()
            raise web.seeother(u'/log')

        if 'clearEM' in qdict and session['category'] == 'admin':
            logEM.clear_email()
            raise web.seeother(u'/log')

        if 'csv' in qdict:
            events = log.finished_runs() + log.active_runs()
            data = "Date; Start Time; Zone; Duration; Program\n"
            for interval in events:
                # return only records that are visible on this day:
                duration = (interval['end'] - interval['start']).total_seconds()
                minutes, seconds = divmod(duration, 60)

                data += '; '.join([
                    interval['start'].strftime("%Y-%m-%d"),
                    interval['start'].strftime("%H:%M:%S"),
                    str(interval['station']),
                    "%02d:%02d" % (minutes, seconds),
                    interval['program_name']
                ]) + '\n'

            web.header('Content-Type', 'text/csv')
            web.header('Content-Disposition', 'attachment; filename="log.csv"')
            return data

        if 'csvEM' in qdict:
            events = logEM.finished_email()
            data = "Date; Time; Subject; Body; Status\n"
            for interval in events:
                data += '; '.join([
                    interval['date'],
                    interval['time'],
                    str(interval['subject']),
                    str(interval['body']),
                    str(interval['status']),
                ]) + '\n'

            web.header('Content-Type', 'text/csv')
            web.header('Content-Disposition', 'attachment; filename="email.csv"')
            return data
   
        watering_records = log.finished_runs()
        email_records = logEM.finished_email()

        if session['category'] == 'admin': 
            return self.core_render.log(watering_records, email_records)
        if session['category'] == 'user': 
            return self.core_render.log_user(watering_records, email_records)

class options_page(ProtectedPage):
    """Open the options page for viewing and editing."""

    def GET(self):
        from ospy.server import session

        if session['category'] != 'admin':
            raise web.seeother(u'/')

        qdict = web.input()
        errorCode = qdict.get('errorCode', 'none')      

        return self.core_render.options(errorCode)

    def POST(self):
        from ospy.server import session

        if session['category'] != 'admin':
            raise web.seeother(u'/')        

    	changing_language = False

        qdict = web.input()       

        if 'lang' in qdict:                         
            if qdict['lang'] != options.lang:     # if changed languages
                changing_language = True          

        if 'aes_gener' in qdict and qdict['aes_gener'] == '1':
            from ospy.helpers import now, password_hash
            options.aes_key = password_hash(str(now()), 'notarandomstring')[:16]
            raise web.seeother(u'/options?errorCode=pw_aesGenerOK') 

        if 'aes_key' in qdict and len(qdict['aes_key'])>16:
            raise web.seeother(u'/options?errorCode=pw_aeslenERR')
        elif 'aes_key' in qdict and len(qdict['aes_key'])<16:
            raise web.seeother(u'/options?errorCode=pw_aeslenERR')
        else: 
            save_to_options(qdict)

        if 'master' in qdict:
            m = int(qdict['master'])
            if m < 0:
                stations.master = None
            elif m < stations.count():
                stations.master = m

        if 'master_two' in qdict:
            m = int(qdict['master_two'])
            if m < 0:
                stations.master_two = None
            elif m < stations.count():
                stations.master_two = m

        if 'old_password' in qdict and qdict['old_password'] != "":
            try:
                if test_password(qdict['old_password']):
                    if qdict['new_password'] == "":
                        raise web.seeother(u'/options?errorCode=pw_blank')
                    elif qdict['new_password'] == qdict['check_password']:
                        options.password_salt = password_salt()  # Make a new salt
                        options.password_hash = password_hash(qdict['new_password'], options.password_salt)
                    else:
                        raise web.seeother(u'/options?errorCode=pw_mismatch')
                else:
                    raise web.seeother(u'/options?errorCode=pw_wrong')
            except KeyError:
                pass
   
        if 'rbt' in qdict and qdict['rbt'] == '1':
            report_rebooted()
            reboot(True) # Linux HW software 
            msg = _(u'The system (Linux) will now restart (restart started by the user in the OSPy settings), please wait for the page to reload.')
            return self.core_render.notice(home_page, msg) 

        if 'rstrt' in qdict and qdict['rstrt'] == '1':
            report_restarted()
            restart()    # OSPy software
            msg = _(u'The OSPy will now restart (restart started by the user in the OSPy settings), please wait for the page to reload.')
            return self.core_render.notice(home_page, msg)            
        
        if 'pwrdwn' in qdict and qdict['pwrdwn'] == '1':
            poweroff(True)   # shutdown HW system
            msg = _(u'The system (Linux) is now shutting down ... The system must be switched on again by the user (switching off and on your HW device).')
            return self.core_render.notice(home_page, msg) 

        if 'deldef' in qdict and qdict['deldef'] == '1':
            try:
                ospy_root   = './ospy/'
                ospy_images = ospy_root + 'images/stations/'

                report_restarted()

                from ospy import server
                from ospy.helpers import determine_platform
                import os
                import sys
                import subprocess

                server.stop()
                stations.clear()

                for s in range(200):
                    try:
                        if os.path.isfile(ospy_images + ('station{}.png').format(s)): 
                            log.debug('webpages.py', _(u'Deleting image file {}').format(ospy_images + ('station{}.png').format(s)))
                            os.remove(ospy_images + ('station{}.png').format(s))
                        if os.path.isfile(ospy_images + ('station{}_thumbnail.png').format(s)):
                            log.debug('webpages.py', _(u'Deleting image file {}').format(ospy_images + ('station{}_thumbnail.png').format(s)))
                            os.remove(ospy_images + ('station{}_thumbnail.png').format(s)) 
                    except:
                        pass

                if os.path.isfile('./ssl/fullchain.pem'):
                    log.debug('webpages.py', _(u'Deleting file fullchain.pem.'))
                    os.remove('./ssl/fullchain.pem')

                if os.path.isfile('./ssl/privkey.pem'):
                    log.debug('webpages.py', _(u'Deleting file privkey.pem.'))
                    os.remove('./ssl/privkey.pem')

                if os.path.isfile(ospy_root + 'data/sessions.db'):
                    log.debug('webpages.py', _(u'Deleting file sessions.db.'))
                    os.remove(ospy_root + 'data/sessions.db') 

                if os.path.isfile(ospy_root + 'backup/ospy_backup.zip'):
                    log.debug('webpages.py', _(u'Deleting file ospy_backup.zip.'))
                    os.remove(ospy_root + 'backup/ospy_backup.zip')
                
                if os.path.isfile(ospy_root + 'data/options.db.bak'):
                    log.debug('webpages.py', _(u'Deleting file options.db.bak.'))
                    os.remove(ospy_root + 'data/options.db.bak')

                if os.path.isfile(ospy_root + 'data/options.db.tmp'):
                    log.debug('webpages.py', _(u'Deleting file options.db.tmp.'))
                    os.remove(ospy_root + 'data/options.db.tmp')

                if os.path.isfile(ospy_root + 'data/options.db'):
                    log.debug('webpages.py', _(u'Deleting file options.db.'))
                    os.remove(ospy_root + 'data/options.db')

                try:
                    import shutil
                    shutil.rmtree(os.path.join(ospy_root, 'data', 'sensors'))
                except:
                    pass

                if os.path.isfile(ospy_root + 'data/events.log'):
                    log.debug('webpages.py', _(u'Deleting file events.log.'))
                    os.remove(ospy_root + 'data/events.log')
               
                if determine_platform() == 'nt':
                    # Use this weird construction to start a separate process that is not killed when we stop the current one
                    subprocess.Popen(['cmd.exe', '/c', 'start', sys.executable] + sys.argv)
                else:
                    os.execl(sys.executable, sys.executable, *sys.argv)

            except:
                print_report('webpages.py', traceback.format_exc())
                raise web.seeother(u'/')
                  

        if changing_language:      
            report_restarted()
            restart()    # OSPy software
            msg = _(u'A language change has been made in the settings, the OSPy will now restart and load the selected language.')
            return self.core_render.notice(home_page, msg)

        report_option_change()
        raise web.seeother(u'/')


class stations_page(ProtectedPage):
    """Stations page"""

    def GET(self):
        return self.core_render.stations()

    def POST(self):
        from ospy.server import session

        if session['category'] != 'admin':
            raise web.seeother(u'/')

        qdict = web.input()

        recalc = False
        for s in xrange(0, stations.count()):
            stations[s].name = qdict["%d_name" % s]
            stations[s].usage = float(qdict.get("%d_usage" % s, 1.0))
            stations[s].precipitation = float(qdict.get("%d_precipitation" % s, 10.0))
            stations[s].capacity = float(qdict.get("%d_capacity" % s, 10.0))
            stations[s].eto_factor = float(qdict.get("%d_eto_factor" % s, 1.0))
            stations[s].enabled = True if qdict.get("%d_enabled" % s, 'off') == 'on' else False
            stations[s].ignore_rain = True if qdict.get("%d_ignore_rain" % s, 'off') == 'on' else False
            if stations.master is not None or options.master_relay:
                stations[s].activate_master = True if qdict.get("%d_activate_master" % s, 'off') == 'on' else False
            if stations.master_two is not None or options.master_relay:
                stations[s].activate_master_two = True if qdict.get("%d_activate_master_two" % s, 'off') == 'on' else False
            balance_adjust = float(qdict.get("%d_balance_adjust" % s, 0.0))
            if balance_adjust != 0.0:
                calc_day = datetime.datetime.now().date() - datetime.timedelta(days=1)
                stations[s].balance[calc_day]['intervals'].append({
                                'program': -1,
                                'program_name': 'Balance adjustment',
                                'done': True,
                                'irrigation': balance_adjust
                            })
                stations[s].balance[calc_day]['total'] += balance_adjust
                recalc = True
            stations[s].notes = qdict["%d_notes" % s]

        if recalc:
            Timer(0.1, programs.calculate_balances).start()

        report_station_names()
        raise web.seeother(u'/')

class help_page(ProtectedPage):
    """Help page"""

    def GET(self): 
        from ospy.server import session       

        qdict = web.input()
        id = get_input(qdict, 'id')
        if id is not None:
            web.header('Content-Type', 'text/html')
            return get_help_file(id)

        docs = get_help_files()

        if options.ospy_readme_error: # true if is ImportError: Failed loading extension partial_gfm               
            errorCode = qdict.get('errorCode', 'gfm')
        else:    
            errorCode = qdict.get('errorCode', 'none')         

        if session['category'] == 'admin':
            return self.core_render.help(docs, errorCode)
        if session['category'] == 'user':
            return self.core_render.help_user(docs, errorCode)            
        
class db_unreachable_page(ProtectedPage):
    """Failed to reach download."""

    def GET(self):
        msg = _(u'System component is unreachable or busy. Please wait (try again later).')
        return self.core_render.notice('/download', msg)    	      

class download_page(ProtectedPage):
    """Download OSPy backup file with settings"""
    def GET(self):
        from ospy.server import session
        from ospy.helpers import mkdir_p, del_rw, ASCI_convert
        import os
        import zipfile  
        import time      

        if session['category'] != 'admin':
            raise web.seeother(u'/')

        def retrieve_file_paths(dirName):
            """Declare the function to return all file paths of the particular directory"""
            filePaths = []

            for root, directories, files in os.walk(dirName):                                 # Read all directory, subdirectories and file lists
                for filename in files:                                                        # Create the full filepath by using os module
                    skip = ['.gitignore', 'sessions.db', '*.tmp'] 
                    if filename not in skip: 
                        filePath = os.path.join(root, filename)
                        filePaths.append(filePath)
            
            return filePaths                                                                  # Return all paths

        def _read_log(path):
            """Read file"""
            try:                
                logf = open(path,'r')
                return logf.read()
            except IOError:
                return []

        try:
            ospy_root = './ospy/'
            backup_path = ospy_root + 'backup/ospy_backup.zip'                                # Where is backup zip file
            dir_name = [ospy_root + 'data', ospy_root + 'data/sensors', ospy_root + 'images/stations']    
            download_name = 'ospy_backup_{}_{}.zip'.format(ASCI_convert(options.name), time.strftime("%d.%m.%Y_%H-%M-%S"))   # Example: ospy_backup_systemname_4.12.2020_18-40-20.zip                         
            filePaths = []

            for name in dir_name:                                                             # Call the function to retrieve all files and folders of the assigned directory
                filePaths += retrieve_file_paths(name) 
   
            if not os.path.exists(ospy_root + 'backup'):                                      # Create folder backup
                mkdir_p(ospy_root + 'backup')

            zip_file = zipfile.ZipFile(backup_path, 'w')
            with zip_file:
                for file in filePaths:                                                        # Writing each file one by one
                    zip_file.write(file)

            if os.path.exists(backup_path):        
                log.debug('webpages.py', _(u'File {} is created successfully!').format(download_name))
                import mimetypes
                content = mimetypes.guess_type(backup_path)[0]
                web.header('Content-type', content)
                web.header('Content-Length', os.path.getsize(backup_path))    
                web.header('Content-Disposition', 'attachment; filename=%s'%download_name)
                return _read_log(backup_path)                
            else:
                log.error('webpages.py', _(u'System component is unreachable or busy. Please wait (try again later).'))                         
                msg = _(u'System component is unreachable or busy. Please wait (try again later).')
                return self.core_render.notice('/download', msg)
             
        except Exception:
            print_report('webpages.py', traceback.format_exc())
            raise web.seeother(u'/')


class upload_page(ProtectedPage):
    """Upload ospy_backup.zip file with settings and images for stations"""
    
    def GET(self):
        raise web.seeother(u'/')

    def POST(self):
        from ospy.server import session
        import os
        from zipfile import ZipFile
        from ospy.helpers import del_rw
        from distutils.dir_util import copy_tree
        import shutil

        if session['category'] != 'admin':
            raise web.seeother(u'/')

        ospy_root = './ospy/'
        backup_path = ospy_root + 'backup/ospy_backup.zip' 

        i = web.input(uploadfile={})

        try:
            # import cgi
            # 0 ==> unlimited input upload
            # cgi.maxlen = 10 * 1024 * 1024 # 10MB
            # print cgi.maxlen 
            log.debug('webpages.py', _(u'Uploading file {}.').format(i.uploadfile.filename))
            upload_type = i.uploadfile.filename[-4:len(i.uploadfile.filename)] # Only .zip file accepted
            if upload_type == '.zip':                                          # Check file type
                fout = open(backup_path,'w')                                   # Write uploaded file to backup folder
                fout.write(i.uploadfile.file.read()) 
                fout.close() 
                
                log.debug('webpages.py', _(u'Uploaded to backup folder OK.'))

                with ZipFile(backup_path, mode='r') as zf:                     # Extract zip file
                    zf.extractall(ospy_root + 'backup/ospy_backup')
                    log.debug('webpages.py', _(u'Extracted from zip OK.'))

                fromDirectory = ospy_root + 'backup/ospy_backup'
                toDirectory = './'
                copy_tree(fromDirectory, toDirectory)                          # Copy from to
                
                log.debug('webpages.py', _(u'Cleaning folder after restoring...'))
                shutil.rmtree(fromDirectory, 'ospy_backup', onerror=del_rw)

                log.debug('webpages.py', _(u'Restoring backup files sucesfully, now restarting OSPy...'))
                
                report_restarted()
                restart(3)
                msg = _(u'Restoring backup files sucesfully, now restarting OSPy...')
                return self.core_render.notice(home_page, msg)                 
            else:        
                errorCode = "pw_filename" 
                return self.core_render.options(errorCode)

        except Exception:
            print_report('webpages.py', traceback.format_exc())
            return self.core_render.options()


class upload_page_SSL(ProtectedPage):
    """Upload certificate file to SSL dir, fullchain.pem or privkey.pem"""
    
    def GET(self):
        raise web.seeother(u'/')

    def POST(self):
        from ospy.server import session

        if session['category'] != 'admin':
            raise web.seeother(u'/')

        SSL_FOLDER = './ssl'
        OPTIONS_FILE_FULL = SSL_FOLDER + '/fullchain.pem' # cert file
        OPTIONS_FILE_PRIV = SSL_FOLDER + '/privkey.pem'   # key file

        qdict = web.input()
        if 'generate' in qdict and qdict['generate'] == '1':   # generating own SSL certificate to ssl folder
            try:
                print_report('webpages.py', _(u'Try-ing generating SSL certificate...'))
                log.debug('webpages.py', _(u'Try-ing generating SSL certificate...'))

                from OpenSSL import crypto, SSL  
                # openssl version
                # sudo apt-get install openssl
                from time import gmtime, mktime
                import random
  
                # create a key pair
                k = crypto.PKey()
                k.generate_key(crypto.TYPE_RSA, 2048)
 
                # create a self-signed cert
                cert = crypto.X509()
                cert.get_subject().C = "EU"                # your country
                cert.get_subject().ST = "Czechia"          # your state
                cert.get_subject().L = "Prague"            # location 
                cert.get_subject().O = "OSPy sprinkler"    # organization
                cert.get_subject().OU = "pihrt.com"        # this field is the name of the department or organization unit making the request
                cert.get_subject().CN = options.domain_ssl # common name
                cert.get_subject().emailAddress = "admin@pihrt.com" # e-mail
                cert.set_serial_number(random.randint(1000, 1000000))
                cert.gmtime_adj_notBefore(0)
                cert.gmtime_adj_notAfter(10*365*24*60*60)
                cert.set_issuer(cert.get_subject())
                cert.set_pubkey(k)
                cert.sign(k, 'sha256')

                open(OPTIONS_FILE_FULL, "wt").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
                open(OPTIONS_FILE_PRIV, "wt").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

                print_report('webpages.py', _('OK'))
                log.debug('webpages.py', _('OK'))

                errorCode = "pw_generateSSLOK"
                return self.core_render.options(errorCode)

            except Exception:
                pass     
                print_report('webpages.py', traceback.format_exc())
                log.debug('webpages.py', traceback.format_exc())
                errorCode = "pw_generateSSLERR"
                return self.core_render.options(errorCode)

        i = web.input(uploadfile={})
        try:
            if i.uploadfile.filename == 'fullchain.pem' or i.uploadfile.filename == 'privkey.pem':
               
                if os.path.isfile(OPTIONS_FILE_FULL) and i.uploadfile.filename == 'fullchain.pem':  # is old files in folder ssl?
                    if os.path.isfile(OPTIONS_FILE_FULL):        # exists file fullchain.pem?
                        os.remove(OPTIONS_FILE_FULL)             # remove file
                        log.debug('webpages.py', _(u'Remove fullchain.pem...'))
                if os.path.isfile(OPTIONS_FILE_PRIV) and i.uploadfile.filename == 'privkey.pem':    # is old files in folder ssl?        
                    if os.path.isfile(OPTIONS_FILE_PRIV):        # exists file privkey.pem?
                        os.remove(OPTIONS_FILE_PRIV)             # remove file  
                        log.debug('webpages.py', _(u'Remove privkey.pem...'))                      

                fout = open('./ssl/' + i.uploadfile.filename,'w') 
                fout.write(i.uploadfile.file.read()) 
                fout.close() 

                log.debug('webpages.py', _('Upload SSL file %s') %i.uploadfile.filename) 
                #report_restarted()
                #restart(3)
                #return self.core_render.restarting(home_page)
                errorCode = "pw_filenameSSLOK"
                return self.core_render.options(errorCode)
            else:        
                errorCode = "pw_filenameSSL" 
                return self.core_render.options(errorCode)

        except Exception:
            return self.core_render.options()            

class images_page(ProtectedPage):
    """Return pictures with information about board connection - for help page."""

    def GET(self):

        import mimetypes

        try:
            qdict = web.input()

            id = get_input(qdict, 'id')                                   # id = name for image (ex: station1.png)
            s_folder = get_input(qdict, 'sf', None, lambda x: x == '1')   # sf = 1 read from folder: images/stations else from images/
        
            if id is not None:
                if s_folder is not None:
                    download_name = 'ospy/images/stations/' + id
                else:
                    download_name = 'ospy/images/' + id

                if os.path.isfile(download_name):     # exists image? 
                    content = mimetypes.guess_type(download_name)[0]
                    web.header('Content-type', content)
                    web.header('Content-Length', os.path.getsize(download_name))    
                    web.header('Content-Disposition', 'attachment; filename=%s' % str(id))
                    img = open(download_name,'r')
                    return img.read()
                else:
                    return None
        except:
            pass  
            return None  
        
################################################################################
# APIs                                                                         #
################################################################################
class api_status_json(ProtectedPage):
    """Simple Status API"""

    def GET(self):
        statuslist = []
        for station in stations.get():
            if station.enabled or station.is_master or station.is_master_two: 
                status = {
                    'station': station.index,
                    'status': 'on' if station.active else 'off',
                    'reason': 'master' if station.is_master or station.is_master_two else '',
                    'master': 1 if station.is_master else 0,
                    'master_two': 1 if station.is_master_two else 0,
                    'programName': '',
                    'remaining': 0}

                if not station.is_master or not station.is_master_two:
                    if options.manual_mode:
                        status['programName'] = 'Manual Mode'
                    else:
                        if station.active:
                            active = log.active_runs()
                            for interval in active:
                                if not interval['blocked'] and interval['station'] == station.index:
                                    status['programName'] = interval['program_name']

                                    status['reason'] = 'program'
                                    status['remaining'] = max(0, (interval['end'] -
                                                                  datetime.datetime.now()).total_seconds())
                        elif not options.scheduler_enabled:
                            status['reason'] = 'system_off'
                        elif not station.ignore_rain and inputs.rain_sensed():
                            status['reason'] = 'rain_sensed'
                        elif not station.ignore_rain and rain_blocks.seconds_left():
                            status['reason'] = 'rain_delay'

                statuslist.append(status)

        web.header('Content-Type', 'application/json')
        return json.dumps(statuslist)


class api_log_json(ProtectedPage):
    """Simple Log API"""

    def GET(self):
        qdict = web.input()
        data = []
        if 'date' in qdict:
            # date parameter filters the log values returned; "yyyy-mm-dd" format
            date = datetime.datetime.strptime(qdict['date'], "%Y-%m-%d").date()
            check_start = datetime.datetime.combine(date, datetime.time.min)
            check_end = datetime.datetime.combine(date, datetime.time.max)
            log_start = check_start - datetime.timedelta(days=1)
            log_end = check_end + datetime.timedelta(days=1)

            events = scheduler.combined_schedule(log_start, log_end)
            for interval in events:
                # Return only records that are visible on this day:
                if check_start <= interval['start'] <= check_end or check_start <= interval['end'] <= check_end:
                    data.append(self._convert(interval))

        web.header('Content-Type', 'application/json')
        return json.dumps(data)

    def _convert(self, interval):
            duration = (interval['end'] - interval['start']).total_seconds()
            minutes, seconds = divmod(duration, 60)
            return {
                'program': interval['program'],
                'program_name': interval['program_name'],
                'active': interval['active'],
                'manual': interval.get('manual', False),
                'fixed': True,
                'cut_off': interval['cut_off'],
                'blocked': interval.get('blocked', False),
                'station': interval['station'],
                'date': interval['start'].strftime("%Y-%m-%d"),
                'start': interval['start'].strftime("%H:%M:%S"),
                'duration': "%02d:%02d" % (minutes, seconds)
            }


class api_balance_json(ProtectedPage):
    """Balance API"""

    def GET(self):
        statuslist = []
        epoch = datetime.date(1970, 1, 1)

        for station in stations.get():
            if station.enabled and any(station.index in program.stations for program in programs.get()):
                statuslist.append({
                    'station': station.name,
                    'balances': {int((key - epoch).total_seconds()): value for key, value in station.balance.iteritems()}})

        web.header('Content-Type', 'application/json')
        return json.dumps(statuslist, indent=2)


class showInFooter(object):
    """Enables plugins to display e.g. sensor reagings in the footer of OSPy's UI"""
    
    def __init__(self, label = "", val = "", unit = "", button = ""):
        self._label = label
        self._val = val
        self._unit = unit
        self._button = button
        self._idx = None
        
        self._idx = len(pluginFtr)
        pluginFtr.append({u"label": self._label, u"val": self._val, u"unit": self._unit, u"button": self._button})
  
           
    @property
    def label(self):
        if not self._label:
            return _(u'Label not set')
        else:
            return self._label
    
    @label.setter
    def label(self, text):
        self._label = text
        if self._label:
            pluginFtr[self._idx][u"label"] = self._label + ": "
    
    @property
    def val(self):
        if self._val == "":
            return _(u'Value not set')
        else:
            return self._val
    
    @val.setter
    def val(self, num):
        self._val = num
        pluginFtr[self._idx][u"val"] = self._val

    @property
    def unit(self):
        if not self.unit:
            return _(u'Unit not set')
        else:
            return self._unit
    
    @unit.setter
    def unit(self, text):
        self._unit = text
        pluginFtr[self._idx][u"unit"] = " " + self._unit 


    @property
    def button(self):
        if not self.button:
            return '-'
        else:
            return self._button
    
    @button.setter
    def button(self, text):
        self._button = text
        pluginFtr[self._idx][u"button"] = self._button


class showOnTimeline:
    """ Used to display plugin data next to station time countdown on home page timeline. """ 

    def __init__(self, val = "", unit = ""):
        self._val = val
        self._unit = unit
        self._idxs = None
    
        self._idxs = len(pluginStn)
        pluginStn.append([self._val, self._unit])
        
    @property
    def clear(self):
        del pluginStn[self._idx][:] #  Remove elements of list but keep empty list
            
    @property
    def unit(self):
        if not self.unit:
            return _(u'Unit not set')
        else:
            return self._unit
    
    @unit.setter
    def unit(self, text):
        self._unit = text
        pluginStn[self._idx][0] = self._unit

        
    @property
    def val(self):
        if not self._val:
            return _(u'Value not set')
        else:
            return self._val
    
    @val.setter
    def val(self, num):
        self._val = num
        pluginStn[self._idx][1] = self._val

class api_plugin_data(ProtectedPage):
    """Simple plugin data API"""

    def GET(self):
        footer_data = []
        station_data = []
        data = {}
        if options.show_plugin_data:
            for i, v in enumerate(pluginFtr):
                footer_data.append((i, v[u"val"]))          
            for v in pluginStn:
                station_data.append((v[1]))

        data["fdata"] = footer_data
        data["sdata"] = station_data

        web.header('Content-Type', 'application/json')
        return json.dumps(data)

class api_update_status(ProtectedPage):
    """Simple plugins and system update status API"""

    def GET(self):
        from ospy.server import session

        if session['category'] != 'admin':
            raise web.seeother(u'/')

        pl_data = []
        data = {}
        must_update = 0
        os_state = 0
        os_avail = '0.0.0'
        os_curr  = '0.0.0'

        running_list = plugins.running()
        current_info = options.plugin_status

        for plugin in plugins.available():
            running = plugin in running_list
            available_info = plugins.checker.available_version(plugin)
            if available_info is not None:
                if plugin in current_info and current_info[plugin]['hash'] != available_info['hash']:
                    pl_data.append((must_update, plugins.plugin_name(plugin)))
                    must_update += 1
                        
        if options.use_plugin_update:                    # if not enable update for plugin -> NO POP-UP on home page
            data["plugin_name"]   = pl_data              # name of plugins where must be updated
            data["plugins_state"] = must_update          # status whether it is necessary to update the plugins (count plugins)
        else:
            data["plugin_name"]   = []    
            data["plugins_state"] = 0   

        try:
            from plugins import system_update
            os_state = system_update.get_all_values()[0] # 0= Plugin is not enabled, 1= Up-to-date, 2= New OSPy version is available,
            os_avail = system_update.get_all_values()[1] # Available new OSPy version
            os_curr  = system_update.get_all_values()[2] # Actual OSPy version

            data["ospy_state"] = os_state  
            data["ospy_aval"]  = os_avail   
            data["ospy_curr"]  = os_curr   

        except Exception:
            data["ospy_state"] = os_state  
            data["ospy_aval"]  = os_avail 
            data["ospy_curr"]  = os_curr             

        web.header('Content-Type', 'application/json')
        return json.dumps(data)    


class api_update_footer(ProtectedPage):
    """Simple footer value status API"""

    def GET(self):
        from ospy.server import session
        from ospy.helpers import uptime, get_cpu_temp, get_cpu_usage, get_external_ip

        if session['category'] != 'admin':
            raise web.seeother(u'/')
        
        data = {}
        data["cpu_temp"]    = get_cpu_temp(options.temp_unit)
        data["cpu_usage"]   = get_cpu_usage()   
        data["sys_uptime"]  = uptime()    
        data["ip"]          = get_external_ip()        

        web.header('Content-Type', 'application/json')
        return json.dumps(data)   


class api_search_sensors(ProtectedPage):
    """APi for Available sensors that are not assigned"""

    def GET(self):
        from ospy.server import session

        if session['category'] != 'admin':
            raise web.seeother(u'/')
        
        searchData = []
        searchData.extend(sensorSearch) if sensorSearch not in searchData else searchData

        web.header('Content-Type', 'application/json')
        return json.dumps(searchData)
              