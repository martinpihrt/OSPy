"""
REST API for OSPy
"""
from __future__ import absolute_import

__author__ = [
    'Teodor Yantcheff',
]

__version__ = '0.9 beta'

from .api import get_app
from .errors import unauthorized, badrequest, notacceptable