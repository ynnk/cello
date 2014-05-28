#!/usr/bin/env python

from setuptools import setup, find_packages

#TODO; better setup
# see https://bitbucket.org/mchaput/whoosh/src/999cd5fb0d110ca955fab8377d358e98ba426527/setup.py?at=default
# for ex

setup(
    name='cello',
    version='1.0',
    description='Cello',
    author='ProxTeam',
    author_email='all@proxteam.net',
    url='http://www.proxteam.net/cello/',
    packages=['cello'] + ['cello.%s' % submod for submod in find_packages('cello')],
)
