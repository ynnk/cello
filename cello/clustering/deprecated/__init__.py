# -*- coding: utf-8 -*-
""" 
"""

from cello.clustering.core import ClusteringMethod, BigraphClusteringMethod

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
            from cello.clustering.fca import fca_kov
            self.fca_fct = fca_kov.compute_concepts_kov
        elif fca_method == "fcbo":
            from cello.clustering.fca import fca_fcbo_wrapper
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
    """ OSLOM
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

