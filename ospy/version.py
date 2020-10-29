# -*- coding: utf-8 -*-
__author__ = 'Rimco'

# System imports
import subprocess
import logging

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
    ver_date = u"2020-10-29"
