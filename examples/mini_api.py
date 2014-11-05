#!/usr/bin/env python
#-*- coding:utf-8 -*-
import sys
from flask import Flask

## create composants
from cello.pipeline import Composable
@Composable
def my_comp(text):
    """ Just do Nothing !"""
    return text

## create Cello Engine
from cello.engine import Engine
engine = Engine()
# configures all the blocks
engine.requires("analyse")
engine.analyse.setup(in_name="query", out_name="result")

# setup the block 'analyse'
engine.analyse.set(my_comp)

## create the API blue print
from cello.utils.web import CelloFlaskView
from cello.types import Text
api = CelloFlaskView(engine)
# configure input/output
api.set_input_type(Text())
api.add_output("result", lambda x: x.encode('utf8'))

## Build the app
app = Flask(__name__, static_url_path='')
app.debug = True

# register the app
app.register_blueprint(api, url_prefix="/api")


## main
def main():
    ## run the app
    from flask.ext.runner import Runner
    runner = Runner(app)
    runner.run()

if __name__ == '__main__':
    sys.exit(main())
