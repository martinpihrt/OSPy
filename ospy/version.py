#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

# System imports
import subprocess
import os

from ospy.log import log


##############################
#### Revision information ####
##############################

major_ver = 3
minor_ver = 0
old_count = 827   # update this to reset revision number.


def _current_branch():
    """Return the checked-out local branch, or an empty value for detached HEAD."""
    try:
        return subprocess.check_output(
            ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
            stderr=subprocess.STDOUT,
        ).strip().decode("utf-8")
    except Exception:
        return ""


def _format_version(revision_count, branch):
    base = "%d.%d.%d" % (major_ver, minor_ver, (revision_count - old_count))
    return base + "-beta" if branch == "beta" else base

try:
    revision = int(subprocess.check_output(["git", "rev-list", "--count", "--first-parent", "HEAD"]))
    branch = _current_branch()
    update_channel = "beta" if branch == "beta" else "stable"
    ver_str = _format_version(revision, branch)
except Exception:
    log.debug('version.py', _('Could not use git to determine revision!'))
    revision = 999
    branch = ""
    update_channel = "stable"
    ver_str = "{}.{}.{}".format(major_ver, minor_ver, revision)
    pass

try:
    ver_date = subprocess.check_output(["git", "log", "-1", "--format=%cd", "--date=short"]).strip().decode('ascii')
except Exception:
    log.debug('version.py', _('Could not use git to determine date of last commit!'))
    ver_date = "2025"
    pass

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
        res = [int(x) for x in str(ver_esp32)]  
        ver_esp32 = "{}.{}{}".format(res[0], res[1], res[2])
    else:
        ver_esp32 = "-"
except Exception:
    log.debug('version.py', _('Could not find ESP32 firmware version!'))
    ver_esp32 = "-"
    pass

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
        res = [int(x) for x in str(ver_esp8266)]  
        ver_esp8266 = "{}.{}{}".format(res[0], res[1], res[2])
    else:
        ver_esp8266 = "-"
except Exception:
    log.debug('version.py', _('Could not find ESP8266 firmware version!'))
    ver_esp8266 = "-"
    pass
