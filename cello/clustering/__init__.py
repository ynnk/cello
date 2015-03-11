#-*- coding:utf-8 -*-
""" :mod:`cello.clustering`
===========================

SubModules
----------

.. toctree::

    cello.clustering.core
    cello.clustering.common
    cello.clustering.filter
    cello.clustering.labelling

Helpers
-------
"""

import logging

import igraph as ig

from cello.clustering.core import OneCluster, ConnectedComponents, MaximalCliques
from cello.clustering.common import Walktrap, Infomap

#{ Pack of methods
def unipartite_clustering_methods():
    """ Returns standart clustering method for unipartite graphs
    
    >>> methods = unipartite_clustering_methods()
    >>> len(methods)
    2
    """
    methods = []
    methods.append(Infomap())
    methods.append(Walktrap())
    return methods


def bipartite_clustering_methods():
    """ Returns standart clustering method for bipartite graphs
    
    >>> methods = bipartite_clustering_methods()
    >>> len(methods)
    1
    """
    methods = []
    methods.append(Infomap())
    return methods
#}

def export_clustering(vertex_cover):
    """ Build a dictionary view of a vertex cover (a clustering)

    :param vertex_cover: the vertex cover to convert
    :type vertex_cover: :class:`igraph.VertexCover` or :class:`.LabelledVertexCover`

    .. Note:: for each cluster 'docnums' are extracted from vertices that have a
        (not None) '_doc' attribute

    Here is an exemple of exported vertex cover:

    .. code-block:: python

        {
            'misc': -1,
            'clusters': [
                {
                    'gids': [1, 3, 5, 8],
                    'docnums': [u'docnum_1', ...]
                },
                ...
            ]
        }

    For the following graph:

    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f, d--f")
    >>> from cello.schema import Doc
    >>> g.vs["_doc"] = [Doc(docnum="d_%d" % vid) if vid%2 == 0 else None for vid in range(g.vcount())]

    you can compute a clustering:

    >>> from cello.clustering import MaximalCliques
    >>> clustering = MaximalCliques()
    >>> cover = clustering(g)
    >>> print(cover)
    Cover with 3 clusters
    [0] a, d, f
    [1] a, c
    [2] a, b

    and then export the clustering this way:

    >>> cover_dict = export_clustering(cover)
    >>> from pprint import pprint
    >>> pprint(cover_dict)
    {'clusters': [{'docnums': ['d_0', 'd_4'], 'vids': [0, 3, 4]},
                  {'docnums': ['d_0', 'd_2'], 'vids': [0, 2]},
                  {'docnums': ['d_0'], 'vids': [0, 1]}],
     'misc': -1}

    One can also have a misc cluster:

    >>> cover.misc_cluster = 2
    >>> cover_dict = export_clustering(cover)
    >>> pprint(cover_dict)
    {'clusters': [{'docnums': ['d_0', 'd_4'], 'vids': [0, 3, 4]},
                  {'docnums': ['d_0', 'd_2'], 'vids': [0, 2]},
                  {'docnums': ['d_0'], 'vids': [0, 1]}],
     'misc': 2}

    Or have labels on clusters:

    >>> from cello.clustering.labelling import Label
    >>> from cello.clustering.labelling.basic import VertexAsLabel
    >>> label_builder = lambda g, clust, vtx: Label(vtx['_doc'].docnum, role='doc_title') if vtx['_doc'] is not None else None
    >>> labelling = VertexAsLabel(label_builder)
    >>> cover = labelling(cover)
    >>> cover_dict = export_clustering(cover)
    >>> pprint(cover_dict)
    {'clusters': [{'docnums': ['d_0', 'd_4'],
                   'labels': [0, 1],
                   'vids': [0, 3, 4]},
                  {'docnums': ['d_0', 'd_2'], 'labels': [2, 3], 'vids': [0, 2]},
                  {'docnums': ['d_0'], 'labels': [4], 'vids': [0, 1]}],
     'labels': [{'id': 0, 'label': u'd_0', 'role': 'doc_title', 'score': 1.0},
                {'id': 1, 'label': u'd_4', 'role': 'doc_title', 'score': 1.0},
                {'id': 2, 'label': u'd_0', 'role': 'doc_title', 'score': 1.0},
                {'id': 3, 'label': u'd_2', 'role': 'doc_title', 'score': 1.0},
                {'id': 4, 'label': u'd_0', 'role': 'doc_title', 'score': 1.0}],
     'misc': 2}

    """
    from cello.clustering.labelling.model import LabelledVertexCover
    has_labels = isinstance(vertex_cover, LabelledVertexCover)
    
    cover = {}
    if hasattr(vertex_cover, "misc_cluster") : # "misc" cluster id
        cover['misc'] = vertex_cover.misc_cluster
    else: # pas de "misc"
        cover['misc'] = -1

    gid_to_doc = None
    if hasattr(vertex_cover, 'graph') and '_doc' in vertex_cover.graph.vs.attributes():
        gid_to_doc = {gid: doc.docnum \
            for gid, doc in enumerate(vertex_cover.graph.vs['_doc']) \
            if doc is not None
        }

    # label's collection
    if has_labels:
        cover["labels"] = [label.as_dict(full=True) for label in vertex_cover.all_labels()]
        full_labels = vertex_cover.labels

    # clusters them self
    clusters = []
    for cnum, vids in enumerate(vertex_cover):
        cluster = {}
        cluster['vids'] = vids
        # doc ?
        cluster['docnums'] = []
        if gid_to_doc:
            cluster['docnums'] = [gid_to_doc[gid] for gid in vids if gid in gid_to_doc]
        # labels ?
        if has_labels:
            cluster['labels'] = [label.id for label in full_labels[cnum]]
        # add the cluster
        clusters.append(cluster)
    cover['clusters'] = clusters
    return cover


