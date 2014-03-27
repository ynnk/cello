#-*- coding:utf-8 -*-
""" :mod:`cello.clustering.core`
================================

Define abstract clustering class and some trivial ones
"""
import igraph as ig

from cello.pipeline import Optionable
from cello.types import Numeric

from cello.graphs import EDGE_WEIGHT_ATTR

class ClusteringMethod(Optionable):
    """ Abstract clustering method, should work for unipartite or bipartite graphs
    """
    def __init__(self, name):
        Optionable.__init__(self, name)
    
    ## tools
    def graph_is_trivial(self, graph, weighted=False):
        """ Check that the graph is not trivial.
        """
        trivial = False
        # In case of empty graph
        if graph.vcount() <= 0:
            self._logger.warn("The graph has no vertices !")
            trivial = True
        elif graph.ecount() == 0:
            if graph.vcount() > 1:
                self._logger.warn("The graph has no edges (and more than one vertex)")
            else:
                self._logger.warn("The graph has only one vertex (no edge)")
            trivial = True
        elif weighted and max(graph.es[EDGE_WEIGHT_ATTR]) == 0:
            #TODO check if EDGE_WEIGHT_ATTR exist
            self._logger.warn("The graph has only null weighted edges")
            trivial = True
        return trivial

    def __call__(self, graph, **kargs):
        """ Compute the clustering of the graph.
        
        .. note:: this method is abstract and should be overriden
        
        :param graph: the input graph
        :type graph: :class:`igraph.Graph`
        
        :return: a cover of graph vertices
        :rtype: :class:`igraph.VertexCover`
        """
        raise NotImplementedError("Should be implemented in a inherited class.")


class BigraphClusteringMethod(ClusteringMethod):
    """ Abstract clustering method for bipartite graph
    """
    def __init__(self, name):
        super(BigraphClusteringMethod, self).__init__(name)

    ## tools
    def graph_is_bipartite(self, graph):
        """ Check that the graph is bipartite
        """
        res = True
        if not graph.is_bipartite():
            self._logger.warn("The graph is not bipartite !")
            res = False
        return res


class OneCluster(ClusteringMethod):
    """ Group all vertices are in one cluster
    
    >>> g = ig.Graph.Formula("a:b--b:c:d, e--f")
    >>> clustering = OneCluster()
    >>> clustering(g).membership
    [[0], [0], [0], [0], [0], [0]]
    """
    def __init__(self, name=None):
        super(OneCluster, self).__init__(name=name)

    def __call__(self, graph):
        cover = [[vtx.index for vtx in graph.vs]]
        return ig.VertexCover(graph, clusters=cover)


class ConnectedComponents(ClusteringMethod):
    """ Clusters are connected components
    
    >>> g = ig.Graph.Formula("a:b--b:c:d, e--f")
    >>> clustering = ConnectedComponents()
    >>> clustering(g).membership
    [[0], [0], [0], [0], [1], [1]]
    """
    def __init__(self, name=None):
        super(ConnectedComponents, self).__init__(name=name)

    def __call__(self, graph):
        vertex_clustering = graph.clusters()
        return vertex_clustering.as_cover()


class MaximalCliques(ClusteringMethod):
    """ Maximal cliques
    
    >>> g = ig.Graph.Formula("a:b--b:c:d, e--f")
    >>> clustering = MaximalCliques()
    >>> [g.vs[cluster]["name"] for cluster in clustering(g)]
    [['f', 'e'], ['a', 'b', 'd'], ['a', 'b', 'c']]
    """
    def __init__(self):
        ClusteringMethod.__init__(self, "maximal_cliques")
        self.add_option("min", Numeric(default=0, help=u"Minimum cliques size"))
        self.add_option("max", Numeric(default=10, help=u"Maximal cliques size"))

    def __call__(self, graph, min=0, max=10):
        return ig.VertexCover(graph, graph.maximal_cliques(min, max))

