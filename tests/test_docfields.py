#-*- coding:utf-8 -*-
import unittest

import cello
from cello.schema import *

class TestDocFields(unittest.TestCase):
    """ test ot DocField subclasses
    """

    def setUp(self):
        pass

    def test_DocField(self):
        df = DocField(Numeric())
        # check is abstract
        self.assertRaises(NotImplementedError, df.get_value)
        # check that 
        self.assertRaises(AssertionError, DocField, 1)

    def test_DocField_FromType(self):
        """ Test DocField.FromType factory
        """
        self.assertIsInstance(DocField.FromType(Numeric()), ValueField)
        self.assertIsInstance(DocField.FromType(Numeric(multi=True)), ListField)
        self.assertIsInstance(DocField.FromType(Numeric(multi=True, uniq=True)), SetField)
        self.assertIsInstance(DocField.FromType(Numeric(uniq=True)), SetField)
        self.assertIsInstance(DocField.FromType(Numeric(attrs={"score": Numeric()})), VectorField)

    def test_ValueField(self):
        vfield = ValueField(Numeric())
        self.assertRaises(TypeError, vfield.set, "op")
        vfield.set(5)
        self.assertEqual(vfield.get_value(), 5)

    def test_SetField(self):
        set_field = SetField(Numeric(default={1,2,3,}))
        # get_value()
        self.assertEqual(set_field.get_value(), set_field)
        # test default default
        self.assertEqual(set_field, set([1,2,3]))
        # remove clear and add
        set_field.remove(2)
        self.assertEqual(set_field, set([1,3]))
        set_field.clear()
        set_field.add(1)
        self.assertEqual(set_field, set([1]))
        # set
        set_field.set([])
        self.assertEqual(set_field, set([]))
        set_field.set((4, 5, 6))
        self.assertEqual(set_field, set([4, 5, 6]))
        # test errors
        self.assertRaises(SchemaError, set_field.set, 'boo')
        self.assertRaises(SchemaError, set_field.set, 57)
        # > test than the failed set didn't change values
        self.assertEqual(set_field, set([4, 5, 6]))
        self.assertRaises(TypeError, set_field.add, 'boo')

    def test_ListField(self):
        # affectation with append
        l_field = ListField(Numeric())
        for x in xrange(5):
            l_field.append(x)
        self.assertEqual(l_field, [0, 1, 2, 3, 4])
        # get_value()
        self.assertEqual(l_field.get_value(), l_field)
        # affectation with set
        l_field2 = ListField(Numeric())
        l_field2.set(xrange(5))
        self.assertEqual(l_field2, list(xrange(5)))
        # affectation fail
        self.assertRaises(SchemaError, l_field2.set, 'boo')
        self.assertRaises(SchemaError, l_field2.set, 57)
        # > test than the failed set didn't change values
        self.assertEqual(l_field2, list(xrange(5)))
        # add and append
        l_field2.add(55)
        self.assertEqual(l_field2, [0, 1, 2, 3, 4, 55])
        self.assertRaises(TypeError, l_field2.append, "e")
        # slicing
        l_field[1:3] = [5,6]
        self.assertEqual(l_field, [0, 5, 6, 3, 4])
        self.assertEqual(l_field[3:5], [3, 4])
        with self.assertRaises(AssertionError):
            l_field[1:3] = [5,6,4]
        # remove element
        del l_field[1]
        self.assertEqual(l_field, [0, 6, 3, 4])


    def test_VectorField_base(self):
        # create a simple field
        v_field = VectorField(Text(
            attrs={
                'tf': Numeric(default=1),
                'positions': Numeric(multi=True),
            }
        ))
        # str and repr
        self.assertNotEqual(str(v_field), "")
        self.assertNotEqual(repr(v_field), "")
        # list attribute names
        self.assertSetEqual(v_field.attribute_names(), set(['tf', 'positions']))
        # get_value()
        self.assertEqual(v_field.get_value(), v_field)
        # set
        v_field.set(["un", "deux", "trois"])
        self.assertTrue(v_field.has("un"))
        self.assertTrue(v_field.has("deux"))
        self.assertTrue(v_field.has("trois"))
        self.assertEqual(len(v_field), 3)
        v_field.set([])
        self.assertEqual(len(v_field), 0)
        # add a key
        v_field.add("chat")
        self.assertEqual(len(v_field), 1)
        self.assertTrue(v_field.has("chat"))
        self.assertTrue("chat" in v_field)
        self.assertFalse("cat" in v_field)
        v_field.add("cat")
        self.assertListEqual(v_field.keys(), ["chat", "cat"])
        # iter
        self.assertListEqual(v_field.keys(), [key for key in v_field])
        
        # test attributes, by direct method call
        self.assertEqual(v_field.get_attr_value("cat", "tf"), 1)
        self.assertEqual(v_field.get_attr_value("cat", "positions"), [])


    def test_VectorField_VectorItem(self):
        # create a simple field
        v_field = VectorField(Text(
            attrs={
                'tf': Numeric(default=1),
                'positions': Numeric(multi=True),
            }
        ))
        v_field.set(["chat", "cat"])
        # test attributes throw *VectorItem*
        self.assertEqual(v_field["cat"].tf, 1)
        v_field["cat"]["tf"] = 80
        self.assertEqual(v_field["cat"].tf, 80)
        v_field["cat"].tf = 15
        self.assertEqual(v_field["cat"].tf, 15)
        self.assertListEqual(v_field["chat"].positions, [])
        v_field["chat"].positions.add(45)
        v_field["chat"].positions.add(4)
        self.assertListEqual(v_field["chat"].positions, [45, 4])
        self.assertSetEqual(v_field["chat"].attribute_names(), set(['tf', 'positions']))
        self.assertDictEqual(v_field["chat"].as_dict(), {'positions': [45, 4], 'tf': 1})


    def test_VectorField_VectorAttr(self):
        # create a simple field
        v_field = VectorField(Text(
            attrs={
                'tf': Numeric(default=1),
                'positions': Numeric(multi=True),
            }
        ))
        v_field.set(["chat", "cat"])
        # test attributes throw *VectorAttr*
        v_field["cat"].tf = 15
        self.assertListEqual(v_field.tf.values(), [1, 15])
        self.assertEqual(v_field.tf[0], 1)         # getitem
        self.assertEqual(v_field.tf[1], 15)
        v_field.tf[1] = 500                        # setitem
        self.assertEqual(v_field.tf[1], 500)
        self.assertListEqual(v_field.tf[0:2], [1, 500]) # getslice
        v_field.tf = [2, 3]
        with self.assertRaises(SchemaError):
            v_field.tf = [2, 3, 45, 4]
        with self.assertRaises(SchemaError):
            var = v_field.cat
        with self.assertRaises(SchemaError):
            v_field.cat = 12
        # add an atribute
        with self.assertRaises(SchemaError):
            v_field.add_attribute("tf", Numeric())
        v_field.add_attribute("score", Numeric(default=0))
        self.assertSetEqual(v_field.attribute_names(), set(['tf', 'positions', 'score']))

#    def test_VectorField_base(self):
#        # declare a schema with term field
#        term_field = Text(attrs={'tf':Numeric(default=1),
#                                 'positions':Numeric(multi=True),
#                                 'score':Numeric(default=17), } )
#        schema = Schema(docnum=Numeric(), terms=term_field)
#        doc = Doc(schema , docnum=1)
#        
#        self.assertRaises(SchemaError, lambda : doc.boo )
#        assert len(doc.schema) == 2
#        terms_tf  = [11, 22, 33]
#        term_keys = ['d', 'f', 'g']
#        with self.assertRaises(TypeError):
#            doc.terms = [1,2]
#        doc.terms = term_keys # 
#        with self.assertRaises(SchemaError):
#            doc.terms.tf = [11,22]
#        doc.terms.tf = terms_tf
#        self.assertRaises(SchemaError, lambda: doc.terms.boo)
#        assert all([key in doc.terms for key in term_keys])
#        assert sorted( list(doc.terms) ) == sorted(doc.terms.keys())\
#                == term_keys
#        assert ('d' in doc.terms) == doc.terms.has('d') == True
#        assert [11,22,33] == doc.terms.tf.values()
#    
#        # VectorAttr
#        assert doc.terms._keys['d'] == 0
#        assert type(doc.terms.tf) == VectorAttr 
#        assert doc.terms.tf.values() == list(doc.terms.tf) == terms_tf
#        doc.terms.score[0] = 99 # setitem
#        assert doc.terms['d'].score == 99
#        assert doc.terms.tf[1:3] == [22,33]
#        
#        # VectorItem
#        vi = doc.terms['g']
#        assert vi._key == 'g'
#        assert type(doc.terms['d']) == type(vi) == VectorItem
#        assert sorted(vi.attribute_names()) == [ 'positions', 'score', 'tf']
#        assert vi.as_dict() == {'tf': 33, 'score':17, 'positions': []}
#        vi.score = 14 # setitem
#        assert vi['score'] == doc.terms['g'].score \
#            == doc.terms.score[2]  == 14

#    def test_VectorField_chickens(self):
#        """ exemple of VectorField usage
#        """
#        from collections import OrderedDict
#        text = "i have seen chicken passing the street and i believed "\
#             + "how many chicken must pass in the street before you "\
#             + "believe"
#        # text analyse 
#        tokens = text.split(' ')
#        text_terms =  list(OrderedDict.fromkeys(tokens))
#        terms_tf = [ tokens.count(k) for k in text_terms ]
#        terms_pos = [[i for i, tok in enumerate(tokens) if tok == k ] for k in text_terms]
#        # define document schema
#        term_field = Text(attrs={'tf':Numeric(default=1),
#                                 'positions':Numeric(multi=True), } )
#        schema = Schema(docnum=Numeric(), title=Text(), text=Text(), terms=term_field)
#        # create a document
#        doc = Doc(schema, docnum=1, text=text, title="chickens")
#        # test text
#        self.assertEqual(doc.text[:6], "i have")
#        self.assertEqual(len(doc.text), len(text))
#        # set terms
#        doc.terms = text_terms
#        # check 
#        # check default values for tf
#        self.assertEqual(doc.terms.tf.values(), [1]*len(text_terms))
#        # set tf and possitions
#        doc.terms.tf = terms_tf
#        doc.terms.positions = terms_pos

#        # test for terms field, for the term "chicken"
#        key = "chicken"
#        self.assertEqual(doc.terms._keys[key], 3)
#        # test tf
#        self.assertEqual(doc.terms[key].tf, 2)
#        # test positions
#        self.assertEqual(doc.terms[key].positions, [3, 12])
#        self.assertEqual(doc.terms[key].positions, doc.terms.positions[3])
#        self.assertEqual(doc.terms[key].positions, doc.terms.get_attr_value(key, 'positions'))

#        doc.boo = Text(default='boo')
#        assert doc.boo == "boo"
