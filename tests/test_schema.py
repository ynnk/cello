
#-*- coding:utf-8 -*-
import unittest
import cello
from cello.schema import *

class TestFieldTypes(unittest.TestCase):
    def setUp(self):
        pass

    def test_schema(self):
        # create a schema
        schema = Schema(title= Text(), rank=Numeric() )
        schema = Schema(**{ 'title':Text(), 'rank':Numeric()} )
        
        assert repr(schema) != ""
        # field count 
        assert len(schema) == len(schema._fields) \
                == len(schema['_fields']) == 2
        # list field names
        assert 'title' in schema.field_names()
        assert 'rank' in schema.field_names()
        # test field by name
        assert schema.has_field('title') == True
        assert schema.has_field('boo') == False
        assert schema.title == schema['title']
        
        self.assertRaises(SchemaError, lambda : schema['boo'])
        
        # add new field
        schema.add_field("text", Text())
        assert schema.has_field('text') == True 
        assert len(schema) == 3
        self.assertRaises(SchemaError, schema.add_field, "_text", Text())
        self.assertRaises(SchemaError, schema.add_field, "te xt", Text())
        self.assertRaises(SchemaError, schema.add_field, "text", Text())
        self.assertRaises(SchemaError, schema.add_field, "a", [])
        # Fields iterator
        schema.iter_fields()
        assert 'text' in [ name for name, fieldtype in  schema.iter_fields()]

        # remove field
        # unimplemented
        field_name = "text"
        self.assertRaises(NotImplementedError, schema.remove_field,  field_name )

