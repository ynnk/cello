#-*- coding:utf-8 -*-
import unittest
import cello

from datetime import datetime
from cello.options import AbstractOption, ValueOption, EnumOption
from cello.pipeline import Optionable

class TestOptions(unittest.TestCase):

    def setUp(self):
        pass

    def testAbstractOption(self):
        with self.assertRaises(NotImplementedError):
            opt = AbstractOption("optname", "chat", "a cool description" )

    def testValueOption(self):
        opt = ValueOption("optname", "chat", "a cool description" )
        # set
        opt.set("chien")
        self.assertEqual(opt.value, "chien")
        self.assertEqual(opt.default, "chat")
        opt.set("girafe", parse=True)
        self.assertEqual(opt.value, "girafe")
        self.assertEqual(opt.default, "chat")
        # invalid name
        with self.assertRaises(ValueError):
            opt = ValueOption("opt name", "chat", "a cool description" )
        # with (stupid) cast
        opt = ValueOption("optname", "chat", "a cool description" ,
            parse=lambda val: int(val)*2
        )
        opt.set("2", True)
        self.assertEqual(opt.value, 4)
        self.assertDictEqual(opt.as_dict(), {
            'default': 'chat',
            'description': 'a cool description',
            'name': 'optname',
            'type': 'value',
            'value': 4
        })

    def testEnumOption(self):
        opt = EnumOption("name", 2, 
            "Some enum option",
            [1, 2, 10],
            parse=int
        )
        self.assertEqual(opt.value, 2)
        opt.value = 10
        self.assertEqual(opt.value, 10)
        opt.set(1)
        self.assertEqual(opt.value, 1)
        opt.set(1)
        self.assertEqual(opt.value, 1)
        opt.set("10", True)
        self.assertEqual(opt.value, 10)
        with self.assertRaises(ValueError):
            opt.value = 3
        with self.assertRaises(ValueError):
            opt.set("3", True)

        opt2 = EnumOption("name", None,"Some enum option",
            [1, 2, 10],
            parse=int
        )
        self.assertEqual(opt2.value, 1)
        self.assertEqual(opt2.default, 1)


class TestOptionable(unittest.TestCase):
    def setUp(self):
        pass

    def testOptionableName(self):
        comp = Optionable("composant")
        self.assertEqual(comp.name, "composant")
        comp.name = "nouveau_nom"
        self.assertEqual(comp.name, "nouveau_nom")
        with self.assertRaises(ValueError):
            print "\n\n", ">>>>>>>>>>>>>>>>>>>>>>>>>><", comp.name, "\n\n"
            comp.name = "nouveau nom"
            print "\n\n", ">>>>>>>>>>>>>>>>>>>>>>>>>><", comp.name, "\n\n"

    def testOptionableAddOption(self):
        comp = Optionable("composant")
        comp.add_option(ValueOption("opt", "default", "description"))
        self.assertTrue("opt" in comp.get_options())

    def testBooleanOption(self):
        comp = Optionable("composant")
        comp.add_bool_option("filtering", True, "whether to activate a funcky filter !")
        self.assertDictEqual(comp.get_options(), {
            'filtering': {
                    'default': True,
                    'description': 'whether to activate a funcky filter !',
                    'name': 'filtering',
                    'type': 'boolean',
                    'value': True
                }
        })
        comp.force_option_value("filtering", False)
        self.assertDictEqual(comp.get_options(), {})

    def testEnumOption(self):
        comp = Optionable("composant")
        comp.add_enum_option("choix", "two", "make the good choice !",["one", "two", "three"])
        self.assertEqual(comp.get_default_value("choix"), "two")
        comp.change_option_default("choix", "three")
        comp.set_option_value("choix", "one")
        self.assertDictEqual(comp.get_options(), {
            'choix': {
                    'default': "three",
                    'description': 'make the good choice !',
                    'enum': ["one", "two", "three"],
                    'name': 'choix',
                    'type': 'enum',
                    'value': "one"
                }
        })


