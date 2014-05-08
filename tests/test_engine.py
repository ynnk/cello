#-*- coding:utf-8 -*-
import unittest

from cello.exceptions import CelloError
from cello.types import Numeric
from cello.pipeline import Composable, Optionable
from cello.engine import Block, Engine


class OptProductEx(Optionable):
    def __init__(self):
        super(OptProductEx, self).__init__("mult_opt")
        self.add_option("factor", Numeric(default=5, help="multipliation factor", vtype=int))

    def __call__(self, arg, factor=5):
        return arg * factor


class CompAddTwoExample(Composable):
    def __init__(self):
        Composable.__init__(self, name="plus_comp")

    def __call__(self, arg):
        print arg
        return arg + 2


class TestBlock(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        # setup 3 components
        self.mult_comp = OptProductEx()
        self.plus_comp = CompAddTwoExample()
        def max20(arg):
            return min(arg, 20)
        self.max_comp = Composable(max20)

    def test_comp(self):
        self.assertEquals(self.mult_comp(0), 0)
        self.assertEquals(self.mult_comp(3), 15)
        self.assertEquals(self.plus_comp(3), 5)
        self.assertEquals(self.plus_comp(3), 5)
        self.assertEquals(self.max_comp(3), 3)
        self.assertEquals(self.max_comp(300), 20)

    def test_init(self):
        with self.assertRaises(ValueError):
            block = Block("foo with space")
        with self.assertRaises(ValueError):
            block = Block(24)
        # good name
        block = Block("foo")
        self.assertListEqual(block.component_names(), [])
        self.assertListEqual(block.selected(), [])

    def test_append(self):
        block = Block("foo")
        block.append(self.mult_comp)
        with self.assertRaises(ValueError):
            block.append(self.mult_comp)
        with self.assertRaises(ValueError):
            block.append(lambda x: x**2)
        block.append(self.plus_comp, default=True)
        block.append(self.max_comp)
        self.assertListEqual(block.component_names(), ['mult_opt', 'plus_comp', 'max20'])
        self.assertListEqual(block.selected(), ['plus_comp'])
        self.assertListEqual(block.defaults, ["plus_comp"])
        self.assertEquals(len(block), 3)
        self.assertDictEqual(block.as_dict(), {
            'name': 'foo',
            'args': None,
            'returns': 'foo',
            'multiple': False,
            'required': True,
            'components': [
                {
                    'name': 'mult_opt',
                    'default': False,
                    'options': [
                        {
                            'name': 'factor',
                            'otype': {
                                'choices': None,
                                'default': 5,
                                'help': 'multipliation factor',
                                'max': None,
                                'min': None,
                                'multi': False,
                                'type': 'Numeric',
                                'uniq': False,
                                'vtype': 'int'
                            },
                            'type': 'value',
                            'value': 5
                        }
                    ]
                },
                {
                    'name': 'plus_comp',
                    'default': True,
                    'options': None
                },
                {
                    'name': 'max20',
                    'default': False,
                    'options': None
                }
            ]
        })


    def test_select_and_clear_selection(self):
        ## select should permits to set options of blocks
        block = Block("foo")
        block.set(self.plus_comp, self.mult_comp)
        self.assertEqual(block.selected(), ['plus_comp'])   #first select by default
        self.assertEqual(block['mult_opt'].get_option_value("factor"), 5)  # default comp option value is 5
        # select the second comp
        block.select("mult_opt", options={"factor": 50})
        self.assertEqual(block.selected(), ['mult_opt'])
        self.assertEqual(block['mult_opt'].get_option_value("factor"), 50)

        ## clear selection 
        block.clear_selections()
        # we should be in intial state
        self.assertEqual(block.selected(), ['plus_comp'])   #first select by default
        self.assertEqual(block['mult_opt'].get_option_value("factor"), 5)  # default comp option value is 5

    def test_play(self):
        block = Block("foo")
        block.set(self.mult_comp, self.plus_comp, self.max_comp)
        # first by default
        self.assertListEqual(block.defaults, ["mult_opt"])
        self.assertListEqual(block.selected(), ["mult_opt"])
        self.assertEquals(block.play(3), 15)
        
        block.setup(required=False)
        self.assertListEqual(block.selected(), [])
        self.assertEqual(block.play(3), None)
            
        # default
        block.setup(defaults="plus_comp")
        self.assertListEqual(block.selected(), ["plus_comp"])
        self.assertListEqual(block.defaults, ["plus_comp"])
        self.assertEquals(block.play(3), 5)
        
        # test select
        with self.assertRaises(ValueError):
            block.select("donotexist")
        block.select("max20")
        self.assertListEqual(block.selected(), ['max20'])

        # test run
        self.assertEquals(block.play(3), 3)
        self.assertEquals(block.play(50), 20)

        # test select with option
        block.select("mult_opt", options={'factor':21})
        self.assertListEqual(block.selected(), ['mult_opt'])
        with self.assertRaises(ValueError):
            block.select("max20", options={'factor':21})
        
        # test run
        self.assertEquals(block.play(10), 210)
        self.assertEquals(block.play(0), 0)
        # run a la main
        self.assertEquals(block['mult_opt'](1), 5)

    def test_play_force_option(self):
        comp = OptProductEx()
        comp.force_option_value("factor", 4)
        block = Block("foo")
        block.set(comp)
        self.assertEquals(block.play(10), 40)

    def test_set_options(self):
        block = Block("foo")
        block.set(self.mult_comp, self.plus_comp, self.max_comp)
        # test set options
        block.setup(required=True)
        self.assertTrue(block.required)
        self.assertFalse(block.hidden)
        self.assertFalse(block.multiple)
        block.setup(required=False)
        self.assertFalse(block.required)
        block.setup(required=True, multiple=True, hidden=True)
        self.assertTrue(block.required)
        self.assertTrue(block.hidden)
        self.assertTrue(block.multiple)
        ## test input output names
        self.assertEquals(block.in_name, None)
        self.assertEquals(block.out_name, "foo")
        block.setup(in_name="doclist", out_name="graph")
        self.assertEquals(block.in_name, "doclist")
        self.assertEquals(block.out_name, "graph")


    def test_multiple(self):
        pass


class TestEngine(unittest.TestCase):
    maxDiff = None
    
    def setUp(self):
        # setup 3 components
        self.mult_comp = OptProductEx()
        self.plus_comp = CompAddTwoExample()
        def max20(arg):
            return min(arg, 20)
        self.max_comp = Composable(max20)

    def test_empty_engine(self):
        engine = Engine()
        with self.assertRaises(CelloError):
            engine.validate()
        with self.assertRaises(ValueError):
            engine.requires()
        with self.assertRaises(ValueError):
            engine.requires("foo", "foo")

    def test_engine_default_pipeline(self):
        engine = Engine("op1", "op2", "op3")

        self.assertEqual(len(engine), 3)
        self.assertTrue("op1" in engine)
        self.assertTrue("op2" in engine)
        self.assertTrue("op3" in engine)
        
        self.assertFalse("op4" in engine)
        with self.assertRaises(CelloError):
            engine.requires("op4")

        engine.op1.set(self.mult_comp)
        with self.assertRaises(ValueError):
            engine.op4.set(self.mult_comp)
        with self.assertRaises(ValueError):
            engine["op4"].set(self.mult_comp)
        with self.assertRaises(ValueError):
            engine.set("op4", self.mult_comp)
        
        with self.assertRaises(CelloError):
            engine.validate()

        engine.op1.select("mult_opt")

        engine.op2.append(self.mult_comp)
        engine.op2.append(self.plus_comp, default=True)
        self.assertFalse(engine.op2.multiple)
        self.assertEqual(engine.op2.selected(), ["plus_comp"])
        self.assertEqual(engine.op2.play(10), 12)
        

        engine.set("op3", self.mult_comp, self.plus_comp, self.max_comp)
        engine.validate()

        res = engine.play(3) # mult * 5 | + 2 | mult
        self.assertEquals(res['input'], 3)
        self.assertEquals(res['op1'], 3*5)
        self.assertEquals(res['op2'], 3*5+2)
        self.assertEquals(res['op3'], (3*5+2)*5)

    def test_configure_errors(self):
        engine = Engine("op1", "op2", "op3")
        engine.set("op1", self.mult_comp, self.plus_comp, self.max_comp)
        engine.set("op2", self.plus_comp, self.mult_comp, self.max_comp)
        engine.op2.setup(hidden=True)
        engine.set("op3", self.mult_comp, self.plus_comp, self.max_comp)

        with self.assertRaises(ValueError): # op2 hidden it can be configured
            engine.configure({
                'op2':{'name': 'max20'}
            })
        with self.assertRaises(ValueError): # 'maxmax' doesn't exist
            engine.configure({
                'op3':{'name': 'maxmax'}
            })
        with self.assertRaises(ValueError): # error in op1 format
            engine.configure({
                'op1':{'namss': 'mult'}
            })
        with self.assertRaises(ValueError): # block doesn't exist
            engine.configure({
                'op5':{'name': 'max20'}
            })
        with self.assertRaises(ValueError): # block required !
            engine.configure({
                'op1':[]
            })
        with self.assertRaises(ValueError): # block not multi !
            engine.configure({
                'op1':[{'name': 'max20'}, {'name': 'plus_comp'}]
            })

    def test_configure(self):
        engine = Engine("op1", "op2")
        engine.set("op1", self.mult_comp, self.plus_comp, self.max_comp)
        engine.set("op2", self.plus_comp)

        engine.configure({
            'op1':{
                'name': 'mult_opt',
                'options': {
                    'factor': '10'
                }
            },
            'op2':{
                'name': 'plus_comp'
            }
        })
        self.assertEqual(engine.op1.selected(), ["mult_opt"])
        self.assertEqual(engine.op1["mult_opt"].get_option_value("factor"), 10)
        self.assertEqual(engine.op1.play(5), 50)
        
        self.assertDictEqual(engine.as_dict(), {
            'args': None,
            'blocks': [
                {
                    'components': [
                        {
                            'default': True,
                            'name': 'mult_opt',
                            'options': [
                                {
                                    'name': 'factor',
                                    'type': 'value',
                                    'value': 10,
                                    'otype': {
                                        'choices': None,
                                        'default': 5,
                                        'help': 'multipliation factor',
                                        'max': None,
                                        'min': None,
                                        'multi': False,
                                        'type': 'Numeric',
                                        'uniq': False,
                                        'vtype': 'int'
                                    }
                               }
                            ]
                        },
                        {
                            'name': 'plus_comp',
                            'default': False,
                            'options': None
                        },
                        {
                            'name': 'max20',
                            'default': False,
                            'options': None
                        }
                 ],
                 'args': None,
                 'multiple': False,
                 'name': 'op1',
                 'returns': 'op1',
                 'required': True
            },
            {
                'components': [
                     {
                         'name': 'plus_comp',
                         'default': True,
                         'options': None
                     }
                 ],
                 'args': None,
                 'multiple': False,
                 'name': 'op2',
                 'returns': 'op2',
                 'required': True
             }
        ]
    })

    def test_engine_named_inout_pipeline(self):
        engine = Engine("op1", "op2", "op3")
        
        engine.op1.set(self.mult_comp)
        engine.op1.setup(in_name="in1", out_name="out1")

        engine.op2.set(self.plus_comp)
        engine.op2.setup(in_name="out1", out_name="out2")

        engine.op3.set(self.mult_comp)
        engine.op3.setup(in_name="out2", out_name="out3")

        res = engine.play(3) # mult * 5 | + 2 | mult
        self.assertEquals(res['in1'], 3)
        self.assertEquals(res['out1'], 3*5)
        self.assertEquals(res['out2'], 3*5+2)
        self.assertEquals(res['out3'], (3*5+2)*5)

    def test_engine_named_inout_pipeline(self):
        engine = Engine("op1", "op2", "op3")
        
        engine.op1.set(self.mult_comp)
        engine.op1.setup(in_name="in1", out_name="out1")

        engine.op2.set(self.plus_comp)
        engine.op2.setup(in_name="out1", out_name="out2")

        engine.op3.set(self.mult_comp)
        engine.op3.setup(in_name="out1", out_name="out3")

        res = engine.play(3) # mult * 5 | + 2 | mult
        self.assertEquals(res['in1'], 3)
        self.assertEquals(res['out1'], 3*5)
        self.assertEquals(res['out2'], 3*5+2)
        self.assertEquals(res['out3'], 3*5*5)

    def test_engine_named_inout_error(self):
        engine = Engine("op1", "op2", "op3")

        engine.op1.set(self.mult_comp)
        engine.op1.setup(in_name="in1", out_name="out1")

        engine.op2.set(self.plus_comp)
        engine.op2.setup(in_name="out_not_exist", out_name="out2")

        engine.op3.set(self.mult_comp)
        engine.op3.setup(in_name="out1", out_name="out3")

        with self.assertRaises(CelloError):
            engine.validate()
        
        engine.op2.setup(in_name="in1", out_name="out2")
        engine.validate()

        engine.op2.setup(required=False)
        engine.op3.setup(in_name="out2")
        with self.assertRaises(CelloError):
            engine.validate()


