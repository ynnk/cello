#!/usr/bin/env python
#-*- coding:utf-8 -*-
import logging        

from cello import Composable
from cello.graphs import EDGE_WEIGHT_ATTR
from cello.graphs.prox import prox_markov_wgt

_logger = logging.getLogger("cello.graphs.transform")


class GraphProjection(Composable):
    def __init__(self, projection_wgt=None, name="PG"):
        """ Projection of a bipartite graph to a unipartite graph of KodexDoc
        """
        Composable.__init__(self, name)
        self._logger = logging.getLogger(self.__class__.__name__)
        
        self._projection_wgt = projection_wgt
        if self._projection_wgt is None:
            self.add_enum_option("proj_wgt",
                                 ['no', 'count', 'p', 'pmin', 'pmax', 'pavg'],
                                 "p",
                                 "Projection weighting method",
                                 str)
    
    def __call__(self, graph, proj_wgt="p"):
        # The projection work only because:
        #  - documents are the first vertices of the graph
        #  - the projection fct do not change the vertices order
        # this two points are checked with following assert
        if __debug__:
            docids = [vtx.index for vtx in graph.vs.select(type=True)]
            assert sorted(docids) == range(max(docids) + 1), \
                "Documents should be the first veritces of the graph"
        if not self._projection_wgt is None:
            proj_wgt = self._projection_wgt
        pgraph = GraphProjection.bigraph_projection(graph, proj_wgt, wgt_attr=EDGE_WEIGHT_ATTR)
        assert pgraph.vs["_doc"] == graph.vs.select(type=True)["_doc"]
        return pgraph

    @staticmethod
    def bigraph_projection(graph, weight=None, wgt_attr=EDGE_WEIGHT_ATTR):
        """
            weight:
                - 'count' : number of terms in commun
                - 'p' :  p(A->B, t=2) * deg(A) == p(B->A, t=2) * deg(B)
                - 'pmin' :  min( p(A->B, t=2), p(B->A, t=2) )
                - 'pmax' :  max( p(A->B, t=2), p(B->A, t=2) )
                - 'pavg' :  mean( p(A->B, t=2), p(B->A, t=2) )
                - else : no weight
        """
        multiplicity = True if weight == "count" else False
        pg, _ = graph.bipartite_projection(types="type", multiplicity=multiplicity, probe1=0)
        
        if weight in ["p", "pmin", "pmax", "pavg"]:
            _wgt = lambda v1,v2: graph.es[graph.get_eid(v1,v2)][wgt_attr]
            P = [prox_markov_wgt(graph, [vid.index], l=2, wgt=_wgt, false_refl=False) for vid in pg.vs]
            if weight == "p":      pwgt = lambda a, b: P[a].get(b, 0.) * graph.degree(a)
            elif weight == "pmin": pwgt = lambda a, b: min(P[a].get(b, 0.), P[b].get(a, 0.))
            elif weight == "pmax": pwgt = lambda a, b: max(P[a].get(b, 0.), P[b].get(a, 0.))
            elif weight == "pavg": pwgt = lambda a, b: (P[a].get(b, 0.) + P[b].get(a, 0.)) / 2.
            pg.es[wgt_attr] = [pwgt(edg.source, edg.target) for edg in pg.es]
        elif weight == "count":  pass
        else:
            pg.es[wgt_attr] = 1

        # clear nul edges.keys
        null_edges = [e.index for e in pg.es if e[wgt_attr] - 1e-6 <= 0]
        _logger.info("Deletion of %d null edges" % (len(null_edges)))
        
        pg.delete_edges(null_edges)
        return pg


