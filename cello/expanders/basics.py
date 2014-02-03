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

from cello.pipeline import Composable
from cello.expanders import AbstractDocListExpand
from cello.schema import VectorField
from cello.types import Text, Numeric, Any


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



class DocLength(FieldFilter):
    """ Counts documents length, (C{terms_df} -> C{dlen})
    """
    def __init__(self, terms_tf_field="terms_tf", dlen_field="dlen"):
        """
        :param terms_tf_field: name of :class:`Doc` field containing the *term frequenc* list (default: "terms_df")
        :param dlen_field: name of :class:`Doc` field where the document length will be save (default: "dlen")
        """
        FieldFilter.__init__(self, sum, terms_tf_field, dlen_field, keep_original=True)

#XXX ?
class Merges:
    @staticmethod
    def first(x,y): return y
    @staticmethod
    def sum(x,y): return x+y
    @staticmethod
    def append(x,y): return x+y

#XXX wtf ??
class TermSet(VectorField):
    def __init__(self, ts_field, term_field, merges=[], posting=False):
        """
        create a termset from docs attribute
        use merges as a reduce function 
    
        :param merges : [('termset_attr','term_attr', Merges.method)]
            used to keep an attributes 
            if value is same for a term in all docs
            value
        :param posting: keep posting list if True   
            (keep a reference to Doc instance)
        """
        # create container
        self._ts_field = ts_field
        self._term_field = term_field
        attrs = [ ts for ts, t , f in merges] 
        self._merges = merges or []
        self._posting = posting 
        VectorField.__init__(self, Text(attrs={}))
        
        self.add_attribute('df_rd', Numeric(default=0))
        if posting : 
            self.add_attribute('postings', Any(multi=True))

    def __repr__(self):
        return "<%s:('%s', '%s') %s>" % ( self.__class__.__name__, self._ts_field, self._term_field, self._attrs.keys())
        

    def __call__(self, docs):
        termset = self
        ts_field, term_field = self._ts_field, self._term_field, 
        merges, posting = self._merges, self._posting
        for doc in docs:
            doc[ts_field] = termset # XXX should be marked as virtual ?
            terms = doc[term_field]
            for term in terms:
                termset.add(term) 
                vi = termset[term]
                for ts_attr, t_attr, merge in merges:
                    if not ts_attr in vi.attribute_names():
                        # create attr
                        fieldtype = doc.schema[term_field].attrs[t_attr]
                        termset.add_attribute(ts_attr, fieldtype )
                    vi[ts_attr] = merge(vi[ts_attr], terms[term][t_attr]) 
                termset[term].df_rd += 1    
                if posting :
                    termset[term].postings.add(doc)
        return docs


#{ KodexLU creation or/and retrieve
class TermSetBuildExpand(AbstractDocListExpand):
    """ Create KodexLU for all terms in the result set.
    This is a key expander for on-line processing.
    
    It does:
    * create one KodexLU object for each term present in at least one document
    of the result set,
    * merge some attr (or data) fields present in the documents into KodexLU,
    * create a attr (data) field in each document to store link to newly
    created KodexLU (by default it is "klus"),
    * compute the df_RD of each term
    * extend all the kodexLU according to a given inverted index (if given).
    """
    def __init__(self, new_klus_field_name="klus",
                       fields_to_merge=[("terms_tf", "tf_RD", lambda x, y: x + y),
                                       ],
                       posting_RD=False,
                       fields_to_invert=[
                                ('terms_tf', 'docs_tf'),
                            ],
                       inverted_index=None):
        """
        """
        AbstractDocListExpand.__init__(self, "term_set_builder")
        self._logger = logging.getLogger("kodex.expanders.TermSetBuildExpand")
        self._klus_field_name = new_klus_field_name
        # check the field_to_expand
        if fields_to_merge is None:
            fields_to_merge = []
        for val in fields_to_merge:
            if len(val) != 3 \
            or not callable(val[2]):
                raise ValueError("The attributes fields_to_merge should be a list of tuple like that: (kdoc_attr_source_field, klu_dest_field, merge_fct)")
        self._fields_to_merge = fields_to_merge
        # posting or not
        self._posting = posting_RD
        # check the field_to_expand
        if fields_to_invert is None:
            fields_to_invert = []
        for val in fields_to_invert:
            if len(val) != 2:
                raise ValueError("The attributes fields_to_invert should be a list of tuple like that: (kdoc_attr_source_field, klu_dest_attr_field)")
        self._fields_to_invert = fields_to_invert
        # inverted index
        self._inverted_index = inverted_index

    def _compute_term_set(self, kdocs):
        """ Build the "set" of L{KodexLU}.
        
        @param kdocs: list of L{KodexDoc}
        @return: {term:L{KodexLU}, ...}
        """
        terms = {}
        for kdoc in kdocs:
            for term in kdoc.iter_all_fields():
                if term in terms:
                    # get KodexLU
                    klu = terms[term]
                    # fields to merge
                    for source_field, dest_field, merge_fct in self._fields_to_merge:
                        value = kdoc.get_element_attr(source_field, term)
                        klu[dest_field] = merge_fct(klu[dest_field], value)
                    terms[term] = klu
                else:
                    # creation du kodexLU
                    klu = KodexLU(term)
                    klu["df_RD"] = 0
                    if self._posting:
                        klu["posting_RD"] = {}
                        for _, target_field in self._fields_to_invert:
                            klu[target_field] = []
                    # merge fields, initial value
                    for source_field, dest_field, _ in self._fields_to_merge:
                        klu[dest_field] = kdoc.get_element_attr(source_field, term)
                    terms[term] = klu
                # MAJ
                klu["df_RD"] += 1
                if self._posting:
                    did = len(klu["posting_RD"])
                    klu["posting_RD"][kdoc.docnum] = did
                    for source_field, target_field in self._fields_to_invert:
                        klu[target_field].append(kdoc.get_element_attr(source_field, term))
        return terms

    def _expand_terms(self, klus):
        """ Expand terms (L{KodexLU}) according to a inverted index (if given)
        """
        if self._inverted_index is None:
            return
        stime = time()
        new_klus = self._inverted_index.get_terms(klus.keys())
        for new_klu in new_klus:
            if isinstance(new_klu.form, str):
                new_klu.form = new_klu.form.decode('utf8')
            klus[new_klu.form].update(new_klu)
        dtime = time() - stime
        self._logger.info("%s KodexLU expanded in %1.2f sec, %1.2f klus/sec." \
                                       % (len(klus), dtime, len(klus) / dtime))

    def __call__(self, kdocs):
        kdocs = [doc for doc in kdocs]
        self._logger.info("Building term set and KLU for %d documents" % len(kdocs))
        # build the list of terms, compute some stat
        klus = self._compute_term_set(kdocs)
        self._logger.info("> %d KodexLU built" % len(klus))
        # update documents terms (from string to KodexLU)
        for kdoc in kdocs:
            kdoc.declare_attr_field(self._klus_field_name)
            for term in kdoc.iter_all_fields():
                kdoc.set_element_attr(self._klus_field_name, term, klus[term])
        # retrieve other stats from the inverted_index
        self._expand_terms(klus)
        return kdocs


