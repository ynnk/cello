#-*- coding:utf-8 -*-

import sys
import json

from flask import Flask
from flask import Blueprint
from flask import abort, request, jsonify

from cello.types import GenericType, Text
from cello.engine import Engine

class CelloFlaskView(Blueprint):

    def __init__(self, engine):
        super(CelloFlaskView, self).__init__("cello", __name__)
        self.engine = engine
        # default input
        self._in_type = None
        self.set_input_type(Text(vtype=unicode, encoding="utf8"))
        # default outputs
        self._outputs = []
        
        # bind entry points
        self.add_url_rule('/options', 'options', self.options)
        self.add_url_rule('/play', 'play', self.play,  methods= ["POST", "GET"] )

    def set_input_type(self, type_or_parse):
        """ Set the input type
        """
        if isinstance(type_or_parse, GenericType):
            self._in_type = type_or_parse
        elif callable(type_or_parse):
            self._in_type = GenericType(parse=type_or_parse)
        else:
            raise ValueError("the given 'type_or_parse' is invalid")

    def add_output(self, out_name, serializer=None):
        """ add an output
        """
        if serializer is not None and not callable(serializer):
            raise ValueError("the given 'serializer' is invalid")
        self._outputs.append((out_name, serializer))

    def options(self):
        conf = self.engine.as_dict()
        conf["returns"] = [oname for oname, _ in self._outputs]
        return jsonify(conf)

    def play(self):
        #if not request.headers['Content-Type'] == 'application/json':
            #abort(415)
        ### get data
        data = request.json
        ### check commun errors
        if self.engine.in_name not in data:
            #XXX ERROR should be handle
            raise NotImplementedError
        ### parse options
        if "options" in data:
            options = data["options"]
            self.engine.configure(options)
        ### parse input (and validate)
        input_data = self._in_type.parse(data[self.engine.in_name])
        self._in_type.validate(input_data)
        ### run the engine
        raw_res = self.engine.play(input_data)
        ### prepare outputs
        results = {}
        for out_name, serializer in self._outputs:
            # serialise output
            if serializer is not None:
                results[out_name] = serializer(raw_res[out_name])
            else:
                results[out_name] = raw_res[out_name]
        ### serialise play metadata
        # TODO
        ### prepare result json
        outputs = {}
        outputs["results"] = results
        return jsonify(outputs)

