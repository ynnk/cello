#!/usr/bin/env python
#-*- coding:utf-8 -*-

class CelloError(Exception):
    """Base KodexError"""

class CelloValueError(CelloError, ValueError):
    """Base KodexValueError"""

