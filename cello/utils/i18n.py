#-*- coding:utf-8 -*-
""" :mod:`cello.utils.i18n`
===========================

helpers for internationalisation
"""
import gettext

trans = gettext.translation('cello', fallback=True)
_ = trans.ugettext

