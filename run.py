#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Rimco'

import sys
import os

if __name__ == '__main__':
    if sys.platform.startswith('linux'):
        if not os.getuid() == 0:
            sys.exit("This script needs to be run as root.")

    import ospy
    ospy.start()