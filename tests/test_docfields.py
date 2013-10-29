#-*- coding:utf-8 -*-

import unittest
import cello
from cello.schema import *

class TestDocTypes(unittest.TestCase):
    def setUp(self):
        pass

    def test_ValueField(self):
        pass

    def test_ListField(self):
        # affectation
        c = ListField(Numeric())
        [c.append(x) for x in xrange(5)]
        c2 = ListField(Numeric())
        c2.set(xrange(5))
        assert c == c2 == [0, 1, 2, 3, 4]
        # slicing
        c[1:3] = [5,6]
        assert c == [0, 5, 6, 3, 4]
        assert c[3:5] == [3, 4]
        # remove element
        del c[1]
        assert c == [0, 6, 3, 4]

    def test_SetField(self):
        s = SetField(Numeric(default={1,2,3,}))
        self.assertRaises(TypeError, s.add, 'boo' )
        assert s == set([1,2,3])
        s.remove(2)
        assert s == set([1,3])
        s.clear()
        s.add(1)
        assert s == set([1])
        

    def test_VectorField_base(self):
        # declare a schema with term field
        term_field = Text(multi=True, uniq=True, 
                          attrs={'tf':Numeric(default=1),
                                 'positions':Numeric(multi=True),
                                 'score':Numeric(default=17), } )
        schema = Schema( docnum=Numeric(), terms=term_field )
        doc = Doc(schema , docnum=1)
        
        self.assertRaises(SchemaError, lambda : doc.boo )
        assert len(doc.schema) == 2
        terms_tf  = [11,22,33]
        term_keys = ['d', 'f', 'g']
        with self.assertRaises(TypeError): doc.terms = [1,2]
        doc.terms = term_keys # 
        with self.assertRaises(SchemaError): doc.terms.tf = [11,22]
        doc.terms.tf =  terms_tf
        self.assertRaises(SchemaError, lambda: doc.terms.boo)
        assert all([key in doc.terms for key in term_keys])
        assert sorted( list(doc.terms) ) == sorted(doc.terms.keys())\
                == term_keys
        assert ('d' in doc.terms) == doc.terms.has('d') == True
        assert [11,22,33] == doc.terms.tf.values()
    
        # VectorAttr
        assert doc.terms._keys['d'] == 0
        assert type(doc.terms.tf) == VectorAttr 
        assert doc.terms.tf.values() == list(doc.terms.tf) == terms_tf
        doc.terms.score[0] = 99 # setitem
        assert doc.terms['d'].score == 99
        assert doc.terms.tf[1:3] == [22,33]
        
        # VectorItem
        vi = doc.terms['g']
        assert vi._key == 'g'
        assert type(doc.terms['d']) == type(vi) == VectorItem
        assert sorted(vi.attribute_names()) == [ 'positions', 'score', 'tf']
        assert vi.as_dict() == {'tf': 33, 'score':17, 'positions': []}
        vi.score = 14 # setitem
        assert vi['score'] == doc.terms['g'].score \
            == doc.terms.score[2]  == 14

    def test_VectorField_chickens(self):
        return
        from collections import OrderedDict
        text = "i have seen chicken passing the street and i believed "\
             + "how many chicken must pass in the street before you "\
             + "believe"
        # text analyse 
        tokens = text.split(' ')  
        text_terms =  list(OrderedDict.fromkeys(tokens))
        terms_tf = [ tokens.count(k) for k in text_terms ]
        terms_pos = [[i for i, tok in enumerate(tokens) if tok == k ] for k in text_terms]
        # document
        term_field = Text(multi=True, uniq=True, 
                          attrs={'tf':Numeric(default=1),
                                 'positions':Numeric(multi=True), } )
        schema = Schema( docnum=Numeric(), title=Text(), text=Text(), terms=term_field )
        doc = Doc(schema , docnum=1, text=text, title="chickens")
        doc.terms = text_terms
        doc.terms.tf = terms_tf
        doc.terms.positions = terms_pos

        # test         
        key = "chicken"
        assert doc.terms._keys[key] == 3
        assert doc.text[:6] == "i have"
        assert doc.terms[key].tf == 2
        assert doc.terms[key].positions == [3, 12]
        assert doc.terms[key].positions == doc.terms.positions[3] \
            == doc.terms.get_attr_value(key, 'positions')

