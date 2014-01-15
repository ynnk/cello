#-*- coding:utf-8 -*-
import unittest

from cello.search.base_search import AbstractSearch

class TestAbstractSearch(unittest.TestCase):
    def setUp(self):
        self.abstract_search = AbstractSearch("test_search")

    def test_call(self):
        self.assertRaises(NotImplementedError, self.abstract_search, "test query")


