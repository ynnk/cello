#-*- coding:utf-8 -*-
""" :mod:`cello.export`
========================

"""
from cello.schema import Doc, Numeric

def export_docs(kdocs, exclude=[]):
    """ Transform the list of kdoc

    remove all the attributes of KodexDoc that are not fields (of elements) or elements attributes
    """
    return [doc.export(exclude=exclude) for doc in kdocs]



