#!/usr/bin/env python

from setuptools import setup, find_packages

#TODO; better setup
# see https://bitbucket.org/mchaput/whoosh/src/999cd5fb0d110ca955fab8377d358e98ba426527/setup.py?at=default
# for ex

# Read requirements from txt file
with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='cello',
    version='1.0.2',
    description='Cello',
    author='KodexLab',
    author_email='contact@kodexlab.com',
    url='http://www.kodexlab.com/',
    packages=['cello'] + ['cello.%s' % submod for submod in find_packages('cello')],
    install_requires=required,
)
