#-*- coding:utf-8 -*-
""" :mod:`cello.schema`
======================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

"""


"""
    Errors  
"""
class SchemaError(Exception):
    pass

"""
    Main Schema class inspired from Matt Chaput's Whoosh.  
"""
class Schema(object):
    """
    Schema definition for docs <Doc>
    
    Creating a schema :
        >>>schema = Schema(**{ 'title': Text(), 'score':Numeric(numtype=int, multi=True) })
        >>># or
        >>>schema = Schema( title=Text(), score=Numeric() )
        >>>schema.field_names()
        >>># ['score', 'title']
        """
    
    def __init__(self, **fields):
        self._fields = {}
        
        for name,fieldtype in fields.iteritems():
            self.add_field(name, fieldtype)
        
    def add_field(self, name, field):
        """s
            Add a named field to the schema.
            :param name : name of the new field
            :param field : FieldType instance for the field 
        """
        # testing names 
        if name.startswith("_"):
            raise SchemaError("Field names cannot start with an underscore")
        if " " in name:
            raise SchemaError("Field names cannot contain spaces")
        
        if name in self._fields: 
            raise SchemaError("Schema already has a field named '%s'" %s)
        if isinstance(field, FieldType) == False:
            raise SchemaError("Wrong FieldType in schema for field :%s, v" % (name, field ) )
        self._fields[name] = field
    
    def remove_field(self, *fields):
        raise NotImplemented()
        
    def iter_fields(self):
        return self._fields.iteritems()
    
    def field_names(self):
        return self._fields.keys()
    
    def has_field(self, name):
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
        return "<%s: %s>"%( self.__class__.__name__, self._fields)


"""
   * FieldTypes to declare in schemas 
"""
class FieldType(object):
    """
    Abstract FieldType
    """
    def __init__(self, multi=False, uniq=False, default=None, attrs={} ):
        """
        :param multi: field is a list or a set
        :param uniq: wether the values are unique. only apply if multi == True-
        :param default: default value for the field
        :param attrs: field attributes name: FieldType
        """
        self.multi = multi 
        self.uniq = uniq
        self.default = default
        self.attrs = attrs
        # self.sorted = sorted
    
    
    def __repr__(self):
        temp = "%s(multi=%s, uniq=%s, default=%s)"
        return temp % (self.__class__.__name__,
                    self.multi, self.uniq, self.default )
    
    def validate(self, value):
        pass

class Numeric(FieldType):
    _types_ = [int, float]
    
    def __init__(self, numtype=int, **field_options):
        """
        :param numtype: the type of numbers that can be stored in this field,
            either ``int``, ``float``. 
        """
        FieldType.__init__(self, **field_options)
        if numtype not in Numeric._types_  : 
            raise ValueError('Wrong type for Numeric %s' % Numeric._types_ )
        self.numtype = numtype
        
    def validate(self, value):
        if isinstance(value, self.numtype) == False :
            raise TypeError("Wrong type '%s' should be '%s'" % (type(value), self.numtype ))
        return value
   
class Text(FieldType):
    """
        
    """
    # valid type for text
    _types_ = [str, unicode]
    
    def __init__(self,texttype=str, **field_options):
        FieldType.__init__(self, **field_options)
        if texttype not in Text._types_  : 
            raise SchemaError('Wrong type for Numeric %s' % Numeric._types_ )
        self.texttype = texttype
        
    def validate(self, value):
        if isinstance(value, self.texttype) == False :
            raise TypeError("Wrong type '%s' should be '%s'" % (type(value), self.texttype ))
        return value



# Add more FiledType here

# ...
# ...

"""
Document fields implementations 
"""
class DocField():
    def __init__(self, field):
        self._field = field
        
    def get_value(self): pass

class ValueField(DocField):
    """
    Store only one value of FieldType
    """
    def __init__(self, field):
        DocField.__init__(self, field)
        self.value = field.default
    
    def get_value(self): 
        return self.value
    
    def set(self, value): 
         self.value = self._field.validate(value)

class SetField(DocField):
    """
        
        usage: 
            doc.schema.add_fields(tags=Text(multi=True, uniq=True) )
            doc.tags # SetField
            doc.tags.add('boo')
            doc.tags.add('foo')
            doc.tags # >>> ['boo', 'foo']
            
    """
    def __init__(self, field):
        DocField.__init__(self, field)
        self.value = set(field.default or [])
    
    def get_value(self):
        return  list(self.value)
    
    def add(self, value):
        self.add( self._field.validate(value) )

       
    def set(self, value):
        if type(value) == list:
            self.value = set([ self._field.validate(v) for v in value ])
        else:
            raise SchemaError("Wrong value '%s' for field 's'" % (value, self._field))

        
class ListField(DocField):
    def __init__(self, field):
        DocField.__init__(self, field)
        self.value = [] 
    
    def get_value(self):
        return self.value
    
    def add(self, value):
        self.value.append( self._field.validate(value) )
        
    def set(self, value):
        if type(value) == list:
            self.value = [ self._field.validate(v) for v in value ]
        else:
            raise SchemaError("Wrong value '%s' for field 's'" % (value, self._field))
    def __iter__(self):
        """ iterator over values """
        for x in self.value: yield x
            
    def __getitem__(self, idx):
        return self.value[idx]

    def __setitem__(self, idx, value):
        self.value[idx] = value 
        
class VectorField(DocField):
    """
        usage: 
            doc.terms # vector
            doc.terms['chat'] # vectoritem
            doc.terms['chat'].tf = 12
            
    """
    def __init__(self, field):
        DocField.__init__(self, field)
        self._field = field
        self._keys = {}   # key: idx
        self._attrs =  {} # attr_name : [FieldType, ]
        self.clear_attributes()
        
    def clear_attributes(self):
        self._attrs =  {} # removes all attr
        for name, attr_field in self._field.attrs.iteritems():
            self._attrs[name] = create_field(attr_field)
       
    def __repr__(self):
        return "<%s:%s >" %( self.__class__.__name__, self._attrs.keys() )
    
    def __str__(self) : return self.__repr__()
    
    def __len__(self):
        """ Vector keys count """
        return len(self._keys)
    
    def keys(self): 
        """ list of keys in the vector """
        return self._keys.keys()

    def get_value(self): 
        return self

    def get_attr_value(self, key , attr):
        idx = self._keys[key]
        return self._attrs[attr][idx]
    
    def set_attr_value(self, key, attr, value):
        idx = self._keys[key]
        self._attrs[attr][idx] = value
    
    
    def has(self, key): 
        """ 
            Return True if the vector has the specified key 
            vector.has('mykey')
            >>> False 
        """
        return key in self._keys
    
    def add(self, key):
        if not self.has(key):
            self._keys[key] = len(self._keys)
        
        #append to attributes
        for name, attr_field  in self._field.attrs.iteritems():
            self._attrs[name].add(attr_field.default)
        
    def set(self, keys):
        """ set new keys 
            this will clear all attributes and keys before adding new keys
        """
        # clear keys and atributes
        self._keys = {}
        self.clear_attributes()
            
        for key in keys:
            if not self.has(key):
                self.add(key)
                
    def __getattr__(self, name):
        if name in ['_attrs']:
            return self.__getitem__(name)
        elif name in self._attrs:
            return VectorAttr(self, name)
        else :
            raise SchemaError("No such attribute '%s' in Vector" % name)
            
    
    def __getitem__(self, key):
        if key.startswith('_') : 
            return self[key]
        else : 
            return VectorItem(self, key )
  
class VectorAttr():
    def __init__(self, vector, attr):
        self.vector = vector
        self.attr = attr
    
    def __iter__(self):
        for attr_value in self.vector._attrs[self.attr]:
            yield attr_value
            
    def __getslice__(self, i, j):
        return self.vector._attrs[self.attr][i:j]
    
    def __getitem__(self, idx):
        return self.vector._attrs[self.attr][idx]
    
    
class VectorItem(object):
    def __init__(self, vector, key):
        self._vector = vector
        self._key = key
    
    def __getattr__(self, attr_name):
        if attr_name.startswith('_'):
            return object.__getattr__(self, attr_name)
        return self._vector.get_attr_value(self._key, attr_name)
    
    def __setattr__(self, attr, value):
        if not(attr.startswith('_')):
            self._vector.set_attr_value(self._key, attr, value)
        else: 
            object.__setattr__(self, attr, value)
    


def create_field(field):
    """
    Create a convenient field to store data
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
    
    __reserved__ = ['docnum', 'schema']
        
    
    def __init__(self, schema, **data):
        # schema 
        self['schema'] = schema
        # fields value(s)
        
        # Doc should always have a docnum
        self['docnum'] = data['docnum'] # or fail
        
        for key,field in schema.iter_fields():
            # field.multi & ! field.uniq >> list
            # field.multi & field.uniq >> set
            # field.multi & field.uniq & fields.attr >> dict
            # ! field.multi >> default or None
            self[key] = create_field(field) 
            if data and data.has_key(key):
                self[key].set(data[key])
            
    def __getattr__(self, name):
        try:
            if name == 'schema':
                return self['schema']
            return self[name].get_value()
        
        except KeyError as e:
            raise AttributeError("%s is not a Doc field (existing attributes are: %s)" % (e, self.keys()))

    def __setattr__(self, name, value):
        assert name in self['schema'].field_names(), \
            "%s is not declared as a field in the schema" %name
        self[name].set( value )
        
