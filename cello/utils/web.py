#-*- coding:utf-8 -*-
""" :mod:`cello.layout.web`
===========================

helpers to build HTTP/Json Api from cello engines
"""

import sys
import json

from flask import Flask
from flask import Blueprint
from flask import abort, request, jsonify

from cello.types import GenericType, Text
from cello.exceptions import CelloPlayError
from cello.engine import Engine

# for error code see http://fr.wikipedia.org/wiki/Liste_des_codes_HTTP#Erreur_du_client


class CelloFlaskView(Blueprint):
    """ Standart Flask json API view over a Cello :class:`.Engine`.

    This is a Flask Blueprint.
    """

    def __init__(self, engine):
        """ Build the Blueprint
        
        :param engine: the cello engine to serve through an json API
        :type engine: :class:`.Engine`.
        """
        super(CelloFlaskView, self).__init__("cello", __name__)
        self.engine = engine
        # default input
        self._in_type = None
        self.set_input_type(Text(vtype=unicode, encoding="utf8"))
        # default outputs
        self._outputs = []
        
        # bind entry points
        self.add_url_rule('/options', 'options', self.options)
        self.add_url_rule('/play', 'play', self.play,  methods= ["POST", "GET"])

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
        if not request.headers['Content-Type'].startswith('application/json'):
            abort(415) # Unsupported Media Type
        ### get data
        data = request.json
        assert data is not None #FIXME: better error than assertError ?
        ### check commun errors
        if not all([inname in data for inname in self.engine.in_name]):
            #XXX ERROR should be handle
            raise NotImplementedError()
        ### parse options
        if "options" in data:
            options = data["options"]
            try:
                self.engine.configure(options)
            except ValueError as err:
                #TODO beter manage input error: indicate what's wrong
                abort(406)  # Not Acceptable
        ### parse input (and validate)
        inputs_data = [data[in_name] for in_name in self.engine.in_name]
        if len(inputs_data):
            self._in_type.validate(inputs_data[0])
        else:
            raise NotImplementedError("le mutlti input est pas encore géré ici...")
        ### run the engine
        error = False #by default ok
        try:
            raw_res = self.engine.play(*inputs_data)
        except CelloPlayError as err:
            # this is the cello error that we can handle
            error = True
        finally:
            pass
        ### prepare outputs
        outputs = {}
        rcode = 200     #default return code if no errors
        results = {}
        if not error:
            # prepare the outputs
            for out_name, serializer in self._outputs:
                # serialise output
                if serializer is not None:
                    results[out_name] = serializer(raw_res[out_name])
                else:
                    results[out_name] = raw_res[out_name]
        else:          # custom return code if managed error
            rcode = 530
        ### prepare the retourning json
        # add the results
        outputs["results"] = results
        ### serialise play metadata
        outputs['meta'] = self.engine.meta.as_dict()
        #note: meta contains the error (if any)
        return jsonify(outputs), rcode

