#!/usr/bin/env python
#-*- coding:utf-8 -*-
""" Graph clustering objects

G{classtree ClusteringMethod}
__author__ = "Emmanuel Navarro <navarro@irit.fr>"
"""

import logging

import igraph as ig

from cello.exceptions import CelloError
from cello.pipeline import Composable, Optionable
from cello.types import Numeric, Text, Boolean

from cello.clustering.walktrap import walktrap_bigraph
from cello.graphs import EDGE_WEIGHT_ATTR
from cello.graphs.transform import GraphProjection
import clustering_external
#import link_clustering

_logger = logging.getLogger("cello.clustering")

class CelloClusteringError(CelloError):
    pass


def filter_cover(cover, min_docs, min_terms, logger=None):
    """ Merge too small clusters in a "misc" one.
    """
    if logger is not None:
       logger.debug("Filter cluster, min_docs:%d min_terms:%d" % (min_docs, min_terms))
    graph = cover.graph
    new_clusters = []
    # recupere les sommets seuls dans le misc
    misc = [idx for idx, member in enumerate(cover.membership) if len(member) == 0]

    for num, cluster in enumerate(cover):
        is_misc = False
        if min_docs > 0 or min_terms > 0:
            vs_cluster = graph.vs[cluster]
            ndocs = len(vs_cluster.select(type=True))
            nterms = len(vs_cluster.select(type=False))
            if ndocs < min_docs or nterms < min_terms:
                misc += cluster
                is_misc = True
        if not is_misc:
            new_clusters.append(cluster)
    if logger is not None:
       logger.info("Cluster misc with %d vertices" % len(misc))
    if len(misc) > 0:
        if logger is not None:
           logger.info("Goes from %d to %d clusters" % (len(cover), len(new_clusters) + 1))
        cover = ig.VertexCover(graph, new_clusters + [misc])
        cover.misc_cluster = len(new_clusters)
    return cover

#{
class ClusteringMethod(Optionable):
    """ Basic abstract clustering method, should work for unipartite or bipartite graphs
    """
    def __init__(self, name):
        Optionable.__init__(self, name)
        self._logger = logging.getLogger(self.__class__.__name__)
        
        self.add_option("min_docs", Numeric(default=2,
                help=u"Minimum number of document per cluster"))

    ## tools
    def check_graph(self, graph):
        """ Check that the graph is not trivial
        """
        # In case of empty graph
        if graph.vcount() <= 0:
            self._logger.warn("The graph has no vertices !")
            return False
        elif graph.ecount() == 0:
            if graph.vcount() > 1:
                self._logger.warn("The graph has NO edges ! (and more than one vertex !)")
            else:
                self._logger.warn("The graph has only one vertex, ok ?")
            return False
        return True

    def _clustering(self, bigraph, **kargs):
        raise NotImplementedError("Should be implemented in a inherited class.")

    def __call__(self, graph, min_docs=0, **kargs):
        if not self.check_graph(graph):
            return ig.VertexCover(graph, clusters=[])
        # call the clustring method it self
        cover = self._clustering(graph, **kargs)
        # filtre des clusters
        cover = filter_cover(cover, min_docs, 0, self._logger)
        return cover


class BigraphClusteringMethod(ClusteringMethod):
    """ Abstract clustering method for bipartite graph
    """
    def __init__(self, name):
        ClusteringMethod.__init__(self, name)
        self.add_option("min_terms", Numeric( default=0,
            help=u"Minimum number of term per cluster"))

    ## tools
    def check_graph(self, graph):
        """ Check that the graph is not trivial
        """
        res = ClusteringMethod.check_graph(self, graph)
        if res:
            if not graph.is_bipartite():
                self._logger.warn("The graph is not bipartite !")
                res = False
        return res

    def _clustering(self, bigraph, **kargs):
        raise NotImplementedError("Should be implemented in a inherited class.")

    def __call__(self, graph, min_docs=0, min_terms=0, **kargs):
        default_cover = self.check_graph(graph)
        if isinstance(default_cover, ig.VertexCover):
            return default_cover
        # call the clustring method it self
        cover = self._clustering(graph, **kargs)
        # filtre des clusters
        cover = filter_cover(cover, min_docs, min_terms, self._logger)
        return cover


#{ Simple clustering methods
class OneCluster(BigraphClusteringMethod):
    """ All vertices are in one cluster
    """
    def __init__(self):
        BigraphClusteringMethod.__init__(self, u"one_cluster")

    def _clustering(self, bigraph):
        cover = [[vtx.index for vtx in bigraph.vs]]
        return ig.VertexCover(bigraph, clusters=cover)


class TermsClusters(BigraphClusteringMethod):
    """ Each term in this own cluster with its documents
    """
    def __init__(self):
        BigraphClusteringMethod.__init__(self, "terms_clusters")

    def _clustering(self, bigraph):
        cover = [[vtx_term.index] + bigraph.neighbors(vtx_term) \
                        for vtx_term in bigraph.vs.select(type=False)]
        return ig.VertexCover(bigraph, clusters=cover)


class DocsClusters(BigraphClusteringMethod):
    """ Each doc in this own cluster with its terms
    """
    def __init__(self):
        BigraphClusteringMethod.__init__(self, "docs_cluster")

    def _clustering(self, bigraph):
        cover = [[vtx_doc.index] + bigraph.neighbors(vtx_doc) \
                        for vtx_doc in bigraph.vs.select(type=True)]
        return ig.VertexCover(bigraph, clusters=cover)


class ConnectedComponents(ClusteringMethod):
    """ Simple clustering: clusters are connected components
    """
    def __init__(self):
        ClusteringMethod.__init__(self, u"connected_components")

    def _clustering(self, graph):
        vertex_clustering = graph.clusters()
        return vertex_clustering.as_cover()


class MaximalCliques(ClusteringMethod):
    """ Maximal cliques
    """
    def __init__(self):
        ClusteringMethod.__init__(self, "maximal_cliques")
        self.add_option("min", Numeric(default=0, help=u"Minimum cliques size"))
        self.add_option("max", Numeric(default=10, help=u"Maximal cliques size"))

    def _clustering(self, graph, min=0, max=10):
        return ig.VertexCover(graph, graph.maximal_cliques(min, max))

def MaximalCliquesPG():
    cluster_fct = GraphProjection(projection_wgt="no") | MaximalCliques()
    cluster_fct.name = "maximal_cliques_PG"
    return cluster_fct

class FormalConceptAnalysis(BigraphClusteringMethod):
    """ Clusters are formal concepts i.e. maximal induced bicliques
    """
    def __init__(self, fca_method="fcbo"):
        """ Just a wrapper to igraph method
        """
        BigraphClusteringMethod.__init__(self, u"formal_concept_analysis")
        self.add_option("no_trivial", Boolean(default=True, 
            help="Remove trivial concepts (i.e. concepts with no objects or no properties)"))
        if fca_method == "kov_py":
            from cello.graphs.fca import fca_kov
            self.fca_fct = fca_kov.compute_concepts_kov
        elif fca_method == "fcbo":
            from cello.graphs.fca import fca_fcbo_wrapper
            self.fca_fct = lambda bigraph: fca_fcbo_wrapper.fcbo(bigraph, min_support=0, obj_type=True, delete_files=True, fcbo_exec=None)
        else:
            raise ValueError("'%s' is not a possible FCA algorithm" % fca_method)

    def _clustering(self, bigraph, no_trivial=True):
        concepts = self.fca_fct(bigraph)
        self._logger.info("Get %d concepts" % len(concepts))
        self._logger.info("Get %d concepts" % len(concepts))
        if no_trivial:
            cover = [list(objs) + list(attrs) for objs, attrs in concepts \
                         if len(objs) > 0 and len(attrs) > 0]
        else:
            cover = [objs + attrs for objs, attrs in concepts]
        return ig.VertexCover(bigraph, clusters=cover)
#}


#{ Walktrap
class Walktrap(ClusteringMethod):
    def __init__(self):
        ClusteringMethod.__init__(self, u"walktrap")
        self.add_option("l", Numeric( default=4, help="lenght of the random walks"))

    def _clustering(self, graph, l=4):
        vertex_clustering = graph.community_walktrap(weights=EDGE_WEIGHT_ATTR, steps=l)
        return vertex_clustering.as_clustering().as_cover()

def WalktrapPG():
    cluster_fct = GraphProjection(projection_wgt=None) | Walktrap()
    cluster_fct.name = u"walktrap_PG"
    return cluster_fct

class WalktrapBigraph(BigraphClusteringMethod):
    """ Walktrap adaptation on bigraph
    """
    def __init__(self):
        BigraphClusteringMethod.__init__(self, u"walktrap_bigraph")

        self.add_option("ldoc", Numeric( default=4, 
                help=u"lenght of the random walks for documents"))
        self.add_option("lterms", Numeric( default=5,
            help=u"lenght of the random walks for terms"))
        self.add_option("cut", Text(default=u"modularity",
            help=u"method to cut the dendrogramme",
            choices=[u'modularity', u'max', u'cc', u'fixed', u'fixed_V2']))

    def _clustering(self, bigraph, ldoc=4, lterms=5, cut="modularity"):
        vertex_clustering = walktrap_bigraph(bigraph, ldoc, lterms, EDGE_WEIGHT_ATTR, cut)
        return vertex_clustering.as_cover()

#}


#{ Infomap
class Infomap(ClusteringMethod):
    def __init__(self):
        ClusteringMethod.__init__(self, u"infomap")

    def _clustering(self, bigraph):
        vertex_clustering = bigraph.community_infomap(edge_weights=EDGE_WEIGHT_ATTR)
        return vertex_clustering.as_cover()

def InfomapPG():
    cluster_fct = GraphProjection(projection_wgt=None) | Infomap()
    cluster_fct.name = u"infomap_PG"
    return cluster_fct

#{ Modularity optimization methods
class Louvain(ClusteringMethod):
    """ Louvain method (modularity optimization)
    """
    def __init__(self):
        ClusteringMethod.__init__(self, u"louvain")

    def _clustering(self, graph):
        vertex_clustering = graph.community_multilevel(weights=EDGE_WEIGHT_ATTR, return_levels=False)
        return vertex_clustering.as_cover()


class Fastgreedy(ClusteringMethod):
    """ Fastgreedy method (modularity optimization)
    """
    def __init__(self):
        ClusteringMethod.__init__(self, u"fastgreedy")

    def _clustering(self, graph):
        vertex_clustering = graph.community_fastgreedyu(weights=EDGE_WEIGHT_ATTR).as_clustering()
        return vertex_clustering.as_cover()

class EdgeBetweenness(ClusteringMethod):
    """ "Edge betweenness heuristic" modularity optimization
    Note: work only for unweighted modularity, graph's weight are ignored
    """
    def __init__(self):
        ClusteringMethod.__init__(self, u"edge_betweenness")

    def _clustering(self, graph):
        vertex_clustering = graph.community_edge_betweenness(clusters=None, directed=False).as_clustering()
        return vertex_clustering.as_cover()

class OptimalModulartity(ClusteringMethod):
    """ Exact modularity optimization
    Note: do not use it for large graph (very slow !)
    Note: work only for unweighted modularity, graph's weight are ignored
    """
    def __init__(self):
        ClusteringMethod.__init__(self, u"optimodularity")

    def _clustering(self, graph):
        vertex_clustering = graph.community_optimal_modularity()
        return vertex_clustering.as_cover()


#}


#{ Label propagation
class LabelPropagation(ClusteringMethod):
    """ Label propagation on the projection graph
    """
    def __init__(self):
        ClusteringMethod.__init__(self, u"label_propagation")

    def _clustering(self, graph):
        vertex_clustering = graph.community_label_propagation(weights=EDGE_WEIGHT_ATTR, initial=None, fixed=None)
        return vertex_clustering.as_cover()


def LabelPropagationPG():
    cluster_fct = GraphProjection(projection_wgt=None) | LabelPropagation()
    cluster_fct.name = u"label_propagation_PG"
    return cluster_fct
#}


#{ Oslom
class Oslom(ClusteringMethod):
    """ OSLMOM
    """
    def __init__(self):
        ClusteringMethod.__init__(self, u"oslom")
        if not clustering_external.check_oslom():
            raise ImportError("OSLOM executables can't be found (see misc/clustering)")

    def _clustering(self, graph):
        if graph.vcount() == 1:
            self._logger.warn("The graph has only one vertex !")
            cover = ig.VertexCover(graph, [])
        else:
            cover = clustering_external.oslom(graph, weights=EDGE_WEIGHT_ATTR, delete_files=True)
        return cover


def OslomPG():
    cluster_fct = GraphProjection(projection_wgt=None) | Oslom()
    cluster_fct.name = u"oslom_PG"
    return cluster_fct
#}


#{ Pack of methods

def modularity_opti_methods():
    methods = []
    methods.append(Louvain())
    methods.append(Fastgreedy())
    methods.append(EdgeBetweenness())
    methods.append(OptimalModulartity())
    return methods


def unipartite_clustering_methods():
    methods = []
    # 
    methods.append(Infomap())
    #methods.append(Oslom())
    methods.append(Walktrap())
    methods.append(LabelPropagation())
    # modularity
    methods.extend(modularity_opti_methods())
    # xtrem
    methods.append(ConnectedComponents())
    methods.append(MaximalCliques())
    return methods

def bipartite_clustering_methods():
    methods = []
    methods.append(Infomap())
    methods.append(InfomapPG())
    #methods.append(OslomPG())
    methods.append(WalktrapBigraph())
    methods.append(WalktrapPG())
    methods.append(LabelPropagationPG())
    methods.append(ConnectedComponents())
    methods.append(MaximalCliquesPG())
    methods.append(FormalConceptAnalysis())
    return methods

from cello.utils import deprecated

@deprecated("This method 'get_basic_clustering_methods' should be updated")
def get_basic_clustering_methods():
    """ Return a list of all clustering method (instance)
    i.e. MaximalCliques and ConnectedComponents
    """
    methods = []
    methods.append(WalktrapBigraph())
    methods.append(Infomap())
    methods.extend(get_xtrem_clustering_methods())
    return methods


@deprecated("This mehtod 'get_good_clustering_methods' should be updated")
def get_good_clustering_methods():
    """ Return a list of 'good' clustering method (instance)
    """
    methods = []
    methods.append(Infomap())
    try:
        pass
        #methods.append(OslomPG())
    except ImportError as error:
        _logger.error("Oslom import error: %s" % error)
    methods.append(WalktrapBigraph())
    return methods


@deprecated("This mehtod 'get_xtrem_clustering_methods' should be updated")
def get_xtrem_clustering_methods():
    """ Return a list of extrems clustering method (instance)
    i.e. MaximalCliques and ConnectedComponents
    """
    methods = []
    methods.append(ConnectedComponents())
    methods.append(MaximalCliques())
    methods.append(FormalConceptAnalysis())
    return methods
#}
