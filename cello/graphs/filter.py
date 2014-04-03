#-*- coding:utf-8 -*-
""" :mod:`cello.graphs.filter`
==============================
"""
import itertools

import igraph as ig

from cello.pipeline import Optionable
from cello.types import Numeric

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
    def __init__(self):
        name = self.__class__.__name__
        Optionable.__init__(self, name)

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

