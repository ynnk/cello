#-*- coding:utf-8 -*-
""" :mod:`cello.types`
======================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

inheritance diagrams
--------------------

.. inheritance-diagram:: GenericType Numeric Text Datetime

Class
-----

"""
import datetime

from cello.exceptions import SchemaError, ValidationError
from cello.validators import TypeValidator, MinValueValidator, MaxValueValidator, ChoiceValidator


class GenericType(object):
    """ Define a type.
    """
    default_validators = []  # Default set of validators

    def __init__(self, default=None, help="", multi=None, uniq=None,
        choices=None, attrs=None, validators=[]):
        """
        :param default: default value for the field
        :param help: description of what the data is
        :type help: str
        :param multi: field is a list or a set
        :type multi: bool
        :param uniq: wether the values are unique, only apply if `multi` is True
        :type uniq: bool
        :param choices: if setted the value should be one of the given choice
        :type choices: list
        :param attrs: field attributes, dictionary of `{"name": AbstractType()}`
        :param validators: list of additional validators
        """
        self._default = default
        self.help = help
        self.multi = multi
        self.uniq = uniq
        self.attrs = attrs
        if self.attrs is not None: # will be a vector field
            if self.multi is None:
                self.multi = True
            elif not self.multi:
                raise SchemaError("If you have attributs you can't have multi=False")
            if self.uniq is None:
                self.uniq = True
            elif not self.uniq:
                raise SchemaError("If you have attributs you can't have uniq=False")
        elif self.uniq:
            if self.multi is None:
                self.multi = True
            elif not self.multi:
                raise SchemaError("If you have uniq=True you can't have multi=False")
        elif self.multi:
            if self.uniq is None:
                self.uniq = False
        else:
            self.multi = False
            self.uniq = False # it is a convention, a uniq value (!multi) is considered as not uniq 
        # TODO self.sorted = sorted
        # self.required = required  # test ds Doc ds le constructeur
        self.validators = self.default_validators + validators
        self.choices = choices
        if choices is not None:
            self.validators.append(ChoiceValidator(choices))
        self._init_validation()

    def _init_validation(self):
        # validate choices
        if self.choices is not None:
            TypeValidator((list,set,tuple))(self.choices)
            for value in self.choices:
                self.validate(value)
        # set the default value
        if self.default is not None:
            if self.multi:
                for val in self.default:
                    self.validate(val)
            else:
                self.validate(self.default)

    @property
    def default(self):
        """ Default value of the type
        """
        return self._default

    @default.setter
    def default(self, value):
        self._default = self.validate(value)

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

    def as_dict(self):
        """ returns a dictionary view of the option
        
        :returns: the option converted in a dict
        :rtype: dict
        """
        info = {}
        info["type"] = self.__class__.__name__
        info["help"] = self.help
        info["default"] = self.default
        info["multi"] = self.multi
        info["uniq"] = self.uniq
        info["choices"] = self.choices
        # TODO appel rec sur les attrs
        #info["attrs"] = self.attrs
        return info


class Numeric(GenericType):
    """ Numerical type (int or float)
    """
    _types_ = [int, float]
    
    def __init__(self, numtype=int, min=None, max=None, **kwargs):
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
        self.min = min
        if min is not None:
            self.validators.append(MinValueValidator(min))
        self.max = max
        if max is not None:
            self.validators.append(MaxValueValidator(max))
        self._init_validation()

    def parse(self, value):
        return self.vtype(value)

    def as_dict(self):
        info = super(Numeric, self).as_dict()
        info["vtype"] = self.vtype
        info["min"] = self.min
        info["max"] = self.max
        return info

class Text(GenericType):
    """ Text type (str or unicode)
    
    if not setted default value is an empty string.
    """
    # valid type for text
    _types_ = [unicode, str]
    default_encoding = "utf8"
    
    def __init__(self, texttype=unicode, **kwargs):
        if "default" not in kwargs and u"default" not in kwargs:
            kwargs["default"] = texttype("")
        super(Text, self).__init__(**kwargs)
        if texttype not in Text._types_:
            raise SchemaError('Wrong type for Text %s' % Numeric._types_ )
        self.vtype = texttype
        self.validators.append(TypeValidator(texttype))
        self._init_validation()

    def parse(self, value):
        if isinstance(value, self.vtype):
            parsed = value
        else:
            #TODO: meilleuir gestion de l'encoding
            if self.vtype == unicode:
                parsed = value.decode(self.default_encoding)
            else:
                parsed = value.encode(self.default_encoding)
        return self.validate(parsed)

    def as_dict(self):
        info = super(Text, self).as_dict()
        info["vtype"] = self.vtype


class Boolean(GenericType):
    default_validators = [TypeValidator(bool)]
    
    TRUE_VALUES = set([True, 1, u'1', u'yes', u'oui', u'o', u'true'])
    
    def __init__(self, **kwargs):
        super(Boolean, self).__init__(**kwargs)

    def parse(self, value):
        if isinstance(value, str):
            value = value.decode("utf8")
        if isinstance(value, unicode):
            value = value.lower()
        return value in Boolean.TRUE_VALUES


class Datetime(GenericType):
    """ datetime type
    """
    def __init__(self, **kwargs):
        super(Datetime, self).__init__(**kwargs)
        self.validators.append(TypeValidator(datetime.datetime))
        self._init_validation()

    def parse(self, value):
        raise NotImplementedError

    def as_dict(self):
        info = super(Datetime, self).as_dict()
        return info

# Add more FiledType here
# ...