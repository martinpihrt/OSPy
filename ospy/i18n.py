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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPTIONS_FILES = [
    os.path.join(BASE_DIR, 'ospy', 'data', 'default', 'options.db'),
    os.path.join(BASE_DIR, 'ospy', 'data', 'tmp', 'options.db'),
    os.path.join(BASE_DIR, 'ospy', 'data', 'backup', 'options.db'),
]


def load_saved_language():
    for options_file in OPTIONS_FILES:
        try:
            if os.path.isdir(os.path.dirname(options_file)):
                db = shelve.open(options_file)
                try:
                    if list(db.keys()) and 'lang' in db:
                        return db['lang']
                finally:
                    db.close()
        except Exception:
            pass
    return 'default'

sd_lang = load_saved_language() # example return sd_lang = 'cs_CZ'

### here add next languages ###
languages = ({
    u"en_US": u"English",
    u"cs_CZ": u"Czech",
    u"sk_SK": u"Slovak",
    u"de_DE": u"German",
    u"pl_PL": u"Polish",
    u"sr_RS": u"Serbian",
    u"ru_RU": u"Russian",
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

# i18n directory.
localedir = os.path.join(BASE_DIR, u'i18n')

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
