#-*- coding:utf-8 -*-
""" :mod:`cello.graphs.transform`
==============================
"""
import igraph as ig

from cello.pipeline import Composable, Optionable
from cello.types import Text

from cello.graphs import EDGE_WEIGHT_ATTR
from cello.graphs.prox import prox_markov_wgt


class EdgeAttr(Composable):
    """ Add one or more attributes to the edges of the graph

    >>> g = ig.Graph.Formula("a--B, a--C, a--D, C--f, D--f")
    >>> edge_label = lambda graph, edg: '-'.join(graph.vs[[edg.source, edg.target]]['name'])
    >>> add_attr = EdgeAttr(weigth=2.0, label=edge_label)
    >>> g = add_attr(g)
    >>> g.es['weigth']
    [2.0, 2.0, 2.0, 2.0, 2.0]
    >>> g.es['label']
    ['a-B', 'a-C', 'a-D', 'C-f', 'D-f']
    """
    def __init__(self, name=None, **kwargs):
        super(EdgeAttr, self).__init__(name=name)
        self._eattrs = kwargs

    def __call__(self, graph):
        for attr, value in self._eattrs.iteritems():
            if callable(value):
                graph.es[attr] = [value(graph, edg) for edg in graph.es]
            else:
                graph.es[attr] = value
        return graph


class VtxAttr(Composable):
    """ Add one or more attributes to the vertices of the graph
    
    >>> g = ig.Graph.Formula("a--B, a--C, a--D, C--f, D--f")
    >>> add_attr = VtxAttr(score=1, type=lambda graph, vtx: vtx['name'].islower())
    >>> g = add_attr(g)
    >>> g.vs["score"]
    [1, 1, 1, 1, 1]
    >>> g.vs["type"]
    [True, False, False, False, True]
    """
    def __init__(self, name=None, **kwargs):
        super(VtxAttr, self).__init__(name=name)
        self._vattrs = kwargs

    def __call__(self, graph):
        for attr, value in self._vattrs.iteritems():
            if callable(value):
                graph.vs[attr] = [value(graph, vtx) for vtx in graph.vs]
            else:
                graph.vs[attr] = value
        return graph


class GraphProjection(Optionable):
    #TODO add test
    def __init__(self, projection_wgt=None, name="PG"):
        """ Projection of a bipartite graph to a unipartite graph
        """
        Optionable.__init__(self, name)
        
        self._projection_wgt = projection_wgt
        if self._projection_wgt is None:
            self.add_option("proj_wgt", Text(default=u"p",
                 help=u"Projection weighting method",
                 choices=[u'no', u'count', u'p', u'pmin', u'pmax', u'pavg']))
    
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


