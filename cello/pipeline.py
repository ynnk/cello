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

from optionable import Optionable

class Composable:
    """ Basic composable element
    
    Composable is abstract, you need to implemented the :meth:`__call__` method
    
    >>> e1 = Composable()
    >>> e2 = Composable()
    >>> e1.__call__ = lambda iterable: (element**2 for element in iterable)
    >>> e2.__call__ = lambda iterable: (element + 10 for element in iterable)
    
    Then Composable can be pipelined this way :

    >>> chain = e1 | e2

    So yo got :
    
    >>> iterable = xrange(0,6,2)
    >>> for e in chain(iterable):
    ...     print("result: %s" % e)
    result: 10
    result: 14
    result: 26

    equivalent to :

    >>> iterable = xrange(0,6,2)
    >>> for e in e2(e1(iterable)):
    ...     print("result: %s" % e)
    result: 10
    result: 14
    result: 26
    """

    def __init__(self):
        pass

    def __or__(self, other):
        if not callable(other):
            raise Exception("%r is not composable with %r" % (self, other))
        return ComposableChain(self, other)

    def __call__(self, filename):
        raise NotImplementedError


class ComposableChain(Composable, Optionable):
    def __init__(self, *composables):
        # Composable init
        Composable.__init__(self)
        self.items = []
        for comp in composables:
            if isinstance(comp, ComposableChain):
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


#{ Document Pipeline

class DocPipelineElmt(Composable):
    """ Basic document pipeline element
    """
    def __init__(self):
        Composable.__init__(self)
    
    def __call__(self, kdocs):
        """
        :param kdocs: input generator of :class:`KodexDoc`
        :type kdocs: 
        
        :returns: generator of L{Doc}
        :rtype: (L{Doc}, ...)
        """
        raise NotImplementedError

class OptDocPipelineElmt(DocPipelineElmt, Optionable):
    """ :class:`Optionable` document pipeline element.
    """
    def __init__(self, name):
        DocPipelineElmt.__init__(self)
        Optionable.__init__(self, name)
    
    def __call__(self, kdocs, **kwargs):
        raise NotImplementedError

class DocListPipelineElmt(OptDocPipelineElmt):
    """ Excactly as :class:`OptDocPipelineElmt` except than the :func:`__call__`
    method returns a list and not a generator.
    """
    def __call__(self, kdocs):
        raise NotImplementedError

class GraphPipelineElement(Optionable, Composable):
    """ 
    """
    def __init__(self, name):
        Optionable.__init__(self, name)
        Composable.__init__(self)
