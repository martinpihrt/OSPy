# -*- coding: utf-8 -*-
__author__ = 'Rimco'


def start():
    # We want to hook the logging before importing other modules which might already use log statements:
    from ospy.log import hook_logging
    hook_logging()

    from ospy import server
    server.start()