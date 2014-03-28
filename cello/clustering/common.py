#-*- coding:utf-8 -*-
""" :mod:`cello.clustering.common`
=================================

Mostly wrapper to igraph clustering methods
"""
import igraph as ig

from cello.types import Numeric
from cello.graphs import EDGE_WEIGHT_ATTR
from cello.clustering.core import ClusteringMethod


class Walktrap(ClusteringMethod):
    """ Walktrap clustering method

    .. note:: the graph edges should have a 'weight' on attribute (see cello.graphs.EDGE_WEIGHT_ATTR)

    .. see_also: :func:`igraph.Graph.community_walktrap`
    
    >>> g = ig.Graph.Formula("a:b--b:c:d, e--f")
    >>> g.es[EDGE_WEIGHT_ATTR] = [1.]       # basic weights
    >>> clustering = Walktrap()
    >>> clustering(g).membership    # here, should be same as connected components
    [[0], [0], [0], [0], [1], [1]]

    >>> g.es[EDGE_WEIGHT_ATTR] = [0.]       # Graph as 'no' real edge
    >>> clustering(g).membership
    [[], [], [], [], [], []]
    """
    def __init__(self, name=None):
        super(Walktrap, self).__init__(name=name)
        self.add_option("l", Numeric(default=4, help="lenght of the random walks"))

    def __call__(self, graph, l=4):
        if self.graph_is_trivial(graph, weighted=True):
            return ig.VertexCover(graph, [])
        vertex_clustering = graph.community_walktrap(weights=EDGE_WEIGHT_ATTR, steps=l)
        return vertex_clustering.as_clustering().as_cover()


class Infomap(ClusteringMethod):
    """ Infomap clustering method

    .. note:: the graph edges should have a 'weight' on attribute (see cello.graphs.EDGE_WEIGHT_ATTR)

    .. see_also: :func:`igraph.Graph.community_walktrap`
    
    >>> g = ig.Graph.Formula("a:b--b:c:d, e--f")
    >>> g.es[EDGE_WEIGHT_ATTR] = [1.]       # basic weights
    >>> clustering = Infomap()
    >>> clustering(g).membership    # here, should be same as connected components
    [[0], [0], [0], [0], [1], [1]]

    >>> g = ig.Graph(n=5)           # in case of graph with no edge
    >>> clustering(g).membership
    [[], [], [], [], []]
    """
    def __init__(self, name=None):
        super(Infomap, self).__init__(name=name)

    def __call__(self, graph):
        if self.graph_is_trivial(graph, weighted=True):
            return ig.VertexCover(graph, [])
        vertex_clustering = graph.community_infomap(edge_weights=EDGE_WEIGHT_ATTR)
        return vertex_clustering.as_cover()

