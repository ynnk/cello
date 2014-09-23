#-*- coding:utf-8 -*-
""" :mod:`cello.providers.solr`
===============================

Set of class to acces a SOLR server
"""

import os
import os.path

# solr api required
try:
    import sunburnt
except:
    print("Error importing sunburnt library for Apache Solr, run $ sudo pip install sunburnt")
    raise

from cello.schema import Doc
from cello.pipeline import Optionable

#FIXME: unused import
from cello.index import Index, CelloIndexError
from cello.search import AbstractSearch
from cello.writers import AbstractWriter


class SolrIndex(Index):
    """ Access an solr index.

    Early version !
    * get solr index

    Here is an usage exemple:

        idx = SolrIndex(idx='yours')
        # get document count
        len(idx)
        # get field names declared in schema
        idx.fields()
        # iter over docnums
        idx.iter_docnums()
        # iter over all docnument in index
        idx.get_document(idx.iter_docnums())
    """
    #TODO: ^ trouvé comment en faire des vrai doctest (fake server)

    # TODO multiple add !

    def __init__(self, host="http://localhost:8983/solr/", idx=None, **kwargs):
        """ 
        @param host: base url for connection
        @param idx: solr index name
        @param kwargs: extra parameters:
            - cache: max document count in each retrieving request
            - fl: field names returned in a document ',' separated ex: "text, url,score"
            - wrap: fct(docdict) function to wrap dict to object such as lambda docdict : kdoc_wrap(docdict)
        """
        Index.__init__(self)
        # FIXME raise error
        assert host is not None
        assert idx is not None
        # create a connection to a solr server and retrive uniq key
        self.conn = sunburnt.SolrInterface(host + idx)
        self.uniq_key = self.conn.schema.unique_key 
        # override specific params for optimizations
        self.cache = kwargs.get("cache", 100)
        self.fl = kwargs.get("fl", "*") # will return all field of 
        self.wrap = kwargs.get("wrap", self._default_wrapper())
        #TODO ^ pourquoi "kwargs" c'est juste des arguments optionelles ?

    def _default_wrapper(self):
        uniq_key = self.uniq_key
        def wrap(doc):
            kdoc = Doc(docnum=doc.pop(uniq_key))
            kdoc.update(doc)
            return kdoc
        return wrap

    def __len__(self):
        """ return count of document in index """
        params = {'q':'docnum:*', 'rows':0}
        result = self.conn.search(**params).result
        return result.numFound
            
    def fields(self):
        """ Returns field names declared in the schema as a list """
        return self.conn.schema.fields.keys()

    def statistics(self):
        return {
            "ndocs": len(self)
        }

    def has_document(self, docnum):
        """Test for a document in Index.  Fetchs document and returns True wether exists """
        return self.get_document(docnum) is not None

    def get_document(self, docnum):
        """ fetch a document given a docnum 
        it will match the given value in field specified as 'uniqueKey' in schema.xml """
        kdoc = None
        params = {'q': "%s:%s"%(self.uniq_key, docnum), 'fl':self.fl, 'rows':1}
        result = self.conn.search(**params).result
        
        if result.numFound > 0:
            for doc in result.docs:
                kdoc = self.wrap(doc)
        return kdoc

    def get_documents(self, docnums):
        """ fetch a set of documents given a docnum list or iterator.
        it will match the given value in field specified as 'uniqueKey' in schema.xml """
        Q = self.conn.Q
        wrap = self.wrap
        uniq_key = self.uniq_key
        dnum_cache = []
        ccount = 0
        params = {'fl':self.fl, 'start':0, 'rows':self.cache}
        for d in docnums:
            dnum_cache.append(d)
            ccount += 1
            if ccount == self.cache:
                solrq = Q()
                for dnum in dnum_cache:
                    solrq |= Q(**{uniq_key:dnum})
                params['q'] = solrq # lucene query
                result = self.conn.search(**params).result
                for doc in result.docs:
                    yield wrap(doc)
                ccount = 0
                dnum_cache = []

    def iter_docnums(self, incr=1000):
        start = 0
        count = len(self)
        params = {
            'q': "%s:*" % self.uniq_key,
            'fl': self.uniq_key,
            'start': 0,
            'rows': incr
        }
        while (start < count):
            params['start'] = start
            result = self.conn.search(**params).result
            for doc in result.docs:
                yield doc[self.uniq_key]
            start += incr

    def add_document(self, kdoc):
        raise NotImplementedError

    def add_documents(self, kdocs):
        #TODO: are each doc correctly added ?
        self.conn.add(kdocs, chunk=self.cache, commit=True)
        return [] 


class SolrSearch(Optionable):
    # FIXME require schema
    def __init__(self, idx):
        #FIXME; doc needed idx c'est uen SolrIndex ?
        Optionable.__init__(self, name=self.__class__.__name__)
        self._index = idx
        #FIXME: add options

    def __call__(self, query, search_field='*', qf="", fl="*,score", nb_res=10, operator="AND"):
        """ Perform a search using the Solr webapp

        :param search_field: field to search for matching term. If '*' one can set the boosts per field in the @param qf.
        :param fl: field names returned in a document ',' separated ex: "text, url,score"
        :param qf : List of fields and the 'boosts' to associate with each of them when building DisjunctionMaxQueries from the user's query. The format supported is fieldOne^2.3 fieldTwo fieldThree^0.4, which indicates that fieldOne has a boost of 2.3, fieldTwo has the default boost, and fieldThree has a boost of 0.4 ... : &qf=
            ths param will be used IF and ONLY  @param search_field is '*'.
        :param nb_res: max count of document to be returned
        :param operator: how terms are handled together in a request. possible values ('AND','OR)'
            ex: query='moteur chat' >> 'chat AND moteur'
        """
        kdocs = []
        Q = self._index.conn.Q
        def _query(lucenequery, term):
            #FIXME: doc needed ! que fait cette fonction interne ?
            qargs = lambda term: Q(**{search_field: term}) if search_field != "*" else Q(term)
            if len(term) > 0:
                if operator == "AND":
                    if term[:1] == "-":
                        return lucenequery & ~qargs(term) # & not
                    else:
                        return lucenequery & qargs(term)
                elif operator == "OR":
                    return lucenequery | qargs(term)
            else:
                return lucenequery

        if query:
            solrq = reduce(_query, query.split(' '), Q())
            params = {'q': solrq, 'fl': fl, 'rows': nb_res}
            if search_field == "*":
                # When qf is used &defType=dismax should be set
                params.update({
                    'defType': 'dismax',
                    'qf': qf
                })
            params.update({"debugQuery": 'on'})
            result = self._index.conn.search(**params).result
            if result.numFound > 0:
                idx = self._index 
                for doc in result.docs:
                    kdocs.append(idx.wrap(doc))
        return kdocs

