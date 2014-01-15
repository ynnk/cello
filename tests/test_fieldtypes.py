#-*- coding:utf-8 -*-
import unittest
import cello

from cello.schema import *

class TestFieldTypes(unittest.TestCase):
    def setUp(self):
        pass

    def test_numeric(self):
        # Numeric Field (int or float)
        f = Numeric(numtype=float)
        self.assertNotEqual(repr(f), "")
        self.assertRaises(SchemaError, lambda: Numeric(numtype=any) )
        self.assertEqual(f.validate(2.), 2.)  # ok
        self.assertEqual(f.validate(-2.2), -2.2)  # ok
        self.assertEqual(f.validate(-5e0), -5.)  # ok
        self.assertEqual(f.validate(0.), 0.)  # ok
        self.assertRaises(TypeError, f.validate, 1)
        self.assertRaises(TypeError, f.validate, "1")
        self.assertRaises(TypeError, f.validate, "blabla")
        self.assertRaises(TypeError, f.validate, int)

        # unsigned field
        f = Numeric(numtype=int, signed=False)
        self.assertEqual(f.validate(2), 2)  # ok
        self.assertEqual(f.validate(0), 0)  # ok
        self.assertRaises(TypeError, f.validate, -1)

    def test_text(self):
        # setting wrong types 
        self.assertRaises(SchemaError, lambda: Text(texttype=any))
        
        # check unicode
        f_unicode = Text(texttype=unicode)
        self.assertNotEqual(repr(f_unicode), "")
        # good type
        self.assertEqual(f_unicode.validate(u"boé"), u'boé')
        self.assertRaises(TypeError, f_unicode.validate, "boo")
        self.assertRaises(TypeError, f_unicode.validate, 1)

        # check str
        f_str = Text(texttype=str)
        self.assertNotEqual(repr(f_str), "")
        # good type
        self.assertEqual(f_str.validate("boé"), 'boé')
        self.assertRaises(TypeError, f_str.validate, u"boo")
        self.assertRaises(TypeError, f_str.validate, 1)


