#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Martin pihrt'

import secrets
import sys
import traceback

from ospy.helpers import print_report
from ospy.options import options


def _confirm_reset():
    if '--yes' in sys.argv:
        return True
    print_report('back_door.py', _('WARNING: This local recovery script resets the OSPy administrator login.'))
    print_report('back_door.py', _('Run it only from the Raspberry Pi console or another trusted local shell.'))
    try:
        answer = input('Type RESET to continue: ')
    except EOFError:
        return False
    return answer == 'RESET'


try:
    if not _confirm_reset():
        print_report('back_door.py', _('Password reset cancelled.'))
        sys.exit(1)

    recovery_password = secrets.token_hex(8)

    options.first_installation = True
    options.first_password_hash = recovery_password
    options.password_salt = ''
    options.password_hash = 'opendoor'
    options.admin_user = 'admin'
    options.no_password = False

    try:
        from ospy import autologin
        autologin.revoke_all()
    except Exception:
        print_report('back_door.py', traceback.format_exc())

    options.save_now()

    print_report('back_door.py', _('Done. Restart the OSPy service: sudo service ospy restart'))
    print_report('back_door.py', _('Then open the login page. OSPy will show a generated recovery password for admin, and you must change it after login.'))
    print_report('back_door.py', _('Recovery password for this reset: {}').format(recovery_password))

except:
    print_report('back_door.py', traceback.format_exc())
