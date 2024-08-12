#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Martin pihrt'


from ospy.helpers import password_hash, password_salt, print_report
from ospy.options import options
import traceback

print_report('back_door.py', _('The password will now be cleared to the default password. Name "admin" and password "admin".'))

try:
    options.first_installation = True
    options.first_password_hash = "admin"
    options.password_salt = password_salt()
    options.password_hash = password_hash(options.first_password_hash, options.password_salt)
    options.admin_user = 'admin'
    options.no_password = False
    print_report('back_door.py', _('Done, now restart the ospy service (sudo service ospy restart) and open the login window in the browser.'))

except:
    print_report('back_door.py', traceback.format_exc())