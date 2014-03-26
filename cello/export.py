#-*- coding:utf-8 -*-
""" :mod:`cello.export`
========================

"""
from cello.schema import Doc, Numeric

def export_docs(kdocs, exclude=[]):
    """ Transform the list of kdoc

    remove all the attributes of KodexDoc that are not fields (of elements) or elements attributes
    """
    return [doc.as_dict(exclude=exclude) for doc in kdocs]

#TODO exclude_gattrs, exclude_vattrs, exclude_eattrs
#TODO: est-ce que l'on passe pas a des include plutot que exclude
def export_graph(graph, exclude_gattrs=[], exclude_vattrs=[], exclude_eattrs=[]):
    """ Transform a graph (igraph graph) to a dictionary
    to send it to template (or json)

    :param graph: the graph to transform
    :type graph: :class:`igraph.Graph`
    :param exclude_gattrs: graph attributes to exclude (TODO)
    :param exclude_vattrs: vertex attributes to exclude (TODO)
    :param exclude_eattrs: edges attributes to exclude (TODO)

    >>> import igraph as ig
    >>> from pprint import pprint
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f, d--f")
    >>> from cello.schema import Doc
    >>> g.vs["docnum"] = [1+vid if vid%2 == 0 else None for vid in range(g.vcount())]
    >>> graph_dict = export_graph(g)
    >>> pprint(graph_dict)
    {'attributes': {'bipartite': False, 'directed': False},
     'es': [{'s': 0, 't': 1},
            {'s': 0, 't': 2},
            {'s': 0, 't': 3},
            {'s': 0, 't': 4},
            {'s': 3, 't': 4}],
     'vs': [{'docnum': 1, 'name': 'a'},
            {'docnum': None, 'name': 'b'},
            {'docnum': 3, 'name': 'c'},
            {'docnum': None, 'name': 'd'},
            {'docnum': 5, 'name': 'f'}]}


    The '_doc' vertex attribute is converted into a 'docnum' attribut :

    >>> from cello.schema import Doc
    >>> del g.vs["docnum"]
    >>> g.vs["_doc"] = [Doc(docnum="d_%d" % vid) if vid%2 == 0 else None for vid in range(g.vcount())]
    >>> graph_dict = export_graph(g)
    >>> pprint(graph_dict)
    {'attributes': {'bipartite': False, 'directed': False},
     'es': [{'s': 0, 't': 1},
            {'s': 0, 't': 2},
            {'s': 0, 't': 3},
            {'s': 0, 't': 4},
            {'s': 3, 't': 4}],
     'vs': [{'docnum': 'd_0', 'name': 'a'},
            {'name': 'b'},
            {'docnum': 'd_2', 'name': 'c'},
            {'name': 'd'},
            {'docnum': 'd_4', 'name': 'f'}]}

    """
    import igraph
    assert isinstance(graph, igraph.Graph)
    # create the graph dict
    graph_dict = {}
    graph_dict['vs'] = []
    graph_dict['es'] = []
    # attributs of the graph
    graph_dict['attributes'] = {} #TODO recopier les attr du graphe
    # check argument
    # default graph attrs
    graph_dict['attributes']['directed'] = graph.is_directed()
    #TODO: attention is bipartite... => le passer en simple attr de graphe, seté dans le graph builder
    graph_dict['attributes']['bipartite'] = 'type' in graph.vs and graph.is_bipartite()
    # vertices
    for vtx in graph.vs:
        vertex = vtx.attributes()
        # transformation des Kodex_Doc en docnum
        if "_doc" in vertex and vertex["_doc"] is not None:
            assert isinstance(vertex["_doc"], Doc)
            assert "docnum" not in vertex
            docnum = vertex["_doc"].docnum
            vertex["docnum"] = docnum
        if "_doc" in vertex:
            del vertex["_doc"]
        graph_dict['vs'].append(vertex)
    # edges
    for edg in graph.es:
        edge = edg.attributes() # recopie tous les attributs
        # add source et target
        edge["s"] = edg.source
        edge["t"] = edg.target
        #TODO check il n'y a pas de 's' 't' dans attr
        graph_dict['es'].append(edge)
    return graph_dict


def export_clustering(vertex_cover):
    """ Build a dictionary view of a vertex cover (a clustering)
    
    .. Note:: for each cluster 'docnums' are extracted from vertices that have a
    (not None) '_doc' attribute
    
    .. code-block:: js
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
    :param vertex_cover: the vertex cover to convert
    :type vertex_cover: :class:`igraph.VertexCover`
    
    >>> import igraph as ig
    >>> from pprint import pprint
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f, d--f")
    >>> from cello.schema import Doc
    >>> g.vs["_doc"] = [Doc(docnum="d_%d" % vid) if vid%2 == 0 else None for vid in range(g.vcount())]

    >>> from cello.clustering import MaximalCliques
    >>> clustering = MaximalCliques()
    >>> cover = clustering(g)
    >>> cover_dict = export_clustering(cover)
    >>> pprint(cover_dict)
    {'clusters': [{'docnums': ['d_0', 'd_4'], 'vids': [0, 3, 4]},
                  {'docnums': ['d_0', 'd_2'], 'vids': [0, 2]},
                  {'docnums': ['d_0'], 'vids': [0, 1]}],
     'misc': -1}
    """
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

    clusters = []
    for cnum, vids in enumerate(vertex_cover):
        cluster = {}
        cluster['vids'] = vids
        # doc ?
        cluster['docnums'] = []
        if gid_to_doc:
            cluster['docnums'] = [gid_to_doc[gid] for gid in vids if gid in gid_to_doc]
        # add the cluster
        clusters.append(cluster)
    cover['clusters'] = clusters
    return cover

