#!/usr/bin/env python

from setuptools import setup, find_packages

#TODO; better setup
# see https://bitbucket.org/mchaput/whoosh/src/999cd5fb0d110ca955fab8377d358e98ba426527/setup.py?at=default

version="1.1.0"

# changes

# 1.1.0 change weighting function signature in prox_markov_dict
# 1.0.8 fix pedgigree rho
# 1.0.7 fix mode on proxextract
# 1.0.6 pedigree computations
# 1.0.3 weighted loops ; sortcut > 0

# Read requirements from txt file
with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='cello',
    version=version,
    description='Cello',
    author='enavarro, ynnk',
    author_email='contact@padagraph.io',
    url='http://www.padagraph.io',
    packages=['cello'] + ['cello.%s' % submod for submod in find_packages('cello')],
    install_requires=required,
)
