#-*- coding:utf-8 -*-
""" :mod:`cello.clustering.filter`
==================================

"""
import igraph as ig

from reliure.types import Numeric
from reliure import Optionable, Composable

from functools import update_wrapper

class OtherInMisc(Composable):
    """ Add all vertices that have no clusters in 'misc' cluster
    
    >>> other_in_misc = OtherInMisc()

    Here is a simple example:

    >>> g = ig.Graph.Formula("0:1--1:2:3, 4--5")
    >>> cover = ig.VertexCover(g, [[0, 1, 2], [3]])
    >>> cover = other_in_misc(cover)
    >>> list(cover)
    [[0, 1, 2], [3], [4, 5]]
    >>> cover.misc_cluster
    2

    One can also a cover that already have a misc cover:

    >>> cover = ig.VertexCover(g, [[0, 1, 2], [3]])
    >>> cover.misc_cluster = 1
    >>> cover = other_in_misc(cover)
    >>> list(cover)
    [[0, 1, 2], [3, 4, 5]]
    """
    def __init__(self):
        super(OtherInMisc, self).__init__()

    def __call__(self, cover):
        # recupere les sommets n'ayant pas de cluster dans le misc
        new_misc = [idx for idx, member in enumerate(cover.membership) \
                    if len(member) == 0]
        
        if len(new_misc):
            # check misc
            if not hasattr(cover, 'misc_cluster'):
                misc_id = len(cover)
                new_clusters = list(cover) + [new_misc]
                cover = ig.VertexCover(cover.graph, new_clusters)
                cover.misc_cluster = misc_id
            else:
                cover[cover.misc_cluster].extend(new_misc)
        return cover


class AbstractClusterFilter(Optionable):
    """ Iterate over a cover and apply an abstract filter function to mouv or
    not clusters to misc.
    
    >>> abstract_filter = AbstractClusterFilter()
    
    This class is abstract and :func:`mv_in_misc` should be overriden:
    
    >>> g = ig.Graph.Formula("0:1--1:2:3, 4--5")
    >>> cover = ig.VertexCover(g, [[0, 1, 2], [3]])
    >>> abstract_filter(cover)
    Traceback (most recent call last):
    ...
    NotImplementedError

    Or one can pass this filter function at construction, here with a dummy fliter:

    >>> filter = lambda cover, num, cluster: 3 in cluster
    >>> no_3_in_cover = AbstractClusterFilter(mv_in_misc=filter)
    >>> cover = ig.VertexCover(g, [[0, 1, 2], [3], [0,4,5], [1,3,4]])
    >>> cover = no_3_in_cover(cover)
    >>> cover.misc_cluster
    2
    >>> cover.membership
    [[0, 1], [0, 2], [0], [2], [1, 2], [1]]
    >>> cover[cover.misc_cluster]
    [1, 3, 4]
    """
    def __init__(self, name=None, mv_in_misc=None):
        """
        :param mv_in_misc: a cluster filter function
        :type mv_in_misc: see :func:`mv_in_misc`
        """
        super(AbstractClusterFilter, self).__init__(name=name)
        if mv_in_misc is not None:
            self._mv_in_misc = mv_in_misc

    def mv_in_misc(self, cover, num, cluster, **kwargs):
        """ Called on each cluster (in :func:`__call__`) if `True` then the
        cluster is mouved to misc.
        """
        if hasattr(self, "_mv_in_misc"):
            return self._mv_in_misc(cover, num, cluster, **kwargs)
        else:
            raise NotImplementedError

    @Optionable.check
    def __call__(self, cover, **kwargs):
        self._logger.debug("Filter cluster, kwargs: %s" % (kwargs))
        misc_id = -1
        if hasattr(cover, 'misc_cluster'):
            misc_id = cover.misc_cluster
        new_clusters = []
        new_misc = set()
        for num, cluster in enumerate(cover):
            if num == misc_id: # already in misc
                continue
            # should we mv it ?
            if self.mv_in_misc(cover, num, cluster, **kwargs):
                new_misc.update(cluster)
            else: # we keep it
                new_clusters.append(cluster)
        
        self._logger.info("Cluster misc with %d new vertices" % len(new_misc))
        if len(new_misc):
            if misc_id >= 0: # already a misc
                new_misc.update(cover[misc_id])
            new_misc = list(new_misc)
            cover = ig.VertexCover(cover.graph, new_clusters + [new_misc])
            cover.misc_cluster = len(new_clusters)
        return cover

class TooSmall(AbstractClusterFilter):
    """ Merge clusters that are 'too' small in a misc cluster
    
    Options are:

    >>> too_small = TooSmall()
    >>> too_small.print_options()
    min_vtx (Numeric, default=2): Minimum number of vertex per cluster

    Here is an usage example:

    >>> g = ig.Graph.Formula("0:1--1:2:3, 4--5")
    >>> cover = ig.VertexCover(g, [[0, 1, 2], [3]])
    >>> cover = too_small(cover, min_vtx=2)
    >>> list(cover)
    [[0, 1, 2], [3]]
    >>> cover.misc_cluster
    1

    It may also be applyed when a misc cluster already exist:
    
    >>> cover = ig.VertexCover(g, [[0, 1, 2], [3]])
    >>> other_in_misc = OtherInMisc()
    >>> cover = other_in_misc(cover)
    >>> list(cover)
    [[0, 1, 2], [3], [4, 5]]
    >>> cover = too_small(cover, min_vtx=2)
    >>> list(cover)
    [[0, 1, 2], [3, 4, 5]]
    """
    def __init__(self, name=None):
        super(TooSmall, self).__init__(name=name)
        self.add_option("min_vtx", Numeric(default=2,
            help=u"Minimum number of vertex per cluster"))

    def mv_in_misc(self, cover, num, cluster, min_vtx=None):
        return len(cluster) < min_vtx


class TooFewDoc(AbstractClusterFilter):
    """ Merge clusters that have 'too' few documents in a misc cluster.
    Documents are vertices that have 'type' equals to True.
    
    Options are:

    >>> too_few_doc = TooFewDoc()
    >>> too_few_doc.print_options()
    min_doc (Numeric, default=2): Minimum number of document per cluster

    Here is an usage example:

    >>> g = ig.Graph.Formula("a, b, c, d, a:b:c--A:B:C:D, d--D:E, c:d--F")
    >>> g.vs["type"] = [vtx["name"].islower() for vtx in g.vs]
    >>> #g.vs["type"]
    >>> cover = ig.VertexCover(g, [[0, 1, 2, 4, 5], [0, 1, 4], [3], [3, 4, 5]])
    >>> cover = too_few_doc(cover)
    >>> list(cover)
    [[0, 1, 2, 4, 5], [0, 1, 4], [3, 4, 5]]
    >>> cover.misc_cluster
    2

    It may also be applyed when a misc cluster already exist:

    >>> cover = ig.VertexCover(g, [[0, 1, 2, 4, 5], [3]])
    >>> other_in_misc = OtherInMisc()
    >>> cover = other_in_misc(cover)
    >>> list(cover)
    [[0, 1, 2, 4, 5], [3], [6, 7, 8, 9]]
    >>> cover.misc_cluster
    2
    >>> cover = too_few_doc(cover)
    >>> list(cover)
    [[0, 1, 2, 4, 5], [8, 9, 3, 6, 7]]
    >>> cover.misc_cluster
    1
    """
    def __init__(self, name=None):
        super(TooFewDoc, self).__init__(name=name)
        self.add_option("min_doc", Numeric(default=2, min=0,
            help=u"Minimum number of document per cluster"))

    def mv_in_misc(self, cover, num, cluster, min_doc=None):
        graphvs = cover.graph.vs
        return len([1 for cid in cluster if graphvs[cid]["type"]]) < min_doc


