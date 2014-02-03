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

from cello.exceptions import SchemaError, ValidationError
from cello.validators import TypeValidator, MinValueValidator, MaxValueValidator

"""
Field types to declare in schemas
*********************************
"""

class GenericType(object):
    """ Define a type.
    """
    default_validators = []  # Default set of validators

    def __init__(self, default=None, multi=False, uniq=False, attrs=None,
        validators=[]):
        """
        :param default: default value for the field
        :param multi: field is a list or a set
        :type multi: bool
        :param uniq: wether the values are unique, only apply if `multi` is True
        :type multi: bool
        :param attrs: field attributes, dictionary of `{"name": AbstractType()}`
        :param validators: list of additional validators
        """
        self.default = default
        self.multi = multi
        self.uniq = uniq
        self.attrs = attrs
        # TODO
        # self.sorted = sorted
        # self.required = required  # test ds Doc ds le constructeur
        # self.choices = 
        self.validators = self.default_validators + validators

    def __repr__(self):
        temp = "%s(multi=%s, uniq=%s, default=%s, attrs=%s)"
        return temp % (self.__class__.__name__,
                self.multi, self.uniq, self.default, self.attrs)
    
    def validate(self, value):
        """ Abstract method, check if a value is correct (type).
        Should raise :class:`TypeError` if the type the validation fail.
        
        :param value: the value to validate
        :return: the given value (that may have been converted)
        """
        for validator in self.validators:
            errors = []
            try:
                validator(value)
            except ValidationError as err:
                errors.append(err)
            if errors:
                raise ValidationError(errors)
        return value

    def parse(self, value):
        """ parsing from string """
        return value


class Numeric(GenericType):
    """ Numerical type (int or float)
    """
    _types_ = [int, float]
    
    def __init__(self, numtype=int, signed=True, min=None, max=None, **kwargs):
        """
        :param numtype: the type of numbers that can be stored in this field,
            either ``int``, ``float``. 
        :param signed: if the value may be negatif (True by default)
        :type signed: bool
        :param min: if not None, the minimal possible value
        :param max: if not None, the maximal possible value
        """
        super(Numeric, self).__init__(**kwargs)
        if numtype not in Numeric._types_:
            raise SchemaError('Wrong type for Numeric %s' % Numeric._types_ )
        self.vtype = numtype
        self.validators.append(TypeValidator(numtype))
        self.signed = signed
        if not signed:
            self.validators.append(MinValueValidator(0))
        self.min_ = min
        if min:
            self.validators.append(MinValueValidator(min))
        self.max = max
        if max:
            self.validators.append(MaxValueValidator(max))

class Text(GenericType):
    """ Text type (str or unicode)
    
    if not setted default value is an empty string.
    """
    # valid type for text
    _types_ = [unicode, str]
    
    def __init__(self, texttype=unicode, **kwargs):
        if "default" not in kwargs and u"default" not in kwargs:
            kwargs["default"] = texttype("")
        super(Text, self).__init__(**kwargs)
        if texttype not in Text._types_:
            raise SchemaError('Wrong type for Text %s' % Numeric._types_ )
        self.vtype = texttype
        self.validators.append(TypeValidator(texttype))


class Datetime(GenericType):
    """ datetime type
    """
    def __init__(self, **kwargs):
        super(Datetime, self).__init__(**kwargs)
        self.validators.append(TypeValidator(datetime.datetime))

# Add more FiledType here
# ...
