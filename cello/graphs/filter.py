#-*- coding:utf-8 -*-
""" :mod:`cello.graphs.filter`
==============================
"""
import itertools

import igraph as ig

from reliure import Composable, Optionable
from reliure.types import Numeric, Boolean

from cello.graphs import EDGE_WEIGHT_ATTR


class RemoveNotConnected(Composable):
    """" Removes not connected vertices 
    

    Here is an example:

    >>> filter = RemoveNotConnected()
    >>> g = ig.Graph.Formula("a--b--c---a, e, f")
    >>> g.vs['name']
    ['a', 'b', 'c', 'e', 'f']
    >>> g = filter(g)
    >>> g.vs['name']
    ['a', 'b', 'c']
    """
    def __call__(self, graph):
        self._logger.info("Remove not connected vertices:")
        self._logger.info("Before filtering: |V|=%d, |E|=%d" % (graph.vcount(), graph.ecount()))
        size_before = graph.ecount()
        order_before = graph.vcount()
        graph.delete_vertices(graph.vs.select(lambda x: graph.degree(x, type=ig.ALL, loops=False)==0))
        self._logger.info("%d vertices deleted" % (order_before-graph.vcount()))
        self._logger.info("%d edges deleted" % (size_before-graph.ecount()))
        self._logger.info("After filtering: |V|=%d, |E|=%d" % (graph.vcount(), graph.ecount()))
        return graph

class BottomFilter(Optionable):
    """ Removes some bottom (type=False) vertices from a bigraph.

    This component has two options:

    >>> filter = BottomFilter()
    >>> filter.print_options()
    top_min (Numeric, default=0): Removes type=False vertices connected to less than top_min (type=True) vertices
    top_max_ratio (Numeric, default=1.0): Removes type=False vertices connected to more than top_max_ratio percents of the (type=True) vertices

    Here is an example:

    >>> g = ig.Graph.Formula("a:b:c--A:B:C:D, d--D:E, c:d--F")
    >>> g.vs["type"] = [vtx["name"].islower() for vtx in g.vs]
    >>> g.vs(type=False)['name']
    ['A', 'B', 'C', 'D', 'E', 'F']
    >>> g = filter(g, top_max_ratio=0.95)
    >>> g.vs(type=False)['name']
    ['A', 'B', 'C', 'E', 'F']
    >>> g = filter(g, top_min=1)
    >>> g.vs(type=False)['name']
    ['A', 'B', 'C', 'F']
    """
    def __init__(self, name=None):
        Optionable.__init__(self, name=name)

        self.add_option("top_min", Numeric(default=0, min=0.,
            help="Removes type=False vertices connected to less than top_min (type=True) vertices"))
        self.add_option("top_max_ratio", Numeric(vtype=float, default=1., min=0., max=1.,
            help="Removes type=False vertices connected to more than top_max_ratio percents of the (type=True) vertices"))

    @Optionable.check
    def __call__(self, graph, top_min=None, top_max_ratio=None):
        """remove bottoms (type false) vertices, that are not enought connected
        or too much connected.

        :param top_min: removes v[false] if degree(g, v[false]) <= top_min
        :type top_min: int
        :param top_max_ratio: removes `v` (type=false) if `degree(g, v) >= top_max_ratio * |V_top|`
        :type top_max_ratio: float
        """
        assert graph.is_bipartite();
        top_count = len(graph.vs.select(type=True))
        self._logger.info("Before filtering: |V_top docs|=%d, |V_bottom terms|=%d, |E|=%d"\
             % (len(graph.vs.select(type=True)), len(graph.vs.select(type=False)), graph.ecount()))
        too_poor_bots = graph.vs.select(type=False, _degree_le=top_min)
        self._logger.info("%d bottoms have less than %s neighbors, will be deleted" % (len(too_poor_bots), top_min))
        too_rich_bots = graph.vs.select(type=False, _degree_gt=top_max_ratio * top_count)
        self._logger.info("%d bottoms have more than %s neighbors (%1.2f * %d), will be deleted"\
             % (len(too_rich_bots), top_max_ratio * top_count, top_max_ratio, top_count))
        graph.delete_vertices(itertools.chain(too_poor_bots, too_rich_bots))
        self._logger.info("After filtering: |V_top|=%d, |V_bottom|=%d, |E|=%d" \
            % (len(graph.vs.select(type=True)), len(graph.vs.select(type=False)), graph.ecount()))
        return graph


class EdgeCut(Optionable):
    """ Keep only a fixed number of edges.
    Edges are ordered (before the cut) according to "weight" attribute.

    >>> filter = EdgeCut()
    >>> filter.print_options()
    m (Numeric, default=0): Number of edges (with stronger weight) to keep
    remove_single (Boolean, default=True): Remove vertices with no links after filtering

    Here is an example:

    >>> g = ig.Graph.Formula("a:b:c--A:B:C:D, d--D:E, c:d--F")
    >>> g.vs["type"] = [vtx["name"].islower() for vtx in g.vs]
    >>> g.es['weight'] = [1, 2, 3, 4, 5, 6, 7, 8]
    >>> g.es['weight']
    [1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8]
    >>> g = filter(g, m=5)
    >>> print(g.summary())
    IGRAPH UNWT 7 5 -- 
    + attr: name (v), type (v), weight (e)
    >>> g.es['weight']
    [6, 7, 8, 7, 8]
    >>> g.vs['name']
    ['b', 'B', 'C', 'D', 'd', 'E', 'F']
    """
    def __init__(self, name=None):
        Optionable.__init__(self, name=name)

        self.add_option("m", Numeric(default=0, min=0.,
            help="Number of edges (with stronger weight) to keep"))
        self.add_option("remove_single", Boolean(default=True,
            help="Remove vertices with no links after filtering"))

    @Optionable.check
    def __call__(self, graph, m=None, remove_single=None):
        assert EDGE_WEIGHT_ATTR in graph.es.attributes(), "the edges should be weighted"
        self._logger.info("Before filtering: |V|=%d, |E|=%d" % (graph.vcount(), graph.ecount()))
        to_del = sorted(graph.es, key=lambda edg: edg["weight"], reverse=True)[m:]
        graph.delete_edges(to_del)
        self._logger.info("After filtering: |V|=%d, |E|=%d" % (graph.vcount(), graph.ecount()))
        if remove_single:
            graph.delete_vertices(graph.vs.select(_degree=0))
            self._logger.info("After removing singles: |V|=%d" % (graph.vcount()))
        return graph


class MaxDensity(Optionable):
    """ Remove edges with lower weight in order to ensure that the mean degree
    (i.e. density) is lower than a given threshold.

    >>> filter = MaxDensity()
    >>> filter.print_options()
    kmax (Numeric, default=10.0): Maximum mean degree

    >>> g = ig.Graph.Formula("a:b:c--A:B:C:D, d--D:E, c:d--F")
    >>> g.vs["type"] = [vtx["name"].islower() for vtx in g.vs]
    >>> g.es['weight'] = [1, 2, 3, 4, 5, 6, 7, 8]
    >>> g.es['weight']
    [1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8]
    >>> import numpy as np
    >>> np.mean(g.degree())
    3.2000000000000002
    >>> # apply the filter :
    >>> g = filter(g, kmax=2.)
    >>> np.mean(g.degree())
    2.0
    >>> # one can check that edges with smaller weight have been removed
    >>> g.es['weight']
    [4, 5, 6, 7, 8, 4, 5, 6, 7, 8]
    >>> g.vs['name']
    ['a', 'b', 'c', 'A', 'B', 'C', 'D', 'd', 'E', 'F']
    """
    def __init__(self, name=None, edge_wgt_attr=EDGE_WEIGHT_ATTR):
        super(MaxDensity, self).__init__(name=name)
        self.edge_wgt_attr = EDGE_WEIGHT_ATTR
        self.add_option("kmax", Numeric(vtype=float, default=10., min=0.1, help="Maximum mean degree"))

    @Optionable.check
    def __call__(self, graph, kmax=None):
        assert not graph.is_directed()
        if graph.vcount() > 0:
            dmean = (2. * graph.ecount()) / graph.vcount()
            self._logger.info("Mean degree is %1.3f, max is %1.3f" % (dmean, kmax))
            if dmean > kmax:
                m = int((kmax*graph.vcount())/2.)
                self._logger.info("Before filtering: |V|=%d, |E|=%d, keep only %d edges" % (graph.vcount(), graph.ecount(), m))
                to_del = sorted(graph.es, key=lambda edg: edg[self.edge_wgt_attr], reverse=True)[m:]
                graph.delete_edges(to_del)
                dmean = (2. * graph.ecount()) / graph.vcount()
                self._logger.info("After filtering: |V|=%d, |E|=%d, <k>=%1.3f" % (graph.vcount(), graph.ecount(), dmean))
        return graph


class GenericVertexFilter(Optionable):
    """ Remove vertices selected by a custom filter.

    >>> remove_filter = lambda vtx: vtx["name"].islower()
    >>> filter = GenericVertexFilter(remove_filter)

    Here is an example:

    >>> g = ig.Graph.Formula("a:b:c--A:B:C:D, d--D:E, c:d--F")
    >>> g.vs['name']
    ['a', 'b', 'c', 'A', 'B', 'C', 'D', 'd', 'E', 'F']
    >>> g = filter(g)
    >>> g.vs['name']
    ['A', 'B', 'C', 'D', 'E', 'F']
    """
    def __init__(self, vtx_select, name=None):
        Optionable.__init__(self, name=name)
        self._vtx_select = vtx_select

    @Optionable.check
    def __call__(self, graph):
        self._logger.info("Filter vertices:")
        self._logger.info("Before filtering: |V|=%d, |E|=%d" % (graph.vcount(), graph.ecount()))
        size_before = graph.ecount()
        to_del = graph.vs.select(self._vtx_select)
        graph.delete_vertices(to_del)
        self._logger.info("%d vertices deleted" % (len(to_del)))
        self._logger.info("%d edges deleted" % (size_before-graph.ecount()))
        self._logger.info("After filtering: |V|=%d, |E|=%d" % (graph.vcount(), graph.ecount()))
        return graph


class GenericEdgeFilter(Optionable):
    """ Remove edges selected by a custom filter.


    Here is an example:

    >>> g = ig.Graph.Formula("a:b:c--A:B:C:D, d--D:E, c:d--F")
    >>> g.es["w"] = range(g.ecount())
    >>> g.es["w"]
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    >>> remove_filter = lambda edge: edge["w"] < 10
    >>> filter = GenericEdgeFilter(remove_filter)
    >>> g = filter(g)
    >>> g.es["w"]   
    [10, 11, 12, 13, 14, 15]
    """
    def __init__(self, edg_select, name=None):
        Optionable.__init__(self, name=name)
        self._edg_select = edg_select

    @Optionable.check
    def __call__(self, graph):
        self._logger.info("Filter edges:")
        self._logger.info("Before filtering: |V|=%d, |E|=%d" % (graph.vcount(), graph.ecount()))
        size_before = graph.ecount()
        to_del = graph.es.select(self._edg_select)
        graph.delete_edges(to_del)
        self._logger.info("%d edges deleted" % (size_before-graph.ecount()))
        self._logger.info("After filtering: |V|=%d, |E|=%d" % (graph.vcount(), graph.ecount()))
        return graph


