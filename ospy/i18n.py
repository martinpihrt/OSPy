# encoding: utf-8
# First Author Dan <dkimberling59@gmail.com>
# for OSPy by Martin Pihrt

__author__ = u'Martin Pihrt'

import os
import locale
import gettext
import shelve

OPTIONS_FILE = './ospy/data/options.db'

try:
    db = shelve.open(OPTIONS_FILE)
    sd_lang = db['lang'] # example return sd_lang = 'cs_CZ'
    db.close()    
except:
    sd_lang = 'default'

### here add next languages ###
languages = ({
    u"en_US": u"English",
    u"cs_CZ": u"Czech",
    u"sk_SK": u"Slovak",
    u"de_DE": u"German",
    u"fr_FR": u"French",
    u"gr_GR": u"Greek",
    u"it_IT": u"Italian",
    u"pt_PT": u"Portuguese",
    u"sl_SL": u"Slovenian",
    u"es_ES": u"Spanish",
    u"ta_TA": u"Tamil",
    u"ar_SA": u"Arabic",
    u"af_AF": u"Afrikaans",
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
curdir = os.path.realpath('i18n')

# i18n directory.
localedir = curdir + '/'

gettext.install(u'ospy_messages', localedir)

sys_lang = get_system_lang()

if sd_lang == u'default':
    if sys_lang in languages:
        ui_lang = sys_lang
    else:
        ui_lang = u'en_US'
else:
    ui_lang = sd_lang

try:
    gettext.translation(u'ospy_messages', localedir, languages=[ui_lang]).install(True)
except IOError:
    pass
