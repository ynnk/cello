#!/usr/bin/env python
#-*- coding:utf-8 -*-
""" Linear search 
returns a ordered list of L{KodexDoc}

G{classtree AbstractSearch}
"""

__author__ = "Emmanuel Navarro <navarro@irit.fr>"
__copyright__ = "Copyright (c) 2011 Emmanuel Navarro"
__license__ = "GPL"
__version__ = "0.1"
__cvsversion__ = "$Revision: $"
__date__ = "$Date: $"

#TODO: Question: est-ce que les searchers ne doivent pas faire comme les tolkenizers 
# dans Whoosh, c'est a dire retourné juste un générateurs, et ne pas créer
# un obj par document ???
import logging

from os.path import join as join_dir

from kodex import Optionable
from kodex.models import KodexDoc
from kodex.index import KodexIndexError

class AbstractSearch(Optionable):
    def __init__(self, name ):
        Optionable.__init__(self, name)
        
    def __call__(self, query, **kargs):
        """ Callable search 
        @param query: query string 
        @type query: L{str}
        
        @param kargs: class dependant options
        @type kargs: L{dict}
        @return: a  set of L{KodexDoc} 
        @see: L{Optionable}
        """
        raise NotImplemented, "Should be implemented in a inherited class"


#XXX: est-ce que cette class n'est pas utile juste pour l'éval ? cad a bouger dans expe/eval.py
class JsonReadSearch(AbstractSearch):
    """ Read the search result for a json stored on the local disk
    """

    def __init__(self, json_path,  name='JsonReadSearch'):
        AbstractSearch.__init__(self, name)
        self._logger = logging.getLogger("kodex.JsonRea dSearch")
        self.add_option("retrieved_count", 10, "Max number of document to retrieve", int )
        if isinstance(json_path, unicode):
            json_path = json_path.decode("utf8")
        self.json_path = json_path

    def __repr__(self):
        return "JsonReadSearch: %s (%s)" % (self.name, self.json_path)
    
    def __call__(self, query, retrieved_count=10):
        assert self.json_path is not None, "'self.json_path' should not be None"
        
        filename = self._get_filename(query, retrieved_count )
        docs = self._read_json(filename)
        return docs

    def _get_filename(self, query, nb_docs):
        assert isinstance(query, unicode)
        filname = "%s-%s.json" % (query, nb_docs)
        return join_dir(self.json_path, filname)

    def _read_json(self, filename):
        self._logger.info("Read %s" % filename)
        import simplejson as json
        json_file = open(filename)
        docs_raw = json.load(json_file)
        json_file.close()
        docs = []
        for idx, docnum in enumerate(docs_raw["docnums"]):
            kdoc = KodexDoc(docnum)
            #TODO: ne lit que les docnum pour le moment
            
            kdoc['length'] =  docs_raw['doclength'][idx]
            kdoc.declare_field("terms")
            kdoc.declare_attr_field("terms_bm25")
            kdoc.declare_attr_field("terms_tf")
            kdoc.declare_attr_field("terms_df")
            kdoc.declare_attr_field("terms_TF")

            for _ti, term in enumerate(docs_raw['terms'][idx]):
                tid, form, tf, bm25, df, TF  = term
                kdoc.add_element("terms", form)
                kdoc.set_element_attr('terms_bm25', form, bm25)
                kdoc.set_element_attr('terms_tf', form, tf)
                kdoc.set_element_attr('terms_df', form, df)
                kdoc.set_element_attr('terms_TF', form, TF)
            #self._logger.debug("Read doc: '%s'" % (kdoc))
            docs.append(kdoc)
            
        return docs


class DocnumSearch(AbstractSearch):
    """ Construct result set from a list of docnum given in the query
    (separated by ';' considered as AND).
    """
    def __init__(self, index, name="docnum_search"):
        AbstractSearch.__init__(self, name)
        self._index = index
        
    def __repr__(self):
        return "%s ( %s )"% (self.name , self._index)
     
    def __call__(self, query):
        docnums = query.split(";")
        docs = []
        for docnum in docnums:
            if self._index.has_document(docnum):
                doc = KodexDoc(docnum)
                docs.append(doc)
        print docs
        return docs

class InvertedIndexSearch(AbstractSearch):
    """ Search in the inverted index.
    Returns intersection of matching document L{KodexDoc} of all term of the query.
    the query is splited by the query_tolkeniser function, considered as AND.
    """
    def __init__(self, inverted_index, query_tolkeniser=None, name="inverted_index_search"):
        """ Initialise searcher with inverted index.
        @param inverted_index: the L{InvertedIndex} used for searching
        @param query_tolkeniser: function that split the query in different forms, by default it split the query on ';'
        """
        AbstractSearch.__init__(self, name)
        self._logger = logging.getLogger("kodex.search.InvertedIndexSearch")
        self._inverted_index = inverted_index
        if query_tolkeniser == None:
            self._query_tolkeniser = lambda query: query.split(";")
        else:
            self._query_tolkeniser = query_tolkeniser
        
    def __repr__(self):
        return "%s ( %s )"% (self.name , self._inverted_index)
    
    def __call__(self, query):
        """ Intersects results of each part_of_query: implement research AND.
        results of a word: posting list of word in inverted index
        
        @param query: the query
        @type query: str
        
        @return : docnums docs that contain, in their (all terms) all words of query. 
        @rtype : list of L{KodexDoc}
        """
        self._logger.info("Boolean AND search: '%s'" % query)
        tokens = self._query_tolkeniser(query)
        token_total = len(tokens)
        token_in_idx = 0
        docnums = set([])
        for token in tokens:
            try:
                kLU = self._inverted_index.get_term(token)
                if token_in_idx == 0 : docnums = set(kLU.posting) # First term
                else: docnums.intersection_update(kLU.posting) #set of docnums
                token_in_idx += 1
            except KodexIndexError as error:
                self._logger.warn(error)
        self._logger.debug("%d/%d tokens present in the index" % (token_in_idx, token_total))
        self._logger.info("get %d documents" % (len(docnums)))
        return [KodexDoc(docnum) for docnum in docnums]


class KGraphProxSearch(AbstractSearch):
    """ Search in a simple graph (an igraph.Graph object)
    """
    #TODO: pour avoir d'autre extract que ProxMarkov:
    # passer ceette class en Abstract, et choix du 'prox' dans class filles (methode protected _extract)

    def __init__(self, kgraph, name="simple_graph_search"):
        """ Initialise searcher with the graph.
        @param kgraph: the L{KodexGraph} to use,
        """
        AbstractSearch.__init__(self, name)
        self._logger = logging.getLogger("kodex.search.KGraphProxSearch")
        self._kgraph = kgraph
        
        self.add_option("nb_results", 30, "Max number of vertices to retrieve", int)
        self.add_option("l", 3, "lenght of the random walk", int)

    def _query_to_p0(self, query):
        """ Transform the query to a list of initial graph ids
        """ 
        vtx_names = query.split(";") #XXX: separateur en dur, pas cool
        vtx_names = [vname.strip() for vname in vtx_names]
        #TODO: etre plus souple sur le séparateur
        #TODO: avoir un format de query plus chiadé (genre des poids sur chaque mot)
        p0 = [self._kgraph.vindex[vname] for vname in vtx_names if vname in self._kgraph.vindex]
        if len(p0) < len(vtx_names):  # certain sommets n'ont pas été trouvé...
            raise IndexError("Some vertices not found !")
            #TODO: si certain sommets ne sont pas trouver, on met *juste* un warning mais on balance les résultats que l'on a quand meme
        return p0

    def _prox_search(self, p0, nb_results, l):
        """ retrive a 'nb_results' number of vertices by random walk starting from p0
        """
        from kodex.utils import prox
        global_graph = self._kgraph.graph
        #TODO: choix de la méthode d'extraction
        #TODO: forcer la reflexivité ou pas
        neighbors_fct = lambda graph, vtx: graph.neighbors(vtx) + [vtx]
        pline = prox.prox_markov(global_graph, p0, neighbors_fct=neighbors_fct, l=l)
        v_extract = prox.sortcut(pline, nb_results)
        return v_extract
    
    def _build_result_set(self, v_extract):
        """ Building of the KodexDoc list from the list of retrived vertices """
        import igraph as ig
        vid_to_docnum = lambda vid: "%d" % vid
        global_graph = self._kgraph.graph
        kdocs = []
        for vid, score in v_extract:
            kdoc = KodexDoc(vid_to_docnum(vid))
            kdoc.score = score
            vtx = global_graph.vs[vid]
            vtx["kgraph_id"] = vid
            # recopie des attribue du sommet dans le KodexDoc
            kdoc.update(vtx.attributes())
            # autres attributs
            kdoc.degree_out = vtx.degree(ig.OUT)
            kdoc.degree_in = vtx.degree(ig.IN)
            # les voisins sont dans un term field
            # TODO: est-ce que c'est nécéssaire ?
            kdoc.declare_field("neighbors")
            for nei in vtx.neighbors(): #TODO: ajout IN/OUT ?
                kdoc.add_element("neighbors", vid_to_docnum(nei.index)) #TODO ajout d'un poids !
            # on ajoute le doc
            kdocs.append(kdoc)
        return kdocs
    
    def __call__(self, query, nb_results=30, l=3):
        """ 
        params : voir definitions des options
        """
        self._logger.info("KGraphProxSearch query: '%s'" % query)
        
        query = query.strip()
        if len(query) == 0: # pas de query
            return []
        
        #step1: extraction du P0
        try:
            p0 = self._query_to_p0(query)
        except IndexError:
            self._logger.error("Some vertices not found !")
            return []
        #step2: recuperation des sommets
        v_extract = self._prox_search(p0, nb_results, l)
        #setp3 construction du result set
        kdocs = self._build_result_set(v_extract)
        
        self._logger.info("get %d vertices" % (len(kdocs)))
        return kdocs



