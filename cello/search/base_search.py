#-*- coding:utf-8 -*-
""" :mod:`cello.search.base_search`
====================================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

Cello basic search components

All search components returns a ordered list of :class:`Doc`

* AbstractSearch
* GraphProxSearch
"""
#TODO: Question: est-ce que les searchers ne doivent pas faire comme les tokenizers 
# dans Whoosh, c'est a dire retourné juste un générateurs, et ne pas créer
# un obj par document ???
import logging

import igraph as ig #TODO: pas térible d'avoir le import igraph ici

from reliure import Optionable

from reliure.types import Numeric, Text
from cello.schema import Schema, Doc


class AbstractSearch(Optionable):
    def __init__(self, name ):
        Optionable.__init__(self, name)
    
    def set_options(): pass
    
    def search(): pass
    
    def __call__(self, query, **kwargs):
        """ Search method itself
        
        :param query: query string 
        :type query: str
        
        :param kwargs: class dependant options
        :type kwargs: dict
        
        :returns: a  set of :class:`Doc` 
        
        :see: :class:`Optionable`
        """
        raise NotImplementedError("Should be implemented in a inherited class")


class GraphProxSearch(AbstractSearch):
    """ Search in a simple graph (an igraph.Graph object)
    """
    
    #TODO: pour avoir d'autre extract que ProxMarkov:
    # passer ceette class en Abstract, et choix du 'prox' dans class filles (methode protected _extract)

    def __init__(self, graph, name="simple_graph_search", copy=[]):
        """ Initialise searcher with the graph.
        @param kgraph: the L{KodexGraph} to use,
        """
        AbstractSearch.__init__(self, name)
        self._logger = logging.getLogger(__name__)
        self.graph = graph
        self.attrs_to_copy = copy
        
        self.add_option("nb_results", Numeric(default=30, 
            help="Max number of vertices to retrieve"))
        self.add_option("l", Numeric(default=3, help="length of the random walk"))

    def _query_to_p0(self, query):
        """ Transform the query to a list of initial graph ids
        """ 
        vtx_names = query.split(";") #XXX: separateur
        vtx_names = [vname.strip() for vname in vtx_names]
        
        # construction d un index inverse sur les labels
        vindex = dict(zip( self.graph.vs['label'], self.graph.vs.indices ) )
        # recherche des label query
        p0 = [ vindex[vname] for vname in vtx_names if vname in vindex]

        if len(p0) < len(vtx_names):  # certain sommets n'ont pas été trouvé...
            raise IndexError("Some vertices not found !")
            #TODO: si certain sommets ne sont pas trouver, on met *juste* un warning mais on balance les résultats que l'on a quand meme
        return p0

    def search(self, p0, nb_results, l):
        """ retrive a 'nb_results' number of vertices by random walk starting from p0
        """
        from cello.graphs import prox
        global_graph = self.graph
        #TODO: choix de la méthode d'extraction
        #TODO: forcer la reflexivité ou pas
        neighbors_fct = lambda graph, vtx: graph.neighbors(vtx) + [vtx]
        pline = prox.prox_markov(global_graph, p0, neighbors_fct=neighbors_fct, l=l)
        v_extract = prox.sortcut(pline, nb_results)
        return v_extract
    
    def _build_result_set(self, v_extract):
        """ Building of the Doc list from the list of retrived vertices """
        
        vid_to_docnum = lambda vid: "%d" % vid
        global_graph = self.graph
        
        kdocs = []
        
        schema = Schema(
            docnum=Numeric(),
            degree_out=Numeric(),
            degree_in=Numeric(),
            score=Numeric(vtype=float),
            label=Text(),
            neighbors=Numeric(multi=True, uniq=True)
        )
        for vid, score in v_extract:
            kdoc = Doc(schema, docnum=vid)
            kdoc.score = score
            vtx = global_graph.vs[vid]
            # autres attributs
            kdoc.degree_out = vtx.degree(ig.OUT)
            kdoc.degree_in = vtx.degree(ig.IN)
            kdoc.label = vtx['label']
            # les voisins sont dans un term field
            for nei in vtx.neighbors(): #TODO: ajout IN/OUT ?
                kdoc["neighbors"].add( nei.index) #TODO ajout d'un poids !
            
            # on ajoute le doc
            kdocs.append(kdoc)
        return kdocs
    
    def __call__(self, query, nb_results=30, l=3):
        """ 
        params : see options in __init__ ()
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
        v_extract = self.search(p0, nb_results, l)
        #setp3 construction du result set
        kdocs = self._build_result_set(v_extract)
        
        self._logger.info("get %d vertices" % (len(kdocs)))
        return kdocs



