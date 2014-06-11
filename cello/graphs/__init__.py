#-*- coding:utf-8 -*-
""" :mod:`cello.graphs`
=======================

SubModules
----------

.. toctree::

    cello.graphs.builder
    cello.graphs.filter
    cello.graphs.transform
    cello.graphs.prox
    cello.graphs.extraction

Helpers
-------
"""
import random

from cello.pipeline import Optionable
from cello.schema import Doc

from cello.graphs.builder import GraphBuilder


# Edge Mode
OUT = 1
IN  = 2
ALL = 3


# default edge attribute for weighted graph
EDGE_WEIGHT_ATTR = "weight"

#TODO: basic AbstractGraph API describtion
class AbstractGraph(object):
    def __init__(self, *args, **kwargs):
        """
        :param bipartite: the graph IS bipartite by 
        :param reflexive: the graph IS reflexive all vertex have loops
        """
        self.gattrs = {}
    
    def __getitem__(self, name):
        """ Get a graph attribute value """
        return self.gattrs[name]

    def __setitem__(self, name, value):
        """ Set a graph attribute value """
        return self.gattrs[name]
    """    
    vcount(self): 
         returns the vertex count
    ecount(self): 
        returns the edges count 
    neighbors(self, vtx, mode=OUT):
    subgraph(self):    
    """

def neighbors(graph, vtx, mode=OUT):
    """:param vertex: a vertex ID"""        
    return graph.neighbors(vtx, mode)

def random_vertex(graph, **kwargs):
    return graph.random_vertex(**kwargs)


# LOCAL GRAPH FUNCTION
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

    >>> from cello.providers.igraphGraph import  IgraphGraph
    >>> g = IgraphGraph.Formula("a--b, a--c, a--d, a--f, d--f")
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
     'vs': [{'docnum': 1, 'id': 0, 'name': 'a'},
            {'docnum': None, 'id': 1, 'name': 'b'},
            {'docnum': 3, 'id': 2, 'name': 'c'},
            {'docnum': None, 'id': 3, 'name': 'd'},
            {'docnum': 5, 'id': 4, 'name': 'f'}]}

    The '_doc' vertex attribute is converted into a 'docnum' attribut:

    >>> from cello.schema import Doc
    >>> g = IgraphGraph.Formula("a--b, a--c, a--d, a--f, d--f")
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
     'vs': [{'docnum': 'd_0', 'id': 0, 'name': 'a'},
            {'docnum': None, 'id': 1, 'name': 'b'},
            {'docnum': 'd_2', 'id': 2, 'name': 'c'},
            {'docnum': None, 'id': 3, 'name': 'd'},
            {'docnum': 'd_4', 'id': 4, 'name': 'f'}]}

    If you have an id 

    >>> g = IgraphGraph.Formula("a--b, a--c, a--d, a--f, d--f")
    >>> g.vs['id'] = [45, 56, 342, 56, 558]
    >>> graph_dict = export_graph(g)
    Traceback (most recent call last):
    ...
    ValueError: The graph already have a vetrex attribute 'id'
    """
    import igraph
    # some check
    assert isinstance(graph, igraph.Graph)
    if 'id' in graph.vs.attributes():
        raise ValueError("The graph already have a vetrex attribute 'id'")
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
    for vid, vtx in enumerate(graph.vs):
        vertex = vtx.attributes()
        # _id : structural vertex attr
        vertex["id"] = vid
        if "_doc" in vertex:
            if vertex["_doc"] is not None:
                assert isinstance(vertex["_doc"], Doc)
                #assert "docnum" not in vertex
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
        edge["s"] = edg.source # match with 'id' vertex attributs
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
              'id': id,    # protected vertex id should not be editable 
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
    ... 'vs': [{'id': 0, 'docnum': 'd_0', 'name': 'a'},
    ...        {'id': 1, 'docnum': None, 'name': 'b'},
    ...        {'id': 2, 'docnum': 'd_2', 'name': 'c'},
    ...        {'id': 3, 'docnum': None, 'name': 'd'},
    ...        {'id': 4, 'docnum': 'd_4', 'name': 'f'}]}
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
        vid = builder.add_get_vertex(v['id'])
        for attr in v_attrs:
            builder.set_vattr(vid, attr, v[attr])

    for e in data['es']:
        eid = builder.add_get_edge(e['s'],e['t'])
        for attr in v_attrs:
            builder.set_vattr(vid, attr, v[attr])
    
    return builder.create_graph()


