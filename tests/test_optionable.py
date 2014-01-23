#-*- coding:utf-8 -*-
import unittest
import cello

from datetime import datetime
from cello.optionable import AbstractOption
from cello.optionable import GenericOption, EnumOption, BooleanOption
from cello.optionable import Optionable

class TestOptions(unittest.TestCase):

    def setUp(self):
        pass

    def testAbstractOption(self):
        with self.assertRaises(NotImplementedError):
            opt = AbstractOption("optname",
                description="a cool description",
                default="chat"
            )

    def testGenericOption(self):
        opt = GenericOption("optname",
            description="a cool description",
            default="chat"
        )
        # set
        opt.set("chien")
        self.assertEqual(opt.value, "chien")
        self.assertEqual(opt.default, "chat")
        opt.set_from_str("girafe")
        self.assertEqual(opt.value, "girafe")
        self.assertEqual(opt.default, "chat")
        # invalid name
        with self.assertRaises(ValueError):
            opt = GenericOption("opt name",
                description="a cool description",
                default="chat"
            )
        # with (stupid) cast
        opt = GenericOption("optname",
            description="a cool description",
            default="chat",
            cast=lambda val: int(val)*2
        )
        opt.set_from_str("2")
        self.assertEqual(opt.value, 4)
        self.assertDictEqual(opt.as_dict(), {
            'default': 'chat',
            'description': 'a cool description',
            'name': 'optname',
            'type': 'generic',
            'value': 4
        })

    def testEnumOption(self):
        opt = EnumOption("name",
            description="Some enum option",
            enum = [1, 2, 10],
            default=2,
            cast=int
        )
        self.assertEqual(opt.value, 2)
        opt.value = 10
        self.assertEqual(opt.value, 10)
        opt.set(1)
        self.assertEqual(opt.value, 1)
        opt.set(1)
        self.assertEqual(opt.value, 1)
        opt.set_from_str("10")
        self.assertEqual(opt.value, 10)
        with self.assertRaises(ValueError):
            opt.value = 3
        with self.assertRaises(ValueError):
            opt.set_from_str("3")

        opt2 = EnumOption("name",
            description="Some enum option",
            enum = [1, 2, 10],
            cast=int
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
            comp.name = "nouveau nom"

    def testOptionableAddOption(self):
        comp = Optionable("composant")
        comp.add_option(GenericOption("opt", "description"))
        self.assertTrue("opt" in comp.get_options())

    def testBooleanOption(self):
        comp = Optionable("composant")
        comp.add_bool_option("filtering", default=True, description="whether to activate a funcky filter !")
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
        comp.add_enum_option("choix", default="two", enum=["one", "two", "three"], description="make the good choice !")
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


