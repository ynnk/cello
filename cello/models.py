#-*- coding:utf-8 -*-
""" :mod:`cello.models`
=======================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

Cello basic objects.
"""

import logging
import random

from cello.errors import CelloError

logger = logging.getLogger("cello.models")


class Doc(dict):
    """ Document

    Exemple d'utilisation sans asssociations des scores et des terms fields :
    
    >>> kdoc = Doc()
    >>> kdoc.declare_field("snippet")
    >>> kdoc.declare_attr_field("snippet_tf")
    >>> kdoc.declare_attr_field("snippet_bm25")
    >>> for term, tf, bm25 in [("chat", 2, 4.34), ("poche", 34, 1.2)]:
    ...     kdoc.add_element("snippet", term)
    ...     kdoc.set_element_attr("snippet_tf", term, tf)
    ...     kdoc.set_element_attr("snippet_bm25", term, bm25)

    Et donc on a ensuite :
    
    >>> kdoc.list_fields()
    ['_all_terms', 'snippet']
    >>> kdoc.list_attr_fields()
    ['snippet_tf', 'snippet_bm25']
    >>> "chat" in kdoc.snippet
    True
    >>> kdoc.get_element_attr("snippet_tf", "chat")
    2
    
    Exemple d'utiliation avec asssociations des scores et des terms fields :
    
    >>> kdoc = Doc()
    >>> kdoc.declare_field("snippet", "tf", "bm25")
    >>> for term, tf, bm25 in [("chat", 2, 4.34), ("poche", 34, 1.2)]:
    ...     kdoc.add_element("snippet", term, tf=tf, bm25=bm25)

    :ivar docnum: uniq identifier of the document
    :type docnum: unicode

    :ivar rank: rank of doc
    :type rank: int

    :ivar title: Title of the document
    :type title: str

    :ivar url: url of the document
    :type url: str

    :ivar text: Full text of the document (may not be stored)
    :type text: str
    """

    # It's a Dictionary who's keys act like attributes as well
    # from: http://code.activestate.com/recipes/577590-dictionary-whos-keys-act-like-attributes-as-well/

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError("%s is not a KodexDoc attribut (existing attributes are: %s)" % (e, self.keys()))

    def __setattr__(self, name, value):
        self[name] = value

    def __init__(self, docnum=None, title=None, url=None, text=None):
        """ Create a new document
        """
        if isinstance(docnum, int):
            docnum = u"%d" % docnum
        if isinstance(docnum, str):
            docnum = docnum.decode("utf8")
        self.docnum = docnum
        self.title = title
        self.url = url
        self.text = text

        self._all_terms = {}
        #self._all_terms_tf = []

        self._term_fields = ["_all_terms"]
        self._attr_fields = []
        self._attr_fields_defaults = []

    def __repr__(self):
        _docnum = self.docnum
        if isinstance(self.docnum, str):
            _docnum = self.docnum.encode("utf8")
        return  ("<KodexDoc(\"%s\")>\n" % _docnum) + \
             "\n".join([ '%s:%s'% (k,repr(v))  for k,v in self.iteritems() ])

    def _get_attr_field_name(self, field_name, attr_field_suffix):
        return "%s_%s" % (field_name, attr_field_suffix)

    def iterfields(self):
        """ return an iterator over all 'standart' fields
        """
        return ((field, value) for field, value in self.iteritems() \
                    if field[0] != "_"
                        and field not in self.list_term_fields()
                        and field not in self.list_attr_fields())

    def declare_field(self, field_name, *associated_attr_fields):
        """ Declare a new field (for terms for ex.)

        :param field_name: The name of the field to create
        :param associated_attr_fields: a list of associated attr field to create
        """
        if field_name in self._term_fields:
            raise ValueError("The field '%s' already exist" % field_name)
        self._term_fields.append(field_name)
        self[field_name] = {}
        if associated_attr_fields is None:
            associated_attr_fields = []
        for attr_field in associated_attr_fields:
            attr_field_name = self._get_attr_field_name(field_name, attr_field)
            self.declare_attr_field(attr_field_name)

    def declare_attr_field(self, attr_field_name, default=0):
        """ Declare a new attr (score or data) field (for terms)
        """
        if attr_field_name in self._attr_fields:
            raise ValueError("The attr field '%s' already exist" % attr_field_name)
        self._attr_fields.append(attr_field_name)
        self._attr_fields_defaults.append(default)
        self[attr_field_name] = [default] * len(self._all_terms)

    def list_fields(self):
        """ Return the list of all document term fields
        """
        return self._term_fields

    def list_attr_fields(self):
        """ Return the list of all document attr or date fields (for terms)
        """
        return self._attr_fields

    def _get_element_id(self, element):
        """ Return the id of a element in fields
        """
        if element not in self._all_terms:
            raise ValueError("'%s' not present in the document" % element)
        tid = self._all_terms[element]
        return tid

    def add_element(self, field_name, element, **associated_attrs):
        """ Add an element into a field
        """
        # get the element id (in the doc)
        if element not in self._all_terms:
            # add a term
            self._all_terms[element] = len(self._all_terms)
            # and default attrs values
            for sid, attr_field_name in enumerate(self._attr_fields):
                self[attr_field_name].append(self._attr_fields_defaults[sid])
        tid = self._all_terms[element]
        # store the term in the good field
        if not element in self[field_name]:
            self[field_name][element] = tid
            # store the associated attrs
            for attr_field, value in associated_attrs.iteritems():
                attr_field_name = self._get_attr_field_name(field_name, attr_field)
                self.set_element_attr(attr_field_name, element, value)

    def iter_all_fields(self):
        """ Return an iterator over all terms
        """
        return self._all_terms.iterkeys()

    def iter_field(self, field_name):
        """ Return an iterator over terms of a field
        """
        if field_name not in self._term_fields:
            raise ValueError("The field '%s' doesn't exist" % field_name)
        return self[field_name].iterkeys()

    def get_element_attr(self, attr_field_name, element, field_name=None):
        """ Get the attr (could be a score or data) of a element
        """
        if field_name is not None:
            attr_field_name = self._get_attr_field_name(field_name, attr_field_name)
        if attr_field_name not in self._attr_fields:
            raise ValueError("The attr field '%s' is not present in the document" % attr_field_name)
        tid = self._get_element_id(element)
        return self[attr_field_name][tid]

    def set_element_attr(self, attr_field_name, element, attr, field_name=None):
        """ Set a attr (score or a data) for a element

        :param attr_field_name: the name of the attr field name
        :param element: the element
        :param attr: the new attr
        :param field_name:
        """
        if field_name is not None:
            attr_field_name = self._get_attr_field_name(field_name, attr_field_name)
        tid = self._get_element_id(element)
        if tid > len(self._all_terms):
            raise IndexError("The element id '%d' is too large ! (> len(_all_terms) = %d)" % (tid, len(self._all_terms)))
        if len(self[attr_field_name]) != len(self._all_terms):
            raise ValueError("The attr field '%s' have incorect size (%d != %d)" % (attr_field_name, len(self[attr_field_name]), len(self._all_terms)))
        self[attr_field_name][tid] = attr

    def inc_element_attr(self, attr_field_name, element, increment=1, field_name=None):
        """ Increment the attr 'attr_field_name'  (or a data) of ans element
        :param increment : add to the current value default is 1
        """
        val = self.get_element_attr(attr_field_name, element, field_name=field_name)
        self.set_element_attr(attr_field_name, element, val + increment, field_name=field_name)


class LU(dict):
    """ Lexical unit

    :ivar form: form of the lexical unit
    :type form: unicode

    :ivar TF: total term frequency in the index
    :type TF: int

    :ivar df: number of documents containing the lexical unit
    :type df: int

    :ivar posting: set of documents that contain lexical unit
    :type posting: set(docnum)
    """
    #It's a Dictionary who's keys act like attributes as well
    #from: http://code.activestate.com/recipes/577590-dictionary-whos-keys-act-like-attributes-as-well/

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError("%s is not a KodexLU attribut (existing attributes are: %s)" % (e, self.keys()))

    def __setattr__(self, name, value):
        self[name] = value

    def __init__(self, form=None, TF=0, df=0, posting=set()):
        """ Create a new lexical unit
        """
        if isinstance(form, str):
            form = form.decode("utf8")
        self.form = form
        self.TF = TF
        self.df = df
        if posting:
            if isinstance(posting, set):
                posting = posting.copy() #XXX: est-ce qu'il faut faire cette copie ?
            self.posting = list(posting)

    def __repr__(self):
        return "<LU(\"%s\")>" % str(self)

    def __hash__(self):
        """ implemented method to make set() works. Standard hash method on KodexLU.form
        :returns: hash(self.form)
        :rtype: int
         """
        return  hash(self.form)

    def __unicode__(self):
        form = repr(self.form)
        if isinstance(form, str):
            return form.decode('utf8')
        return form

    def __str__(self):
        return unicode(self).encode('utf8')

