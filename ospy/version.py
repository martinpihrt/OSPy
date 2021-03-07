# -*- coding: utf-8 -*-
__author__ = 'Rimco' # add sensor version 'Martin Pihrt'

# System imports
import subprocess
import logging
import os
import json

##############################
#### Revision information ####
##############################

major_ver = 4
minor_ver = 0
old_count = 672   # update this to reset revision number.

try:
    revision = int(subprocess.check_output([u"git", u"rev-list", u"--count", u"--first-parent", u"HEAD"]))
    ver_str = u"%d.%d.%d" % (major_ver, minor_ver, (revision-old_count))
except Exception:
    logging.warning(_(u'Could not use git to determine revision!'))
    revision = 999
    ver_str = u"{}.{}.{}".format(major_ver, minor_ver, revision)

try:
    ver_date = subprocess.check_output([u"git", u"log", u"-1", u"--format=%cd", u"--date=short"]).strip()
    ver_date = ver_date.decode('utf-8')
except Exception:
    logging.warning(_(u'Could not use git to determine date of last commit!'))
    ver_date = u"2021-03-07"

try:
    esp32_file = os.path.join('.', 'hardware_pcb', 'sensors_pcb_fw', 'ESP32' , 'lastfw.info')
    with open(esp32_file) as file:
        ver_esp32 = json.load(file)
        ver_esp32 = float(ver_esp32)/100.0
except Exception:
    logging.warning(_(u'Could not find ESP32 firmware version!'))
    ver_esp32 = u"-"

try:
    esp8266_file = os.path.join('.', 'hardware_pcb', 'sensors_pcb_fw', 'ESP8266' , 'lastfw.info')
    with open(esp8266_file) as file:
        ver_esp8266 = json.load(file)
        ver_esp8266 = float(ver_esp8266)/100.0
except Exception:
    logging.warning(_(u'Could not find ESP8266 firmware version!'))
    ver_esp8266 = u"-"    
