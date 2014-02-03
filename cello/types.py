#-*- coding:utf-8 -*-
""" :mod:`cello.types`
======================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

inheritance diagrams
--------------------

.. inheritance-diagram:: AbstractType Any Numeric Text Datetime

Class
-----

"""
import datetime



"""
Field types to declare in schemas
*********************************
"""

class AbstractType(object):
    """ Define a type. Abstract class.
    """

    def __init__(self, multi=False, uniq=False, default=None, attrs=None):
        """
        :param multi: field is a list or a set
        :type multi: boolean
        :param uniq: wether the values are unique, only apply if multi == True
        :type multi: boolean
        :param default: default value for the field
        :param attrs: field attributes, dictionary of  ``{"name": AbstractType()}``
        """
        self.multi = multi 
        self.uniq = uniq
        self.default = default
        self.attrs = attrs
        # TODO
        # self.sorted = sorted
        # self.required = required  # test ds Doc ds le constructeur
        # self.choices = 

    def __repr__(self):
        temp = "%s(multi=%s, uniq=%s, default=%s, attrs=%s)"
        return temp % (self.__class__.__name__,
                self.multi, self.uniq, self.default, self.attrs)
    
    #TODO: est-ce que validate permet le cast, comme c'est pour le moment ? ou return juste True/False ?
    def validate(self, value):
        """ Abstract method, check if a value is correct (type).
        Should raise :class:`TypeError` if the type the validation fail.
        
        :param value: the value to validate
        :return: the given value (that may have been converted)
        """
        raise NotImplementedError("This is an abstract class, you should use one of the ")

    def parse(self, value):
        """ parsing from string"""
        return value

class Any(AbstractType):
    """ Any kind of data type, no validation
    """
    def __init__(self, **field_options):
        AbstractType.__init__(self, **field_options)

    def validate(self, value):
        return value


class Numeric(AbstractType):
    """ Numerical type (int or float)
    """
    _types_ = [int, float]
    
    def __init__(self, numtype=int, signed=True, **field_options):
        """
        :param numtype: the type of numbers that can be stored in this field,
            either ``int``, ``float``. 
        :param signed: if the value may be negatif (True by default)
        :type signed: boolean
        """
        AbstractType.__init__(self, **field_options)
        if numtype not in Numeric._types_:
            raise SchemaError('Wrong type for Numeric %s' % Numeric._types_ )
        self.numtype = numtype
        self._signed = signed
    
    def validate(self, value):
        if not isinstance(value, self.numtype):
            raise TypeError("Wrong type: get '%s' but '%s' expected" % (type(value), self.numtype))
        if not self._signed and value < 0:
            raise TypeError("The value can't be negatif ! (got '%s')" % (value))
        return value


class Text(AbstractType):
    """ Text type (str or unicode)
    
    if not setted default value is an empty string.
    """
    # valid type for text
    _types_ = [unicode, str]
    
    def __init__(self, texttype=unicode, **field_options):
        if 'default' not in field_options:
            field_options['default'] = ""
        AbstractType.__init__(self, **field_options)
        if texttype not in Text._types_:
            raise SchemaError('Wrong type for Text %s' % Numeric._types_ )
        self._texttype = texttype

    def validate(self, value):
        if not isinstance(value, self._texttype):
            raise TypeError("Wrong type: get '%s' but '%s' expected" % (type(value), self._texttype))
        return value


class Datetime(AbstractType):
    """ datetime type
    """
    def __init__(self, **field_options):
        AbstractType.__init__(self, **field_options)

    def validate(self, value):
        if not isinstance(value, datetime.datetime):
            raise SchemaError("Wrong type for Datetime %s : '%s' (should be 'datetime.datetime')" % (value, type(value)))
        return value

# Add more FiledType here
# ...
