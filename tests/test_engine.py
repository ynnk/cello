#-*- coding:utf-8 -*-
import unittest

from cello import CelloError
from cello.types import Numeric
from cello.pipeline import Composable, Optionable
from cello.engine import Block, Engine


class OptCompExample(Optionable):
    def __init__(self):
        super(OptCompExample, self).__init__("mult_opt")
        self.add_option("factor", Numeric(default=5, help="multipliation factor", numtype=int))

    def __call__(self, arg, factor=5):
        return arg * factor


class CompCompExample(Composable):
    def __init__(self):
        Composable.__init__(self, name="plus_comp")

    def __call__(self, arg):
        return arg + 2


class TestBlock(unittest.TestCase):
    def setUp(self):
        # setup 3 components
        self.cmpt_mult = OptCompExample()
        self.cmpt_plus = CompCompExample()
        def max20(arg):
            return min(arg, 20)
        self.cmpt_max = Composable(max20)

    def test_simple(self):
        with self.assertRaises(ValueError):
            block = Block("foo with space")
        block = Block("foo")
        block.append(self.cmpt_mult)
        with self.assertRaises(ValueError):
            block.append(self.cmpt_mult)
        block.append(self.cmpt_plus, default=True)
        block.append(self.cmpt_max)
        
        self.assertListEqual(block.component_names(), ['mult_opt', 'plus_comp', 'max20'])
        self.assertListEqual(block.selected(), ['plus_comp'])
        self.assertEquals(len(block), 3 )
        
        # test select
        with self.assertRaises(ValueError):
            block.select("donotexist")
        block.select("max20")
        self.assertListEqual(block.selected(), ['max20'])

        # test run
        res = block.play(50)
        self.assertEquals(res, 20)
        
        # test select with option
        block.select("mult_opt", options={'factor':21})
        self.assertListEqual(block.selected(), ['mult_opt'])
        # test run
        res = block.play(10)
        self.assertEquals(res, 210)

        # test set options
        #TODO

    def test_multiple(self):
        pass


class TestEngine(unittest.TestCase):
    def setUp(self):
        # setup 3 components
        self.cmpt_mult = OptCompExample()
        self.cmpt_plus = CompCompExample()
        def max20(arg):
            return min(arg, 20)
        self.cmpt_max = Composable(max20)

    def test_empty_engine(self):
        engine = Engine()
        with self.assertRaises(CelloError):
            engine.validate()

    def test_engine(self):
        engine = Engine()
        engine.requires("op1", "op2", "op3")
        self.assertTrue("op1" in engine)
        self.assertTrue("op2" in engine)
        self.assertTrue("op3" in engine)
        self.assertTrue("op4" not in engine)
        with self.assertRaises(CelloError):
            engine.requires("op4")

        engine["op1"].set(self.cmpt_mult)
        
        with self.assertRaises(CelloError):
            engine.validate()

        engine["op2"].append(self.cmpt_mult)
        engine["op2"].append(self.cmpt_plus, default=True)

        engine.set("op3", self.cmpt_mult, self.cmpt_plus, self.cmpt_max)

        engine.validate()

        engine["op1"].select("mult_opt")


