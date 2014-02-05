#-*- coding:utf-8 -*-
import unittest
import cello

from datetime import datetime
from cello.exceptions import ValidationError
from cello.types import GenericType, Numeric, Text, Boolean
from cello.pipeline import Optionable

class TestOptionable(unittest.TestCase):
    maxDiff = None
    
    def setUp(self):
        pass

    def testOptionableName(self):
        comp = Optionable("composant")
        self.assertEqual(comp.name, "composant")
        comp.name = "nouveau_nom"
        self.assertEqual(comp.name, "nouveau_nom")
        with self.assertRaises(ValueError):
            comp.name = "nouveau nom"

    def testAddOption(self):
        comp = Optionable("composant")
        comp.add_option("alpha", Numeric())
        self.assertTrue("alpha" in comp.get_options())
        comp.add_option("beta", Numeric(), hidden=True)
        self.assertFalse("beta" in comp.get_options())

        with self.assertRaises(ValueError):
            comp.add_option("alpha", Numeric())

        with self.assertRaises(ValueError):
            comp.add_option("alpha beta", Numeric())

        # for now, no multiple value
        with self.assertRaises(NotImplementedError):
            comp.add_option("gamma", Numeric(multi=True))
        # for now, no vector value
        with self.assertRaises(NotImplementedError):
            comp.add_option("gamma", Numeric(uniq=True))
        # for now, no attribut value
        with self.assertRaises(NotImplementedError):
            comp.add_option("gamma", Numeric(attrs={"a": Numeric()}))

    def testGetSetOption(self):
        comp = Optionable("composant")
        comp.add_option("alpha", Numeric(
                help="A short description",
                default=2,
                numtype=int,
                min=0,
                max=4,
            )
        )
        comp.add_option("name", Text(
                help="A text ?",
                default=u"chat"
            )
        )
        # value
        self.assertEquals(comp.get_option_value("alpha"), 2)
        with self.assertRaises(ValidationError):
            comp.set_option_value("alpha", -1)
        with self.assertRaises(ValidationError):
            comp.set_option_value("alpha", 3.21)
        comp.set_option_value("alpha", 0)
        self.assertEquals(comp.get_option_value("alpha"), 0)
        comp.set_option_value("alpha", "4", parse=True)
        self.assertEquals(comp.get_option_value("alpha"), 4)
        # value set for text
        self.assertEquals(comp.get_option_value("name"), u"chat")
        comp.set_option_value("name", "chien", parse=True)
        self.assertEquals(comp.get_option_value("name"), u"chien")
        # 
        # default value
        self.assertEquals(comp.get_option_default("alpha"), 2)
        with self.assertRaises(ValidationError):
            comp.change_option_default("alpha", 55)
        with self.assertRaises(ValueError):
            comp.change_option_default("beta", 55)
        comp.change_option_default("alpha", 1)
        self.assertEquals(comp.get_option_default("alpha"), 1)


    def testBooleanOption(self):
        comp = Optionable("composant")
        comp.add_option("filtering", Boolean(default=True, help="whether to activate a funcky filter !"))
        self.assertDictEqual(comp.get_options(), {
            'filtering': {
                    'name': 'filtering',
                    'value': True,
                    'type': 'value',
                    'otype': {
                        'type': 'Boolean',
                        'default': True,
                        'choices': None,
                        'multi': False,
                        'uniq': False,
                        'help': 'whether to activate a funcky filter !',
                    }
                }
        })
        comp.force_option_value("filtering", False)
        self.assertDictEqual(comp.get_options(), {})
        with self.assertRaises(ValueError):
            comp.set_option_value("filtering", True)

    def _testEnumOption(self):
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


