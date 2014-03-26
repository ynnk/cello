#-*- coding:utf-8 -*-
""" :mod:`cello.clustering.filter`
==================================
"""
import igraph as ig

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
