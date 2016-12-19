#-*- coding:utf-8 -*-
""" :mod:`cello.expanders.basics`
=================================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}


inheritance diagrams
--------------------

.. inheritance-diagram:: AddFixedScore FieldFilter TermSet

Class
-----
"""
import six

from reliure import Composable
from reliure.types import GenericType, Text, Numeric
from reliure.schema import VectorField

from cello.expanders import AbstractDocListExpand


class GuestLanguage(Composable):
    """ Guest the language of a document according to a text field
    """
    def __init__(self, text_fields, out_field="language"):
        """
        :param text_fields: document fields that contains the text used to guest language
        :param out_field: field where to store language
        """
        super(GuestLanguage, self).__init__()
        if isinstance(text_fields, six.string_types):
            text_fields = [text_fields]
        self.text_fields = text_fields
        self.out_field = out_field
        from guess_language import guess_language
        self.guess_language = guess_language

    def __call__(self, docs):
        text_fields = self.text_fields
        out_field = self.out_field
        guess_language = self.guess_language
        for doc in docs:
            if out_field not in doc:
                doc[out_field] = Text()
            texte = "\n".join(doc[text_field] for text_field in text_fields)
            doc[out_field] = guess_language(texte)
        return docs


class RmStopwords(Composable):
    """ Remove stopwords
    """
    def __init__(self, terms_field, get_lang=None):
        """
        
        :param terms_field: document field containings the terms
        :param get_lang: function that return the language of a document
        """
        super(RmStopwords, self).__init__()
        self.terms_field = terms_field
        if get_lang is None:
            get_lang = lambda doc: "english"
        self.get_lang = get_lang
        from nltk.corpus import stopwords
        self._stopwords = stopwords.words

    def __call__(self, docs):
        terms_field = self.terms_field
        get_lang = self.get_lang
        stopwords = self._stopwords
        for doc in docs:
            lang = get_lang(doc)
            lang_stopwords = stopwords(lang)
            tfield = doc[terms_field]
            to_del = []
            for term in tfield:
                if term in lang_stopwords:
                    to_del.append(term)
            self._logger.debug("Remove %s stopwords" % (len(to_del)))
            for keys in to_del:
                del tfield[keys]
        return docs


class AddFixedScore(Composable):
    """ Add a score field with a fixed value for each term
    """
    def __init__(self, term_field, score_field, value=1., default_value=0.):
        Composable.__init__(self)
        self._term_field = term_field
        self._score_field = score_field
        
        self._value = value
        self._default_value = default_value
        
    def __call__(self, kdocs):
        for kdoc in kdocs:
            kdoc.declare_attr_field(self._score_field, self._default_value)
            for term in kdoc.iter_field(self._term_field):
                kdoc.set_element_attr(self._score_field, term, self._value)
            yield kdoc


class FieldFilter(Composable):
    """ Apply an filter function to a given field of the document.
    """
    def __init__(self, filter, field, dest_field=None, keep_original=True):
        """ Apply a filter to a given document:
        doc[dest_flield] = filter(doc[flield])
        
        :param filter: the filter to apply
        :param field: the field on whish the filter is applyied
        :param dest_field: if None, the field is changed in place
        :param keep_original: if False the original field is removed
        """
        Composable.__init__(self)
        self._filter = filter
        self._field = field
        self._dest_field = dest_field or field
        self._keep_original = keep_original

    def __call__(self, docs):
        # link attr in local var, optimisation
        dest_field = self._dest_field
        field = self._field
        filter = self._filter
        keep_original = self._keep_original
        for doc in docs:
            doc[dest_field] = filter(doc[field])
            if not keep_original and field != dest_field:
                doc.pop(field)
            yield doc



