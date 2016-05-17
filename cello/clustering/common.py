#-*- coding:utf-8 -*-
""" :mod:`cello.clustering.common`
=================================

Mostly wrapper to igraph clustering methods
"""
import igraph as ig

from reliure.types import Numeric

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

    >>> g = ig.Graph.Formula("e")
    >>> g.es[EDGE_WEIGHT_ATTR] = []       # basic weights
    >>> clustering(g).membership
    [[]]

    Note: this last exemple illustrate a bug in igraph when there is a simple
    pair of adjacent vertices and some singletons. There is a fix in the code
    to avoid this issue.

    >>> g = ig.Graph.Formula("a--b, e")
    >>> g.es[EDGE_WEIGHT_ATTR] = [1.]       # basic weights
    >>> clustering(g).membership
    [[0], [0], [1]]

    """
    def __init__(self, name=None):
        super(Walktrap, self).__init__(name=name)
        self.add_option("l", Numeric(default=4, help="lenght of the random walks"))

    def __call__(self, graph, l=4):
        if self.graph_is_trivial(graph, weighted=True):
            return ig.VertexCover(graph, [])
        vertex_clustering = graph.community_walktrap(weights=graph.es[EDGE_WEIGHT_ATTR], steps=l)
        #self.fix_dendrogram(graph, vertex_clustering)
        merges = vertex_clustering.merges
        n = graph.vcount()
        singles = graph.vs.select(_degree=0)
        for vtx in singles:
            last_merge = n - len(singles) + len(merges) - 1
            merges.append((last_merge, vtx.index))
        fixed_vertex_clustering = ig.VertexDendrogram(
            graph,
            merges,
            vertex_clustering.optimal_count,
            modularity_params=dict(weights=graph.es[EDGE_WEIGHT_ATTR])
        )
        return fixed_vertex_clustering.as_clustering().as_cover()

    def fix_dendrogram(self, graph, cl):
        """ Fix the dendrogramm to add singletons because igraph forget it...
        """
        #TODO: code proposé par yann dans  Commit 5fb4db847d394fc44b838a09fae6f77eaf849861 
        #TODO: j'ai une erreur sur le doctest avec ce code... et je ne capte pas ce qu'il fait, desactivé pour le moment
        from itertools import izip
        already_merged = set()
        for merge in cl.merges:
            already_merged.update(merge)

        num_dendrogram_nodes = graph.vcount() + len(cl.merges)
        not_merged_yet = sorted(set(xrange(num_dendrogram_nodes)) - already_merged)
        if len(not_merged_yet) < 2:
            return

        v1, v2 = not_merged_yet[:2]
        cl._merges.append((v1, v2))
        del not_merged_yet[:2]

        missing_nodes = xrange(num_dendrogram_nodes,
                num_dendrogram_nodes + len(not_merged_yet))
        cl._merges.extend(izip(not_merged_yet, missing_nodes))
        cl._nmerges = graph.vcount()-1


class Infomap(ClusteringMethod):
    """ Infomap clustering method

    .. note:: the graph edges should have a 'weight' on attribute (see cello.graphs.EDGE_WEIGHT_ATTR)

    .. see_also: :func:`igraph.Graph.community_walktrap`
    
    >>> g = ig.Graph.Formula("a:b--b:c:d, e--f")
    >>> g.es[EDGE_WEIGHT_ATTR] = [1.]       # basic weights
    >>> clustering = Infomap()
    >>> clustering(g).membership    # here, should be same as connected components
    [[0], [0], [0], [0], [1], [1]]

    >>> g.es[EDGE_WEIGHT_ATTR] = [0.]       # Graph as 'no' real edge
    >>> clustering(g).membership
    [[], [], [], [], [], []]

    >>> g = ig.Graph.Formula("e")
    >>> g.es[EDGE_WEIGHT_ATTR] = []       # basic weights
    >>> clustering(g).membership
    [[]]

    >>> g = ig.Graph(n=5)           # in case of graph with no edge
    >>> clustering(g).membership
    [[], [], [], [], []]
    """
    def __init__(self, name=None):
        super(Infomap, self).__init__(name=name)

    def __call__(self, graph):
        if self.graph_is_trivial(graph, weighted=True):
            return ig.VertexCover(graph, [])
        vertex_clustering = graph.community_infomap(edge_weights=graph.es[EDGE_WEIGHT_ATTR])
        return vertex_clustering.as_cover()

