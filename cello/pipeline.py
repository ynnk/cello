#-*- coding:utf-8 -*-
""" :mod:`cello.pipeline`
=========================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

Abstract objects used to setup processing pipelines.


inheritance diagrams
--------------------

.. inheritance-diagram:: cello.pipeline

Class
-----
"""
import logging
from collections import OrderedDict

from cello.options import ValueOption

class Composable(object):
    """ Basic composable element
    
    Composable is abstract, you need to implemented the :meth:`__call__` method
    
    >>> e1 = Composable(lambda iterable: (element**2 for element in iterable))
    >>> e2 = Composable(lambda iterable: (element + 10 for element in iterable))
    
    Then Composable can be pipelined this way :

    >>> chain = e1 | e2

    So yo got :
    
    >>> iterable = xrange(0, 6, 2)
    >>> for e in chain(iterable):
    ...     print("result: %s" % e)
    result: 10
    result: 14
    result: 26

    which is equivalent to :

    >>> iterable = xrange(0, 6, 2)
    >>> for e in e2(e1(iterable)):
    ...     print("result: %s" % e)
    result: 10
    result: 14
    result: 26
    """

    def __init__(self, func=None, name=None):
        self._name = None
#        print "###########################################%s, %s"%(func,name)
        if func and callable(func):
            self._func=func
            self.name = func.func_name
            self.__doc__ = func.__doc__
        if name is not None:
            self.name = name

    @property
    def name(self):
        """Name of the optionable component"""
        return self._name

    @name.setter
    def name(self, name):
        if ' ' in name:
            raise ValueError("Component name should not contain space")
        self._name = name

    def __or__(self, other):
        if not callable(other):
            raise Exception("%r is not composable with %r" % (self, other))
        return Pipeline(self, other)

    def __call__(self, *args):
        if hasattr(self, "_func"):
            return self._func(*args)
        else: raise NotImplementedError


class Optionable(Composable):
    """ Abstract class for an optionable component
    """

    def __init__(self, name):
        """ 
        :param name: name of the component
        :type name: str
        """
        Composable.__init__(self, name=name)
        self._options = OrderedDict()
        self._logger = logging.getLogger(__name__)

    def add_option(self, opt_name, otype, hidden=False):
        """ Add an option to the object
        
        :param opt_name: option name
        :type opt_name: str
        :param otype: option type
        :type otype: subclass of :class:`.GenericType`
        :param hidden: if True the option will be hidden
        :type hidden: bool
        """
        if opt_name in self._options:
            raise ValueError("The option is already present !")
        opt = ValueOption.FromType(opt_name, otype)
        opt.hidden = hidden
        self._options[opt_name] = opt

    def set_option_value(self, opt_name, value, parse=False):
        """ Set tthe value of one option.
        
        :param opt_name: option name
        :type opt_name: str
        :param value: the new value
        :param parse: if True the value is converted from string to the correct type
        :type parse: bool
        """
        if not opt_name in self._options:
            raise ValueError("Unknow option name (%s)" % opt_name)
        self._options[opt_name].set(value, parse=parse)

    def get_option_value(self, opt_name):
        """ Return the value of a given option
        
        :param opt_name: option name
        :type opt_name: str
        
        :returns: the value of the option
        """
        if not opt_name in self._options:
            raise ValueError("Unknow option name (%s)" % opt_name)
        return self._options[opt_name].value

    def change_option_default(self, opt_name, default_val):
        """ Change the default value of an option
        
        :param opt_name: option name
        :type opt_name: str
        
        :param value: new default option value
        """
        if opt_name not in self._options:
            raise ValueError("Unknow option name (%s)" % opt_name)
        self._options[opt_name].default = default_val

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

    def get_option_default(self, opt_name):
        """ Return the default value of a given option
        
        :param opt_name: option name
        :type opt_name: str
        
        :returns: the default value of the option
        """
        if not opt_name in self._options:
            raise ValueError("Unknow option name (%s)" % opt_name)
        return self._options[opt_name].default

    def set_options_values(self, option_values, parse=True):
        """ Set the options from a dict of values (in string).
        
        :param option_values: the values of options (in format `{"opt_name": "new_value"}`)
        :type option_values: dict
        """
        for opt_name, opt in self._options.iteritems():
            if opt.hidden:
                continue
            if opt_name in option_values:
                opt.set(option_values[opt_name], parse=parse)

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
        #XXX: doit disparaitre
        self.set_options_values(option_values)
        return self.get_options_values()

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



class Pipeline(Optionable):
    """ A Pipeline is a sequence of function called sequentially.
    
    It may be create explicitely:
    
    >>> step1 = lambda x: x**2
    >>> step2 = lambda x: x-1
    >>> step3 = lambda x: min(x, 22)
    >>> processing = Pipeline(step1, step2, step3)
    >>> processing(4)
    15
    >>> processing(40)
    22

    Or it can be created implicitely with the pipe operator (__or__) if the
    first function is :class:`Composable`:
    
    >>> step1 = Composable(step1)
    >>> processing = step1 | step2 | step3
    >>> processing(3)
    8
    >>> processing(0)
    -1

    
    """

    def __init__(self, *composables):
        # Composable init
        self._logger = logging.getLogger(__name__)
#        Composable.__init__(self)
        self.items = []
        for comp in composables:
            if isinstance(comp, Pipeline):
                # if already a composable chain, merge it
                self.items.extend(comp.items)
            else:
                self.items.append(comp)
        # Optionable init
        opt_items = [item for item in self.items if isinstance(item, Optionable)]
        # Check than a given options is not in two items
        all_opt_names = {}
        for item in opt_items:
            opt_names = item.get_options().keys()
            for opt_name in opt_names:
                assert not opt_name in all_opt_names, "Option '%s' present both in %s and in %s" % (opt_name, item, all_opt_names[opt_name])
                all_opt_names[opt_name] = item
        # create the "meta" name of the optionable pipeline, and init optionable
        name = "|".join(item.name for item in opt_items)
        Optionable.__init__(self, name)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           ", ".join(repr(item) for item in self.items))

    def __call__(self, element_iter, **kwargs):
        
        items = self.items
        for item in items:
            item_kwargs = {}
            item_name = ""            
            # if Optionable, build kargs
            if isinstance(item, Optionable):
                item_kwargs = item.parse_options(kwargs)
                item_name = item.name
            self._logger.info("\n\tcalling %s '%s' with %s", item,  item_name, item_kwargs )
            element_iter = item(element_iter, **item_kwargs)
        return element_iter

    def __getitem__(self, item):
        return self.items.__getitem__(item)

    def __len__(self):
        return len(self.items)

    def __eq__(self, other):
        return (other
                and self.__class__ is other.__class__
                and self.items == other.items)

    def parse_options(self, options):
        opt = {}
        for item in self.items:
            if isinstance(item, Optionable):
                opt.update(item.parse_options(options))
        return opt

    def get_options(self):
        opt = {}
        for item in self.items:
            if isinstance(item, Optionable):
                opt.update(item.get_options())
        return opt

    def get_ordered_options(self):
        opts = []
        for item in self.items:
            if isinstance(item, Optionable):
                opts += item.get_ordered_options()
        return opts

    def force_option_value(self, opt_name, value):
        flg = False
        for item in self.items:
            if isinstance(item, Optionable):
                if opt_name in item.get_options():
                    item.force_option_value(opt_name, value)
                    flg  = True
        if not flg :
            raise ValueError, "Unknow option name (%s)" % opt_name

    def change_option_default(self, opt_name, default_val):
        flg = False
        for item in self.items:
            if isinstance(item, Optionable):
                if opt_name in item.get_options():
                    item.change_option_default(opt_name, default_val)
                    flg  = True
        if not flg :
            raise ValueError, "Unknow option name (%s)" % opt_name

    def get_default_value(self, opt_name):
        val = None
        for item in self.items:
            if isinstance(item, Optionable):
                if opt_name in item.get_options():
                    val = item.get_default_value(opt_name)
        if val is None:
            raise ValueError("'%s' is not an existing option" % opt_name)
        return val

    def close(self):
        """ Close all the element of the pipeline
        """
        for item in self.items:
            if hasattr(item, "close"):
                item.close()

