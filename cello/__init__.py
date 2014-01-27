#-*- coding:utf-8 -*-
""":mod:`cello`
===============

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

"""

class CelloError(Exception):
    """Basic cello error"""

class CelloValueError(CelloError, ValueError):
    """Cello value error: one value (attribute) was wrong"""



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

    def __init__(self):
        pass

    def __or__(self, other):
        if not callable(other):
            raise Exception("%r is not composable with %r" % (self, other))
        return Pipeline(self, other)

    def __call__(self, *args):
        raise NotImplementedError


def composable(function):
    """ Make a simple function composable
    """
    cfct = Composable()
    cfct.__call__ = function
    cfct.__doc__ = function.__doc__
    return cfct
