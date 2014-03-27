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

