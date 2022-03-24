#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = u'Martin Pihrt'

import os
import locale
import gettext
import shelve
import sys
import traceback

from ospy.helpers import print_report

OPTIONS_FILE = './ospy/data/default/options.db'

try:
    db = shelve.open(OPTIONS_FILE)
    sd_lang = db['lang'] # example return sd_lang = 'cs_CZ'
    db.close()    
except:
    sd_lang = 'default'
    #print_report('i18n.py', traceback.format_exc())
    pass

### here add next languages ###
languages = ({
    u"en_US": u"English",
    u"cs_CZ": u"Czech",
    u"sk_SK": u"Slovak",
    #u"de_DE": u"German",
    #u"fr_FR": u"French",
    #u"gr_GR": u"Greek",
    #u"it_IT": u"Italian",
    #u"pt_PT": u"Portuguese",
    #u"sl_SL": u"Slovenian",
    #u"es_ES": u"Spanish",
    #u"ta_TA": u"Tamil",
    #u"ar_SA": u"Arabic",
    #u"af_AF": u"Afrikaans",
})
###############################

def get_system_lang():
    """Return default system locale language"""
    lc, encoding = locale.getdefaultlocale()
    if lc:
        return lc
    else:
        return None

# File location directory.
curdir = os.path.realpath(u'i18n')

# i18n directory.
localedir = curdir + u'/'

gettext.install(u'ospy_messages', localedir)

sys_lang = get_system_lang()

if sd_lang == u'default':
    if sys_lang in languages:
        ui_lang = sys_lang
    else:
        ui_lang = u'en_US'
else:
    ui_lang = sd_lang

print_report('i18n.py', 'The language will be set to: {}'.format(ui_lang))

try:
    install_kwargs = {}    # support for Python 3.7.9
    if sys.version_info.major == 2:
        install_kwargs[u'unicode'] = True
    gettext.translation(u"ospy_messages", localedir, languages=[ui_lang]).install(**install_kwargs)    
except IOError:
    print_report('i18n.py', traceback.format_exc())
    pass
