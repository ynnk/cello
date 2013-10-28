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
        self.assertTrue( 2. == f.validate(2.) )  # ok
        self.assertTrue( 2 ==  f.validate(2.) )  # ok 
        try : 
            f.validate('2')  # raise type error
            self.assertTrue(False) # test fail if we are here
        except TypeError as e: print "test passed",  e
    
    def test_text(self):
        # Text Field (unicode or str )
        f = Text(texttype=unicode)
        # good type
        self.assertTrue( u'boé' == f.validate(u"boé"))
        # setting wrong types 
        self.assertRaises(  TypeError,  f.validate, "boo" )
        self.assertRaises(  TypeError,  f.validate, 1 )

