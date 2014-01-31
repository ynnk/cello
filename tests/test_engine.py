#-*- coding:utf-8 -*-
import unittest

from cello.pipeline import Composable, Optionable
from cello.engine import Block, Cellist

class OptCompExample(Optionable):
    def __init__(self):
        Optionable.__init__(self, "mult_opt")
        self.add_value_option("factor", 5, "multipliation factor")

    def __call__(self, arg, factor=5):
        return arg * factor


class CompCompExample(Composable):
    def __init__(self):
        Composable.__init__(self, name="plus_comp")

    def __call__(self, arg):
        return arg + 2

class TestBlock(unittest.TestCase):
    def setUp(self):
        # setup 4 components
        self.cmpt_mult = OptCompExample()
        self.cmpt_plus = CompCompExample()
        def max20(arg):
            return min(arg, 20)
        self.cmpt_max = Composable(max20)

    def test_append(self):
        block = Block("foo")
        block.append(self.cmpt_mult)
        with self.assertRaises(ValueError):
            block.append(self.cmpt_mult)
        block.append(self.cmpt_plus, default=True)
        block.append(self.cmpt_max)
        
        self.assertListEqual(block.component_names(), ['mult_opt', 'plus_comp', 'max20'])
