#-*- coding:utf-8 -*-
""" :mod:`cello.graphs`
=======================

SubModules
----------

.. toctree::

    cello.graphs.builder
    cello.graphs.filter
    cello.graphs.transform


Helpers
-------
"""
import random
import igraph as ig

from cello.pipeline import Optionable
from cello.schema import Doc

from cello.graphs.builder import GraphBuilder

# default edge attribute for weighted graph
EDGE_WEIGHT_ATTR = "weight"



def random_vertex(graph, attr=None, from_edges=False):
    """ return a random vertex of the given graph

    :param attr: if not None return the attribute 'attr' of the random vertex, instead of the id (of the random vertex).
    :param from_edges: if True get an edges by random and then pick one of the ends of the edge by random
    
    >>> import random ; random.seed(1) # fix the random seed to test purpose
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f, d--f")
    >>> random_vertex(g)
    0
    >>> random_vertex(g, attr='name')
    'f'
    >>> random_vertex(g, attr='name')
    'd'
    >>> random_vertex(g, from_edges=True)
    0
    >>> random_vertex(g, attr='name', from_edges=True)
    'd'
    >>> random_vertex(g, attr='name', from_edges=True)
    'a'
    """
    if from_edges:
        # random edge
        es = random.choice(graph.es)
        vid = random.choice([es.source, es.target])
    else:
        # random node
        vid = random.choice(xrange(graph.vcount()))
    # return attr or vid
    if attr is not None:
        return graph.vs[vid][attr]
    else:
        return vid


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

    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f, d--f")
    >>> g.vs["docnum"] = [1+vid if vid%2 == 0 else None for vid in range(g.vcount())]
    >>> g.summary()
    'IGRAPH UN-- 5 5 -- \\n+ attr: docnum (v), name (v)'
    >>> graph_dict = export_graph(g)
    >>> g.summary()     # the graph hasn't changed !
    'IGRAPH UN-- 5 5 -- \\n+ attr: docnum (v), name (v)'
    >>> from pprint import pprint
    >>> pprint(graph_dict)
    {'attributes': {'bipartite': False,
                    'directed': False,
                    'e_attrs': [],
                    'v_attrs': ['docnum', 'name']},
     'es': [{'s': 0, 't': 1},
            {'s': 0, 't': 2},
            {'s': 0, 't': 3},
            {'s': 0, 't': 4},
            {'s': 3, 't': 4}],
     'vs': [{'_id': 0, 'docnum': 1, 'name': 'a'},
            {'_id': 1, 'docnum': None, 'name': 'b'},
            {'_id': 2, 'docnum': 3, 'name': 'c'},
            {'_id': 3, 'docnum': None, 'name': 'd'},
            {'_id': 4, 'docnum': 5, 'name': 'f'}]}

    The '_doc' vertex attribute is converted into a 'docnum' attribut:

    >>> from cello.schema import Doc
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f, d--f")
    >>> g.vs["_doc"] = [Doc(docnum="d_%d" % vid) if vid%2 == 0 else None for vid in range(g.vcount())]
    >>> g.es["weight"] = [4, 4, 5, 5, 1]    # add an edge attribute
    >>> graph_dict = export_graph(g)
    >>> pprint(graph_dict)
    {'attributes': {'bipartite': False,
                    'directed': False,
                    'e_attrs': ['weight'],
                    'v_attrs': ['docnum', 'name']},
     'es': [{'s': 0, 't': 1, 'weight': 4},
            {'s': 0, 't': 2, 'weight': 4},
            {'s': 0, 't': 3, 'weight': 5},
            {'s': 0, 't': 4, 'weight': 5},
            {'s': 3, 't': 4, 'weight': 1}],
     'vs': [{'_id': 0, 'docnum': 'd_0', 'name': 'a'},
            {'_id': 1, 'docnum': None, 'name': 'b'},
            {'_id': 2, 'docnum': 'd_2', 'name': 'c'},
            {'_id': 3, 'docnum': None, 'name': 'd'},
            {'_id': 4, 'docnum': 'd_4', 'name': 'f'}]}

    """
    import igraph
    assert isinstance(graph, igraph.Graph)
    # create the graph dict
    graph_dict = {}
    graph_dict['vs'] = []
    graph_dict['es'] = []
    # attributs of the graph
    graph_dict['attributes'] = { attr:graph[attr] for attr in graph.attributes()}
    graph_dict['attributes']['directed'] = graph.is_directed()
    # FIXME: bipartite... => le passer en simple attr de graphe, 
    #                        setté par le graph builder
    graph_dict['attributes']['bipartite'] = 'type' in graph.vs and graph.is_bipartite()
    graph_dict['attributes']['e_attrs'] = graph.es.attribute_names()
    graph_dict['attributes']['v_attrs'] = [attr for attr in graph.vs.attribute_names() \
                                            if not attr.startswith('_')]
    # add a docnum if there are `Doc` in an _doc attribute
    if '_doc' in graph.vs.attribute_names():
        graph_dict['attributes']['v_attrs'].append('docnum')

    graph_dict['attributes']['e_attrs'] = sorted(graph_dict['attributes']['e_attrs'])
    graph_dict['attributes']['v_attrs'] = sorted(graph_dict['attributes']['v_attrs'])

    # vertices
    for _id, vtx in enumerate(graph.vs):
        vertex = vtx.attributes()
        # _id : structural vertex attr
        vertex["_id"] = _id
        # transformation des Kodex_Doc en docnum
        if "_doc" in vertex:
            if vertex["_doc"] is not None:
                assert isinstance(vertex["_doc"], Doc)
                assert "docnum" not in vertex
                docnum = vertex["_doc"].docnum
                vertex["docnum"] = docnum
            else:
                vertex["docnum"] = None
        if "_doc" in vertex:
            del vertex["_doc"]
        graph_dict['vs'].append(vertex)

    # edges
    for edg in graph.es:
        edge = edg.attributes() # recopie tous les attributs
        # add source et target
        edge["s"] = edg.source # match with '_id' vertex attributs
        edge["t"] = edg.target
        #TODO check il n'y a pas de 's' 't' dans attr
        graph_dict['es'].append(edge)
    
    return graph_dict


def read_json(data):
    """ read, parse and return a :class:`igraph.Graph` from a dict

    :param data: deserialized json data
    :param filename: path to a file

    graph format:

    .. code-block:: python

        {
          'attributes': { # graph attributes
            'v_attrs': [], # vertex attrs names , otype ??
            'e_attrs': [], # edges attrs names 

            'directed': True/False,   # default = False
            'bipartite': True/False,  # default = False

            'key': value, ... # any pair of key, value
          },
          
          'vs': [ # vertices list
            { # vertex
              '_id': id,    # protected vertex id should not be editable 
              'key': value,  # any pair of key value may match a type
            }, ...
          ],

          'es': [ # edge list
            { # edge
              's': source vid,
              't': target vid, 
              'key': value, ...
            }, ...
          ],
        }

    Here is an usage exemple:

    >>> graph_data = {'attributes': {'bipartite': False,
    ...                'directed': False,
    ...                'e_attrs': ['weight'],
    ...                'v_attrs': ['name', 'docnum']},
    ... 'es': [{'s': 0, 't': 1, 'weight': 4},
    ...        {'s': 0, 't': 2, 'weight': 4},
    ...        {'s': 0, 't': 3, 'weight': 5},
    ...        {'s': 0, 't': 4, 'weight': 5},
    ...        {'s': 3, 't': 4, 'weight': 1}],
    ... 'vs': [{'_id': 0, 'docnum': 'd_0', 'name': 'a'},
    ...        {'_id': 1, 'docnum': None, 'name': 'b'},
    ...        {'_id': 2, 'docnum': 'd_2', 'name': 'c'},
    ...        {'_id': 3, 'docnum': None, 'name': 'd'},
    ...        {'_id': 4, 'docnum': 'd_4', 'name': 'f'}]}
    >>> graph = read_json(graph_data)
    >>> print(graph.summary())
    IGRAPH UNW- 5 5 -- 
    + attr: bipartite (g), directed (g), docnum (v), name (v), weight (e)
    >>> graph.vs[0].attributes()
    {'docnum': 'd_0', 'name': 'a'}

    """
    g_attrs = {}
    g_attrs.update(data['attributes'])
    v_attrs = g_attrs.pop('v_attrs')
    e_attrs = g_attrs.pop('e_attrs')
    
    directed = g_attrs.get('directed', False)

    builder = GraphBuilder(directed=directed)
    
    builder.declare_vattr(v_attrs)
    builder.declare_eattr(e_attrs)
    
    builder.reset()
    builder.set_gattrs(**g_attrs)

    for v in data['vs']:
        vid = builder.add_get_vertex(v['_id'])
        for attr in v_attrs:
            builder.set_vattr(vid, attr, v[attr])

    for e in data['es']:
        eid = builder.add_get_edge(e['s'],e['t'])
        for attr in v_attrs:
            builder.set_vattr(vid, attr, v[attr])
    
    return builder.create_graph()


