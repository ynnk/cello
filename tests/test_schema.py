
#-*- coding:utf-8 -*-
import unittest
import cello
from cello.schema import *

class TestFieldTypes(unittest.TestCase):
    def setUp(self):
        pass

    def test_numeric(self):

        # create a schema
        schema = Schema(title= Text(), rank=Numeric() )
        schema = Schema(**{ 'title':Text(), 'rank':Numeric()} )
        
        # field count 
        assert len(schema) == 2
        # list field names
        assert 'title' in schema.field_names()
        assert 'rank' in schema.field_names()
        # test field by name
        assert schema.has_field('title') == True
        assert schema.has_field('boo') == False
        # add new field
        schema.add_field("text", Text())
        assert schema.has_field('text') == True 
        assert len(schema) == 3

        # Fields iterator
        schema.iter_fields()
