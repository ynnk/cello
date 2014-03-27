#-*- coding:utf-8 -*-
""" :mod:`cello.clustering.filter`
==================================

"""
import igraph as ig

from cello.types import Numeric
from cello.pipeline import Optionable, Composable

from functools import update_wrapper

class OtherInMisc(Composable):
    """ Add all vertices that have no clusters in 'misc' cluster
    
    >>> g = ig.Graph.Formula("0:1--1:2:3, 4--5")
    >>> cover = ig.VertexCover(g, [[0, 1, 2], [3]])

    >>> other_in_misc = OtherInMisc()
    >>> cover = other_in_misc(cover)
    >>> list(cover)
    [[0, 1, 2], [3], [4, 5]]
    >>> cover.misc_cluster
    2
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


class TooSmall(Optionable):
    """ Merge clusters that are 'too' small in a misc cluster
    
    >>> g = ig.Graph.Formula("0:1--1:2:3, 4--5")
    >>> cover = ig.VertexCover(g, [[0, 1, 2], [3]])
    >>> too_small = TooSmall()
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
    def __init__(self):
        super(TooSmall, self).__init__()
        self.add_option("min_vtx", Numeric(default=2,
            help=u"Minimum number of vertex per cluster"))

    def __call__(self, cover, min_vtx):
        self._logger.debug("Filter cluster, min_vtx: %d" % (min_vtx))
        misc_id = -1
        if hasattr(cover, 'misc_cluster'):
            misc_id = cover.misc_cluster
        new_clusters = []
        new_misc = []
        for num, cluster in enumerate(cover):
            if num == misc_id: # already in misc
                continue
            if len(cluster) < min_vtx: # cluster too smal ==> to misc
                new_misc += cluster
            else:  # we keep it
                new_clusters.append(cluster)
        
        self._logger.info("Cluster misc with %d new vertices" % len(new_misc))
        if len(new_misc):
            if misc_id >= 0: # already a misc
                new_misc += cover[misc_id]
            cover = ig.VertexCover(cover.graph, new_clusters + [new_misc])
            cover.misc_cluster = len(new_clusters)
        return cover


def basic_cover_filter():
    """ Return a basic filter
    """
    return OtherInMisc() | TooSmall()
