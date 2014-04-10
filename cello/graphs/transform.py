#-*- coding:utf-8 -*-
""" :mod:`cello.graphs.transform`
==============================
"""
import igraph as ig

import logging

from cello.pipeline import Composable, Optionable
from cello.types import Text

from cello.graphs import EDGE_WEIGHT_ATTR
from cello.graphs.prox import prox_markov_wgt


_logger = logging.getLogger("cello.graphs.transform")


class EdgeAttr(Composable):
    """ Add one or more attributes to the edges of the graph

    >>> g = ig.Graph.Formula("a--B, a--C, a--D, C--f, D--f")
    >>> edge_label = lambda graph, edg: '-'.join(graph.vs[[edg.source, edg.target]]['name'])
    >>> add_attr = EdgeAttr(weight=2.0, label=edge_label)
    >>> g = add_attr(g)
    >>> g.es['weight']
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

class TrueInFirst(Composable):
    """ Permute bigraph vertices to move True vertices in first places.

    >>> true_in_first = TrueInFirst()
    >>> g = ig.Graph.Formula("a:b:c--A:B:C:D, d--D:E, c:d--F")
    >>> g.vs["type"] = [vtx["name"].islower() for vtx in g.vs]
    >>> g.vs["name"]
    ['a', 'b', 'c', 'A', 'B', 'C', 'D', 'd', 'E', 'F']
    >>> ng = true_in_first(g)
    >>> ng.vs["name"]
    ['a', 'b', 'c', 'd', 'A', 'B', 'C', 'D', 'E', 'F']
    """
    def __init__(self, name=None):
        super(TrueInFirst, self).__init__(name=name)

    def __call__(self, bigraph):
        new_ids = {vtx.index: vid for vid, vtx in enumerate(bigraph.vs.select(type=True))}
        nb_true = len(new_ids)
        new_ids.update({vtx.index: nb_true+vid for vid, vtx in enumerate(bigraph.vs.select(type_ne=True))})
        new_order = [new_ids[vid] for vid in xrange(bigraph.vcount())]
        bigraph_true_first = bigraph.permute_vertices(new_order)
        return bigraph_true_first


class GraphProjection(Optionable):
    """ Project a bipartite graph to an unipartite one

    >>> projection = GraphProjection()
    >>> projection.print_options()
    proj_wgt (Text, default=p): projection weighting method

    .. Warning:: The bipartite graph should have True vertices in first in
        vertex sequence, if not see  :class:`TrueInFirst`:.

    This could be used without weights on original graph:

    >>> g = ig.Graph.Formula("a:b:c--A:B:C:D, d--D:E, c:d--F")
    >>> g.vs["type"] = [vtx["name"].islower() for vtx in g.vs]

    As the graph do not have True vertices in first we add :class:`TrueInFirst`:

    >>> projection = TrueInFirst() | GraphProjection()

    One can then compute a projection without weights:

    >>> gp = projection(g, proj_wgt='no')
    >>> gp.vs["name"]
    ['a', 'b', 'c', 'd']
    
    Note that edges always have weight attribute:
    
    >>> gp.es["weight"]
    [1, 1, 1, 1, 1, 1]

    One can also use the weight to coun the number of commun neighbors in the
    original bipartite graph:
    
    >>> gp = projection(g, proj_wgt='count')
    >>> gp.es["weight"]
    [4, 4, 1, 4, 1, 2]


    For other projection weighting we need to add a weight on the graph

    >>> add_weight = EdgeAttr(weight=1.0)
    >>> g = add_weight(g)
    >>> g.es["weight"]
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]


    Then different weight are possible (see :meth:`GraphProjection.bigraph_projection`):
    
    >>> gp = projection(g, proj_wgt='p')
    >>> gp.es["weight"]
    [1.25, 1.25, 0.25, 1.25, 0.25, 0.7500000000000001]
    >>> gp = projection(g, proj_wgt='pavg')
    >>> gp.es["weight"]
    [0.3125, 0.28125, 0.07291666666666666, 0.28125, 0.07291666666666666, 0.2]
    >>> gp = projection(g, proj_wgt='confl')
    >>> gp.es["weight"]
    [0.5555555555555556, 0.5, 0.25, 0.5, 0.25, 0.4444444444444445]
    """
    #TODO add test
    def __init__(self, name=None):
        """ Projection of a bipartite graph to a unipartite graph
        """
        Optionable.__init__(self, name=name)
        self.add_option("proj_wgt", Text(default='p', vtype=str,
             help=u"projection weighting method",
             choices=['no', 'count', 'p', 'pmin', 'pmax', 'pavg', 'confl']))

    @Optionable.check
    def __call__(self, graph, proj_wgt=None):
        # The projection work only because:
        #  - documents are the first vertices of the graph
        #  - the projection fct do not change the vertices order
        # this two points are checked with following assert
        if __debug__:
            docids = [vtx.index for vtx in graph.vs.select(type=True)]
            assert sorted(docids) == range(max(docids) + 1), \
                "Documents should be the first veritces of the graph"
        pgraph = GraphProjection.bigraph_projection(graph, proj_wgt, wgt_attr=EDGE_WEIGHT_ATTR)
        if __debug__ and "_doc" in graph.vs.attributes():
            assert pgraph.vs["_doc"] == graph.vs.select(type=True)["_doc"]
        return pgraph

    @staticmethod
    def bigraph_projection(graph, weight=None, wgt_attr=EDGE_WEIGHT_ATTR):
        """ Projection of a bipartite graph
    
            .. note:: this method is static it may be use independently

            weight:
                - 'count': number of neighbors in commun
                - 'p': 
                    :math:`w(u, v) = p(u\\rightarrow v, t=2) . deg(u) = p(v \\rightarrow u, t=2) . deg(v)`
                - 'confl': 
                    :math:`w(u, v) = \\frac{ p(u\\rightarrow v, t=2) }{p(u \\rightarrow v, t=2) + \\pi_v} \\quad`
                    avec 
                    :math:`\\quad \\pi_v = \\frac{deg(v)}{ \\sum_j deg(j)}`
                - 'pmin': 
                    :math:`w(u, v) = \\min\\big(p(u\\rightarrow v, t=2), \quad p(v \\rightarrow u, t=2) \\big )`
                - 'pmax':  
                    :math:`w(u, v) = \\max\\big(p(u\\rightarrow v, t=2), \quad p(v \\rightarrow u, t=2) \\big )`
                - 'pavg':
                    :math:`w(u, v) = \\frac{1}{2} . \\big ( p(u\\rightarrow v, t=2) + p(v \\rightarrow u, t=2)\\big )`
                - else: no weight
        """
        multiplicity = True if weight == "count" else False
        pg, _ = graph.bipartite_projection(types="type", multiplicity=multiplicity, probe1=0)
        if weight in ["p", "pmin", "pmax", "pavg", "confl"]:
            _wgt = lambda v1,v2: graph.es[graph.get_eid(v1,v2)][wgt_attr]
            P = [prox_markov_wgt(graph, [vid.index], l=2, wgt=_wgt, false_refl=False) for vid in pg.vs]
            if weight == "p":
                pwgt = lambda a, b: P[a].get(b, 0.) * graph.degree(a)
            elif weight == "confl":
                degtot = 1. * sum(graph.vs.select(type=True).degree())
                pwgt = lambda a, b: P[a].get(b, 0.) / ( P[a].get(b, 0.) + graph.degree(b)/degtot )
            elif weight == "pmin":
                pwgt = lambda a, b: min(P[a].get(b, 0.), P[b].get(a, 0.))
            elif weight == "pmax":
                pwgt = lambda a, b: max(P[a].get(b, 0.), P[b].get(a, 0.))
            elif weight == "pavg":
                pwgt = lambda a, b: (P[a].get(b, 0.) + P[b].get(a, 0.)) / 2.
            pg.es[wgt_attr] = [pwgt(edg.source, edg.target) for edg in pg.es]
        elif weight == "count":
            pass
        else:
            pg.es[wgt_attr] = 1

        # clear nul edges.keys
        null_edges = [e.index for e in pg.es if e[wgt_attr] - 1e-6 <= 0]
        _logger.info("Deletion of %d null edges" % (len(null_edges)))
        
        pg.delete_edges(null_edges)
        return pg


