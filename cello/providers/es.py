#-*- coding:utf-8 -*-
""" :mod:`cello.providers.solr`
==================================

Set of class to acces a SOLR server
"""

import os
import os.path
import logging

import elasticsearch
import elasticsearch.helpers as ESH

from cello.schema import Doc
from cello.pipeline import Optionable
from cello.types import *

#FIXME: unused import
from cello.index import Index, CelloIndexError
from cello.search import AbstractSearch
from cello.writers import AbstractWriter


class EsIndex(Index):
    """ Access an Elasticsearch index.

    Here is an usage exemple:
        idx = EsIndex(idx='yours')
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

    def __init__(self, host="http://localhost:9200", **kwargs):
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
        # create a connection to a es server and retrive mapping and  uniq key
        self._es = elasticsearch.Elasticsearch(hosts=host)
                
        # override specific params for optimizations
        self.cache = kwargs.get("cache", 100)
        self.fl = kwargs.get("fl", "*") # will return all field of 
        
    def create_index(idx, doc_type, schema):
        self._es.indices.create(idx, ignore=400)
        self._es.indices.put_mapping(index=idx, doc_type=doc_type, body=schema)
    
    def drop_index():
        self._es.indices.delete_mapping(INDEX, doc_type="_all", ignore=400)
        self._es.indices.delete(INDEX,ignore=400)

        
    def get_mappings(self, idx):
        return self._es.indices.get_mapping(index=idx)[idx]['mappings']
    
    def get_uniq_key(self, idx, doc_type):
        uniq_key = None
        mappings = self.get_mappings(idx)
        if doc_type in mappings:
            if '_id' in mappings[doc_type] and 'path' in mappings[doc_type]['_id']:
                uniq_key = mappings[doc_type]['_id']['path']
        return uniq_key
        
    def get_fields(self,idx, doc_type):
        """ Returns field names declared in the schema as a list """
        return self.get_mappings(idx)[doc_type]['properties'].keys()

    def __len__(self):
        """ return count of document in index """
        raise NotImplementedError
            
    def statistics(self):
        return {
            "ndocs": len(self)
        }

    def has_document(self, idx, doc_type, docnum):
        """Test for a document in Index.  Fetchs document and returns True wether exists """
        return self.get_document(docnum) is not None

    def get_document(self, idx, doc_type, docid, **kwargs):
        """ fetch a document given a docnum 
        it will match the given value in field specified as 'uniqueKey' in schema.xml """
        docs = list(self.get_documents(idx, doc_type, [docid], **kwargs))
        return docs[0] if len(docs) else None

    def get_documents(self, idx, doc_type, docids, **kwargs):
        """ fetch a set of documents given a docnum list or iterator.
        it will match the given value in field specified as 'uniqueKey' in schema.xml """
        body = {'ids': docids}
        docs = self._es.mget(index=idx, doc_type=doc_type, body=body, **kwargs) 
        docs = list(d for d in docs["docs"] if d["found"])
        return docs
        

    def iter_docnums(self, incr=1000):
        raise NotImplementedError

    def add_document(self, idx, doc_type, doc):
        return add_documents(idx, doc_type, [doc])

    def add_documents(self, idx, doc_type, docs):
        for doc in docs:
            doc['_index'] = idx
            doc['_type'] = doc_type
        res = ESH.bulk_index(client=self._es, actions=docs)
        return res



class EsSearch(AbstractSearch):
    """ Make a search using ElasticSearch """
    QF = u"title^5 redirects^3 text"

    def __init__(self, host="http://localhost:9200", idx=None, doc_type=None, lang=None, connect=True, name=None):
        name = name or __name__
        super(AbstractSearch, self).__init__( name )
        self._logger = logging.getLogger(name)
        self.es_index = EsIndex(host=host)
        self._es_host = host
        self._es_idx = idx
        self._es_doctype = doc_type
        self._lang = lang
        
        if connect :
            assert idx is not None, "No Index provided"
            assert lang is not None, "No lang  provided"
         
        # FIXME
#        self.add_bool_option("in_title", True, "Search in titles")
#        self.add_bool_option("in_redirects", True, "Search in redirects")
#        self.add_option("fl", '*,score', "fields returned by solr; &fl=", str)
        self.add_option("articles", Numeric(default=10, help=u"Number of results; &rows="))
        self.add_option("operator", Text(choices=[u"AND", u"OR",], default=u"AND", 
            help=u"operator used for chaining terms"))
        if connect:
            fields = sorted(self.es_index.get_fields(idx, doc_type))
            self.add_option("search_field",
                            Text(choices=[u"*"] + [unicode(e) for e in fields],
                            default=u"*", help=u"field to search")
                            )
        else:
            self.add_option(
                    "search_field", Text(default=u"text", 
                        help=u"""field to search for matching term.
                         If '*' one can set the boosts per field in the @param qf.""",
                ))

        self.add_option(
                    "qf", Text(default=EsSearch.QF, help=u"""List of fields 
                    and the 'boosts' to associate with each of them when building
                    DisjunctionMaxQueries from the user's query. The format supported 
                    is fieldOne^2.3 fieldTwo fieldThree^0.4, which indicates that
                    fieldOne has a boost of 2.3, fieldTwo has the default boost, 
                    and fieldThree has a boost of 0.4 ... : &qf=""")
               )

    def __call__(self, query, search_field=u'text', qf=QF, fl=u"id, title, out_links, premierParagraphe,score", articles=10, operator=u"AND", raw=False):
        """ Perform a search using the Elasticsearch
        :param search_field: field to search for matching term. 
          If '*' one can set the boosts per field in the @param qf.
        :param nb_res: max count of document to be returned
        :param qf : List of fields and the 'boosts' to associate with each fields,
          when building DisjunctionMaxQueries from the user's query. 
          The format supported is fieldOne^2.3 fieldTwo fieldThree^0.4, indicates
          that fieldOne has a boost of 2.3, fieldTwo has the default boost, and 
          fieldThree has a boost of 0.4 ... : &qf=
          this param will be used IF and ONLY `search_field` is '*'.
          When qf is used &defType=dismax should be set
        """
        self._logger.info("query: '%s'" % query)
        idx = self._es_idx
        doc_type = self._es_doctype
        kdocs = []

        get_by_id = self.es_index.get_uniq_key(idx, doc_type) == search_field
        
        if not get_by_id:
            if search_field == "*":
                query_string = { 
                        "query": query,
                        "fields": qf.split(" "),
                        "use_dis_max": True
                        }
            else:
                query_string = {
                        "query": query,
                        "default_field": search_field,
                        }
            query_dsl = {
                    "size": articles,
                    "query": {
                        "query_string": query_string
                        }
                    }

        if query:
            self._logger.info("Elasticsearch query: '%s'" % query)
            if get_by_id:
                retrieved = [d for d in self.es_index._es.mget(index=self._es_idx, doc_type=self._es_doctype, body={'ids': list(query)})["docs"] if d["found"]]
                for rank, doc in enumerate(retrieved):
                    kdocs.append(self._es_to_kdoc(doc, rank+1))
            else:
                result = self.es_index._es.search(self._es_idx, doc_type=self._es_doctype, body=query_dsl)
                if result["hits"]["total"] > 0:      
                    for rank, doc in enumerate(result["hits"]["hits"]):
                        if raw == False:
                            kdoc = self.to_doc(doc, rank+1)
                        else : 
                            kdoc = doc
                        kdocs.append(kdoc)
        return kdocs
    
    def to_doc(self, doc, rank):
        raise NotImplementedError
