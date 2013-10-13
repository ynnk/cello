#!/usr/bin/env python
#-*- coding:utf-8 -*-
""" Linear search 
    
    returns a ordered list of L{Doc}

    * AbstractSearch
    * GraphProxSearch
G{classtree AbstractSearch}
"""


#TODO: Question: est-ce que les searchers ne doivent pas faire comme les tolkenizers 
# dans Whoosh, c'est a dire retourné juste un générateurs, et ne pas créer
# un obj par document ???
import logging

from cello.pipeline import Optionable
from cello.models import Doc

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



class GraphProxSearch(AbstractSearch):
    """ Search in a simple graph (an igraph.Graph object)
    """
    #TODO: pour avoir d'autre extract que ProxMarkov:
    # passer ceette class en Abstract, et choix du 'prox' dans class filles (methode protected _extract)

    import igraph as ig

    def __init__(self, kgraph, name="simple_graph_search"):
        """ Initialise searcher with the graph.
        @param kgraph: the L{KodexGraph} to use,
        """
        AbstractSearch.__init__(self, name)
        self._logger = logging.getLogger("kodex.search.GraphProxSearch")
        self._kgraph = kgraph
        
        self.add_option("nb_results", 30, "Max number of vertices to retrieve", int)
        self.add_option("l", 3, "lenght of the random walk", int)

    def _query_to_p0(self, query):
        """ Transform the query to a list of initial graph ids
        """ 
        vtx_names = query.split(";") #XXX: separateur
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
        """ Building of the Doc list from the list of retrived vertices """
        
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
        v_extract = self._prox_search(p0, nb_results, l)
        #setp3 construction du result set
        kdocs = self._build_result_set(v_extract)
        
        self._logger.info("get %d vertices" % (len(kdocs)))
        return kdocs



