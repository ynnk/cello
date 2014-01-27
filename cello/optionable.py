#-*- coding:utf-8 -*-
""" :mod:`cello.optionable`
==========================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

Management of optionable processing component.


inheritance diagrams
--------------------

.. inheritance-diagram:: Optionable
.. inheritance-diagram:: GenericOption  GenericOption  BooleanOption EnumOption

Class
-----
"""
from collections import OrderedDict
import logging
from cello.utils import parse_bool

# ynnk
# ^^^^

# GenericOption : why do we need an Abstract where there is a Generic that can be extended
# abstract to generic

# default: why setting default also set the value

# set()  :setting value with set is unnecessary the property covers use case perfectly

# cast/parse : cast is an attribute function parse is part of interface
#         should use cast only or call it parse  but remove one from interface

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



class GenericOption(object):
    """ Generic option
    """
    def __init__(self, name, description, default=None, hidden=False, parse=None, validate=None):
        """
        :param name: option's name
        :type name: str
        
        :param description: short description of the option
        :type description: str
        
        :param default: default option value
        :type default: any
        
        :param hidden: it True the option will not be discoverable
        :type hidden: bool

        :param parse: function to transform the option value from string to
             appropriate format
        :type parse: function
        """
        self.name = name
        self.description = description
        self.hidden = hidden 
        self.default = default or []
        self.parse = parse or self.parse
        self.validate = validate or self.validate

    @property
    def name(self):
        """ Name of the option.
        
        An option name can't contain space.
        """
        return self._name

    @name.setter
    def name(self, name):
        if ' ' in name:
            raise ValueError("The option name souldn't contain space")
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

        >>> opt = GenericOption("oname", "an option exemple")
        >>> opt.value = 12
        
        :param value: the new value
        """
        self.value = self.parse(value) if parse else value

    # XXX to delete
    def set_from_str(self, value_str):
        """ Set the value with a convertion from a string

        :param value_str: new value of the option
        :type value_str: str
        """
        self.value = self.parse(value_str)


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



class BooleanOption(GenericOption):
    """ Basic boolean option
    """
    def __init__(self, name, description, default=False):
        GenericOption.__init__(self, name, description, default)

    def validate(self, value):
        if not isinstance(value, bool):
            raise ValueError("The value should be a boolean")
        return value

    def parse(self, value_str):
        return parse_bool(value_str)

    def as_dict(self):
        opt_info = GenericOption.as_dict(self)
        opt_info["type"] = "boolean"
        return opt_info


class EnumOption(GenericOption):
    """ Enumerate option
    """
    def __init__(self, name, description, enum, default=None, cast=None):
        """
        :param cast: function to transform the option value from string to
             appropriate format
        :type cast: function
        """
        if default is None:
            default = enum[0]
        self._enum = enum
        GenericOption.__init__(self, name, description, default=default, cast=cast)

    def validate(self, value):
        if value not in self._enum:
            raise ValueError("The value '%s' is not in %s" % (value, self._enum))
        return value

    def as_dict(self):
        """ returns a dictionary version of the option
        """
        opt_info = GenericOption.as_dict(self)
        opt_info["type"] = "enum"
        opt_info["enum"] = self._enum
        return opt_info


class Optionable(object):
    """ Abstract class for an optionable component
    """

    def __init__(self, name):
        """ 
        :param name: name of the Optionable component
        :type name: str
        """
        self._options = OrderedDict()
        self.name = name
        self._logger = logging.getLogger(__name__)

    @property
    def name(self):
        """Name of the optionable component"""
        return self._name

    @name.setter
    def name(self, name):
        if ' ' in name:
            raise ValueError("Component name should not contain space")
        self._name = name

    def add_option(self, option):
        """ Add an option to the object
        
        :param option: option name
        :type option: subclass of :class:`.GenericOption`
        """
        if not isinstance(option, GenericOption):
            raise ValueError("The option should be a subclass of GenericOption")
        if option.name in self._options:
            raise ValueError("There is already an option with the same name (='%s')" % option.name)
        self._options[option.name] = option


    def add_generic_option(self, opt_name, default, description, cast=None):
        """ Add a generic option
        
        :param opt_name: option name
        :type opt_name: str
        
        :param default: default value
        :type default: str
        
        :param description: short description of the option
        :type description: str
        
        :param cast: function to transform the option value from string to
            appropriate format
        :type cast: function
        """
        opt = GenericOption(name=opt_name, default=default, description=description, cast=cast)
        self.add_option(opt)

    def add_bool_option(self, opt_name, default, description):
        """ Add a boolean option
        
        :param opt_name: option's name
        :type opt_name: str
        
        :param default: default value of the option
        :type default: str
    
        :param description: short description of the option
        :type description: str
        """
        opt = BooleanOption(name=opt_name, default=default, description=description)
        self.add_option(opt)

    def add_enum_option(self, opt_name, enum, default, description, cast=None):
        """ Add an option to the object same as add option except enum can be provided  
        
        :param opt_name: option name
        :type opt_items: str
        
        :param enum: list of possible values
        
        :param default_val: default value
        
        :param description: short description of the option
        :type description: str
        
        :param cast: function to transform the option value from string to
             appropriate format
        :type cast: function
        """
        opt = EnumOption(name=opt_name, enum=enum, default=default, description=description, cast=cast)
        self.add_option(opt)

    def force_option_value(self, opt_name, value):
        """ force the (default) value of an option.
        The option is then no more listed by :func:`get_options()`.
        
        :param opt_name: option name
        :type opt_name: str
        
        :param value: option value
        """
        if not opt_name in self._options:
            raise ValueError("Unknow option name (%s)" % opt_name)
        self._options[opt_name].default = value # also change the value
        self._options[opt_name].hidden = True

    def change_option_default(self, opt_name, default_val):
        """ Change the default value of an option
        
        :param opt_name: option name
        :type opt_name: str
        
        :param value: new default option value
        """
        print "change_option_default %s %s" % (opt_name, default_val)
        if opt_name not in self._options:
            raise ValueError("Unknow option name (%s)" % opt_name)
        self._options[opt_name].default = default_val

    def get_default_value(self, opt_name):
        """ Return the default value of a given option
        
        :param opt_name: option name
        :type opt_name: str
        
        :returns: the default value of the option
        """
        if not opt_name in self._options:
            raise ValueError("Unknow option name (%s)" % opt_name)
        return self._options[opt_name].default

    def set_option_value(self, opt_name, value, from_str=False):
        """ Set tthe value of one option.
        
        :   param opt_name: option name
        :type opt_name: str
        :param value: the new value
        """
        if not opt_name in self._options:
            raise ValueError("Unknow option name (%s)" % opt_name)
        if self._options[opt_name].hidden:
            raise ValueError("This option is hidden, you can't change the value")
        if from_str:
            self._options[opt_name].set_from_str(value)
        else:
            self._options[opt_name].value = value


    def set_option_values(self, option_values):
        """ Set the options from a dict of values (in string).
        
        :param option_values: the values of options (in format `{"opt_name": "new_value"}`)
        :type option_values: dict
        """
        for opt_name, opt in self._options.iteritems():
            if opt.hidden:
                continue
            if opt_name in option_values:
                opt.set_from_str(option_values[name])

    def get_options_values(self):
        """ return a dictionary of options values
        
        :returns: dictionary of all option values
        :rtype: dict
        """
        values = {}
        for opt_name, opt in self._options.iteritems():
            values[opt_name] = opt.value
        return values

    def parse_options(self, option_values):
        """ Set given option values and returns all option values
        
        :param option_values: the values of options (in format `{"opt_name": "new_value"}`)
        :type option_values: dict
        
        :returns: dictionary of all option values
        :rtype: dict
        """
        self.set_options_value(option_values)
        return self.get_options_value()

    def get_options(self):
        """
        :returns: dictionary of all options (with option's information)
        :rtype: dict
        """
        return dict(self.get_ordered_options())

    def get_ordered_options(self):
        """
        :returns: **ordered** list of all options (with option's information)
        :rtype: list ::
            [(<opt_name>, opt_dict)]
        """
        return [(opt_name, opt.as_dict()) \
                        for opt_name, opt in self._options.iteritems() \
                        if not opt.hidden]



