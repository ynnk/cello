#-*- coding:utf-8 -*-
""" :mod:`cello.providers.es`
=============================

Set of class to acces a Elastic Search server
"""

import os.path
import logging

import elasticsearch
import elasticsearch.helpers as ESH


from cello.types import Numeric, Text

from cello.pipeline import Optionable
from cello.index import Index, CelloIndexError
from cello.search import AbstractSearch


class EsIndex(Index):
    """ Elasticsearch index for a particular doc_type
    """

    def __init__(self, index, doc_type="document", schema=None, es=None, host=None):
        """

        :param index: index name
        :param doc_type: the name of document type to use
        :param schema: the schema of documents
        :param es: initialised Elastic Search python client :class:`elasticsearch.Elasticsearch` (if None one is created with given host)
        :param host: base url for connection
        :param idx: solr index name
        """
        #TODO: wrap param
        Index.__init__(self)
        # FIXME raise error
        assert es is not None or host is not None, "'es' or 'host' should be given"
        # create a connection to a es server and retrive mapping and  uniq key
        if es is None:
            self._es = elasticsearch.Elasticsearch(hosts=host)
        else:
            self._es = es
        self.index = index
        self.doc_type = doc_type
        self.schema = schema

    def __len__(self):
        """ return count of document in index """
        res = self._es.count(self.index, doc_type=self.doc_type)
        print res
        return res["count"]

    def statistics(self):
        return {
            "ndocs": len(self)
        }

    def exist(self):
        return self._es.indices.exists(self.index)

    def create(self):
        """ Create the index, and add the doc type schema (if given)
        """
        if not self.exist():
            self._es.indices.create(self.index, ignore=400)
        if self.schema is not None:
            self._es.indices.put_mapping(index=self.index, doc_type=self.doc_type, body=self.schema)

    def delete(self):
        """ Remove the index from ES instance
        """
        #XXX; it delete the whole index, not only the doc_type
        if self.get_schema():
            self._es.indices.delete_mapping(self.index, doc_type=self.doc_type, ignore=400)
        self._es.indices.delete(self.index, ignore=400)

    def get_schema(self):
        """ Get the mappings (or schema) for the current doc_type in the index
        """
        mappings = self._es.indices.get_mapping(index=self.index, doc_type=self.doc_type)
        if self.index in mappings and self.doc_type in mappings[self.index]['mappings']:
            return mappings[self.index]['mappings'][self.doc_type]
        else:
            return {}

    def get_uniq_key(self):
        uniq_key = None
        mappings = self.get_mappings(self.index)
        if self.doc_type in mappings:
            if '_id' in mappings[doc_type] and 'path' in mappings[doc_type]['_id']:
                uniq_key = mappings[doc_type]['_id']['path']
        return uniq_key

    def get_fields(self):
        """ Returns field names declared in the schema as a list """
        return self.get_mappings(self.index)[self.doc_type]['properties'].keys()

    def has_document(self, docnum):
        """Test for a document in Index.  Fetchs document and returns True wether exists """
        return self.get_document(docnum) is not None

    def get_document(self, docnum, **kwargs):
        """ fetch a document given a docnum 
        it will match the given value in field specified as 'uniqueKey' in schema
        """
        docs = list(self.get_documents([docnum], **kwargs))
        return docs[0] if len(docs) else None

    def get_documents(self, docnums, **kwargs):
        """ fetch a set of documents given a docnum list or iterator.
        it will match the given value in field specified as 'uniqueKey' in schema
        """
        body = {'ids': docnums}
        docs = self._es.mget(index=self.index, doc_type=self.doc_type, body=body, **kwargs)
        docs = list(doc for doc in docs["docs"] if doc["found"])
        return docs

    def iter_docnums(self, incr=1000):
        raise NotImplementedError

    def add_document(self, doc):
        res = self._es.index(index=self.index, doc_type=self.doc_type, body=doc)
        return res

    def add_documents(self, docs):
        for doc in docs:
            doc['_index'] = self.index
            doc['_type'] = self.doc_type
        res = ESH.bulk_index(client=self._es, actions=docs)
        return res


class ESQueryStringBuilder(Optionable):
    """ Create a json query for :class:`ESSearch`
    
    >>> qbuilder = ESQueryStringBuilder()
    >>> qbuilder.print_options()
    operator (Text, default=OR, in: {AND, OR}): operator used for chaining terms
    fields (Text, default=_all): List of fields 
                and the 'boosts' to associate with each of them. The format
                supported is "fieldOne^2.3 fieldTwo fieldThree^0.4", which indicates
                that fieldOne has a boost of 2.3, fieldTwo has the default boost, 
                and fieldThree has a boost of 0.4 ...
    >>> qbuilder("cat")
    {'query_string': {'query': 'cat', 'default_operator': u'OR', 'fields': [u'_all']}}
    >>> qbuilder("cat", operator=u'AND')
    {'query_string': {'query': 'cat', 'default_operator': u'AND', 'fields': [u'_all']}}
    """
    #TODO: add docstring
    def __init__(self, name=None):
        super(ESQueryStringBuilder, self).__init__(name=name)
        self.add_option("operator", Text(choices=[u"AND", u"OR",], default=u"OR",
            help=u"operator used for chaining terms"))
        self.add_option("fields", Text(default=u"_all", help=u"""List of fields 
            and the 'boosts' to associate with each of them. The format
            supported is "fieldOne^2.3 fieldTwo fieldThree^0.4", which indicates
            that fieldOne has a boost of 2.3, fieldTwo has the default boost, 
            and fieldThree has a boost of 0.4 ...""")
       )

    @Optionable.check
    def __call__(self, query, fields=None, operator=None):
        query_dsl = {
            "query_string": {
                "query": query,
                "fields": fields.split(),
                "default_operator": operator,
            }
        }
        return query_dsl


class ESSearch(Optionable):
    #TODO: add docstring ? not easy with ES connection
    def __init__(self, index=None, doc_type=None, host="localhost:9200", name=None):
        super(ESSearch, self).__init__(name=name)
        self.add_option("size", Numeric(vtype=int, default=10, min=0, help="number of document to returns"))
        # configure ES connection
        self.host = host
        self._es_conn = elasticsearch.Elasticsearch(hosts=self.host)
        if not self._es_conn.ping():
            raise RuntimeError("Imposible to ping ES server at '%s'" % self.host)
        self.index = index
        self.doc_type = doc_type

    @Optionable.check
    def __call__(self, query_dsl, size=None):
        self._logger.info("query: %s" % query_dsl)
        body = {
            "query": query_dsl,
        }
        return self._es_conn.search(index=self.index, doc_type=self.doc_type, body=body, size=size)


class ESPhraseSuggest(Optionable):
    #TODO: add docstring ? not easy with ES connection
    def __init__(self, index=None, host="localhost:9200", name=None):
        super(ESPhraseSuggest, self).__init__(name=name)
        # configure ES connection
        self.host = host
        self._es_conn = elasticsearch.Elasticsearch(hosts=self.host)
        if not self._es_conn.ping():
            raise RuntimeError("Imposible to ping ES server at '%s'" % self.host)
        self.index = index

    @Optionable.check
    def __call__(self, text):
        self._logger.info("text: %s" % text)
        size = 3 #number of proposition
        body = {
            "text": text,
            "simple_phrase": {
                "phrase": {
                    "field": "intro",
                    "size": size,
                    "real_word_error_likelihood": 0.95,
                    "max_errors": 0.5,
                    "gram_size": 1,
                    "direct_generator": [{
                        "field": "intro",
                        "suggest_mode": "always",
                        "min_word_length": 1
                    }],
                    "highlight": {
                        "pre_tag": "<em>",
                        "post_tag": "</em>"
                    }
                }
            }
        }
        return self._es_conn.suggest(index=self.index, body=body)

#---

#class EsSearch(AbstractSearch):
#    """ Make a search using ElasticSearch """
#    QF = u"title^5 redirects^3 text"

#    def __init__(self, host="http://localhost:9200", idx=None, doc_type=None, lang=None, connect=True, name=None):
#        name = name or __name__
#        super(AbstractSearch, self).__init__(name)
#        self._logger = logging.getLogger(name)
#        self.es_index = EsIndex(index=idx, host=host)
#        self._es_host = host
#        self._es_idx = idx
#        self._es_doctype = doc_type
#        self._lang = lang
#        
#        if connect:
#            assert idx is not None, "No Index provided"
#            assert lang is not None, "No lang  provided"
#         
#        # FIXME
##        self.add_bool_option("in_title", True, "Search in titles")
##        self.add_bool_option("in_redirects", True, "Search in redirects")
##        self.add_option("fl", '*,score', "fields returned by solr; &fl=", str)
#        self.add_option("doc_count", Numeric(default=10, help=u"Number of results; &rows="))
#        self.add_option("operator", Text(choices=[u"AND", u"OR",], default=u"AND", 
#            help=u"operator used for chaining terms"))
#        if connect:
#            fields = sorted(self.es_index.get_fields(doc_type))
#            self.add_option("search_field",
#                            Text(choices=[u"*"] + [unicode(e) for e in fields],
#                            default=u"*", help=u"field to search")
#                            )
#        else:
#            self.add_option(
#                    "search_field", Text(default=u"text", 
#                        help=u"""field to search for matching term.
#                         If '*' one can set the boosts per field in the @param qf.""",
#                ))

#        self.add_option(
#                    "qf", Text(default=EsSearch.QF, help=u"""List of fields 
#                    and the 'boosts' to associate with each of them when building
#                    DisjunctionMaxQueries from the user's query. The format supported 
#                    is fieldOne^2.3 fieldTwo fieldThree^0.4, which indicates that
#                    fieldOne has a boost of 2.3, fieldTwo has the default boost, 
#                    and fieldThree has a boost of 0.4 ... : &qf=""")
#               )

#    def __call__(self, query, search_field=u'text', qf=QF, fl=u"", doc_count=10, operator=u"AND", raw=False):
#        """ Perform a search using the Elasticsearch
#        :param search_field: field to search for matching term. 
#          If '*' one can set the boosts per field in the @param qf.
#        :param nb_res: max count of document to be returned
#        :param qf : List of fields and the 'boosts' to associate with each fields,
#          when building DisjunctionMaxQueries from the user's query. 
#          The format supported is fieldOne^2.3 fieldTwo fieldThree^0.4, indicates
#          that fieldOne has a boost of 2.3, fieldTwo has the default boost, and 
#          fieldThree has a boost of 0.4 ... : &qf=
#          this param will be used IF and ONLY `search_field` is '*'.
#          When qf is used &defType=dismax should be set
#        """
#        self._logger.info("query: '%s'" % query)
#        idx = self._es_idx
#        doc_type = self._es_doctype
#        kdocs = []

#        get_by_id = self.es_index.get_uniq_key(doc_type) == search_field

#        if not get_by_id:
#            if search_field == "*":
#                query_string = { 
#                        "query": query,
#                        "fields": qf.split(" "),
#                        "use_dis_max": True
#                        }
#            else:
#                query_string = {
#                        "query": query,
#                        "default_field": search_field,
#                        }
#            query_dsl = {
#                    "size": doc_count,
#                    "query": {
#                        "query_string": query_string
#                        }
#                    }

#        if query:
#            if get_by_id:
#                if type(query) not in (set, list, tuple):
#                    query = [query]
#                res = self.es_index._es.mget(index=idx, doc_type=doc_type, body={'ids': query})
#                retrieved = [d for d in res["docs"] if d["found"]]
#                for rank, doc in enumerate(retrieved):
#                    kdocs.append(self.to_doc(doc, rank+1))
#            else:
#                result = self.es_index._es.search(self._es_idx, doc_type=self._es_doctype, body=query_dsl)
#                if result["hits"]["total"] > 0:      
#                    for rank, doc in enumerate(result["hits"]["hits"]):
#                        if raw == False:
#                            kdoc = self.to_doc(doc, rank+1)
#                        else:
#                            kdoc = doc
#                        kdocs.append(kdoc)
#        return kdocs

#    def to_doc(self, doc, rank):
#        raise NotImplementedError
