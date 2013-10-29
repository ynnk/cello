#-*- coding:utf-8 -*-
""" :mod:`cello.schema`
======================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}


TODO:

schema ds doc doit pas etre une key
DocField => DocContainer 
rename _field => _ftype

clean notebook in progress
"""

#TODO: précissé le docstr, c'est quoi quand on a cette erreur exactement ?
class SchemaError(Exception):
    """ Error
    """
    pass


class Schema(object):
    """ Schema definition for docs <Doc>
    class inspired from Matt Chaput's Whoosh.  
    
    Creating a schema :
        >>> schema = Schema(**{ 'title': Text(), 'score':Numeric(numtype=int, multi=True) })
        >>> # or
        >>> schema = Schema( title=Text(), score=Numeric() )
        >>> schema.field_names()
        ['score', 'title']
    """
    
    def __init__(self, **fields):
        self._fields = {}
        # Create fields
        for name, fieldtype in fields.iteritems():
            self.add_field(name, fieldtype)
    
    def add_field(self, name, field):
        """ Add a named field to the schema.
        
        :param name: name of the new field
        :param field:  FieldType instance for the field 
        """
        # testing names 
        if name.startswith("_"):
            raise SchemaError("Field names cannot start with an underscore.")
        if " " in name:
            raise SchemaError("Field names cannot contain spaces.")
        
        if name in self._fields:
            raise SchemaError("Schema already has a field named '%s'" % name)
        if not isinstance(field, FieldType):
            raise SchemaError("Wrong FieldType in schema for field: %s, %s is not a FieldType" % (name, field))
        #TODO: est-ce que ces quatres erreurs ne sont pas plutot des ValueError ? 
        # (erreur sur les valeurs)
        self._fields[name] = field
    
    def remove_field(self, field_name):
        raise NotImplementedError()
    
    def iter_fields(self):
        return self._fields.iteritems()
    
    def field_names(self):
        return self._fields.keys()
    
    def has_field(self, name):
        return self.__contains__(name)
    
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
        return "<%s: %s>" % (self.__class__.__name__, self._fields)

#XXX: est-ce que ca marche ces docstring "volante" ?? jms vu ca...
"""
   * FieldTypes to declare in schemas 
"""
class FieldType(object):
    """ Abstract FieldType
    """
    def __init__(self, multi=False, uniq=False, default=None, attrs=None):
        """
        :param multi: field is a list or a set
        :param uniq: wether the values are unique, only apply if multi == True
        :param default: default value for the field
        :param attrs: field attributes dict of {name: FieldType()}
        """
        self.multi = multi 
        self.uniq = uniq
        self.default = default
        self.attrs = attrs
        # TODO
        # self.sorted = sorted
        # self.required = required  # test ds Doc ds le constructeur
        # self.choices = 

    def __repr__(self):
        temp = "%s(multi=%s, uniq=%s, default=%s, attrs=%s)"
        return temp % (self.__class__.__name__,
                    self.multi, self.uniq, self.default, self.attrs )
    
    #TODO: est-ce que validate permet le cast, comme c'est pour le moment ? ou return juste True/False ?
    def validate(self, value):
        """ check if a value is correct (type).
        Should be override.
        
        This method should:
        * raise :class:`TypeError` if the type 
        * return the given value, that may have been converted
        """
        return value


class Numeric(FieldType):
    """ Numerical type (int or float)
    """
    _types_ = [int, float]
    
    def __init__(self, numtype=int, **field_options):
        """
        :param numtype: the type of numbers that can be stored in this field,
            either ``int``, ``float``. 
        """
        FieldType.__init__(self, **field_options)
        if numtype not in Numeric._types_  : 
            raise SchemaError('Wrong type for Numeric %s' % Numeric._types_ )
        self.numtype = numtype
    
    def validate(self, value):
        if not isinstance(value, self.numtype):
            raise TypeError("Wrong type: get '%s' but '%s' expected" % (type(value), self.numtype))
        return value


class Text(FieldType):
    """ Text type (str or unicode)
    """
    # valid type for text
    _types_ = [str, unicode]
    
    def __init__(self, texttype=str, **field_options):
        FieldType.__init__(self, **field_options)
        if texttype not in Text._types_:
            raise SchemaError('Wrong type for Text %s' % Numeric._types_ )
        self.texttype = texttype
    
    def validate(self, value):
        if not isinstance(value, self.texttype):
            raise TypeError("Wrong type: get '%s' but '%s' expected" % (type(value), self.texttype))
        return value


# Add more FiledType here
# ...

"""
Document fields implementations interna use only
"""
class DocField(object):
    """ Abstract document field
    
    Theses objects are containers of document's data.
    """
    def __init__(self, fieldtype):
        """
        :param fieldtype: the type for the field
        :type fieldtype: one of the :class:`FieldType` subclass
        """
        self._field = fieldtype
    
    def get_value(self):
        return self


class ValueField(DocField):
    """
    Store only one value of FieldType
    """
    def __init__(self, fieldtype):
        DocField.__init__(self, fieldtype)
        self.value = fieldtype.default
    
    def get_value(self): 
        return self.value
    
    def set(self, value): 
        self.value = self._field.validate(value)


class SetField(DocField, set ):
    """ Document field for a set of values (i.e. the fieldtype is "multi" and "uniq")
    
    usage example:
    >>> schema = Schema(tags=Text(multi=True, uniq=True))
    >>> doc = Doc(schema, docnum=42)
    >>> doc.tags.add('boo')
    >>> doc.tags.add('foo')
    >>> len(doc.tags)
    2
    
    """
    def __init__(self, fieldtype):
        DocField.__init__(self, fieldtype)
        self.set(fieldtype.default or [])
    
    def add(self, value):
        set.add(self, self._field.validate(value))

    def set(self, values):
        # TODO values should be iterable 
        if type(values) in [set, list]:
            items = set([ self._field.validate(v) for v in values ])
            self.clear()
            self.update(items)
        else:
            raise SchemaError("Wrong value '%s' for field '%s'" % (values, self._field))


class ListField(DocField, list):
    """ list container for non uniq field  """
    def __init__(self, fieldtype):
        DocField.__init__(self, fieldtype)
    
    def add(self, value):
        """ XXX convenience mthd keep it ? never called in tests"""
        self.append(value)
    
    def append(self, value ):
        list.append(self, self._field.validate(value))
        
    def set(self, iterable):
        """ set new values (values have to be iterable )     
        """
        # check data are valid before deleting the data
        # prevents losing data if wrong type is passed
        values = [ self._field.validate(v) for v in iterable ]
        del self[:]
        for v in values: list.append(self ,v)
    
    def __setitem__(self, idx, value):
        list.__setitem__(self, idx, self._field.validate(value) )
        
    def __setslice__(self, i, j, values):
        assert j-i == len(values), "%s %s %s "% (i, j , len(values))
        for x, xi in enumerate(xrange(i,j)):
            self[xi] = values[x]
            


class VectorField(DocField):
    """
        usage: 
            doc.terms # vector
            doc.terms['chat'] # vectoritem
            doc.terms['chat'].tf = 12
            
    """
    def __init__(self, fieldtype):
        DocField.__init__(self, fieldtype)
        self._attrs =  {} # attr_name : [DocField, ]
        self._keys = {}   # key: idx
    
    def attribute_names(self):
        return self._attrs.keys()
    
    def clear_attributes(self):
        self._attrs = {} # removes all attr
        for name, attr_field in self._field.attrs.iteritems():
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
        return key in self._keys
        
    def has(self, key): 
        return self.__contains__(key)

    def __getitem__(self, key):
        return VectorItem(self, key )
    
    def get_value(self): 
        """ from DocField, convenient method """
        return self

    def add(self, key):
        """ Add a key to the vector """
        if not self.has(key):
            self._keys[key] = len(self._keys)
        #append to attributes
        for name, attr_field  in self._field.attrs.iteritems():
            self._attrs[name].append(create_field(attr_field))
        
    def set(self, keys):
        """ set new keys 
            Mind this will clear all attributes and keys before adding new keys
            doc.terms = ['a', 'b']
        """
        # XXX clear keys and atributes
        self._keys = {}
        _field = self._field 
        self.clear_attributes()
        for key in keys:
            if not self.has(key):
                self.add(_field.validate(key))
                
    def get_attr_value(self, key , attr):
        idx = self._keys[key]
        return self._attrs[attr][idx].get_value()
    
    def set_attr_value(self, key, attr, value):
        idx = self._keys[key]
        self._attrs[attr][idx].set(value)

    def __getattr__(self, name):
        """
            :param name: attribute name
        """
        if name in self._attrs: 
            return VectorAttr(self, name)
        else :
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
            _attr = [create_field(self._field.attrs[name]) for _ in xrange(len(values)) ]
            for idx, val in enumerate(values):
                _attr[idx].set(val)
            self._attrs[name] = _attr


class VectorAttr(object):
    def __init__(self, vector, attr):
        self.vector = vector
        self.attr = attr
            
    def __iter__(self):
        for attr_value in self.vector._attrs[self.attr]:
            yield attr_value.get_value()
    
    def values(self):
        # should we use doc.terms.tf() ??? 
        return list(self)
            
    def __getslice__(self, i, j):
        return [ x.get_value() for x in self.vector._attrs[self.attr][i:j] ]
    
    def __getitem__(self, idx):
        return self.vector._attrs[self.attr][idx].get_value()
        
    def __setitem__(self, idx, value):
        self.vector._attrs[self.attr][idx].set(value)


class VectorItem(object):
    def __init__(self, vector, key):
        self._vector = vector
        self._key = key
    
    def attribute_names(self):
        return self._vector.attribute_names()
    
    def as_dict(self):
        return { k: self[k] for k in self.attribute_names()  }
        
    def __getattr__(self, attr_name):
        return self._vector.get_attr_value(self._key, attr_name)
    
    def __setattr__(self, attr, value):
        if not(attr.startswith('_')):
            self._vector.set_attr_value(self._key, attr, value)
        else: 
            object.__setattr__(self, attr, value)
            
    def __getitem__(self, name ):
        return getattr(self, name)

#TODO: ca doit être une métode de field
def create_field(field):
    """ Create a convenient field to store data
    
    not multi => default or None
    multi and uniq and fields.attr => dict
    multi and uniq => set
    multi and not uniq => list
    """
    if not(field.multi):
        return ValueField(field)
    elif field.multi and not field.uniq:
        return ListField(field)
    elif field.multi and field.uniq and field.attrs == None:
        return SetField(field)
    else:
        return VectorField(field)


class Doc(dict):
    """ Cello Document object
    """
    __reserved__ = ['docnum', 'schema']
    
    def __init__(self, schema, **data):
        dict.__init__(self)
        # schema 
        self['schema'] = schema
        # fields value(s)
        
        #TODO: docnum doit etre un field spécial
        #TODO: la valeur de docnum doit être passer en argument de __init__
        # Doc should always have a docnum ? YES
        self['docnum'] = data['docnum'] # or fail
        
        for key, field in schema.iter_fields():
            self[key] = create_field(field) 
            if data and data.has_key(key):
                self[key].set(data[key])
    
    def __getattr__(self, name):
        try:
            field = self[name]
            if type(field) == ValueField:
                return self[name].get_value()
            return field  
        except KeyError as err:
            raise SchemaError("%s is not a Doc field (existing attributes are: %s)" % (err, self.keys()))

    def __setattr__(self, name, value):
        assert name in self['schema'].field_names(), \
            "%s is not declared as a field in the schema" %name
        self[name].set( value )
        
