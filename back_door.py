#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Martin pihrt'

import os
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
    options.two_factor_method = 'none'
    options.two_factor_secret = ''
    options.two_factor_backup_codes = []

    remembered_logins_revoked = False
    try:
        from ospy import autologin
        autologin.revoke_all()
        remembered_logins_revoked = True
    except Exception:
        print_report('back_door.py', traceback.format_exc())

    # A new session secret invalidates every existing web session after the
    # requested OSPy restart.  Replacing the secret is safe while the current
    # process is still running because it keeps its old value in memory.
    active_sessions_revoked = False
    try:
        session_secret_file = os.path.join('ospy', 'data', 'session_secret')
        session_secret_tmp = session_secret_file + '.recovery'
        os.makedirs(os.path.dirname(session_secret_file), exist_ok=True)
        with open(session_secret_tmp, 'w') as secret_file:
            secret_file.write(secrets.token_hex(64))
        try:
            os.chmod(session_secret_tmp, 0o600)
        except Exception:
            pass
        os.replace(session_secret_tmp, session_secret_file)
        active_sessions_revoked = True
    except Exception:
        print_report('back_door.py', traceback.format_exc())

    options.save_now()

    print_report('back_door.py', _('Done. Restart the OSPy service: sudo service ospy restart'))
    print_report('back_door.py', _('Two-factor authentication was disabled.'))
    if remembered_logins_revoked and active_sessions_revoked:
        print_report('back_door.py', _('All remembered logins and active web sessions were revoked.'))
    else:
        print_report('back_door.py', _('WARNING: Some existing login sessions could not be revoked; check the errors above.'))
    print_report('back_door.py', _('Then open the login page. OSPy will show a generated recovery password for admin, and you must change it after login.'))
    print_report('back_door.py', _('Recovery password for this reset: {}').format(recovery_password))

except:
    print_report('back_door.py', traceback.format_exc())
