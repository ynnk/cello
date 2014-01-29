#-*- coding:utf-8 -*-
""" :mod:`cello.optionable`
==========================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

Management of optionable processing component.


inheritance diagrams
--------------------

.. inheritance-diagram:: Optionable
.. inheritance-diagram:: AbstractOption  AbstractOption  BooleanOption EnumOption

Class
-----
"""
import logging

from cello.utils import parse_bool

# ynnk
# ^^^^

# AbstractOption : why do we need an Abstract where there is a Generic that can be extended
# abstract to generic

# default: why setting default also set the value

# set()  :setting value with set is unnecessary the property covers use case perfectly

# parse/parse : parse is an attribute function parse is part of interface
#         should use parse only or call it parse  but remove one from interface

# parse_options :should parse only not be a setter
# set_from_str : if options are given as str , other way are
#           >>> option.set(string, parse=True)

# validate : we should be able to override validate from __init__
#    instead of writting a new class to override validate.
#    validate raises exception catch by caller         
#    ex: we want an int in range [0:5] 
#           >>> Option("name", "desc", parse=lambda x : int(x), validate=lamdba x : O if x < 0 else min(4,x) )
# or create a RangeOption ?
# first case is fast an easy way but not intended for reusability 




class AbstractOption(object):
    """ Abstract option
    """
    def __init__(self, name, default, description, otype=None, parse=None, validate=None, hidden=False):
        """
        :param name: option's name
        :type name: str
        
        :param description: short description of the option
        :type description: str
        
        :param default: default option value
        :type default: any

        :param parse: function to transform the option value from string to
             internal appropriate format
        :type parse: function
        
        :param hidden: it True the option will not be discoverable
        :type hidden: bool
        """
        self.name = name
        self._value = None
        self._default = None
        self.description = description
        self.opt_type = otype        
        self.parse = parse or self.parse
        self.validate = validate or self.validate
        self.hidden = hidden 

    @property
    def name(self):
        """ Name of the option. """
        return self._name

    @name.setter
    def name(self, name):
        """ Set name of the option.
        An option name can't contain space. """
        if ' ' in name:
            raise ValueError("Option's name should not contain space '%s'" % name)
        self._name = name

    @property
    def value(self):
        """ Value of the option
        """
        return self._value

    @value.setter
    def value(self, value):
        self._value = self.validate(value)

    @property
    def default(self):
        """ Default value of the option
        
        .. warning:: changing the default value also change the current value
        """
        return self._default

    @default.setter
    def default(self, value):
        self._default = self.validate(value)
        self.value = value

    def validate(self, value):
        """ Raises :class:`ValueError` if the value is not correct, else just
        returns the given value.

        It is called when a new value is setted.

        :param value: the value to validate
        :returns: the value
        """
        return value

    def parse(self, value_str):
        """ Convert the value from a string.
        Raises :class:`ValueError` if convertion isn't possible.

        :param value_str: a potential value for the option
        :type value_str: str
        :returns: the value converted to the good type
        """
        return str(value_str)

    def set(self, value, parse=False):
        """ Set the value of the option.
        
        One can also set the 'value' property:

        >>> opt = AbstractOption("oname", "an option exemple")
        >>> opt.value = 12
        
        :param value: the new value
        """
        self.value = self.parse(value) if parse else value


    def as_dict(self):
        """ returns a dictionary view of the option
        
        :returns: the option converted in a dict
        :rtype: dict
        """
        opt_info = {}
        opt_info["type"] = "generic"
        opt_info["name"] = self.name
        opt_info["description"] = self.description
        opt_info["value"] = self.value
        opt_info["default"] = self.default
        return opt_info

class ValueOption(AbstractOption):
    def __init__(self, name, default, desc, **kwargs):
        if not( kwargs.get("otype", None) ):
            pass # XXX            
            #kwargs['otype'] = Any
        AbstractOption.__init__(self, name, default, desc, **kwargs)
        self.default = default

    def as_dict(self):
        """ returns a dictionary version of the option
        """
        opt_info = AbstractOption.as_dict(self)
        opt_info["type"] = "value"
        return opt_info

class BooleanOption(AbstractOption):
    def __init__(self, name, default, desc, **kwargs):
        AbstractOption.__init__(self, name, default, desc, **kwargs)
        self.default = default

    def as_dict(self):
        """ returns a dictionary version of the option
        """
        opt_info = AbstractOption.as_dict(self)
        opt_info["type"] = "boolean"
        return opt_info

class RangeOption(AbstractOption):
    def __init__(self, name, default, desc, min_value=0, max_value=10,  **kwargs):
        AbstractOption.__init__(self, name, default, desc, **kwargs)
        self.default = default
        # TODO check for correct value types
        self.min_value = min_value
        self.max_value = max_value
        
    def validate(self, value):
        if value < self.min_value or value > self.max_value:
            raise ValueError( "Value should be in range(%s,%s) " % \
                (self.min_value, self.max_value) )

    def as_dict(self):
        """ returns a dictionary version of the option
        """
        opt_info = AbstractOption.as_dict(self)
        opt_info["type"] = "range"
        return opt_info


class EnumOption(AbstractOption):
    """ Enumerate option
    """
    def __init__(self, name, default, desc, enum, **kwargs):
        """
        :param parse: function to transform the option value from string to
             appropriate format
        :type parse: function
        """
        AbstractOption.__init__(self, name, default, desc, **kwargs)
        if not(len(enum)):
            raise ValueError('Empty Enum %s' % enum)
        self._enum = enum
        if default is None:
           self.default = enum[0]

    def validate(self, value):
        if value not in self._enum:
            raise ValueError("The value '%s' is not in %s" % (value, self._enum))
        return value

    def as_dict(self):
        """ returns a dictionary version of the option
        """
        opt_info = AbstractOption.as_dict(self)
        opt_info["type"] = "enum"
        opt_info["enum"] = self._enum
        return opt_info



