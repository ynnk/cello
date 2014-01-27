#-*- coding:utf-8 -*-
""":mod:`cello`
===============

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

"""


class CelloError(Exception):
    """Basic cello error"""

class CelloValueError(CelloError, ValueError):
    """Cello value error: one value (attribute) was wrong"""



