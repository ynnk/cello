
#-*- coding:utf-8 -*-
import unittest
import cello
from cello.schema import *

class TestDocTypes(unittest.TestCase):
    def setUp(self):
        pass

    def test_ValueField(self):
        pass

    def test_ListField(self):
        # affectation
        c = ListField(Numeric())
        [c.append(x) for x in xrange(5)]
        c2 = ListField(Numeric())
        c2.set(xrange(5))
        assert c == c2 == [0, 1, 2, 3, 4]
        # slicing
        c[1:3] = [5,6]
        assert c == [0, 5, 6, 3, 4]
        assert c[3:5] == [3, 4]
        # remove element
        del c[1]
        assert c == [0, 6, 3, 4]

    def test_SetField(self):
        pass

    def test_VectorField(self):
        pass
