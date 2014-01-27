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

from cello import Composable
from cello.optionable import Optionable

class Pipeline(Composable, Optionable):
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
    
    >>> step1 = composable(step1)
    >>> processing = step1 | step2 | step3
    >>> processing(3)
    8
    >>> processing(0)
    -1

    
    """

    def __init__(self, *composables):
        # Composable init
        Composable.__init__(self)
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
            if isinstance(item, Optionable):
                # if Optionable, build kargs
                item_kwargs = item.parse_options(kwargs)
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
            raise KodexValueError, "Unknow option name (%s)" % opt_name

    def change_option_default(self, opt_name, default_val):
        flg = False
        for item in self.items:
            if isinstance(item, Optionable):
                if opt_name in item.get_options():
                    item.change_option_default(opt_name, default_val)
                    flg  = True
        if not flg :
            raise KodexValueError, "Unknow option name (%s)" % opt_name

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

