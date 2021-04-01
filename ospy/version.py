# -*- coding: utf-8 -*-
__author__ = 'Rimco' # add sensor version 'Martin Pihrt'

# System imports
import subprocess
import logging
import os

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
    ver_date = u"2021-04-01"

### ESP32 sensor last fw version in folder
try:
    esp32_folder_fw = os.path.join('.', 'hardware_pcb', 'sensors_pcb_fw', 'ESP32' , 'firmware')
    entries_32 = os.listdir(esp32_folder_fw)
    ver_esp32 = 0
    for i in entries_32:
        val_32 = int(i[:-4])     # ex: 105.bin -> 105
        if ver_esp32 < val_32: 
            ver_esp32 = val_32    
    if ver_esp32 != 0:        
        ver_esp32 = float(ver_esp32)/100.0
    else:
        ver_esp32 = u"-"
except Exception:
    logging.warning(_(u'Could not find ESP32 firmware version!'))
    ver_esp32 = u"-"

### ESP8266 sensor last fw version in folder
try:
    esp8266_folder_fw = os.path.join('.', 'hardware_pcb', 'sensors_pcb_fw', 'ESP8266' , 'firmware')
    entries_8266 = os.listdir(esp8266_folder_fw)
    ver_esp8266 = 0
    for i in entries_8266:
        val_8266 = int(i[:-4])     
        if ver_esp8266 < val_8266: 
            ver_esp8266 = val_8266 
    if ver_esp8266 != 0:        
        ver_esp8266 = float(ver_esp8266)/100.0
    else:
        ver_esp8266 = u"-"
except Exception:
    logging.warning(_(u'Could not find ESP8266 firmware version!'))
    ver_esp8266 = u"-"