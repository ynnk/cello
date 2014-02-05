#-*- coding:utf-8 -*-
""" :mod:`cello.schema`
======================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

inheritance diagrams
--------------------

.. inheritance-diagram:: Schema 

.. inheritance-diagram:: Doc
.. inheritance-diagram:: DocField VectorField ValueField SetField

Class
-----

"""
from cello.types import GenericType, Numeric
from cello.exceptions import SchemaError


class Schema(object):
    """ Schema definition for docs <Doc>
    class inspired from Matt Chaput's Whoosh.  
    
    Creating a schema :
    >>> from cello.types import Text, Numeric
    >>> schema = Schema(title=Text(), score=Numeric())
    >>> schema.field_names()
    ['score', 'title']
    """
    
    def __init__(self, **fields):
        self._fields = {}
        # Create fields
        for name, fieldtype in fields.iteritems():
            self.add_field(name, fieldtype)
    
    def copy(self):
        """ Returns a copy of the schema
        """
        return Schema(**self._fields)
    
    def add_field(self, name, field):
        """ Add a named field to the schema.
        
        :param name: name of the new field
        :type name: str
        :param field:  type instance for the field 
        """
        # testing names 
        if name.startswith("_"):
            raise SchemaError("Field names cannot start with an underscore.")
        if " " in name:
            raise SchemaError("Field names cannot contain spaces.")
        if name in self._fields:
            raise SchemaError("Schema already has a field named '%s'" % name)
        if not isinstance(field, GenericType):
            raise SchemaError("Wrong type in schema for field: %s, %s is not a GenericType" % (name, field))
        self._fields[name] = field
    
    def remove_field(self, field_name):
        raise NotImplementedError()
    
    def iter_fields(self):
        return self._fields.iteritems()
    
    def field_names(self):
        return self._fields.keys()
    
    def has_field(self, name):
        return self.__contains__(name)
    
    def __iter__(self):
        return self._fields.iterkeys()
        
    def __contains__(self, name):
        return name in self._fields    
    
    def __len__(self): 
        """ returns field count in schema """
        return len(self._fields)
    
    def __getattr__(self, name): 
        return self.__getitem__(name)
        
    def __getitem__(self, name): 
        if name == '_fields': 
            return self._fields
        elif name in self._fields:
            return self._fields[name]
        else : 
            raise SchemaError("Field '%s' does not exist in Schema (%s)" % (name, self.field_names()))
    
    def __repr__(self):
        fields_repr = "\n".join(
            " * %s: %s" % (key, value)
            for key, value in self._fields.iteritems()
        )
        return "<%s:\n%s\n>" % (self.__class__.__name__, fields_repr)

"""
Document fields implementations internal use only
"""
class DocField(object):
    """ Abstract document field
    
    Theses objects are containers of document's data.
    """
    def __init__(self, ftype):
        """
        :param ftype: the type for the field
        :type ftype: subclass of :class:`.GenericType` 
        """
        assert isinstance(ftype, GenericType)
        self._ftype = ftype

    def get_value(self):
        """ return the value of the field.
        """
        raise NotImplementedError

    @staticmethod
    def FromType(ftype):
        """ DocField subclasses factory, creates a convenient field to store
        data from a given Type.

        attribute precedence :
        
        * ``|attrs| > 0`` (``multi`` and ``uniq`` are implicit) => VectorField
        * ``uniq`` (``multi`` is implicit) => SetField 
        * ``multi`` and ``not uniq`` => ListField 
        * ``not multi`` => ValueField
        
        :param ftype: the desired type of field
        :type ftype: subclass of :class:`.GenericType`
        """
        if ftype.attrs is not None and len(ftype.attrs):
            return VectorField(ftype)
        elif ftype.uniq:
            return SetField(ftype)
        elif ftype.multi:
            return ListField(ftype)
        else:
            return ValueField(ftype)


class ValueField(DocField):
    """ Stores only one value
    """
    def __init__(self, fieldtype):
        DocField.__init__(self, fieldtype)
        self.value = fieldtype.default
    
    def get_value(self): 
        return self.value
    
    def set(self, value): 
        self.value = self._ftype.validate(value)


class SetField(DocField, set):
    """ Document field for a set of values (i.e. the fieldtype is "multi" and "uniq")
    
    usage example:
    
    >>> from cello.types import Text
    >>> schema = Schema(tags=Text(multi=True, uniq=True))
    >>> doc = Doc(schema, docnum=42)
    >>> doc.tags.add(u'boo')
    >>> doc.tags.add(u'foo')
    >>> len(doc.tags)
    2
    """
    #XXX; maybe it can use collections.MutableSet
    # http://docs.python.org/2/library/collections.html#collections-abstract-base-classes
    def __init__(self, fieldtype):
        DocField.__init__(self, fieldtype)
        self.set(fieldtype.default or [])

    def add(self, value):
        set.add(self, self._ftype.validate(value))

    def get_value(self):
        # the field is a set itself...
        return self

    def set(self, values):
        if not hasattr(values, '__iter__'):
            raise SchemaError("Wrong value '%s' for field '%s'" % (values, self._ftype))
        # check data are valid before deleting the data
        # prevents losing data if wrong type is passed
        items = set(self._ftype.validate(v) for v in values)
        self.clear()
        self.update(items)


class ListField(DocField, list):
    """ list container for non-uniq field """
    #XXX; maybe it can use collections.MutableSequence
    # http://docs.python.org/2/library/collections.html#collections-abstract-base-classes
    def __init__(self, fieldtype):
        DocField.__init__(self, fieldtype)

    def add(self, value):
        """ Adds a value to the list (as append).
        convenience method, to have the same signature than :class:`.SetField` and :class:`.VectorField`"""
        self.append(value)

    def get_value(self):
        # the field is a list itself...
        return self

    def append(self, value):
        list.append(self, self._ftype.validate(value))

    def set(self, values):
        """ set new values (values have to be iterable)
        """
        if not hasattr(values, '__iter__'):
            raise SchemaError("Wrong value '%s' for field '%s'" % (values, self._ftype))
        # check data are valid before deleting the data
        # prevents losing data if wrong type is passed
        values = [self._ftype.validate(v) for v in values]
        del self[:]
        for v in values:
            list.append(self, v)

    def __setitem__(self, idx, value):
        list.__setitem__(self, idx, self._ftype.validate(value) )

    def __setslice__(self, i, j, values):
        assert j-i == len(values), "given data don't fit slice size (%s-%s != %s)" % (i, j, len(values))
        for x, xi in enumerate(xrange(i, j)):
            self[xi] = values[x]


class VectorField(DocField):
    """ 
    usage: 

    >>> from cello.types import Text, Numeric
    >>> doc = Doc(Schema(), docnum=1)
    >>> doc.terms = Text(multi=True, uniq=True, attrs={'tf': Numeric()}) 
    >>> doc.terms.add('chat') # vectoritem
    >>> doc.terms['chat'].tf = 12
    >>> doc.terms['chat'].tf
    12
    >>> doc['boo'] = Text(default="boo")
    >>> doc.boo
    'boo'
    >>> doc.terms.add_attribute('foo', Numeric(default=42))
    >>> doc.terms.foo.values()
    [42]
    """
    def __init__(self, ftype):
        DocField.__init__(self, ftype)
        self._attrs =  {} # attr_name : [DocField, ]    
        self._keys = {}   # key: idx
        self.clear_attributes()

    def attribute_names(self):
        """ returns the names of field's data attributes
        
        :return: set of attribute names
        :rtype: frozenset
        """
        return frozenset(self._attrs.keys())

    def add_attribute(self, name, ftype):
        """ Add a data attribute.
        Note that the field type will be modified !
        
        :param name: name of the new attribute
        :type name: str
        :param ftype: type of the new attribute
        :type ftype: subclass of :class:`.GenericType`
        """
        if name in self._ftype.attrs:
            raise SchemaError("Vector has a attribute named '%s'" % name)
        # add the attr to the underlying GenericType
        self._ftype.attrs[name] = ftype
        # add the attr it self
        self._attrs[name] = [DocField.FromType(ftype) for _ in xrange(len(self))]

    def clear_attributes(self):
        """ removes all attributes
        """
        self._attrs = {} # removes all attr
        for name, attr_field in self._ftype.attrs.iteritems():
            self._attrs[name] = []

    def __repr__(self):
        return "<%s:%s>" % ( self.__class__.__name__, self._attrs.keys())

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        """ Vector keys count """
        return len(self._keys)

    def __iter__(self):
        return self._keys.iterkeys()

    def keys(self): 
        """ list of keys in the vector """
        return self._keys.keys()

    def __contains__(self, key):
        """ returns True if the vector has the specified key
        """
        return self.has(key)

    def has(self, key): 
        return key in self._keys

    def __getitem__(self, key):
        return VectorItem(self, key)

    def get_value(self): 
        """ from DocField, convenient method """
        return self

    def as_dict(self):
        #XXX: TODO ?
        d = {}
        for k in self._keys():
            for attr in self._attrs:
                pass

    def add(self, key):
        """ Add a key to the vector, do nothing if the key is already present """
        if not self.has(key):
            self._keys[key] = len(self._keys)
            #append to attributes
            for name, attr_type in self._ftype.attrs.iteritems():
                self._attrs[name].append(DocField.FromType(attr_type))

    def set(self, keys):
        """ Set new keys.
        
        Mind this will clear all attributes and keys before adding new keys
        doc.terms = ['a', 'b']
        """
        # clear keys and atributes
        self._keys = {}
        self.clear_attributes()
        _validate = self._ftype.validate 
        for key in keys:
            self.add(_validate(key))

    def get_attr_value(self, key, attr):
        """ returns the value of a given attribute for a given key
        """
        idx = self._keys[key]
        return self._attrs[attr][idx].get_value()

    def set_attr_value(self, key, attr, value):
        """ set the value of a given attribute for a given key
        """
        idx = self._keys[key]
        self._attrs[attr][idx].set(value)

    def __getattr__(self, name):
        """
        :param name: attribute name
        """
        if name in self._attrs: 
            return VectorAttr(self, name)
        else:
            raise SchemaError("No such attribute '%s' in Vector" % name)

    def __setattr__(self, name, values):
        """
        doc.terms.x = [1,2]
        """
        if name.startswith('_'):
            DocField.__setattr__(self, name, values)
            #self.__dict__[attr] = value
        elif self.__dict__['_attrs'].has_key(name):
            if len(values) != len(self):
                raise SchemaError('Wrong size : |values| (=%s) should be equals to |keys| (=%s) ' \
                        % (len(values), len(self)))
            _attr = [DocField.FromType(self._ftype.attrs[name]) for _ in xrange(len(values)) ]
            for idx, val in enumerate(values):
                _attr[idx].set(val)
            self._attrs[name] = _attr
        else:
            raise SchemaError("No such attribute '%s' in Vector" % name)

class VectorAttr(object):
    """ Internal class used to acces an attribute of a :class:`.VectorField`
    """
    #XXX; maybe it can be a "list" or a collections.Sequence
    # http://docs.python.org/2/library/collections.html#collections-abstract-base-classes

    def __init__(self, vector, attr):
        self.vector = vector
        self.attr = attr

    def __iter__(self):
        vector, attr = self.vector, self.attr
        for attr_value in vector._attrs[attr]:
            yield attr_value.get_value()

    def values(self):
        # should we use doc.terms.tf() ??? 
        return list(self)

    def __getslice__(self, i, j):
        vector, attr = self.vector, self.attr
        return [ x.get_value() for x in vector._attrs[attr][i:j] ]

    def __getitem__(self, idx):
        return self.vector._attrs[self.attr][idx].get_value()

    def __setitem__(self, idx, value):
        self.vector._attrs[self.attr][idx].set(value)


class VectorItem(object):
    """ Internal class used to acces an item (= a value) of a :class:`.VectorField`
    """
    def __init__(self, vector, key):
        self._vector = vector
        self._key = key

    def attribute_names(self):
        return self._vector.attribute_names()

    def as_dict(self):
        return { k: self[k] for k in self.attribute_names() }
        
    def __getattr__(self, attr_name):
        return self._vector.get_attr_value(self._key, attr_name)

    def __setitem__(self, attr, value):
        setattr(self, attr, value)

    def __setattr__(self, attr, value):
        if not(attr.startswith('_')):
            self._vector.set_attr_value(self._key, attr, value)
        else: 
            object.__setattr__(self, attr, value)

    def __getitem__(self, name ):
        return getattr(self, name)


class Doc(dict):
    """ Cello Document object
    
    Here is an exemple of document construction from a simple text.
    First we define document's schema:
    
    >>> from cello.types import Text, Numeric
    >>> term_field = Text(attrs={'tf':Numeric(default=1), 'positions':Numeric(multi=True)})
    >>> schema = Schema(docnum=Numeric(), text=Text(), terms=term_field)
    
    
    Now it is how one can build a document from this simple text:
    
    >>> text = u\"\"\"i have seen chicken passing the street and i believed
    ... how many chicken must pass in the street before you
    ... believe\"\"\"
    
    Then we can create the document:

    >>> doc = Doc(schema, docnum=1, text=unicode(text))
    >>> doc.text[:6]
    u'i have'
    >>> len(doc.text)
    113
    
    Then we can analyse the text:

    >>> tokens = text.split(' ')
    >>> from collections import OrderedDict
    >>> text_terms =  list(OrderedDict.fromkeys(tokens))
    >>> terms_tf = [ tokens.count(k) for k in text_terms ]
    >>> terms_pos = [[i for i, tok in enumerate(tokens) if tok == k ] for k in text_terms]

    .. note:: there is better way to analyse a text with Cello !
    
    and one can store the result in the field "terms":
    
    >>> doc.terms = text_terms
    >>> doc.terms.tf.values()   # here we got only '1', it's the default value
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    >>> doc.terms.tf = terms_tf
    >>> doc.terms.positions = terms_pos

    One can access the information, for example, for the term "chicken":
    
    >>> key = "chicken"
    >>> doc.terms[key].tf
    2
    >>> doc.terms[key].positions
    [3, 11]
    >>> doc.terms.get_attr_value(key, 'positions')
    [3, 11]
    >>> doc.terms._keys[key]
    3
    >>> doc.terms.positions[3]
    [3, 11]
    
    
    #TODO: docnum doit etre un field spécial
    #TODO: la valeur de docnum doit être passer en argument de __init__
    """
    
    def __repr__(self):
        return "<%s %s %s>" % (self.__class__.__name__, self.schema,
            { k: self[k] for k in self.schema.field_names() }
        )

    def __init__(self, schema, **data):
        """ Document initialisation
        
        .. warning:: a copy of the given schema is stored in the document
        
        Simple exemple:
        
        >>> from cello.types import Text, Numeric
        >>> doc = Doc(Schema(titre=Text()), titre=u'Un titre')
        """
        dict.__init__(self)
        # set the document schema
        object.__setattr__(self, 'schema', schema.copy())
        #    i.e. "self.schema = schema.copy()" but this is forbiden
        # Doc should always have a docnum !
        if 'docnum' not in self.schema:
            self.add_field('docnum', Numeric())
        #elf.docnum = data['docnum'] if "docnum" in data else 0# or fail
        # fields value(s)
        for key, ftype in schema.iter_fields():
            self[key] = DocField.FromType(ftype)
            if data.has_key(key):
                # explicit getitem needed for ValueField
                dict.__getitem__(self, key).set(data[key])

    def add_field(self, name, ftype, docfield=None):
        """ Add a field to the document (and to the underlying schema)
        
        :param name: name of the new field
        :type name: str
        :param ftype: type of the new field
        :type ftype: subclass of :class:`.GenericType`
        """
        self.schema.add_field(name, ftype)
        self[name] = docfield or DocField.FromType(ftype)

    def __getitem__(self, name):
        return getattr(self, name)

    def __getattr__(self, name):
        # this is called if there is no 'real' object attribute of the given name
        # http://docs.python.org/2/reference/datamodel.html#object.__getattr__s
        try:
            field = dict.__getitem__(self, name)
            if type(field) == ValueField:
                return field.get_value()
            else:
                return field
        except KeyError as err:
            raise SchemaError("'%s' is not a document field (existing attributes are: %s)" % (err, self.keys()))

    def __setitem__(self,name, value):
        setattr(self, name, value)

    def __setattr__(self, name, value):
        if name == 'schema':
            raise SchemaError("Impossible to replace the schema of a document")
        elif isinstance(value, GenericType):
            # the value is a "Type" => creation of a new attribute
            self.add_field(name, value)
        elif isinstance(value, DocField):
            # the new value is a 'Field', we just add it
            dict.__setitem__(self, name, value)
        elif name in self.schema.field_names():
            # set a value to one field
            dict.__getitem__(self, name).set(value)
        else:
            raise SchemaError("'%s' is not a document field (existing attributes are: %s)" % (name, self.keys()))

    def as_dict(self, exclude=[]):
        """ returns a dictionary representation of the document
        """
        doc = { key: getattr(self, key) for key in self.schema \
                        if not key.startswith("_") and key not in exclude }
        return doc 

