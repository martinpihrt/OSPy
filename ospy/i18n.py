#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = u'Martin Pihrt'

import os
import locale
import gettext
import sys
import traceback

from ospy.helpers import print_report
from ospy.settings_storage import (
    settings_store, sqlite_capability, sqlite_mirror_store,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get(
    'OSPY_DATA_DIR', os.path.join(BASE_DIR, 'ospy', 'data')
)
OPTIONS_FILES = [
    os.path.join(DATA_DIR, 'default', 'options.db'),
    os.path.join(DATA_DIR, 'tmp', 'options.db'),
    os.path.join(DATA_DIR, 'backup', 'options.db'),
]


def _valid_saved_language(value):
    return (
        isinstance(value, str) and
        1 <= len(value) <= 32 and
        all(character.isalnum() or character in ('_', '-') for character in value)
    )


def load_saved_language():
    for options_file in OPTIONS_FILES:
        try:
            values = settings_store.read(options_file)
            if not values or not _valid_saved_language(values.get('lang')):
                continue
            shelve_language = values['lang']
            if (values.get('sqlite_preferred_reads') is True and
                    sqlite_capability().get('available')):
                try:
                    mirror_path = sqlite_mirror_store.path_for(options_file)
                    comparison = sqlite_mirror_store.compare(
                        mirror_path, values
                    )
                    if comparison.get('state') == 'verified':
                        sqlite_language = sqlite_mirror_store.read_verified_value(
                            mirror_path, 'lang', values
                        )
                        if _valid_saved_language(sqlite_language):
                            return sqlite_language
                except Exception:
                    pass
            return shelve_language
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
