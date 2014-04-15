#-*- coding:utf-8 -*-
""" :mod:`cello.utils.cli`
==========================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

Helper function to setup argparser from cello components and engines
"""
import sys
import argparse

from cello.pipeline import Optionable

from cello.exceptions import ValidationError
from cello.types import Boolean, Text, Numeric


def argument_from_option(parser, component, opt_name, prefix=""):
    """
    >>> comp = Optionable()
    >>> comp.add_option("num", Numeric(default=1, max=12, help="An exemple of option"))
    >>> parser = argparse.ArgumentParser(prog="PROG")
    >>> argument_from_option(parser, comp, "num")
    >>> parser.print_help()
    usage: PROG [-h] [--num NUM]
    <BLANKLINE>
    optional arguments:
      -h, --help  show this help message and exit
      --num NUM   An exemple of option
    >>> parser.parse_args(["--num", "2"])
    Namespace(num=2)
    >>> parser.parse_args(["--num", "20"])
    Traceback (most recent call last):
    ...
    SystemExit: 2

    """
    assert component.has_option(opt_name)
    option = component.options[opt_name]
    otype = option.otype
    config = {}
    config["action"] = "store"
    config["help"] = otype.help
    config["default"] = otype.default
    if otype.choices is not None:
        config["choices"] = otype.choices
    def check_type(value):
        try:
            value = option.parse(value)
            option.validate(value)
        except ValidationError as err_list:
            raise argparse.ArgumentTypeError("\n".join(err for err in err_list))
        return value
    config["type"] = check_type

    if isinstance(otype, Boolean):
        config["action"] = "store_true"
    parser.add_argument(
        "--%s%s" % (prefix, opt_name),
        **config
    )
