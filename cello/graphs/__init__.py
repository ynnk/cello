#-*- coding:utf-8 -*-
""" :mod:`cello.graphs`
=======================
"""
import random
import igraph as ig

from cello.pipeline import Optionable
from cello.schema import Doc

EDGE_WEIGHT_ATTR = "weight"

"""


"""


def random_vertex(graph, attr=None, from_edges=False):
    """ return a random vertex of the given graph

    :param attr: if not None return the attribute 'attr' of the random vertex, instead of the id (of the random vertex).
    :param from_edges: if True get an edges by random and then pick one of the ends of the edge by random
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
        return self.graph.vs[vid][attr]
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

    >>> from pprint import pprint

    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f, d--f")
    >>> g.vs["docnum"] = [1+vid if vid%2 == 0 else None for vid in range(g.vcount())]
    >>> g.summary()
    'IGRAPH UN-- 5 5 -- \\n+ attr: docnum (v), name (v)'
    >>> graph_dict = export_graph(g)
    >>> g.summary()     # the graph hasn't changed !
    'IGRAPH UN-- 5 5 -- \\n+ attr: docnum (v), name (v)'
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

    The '_doc' vertex attribute is converted into a 'docnum' attribut :

    >>> from cello.schema import Doc
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f, d--f")
    >>> g.vs["_doc"] = [Doc(docnum="d_%d" % vid) if vid%2 == 0 else None for vid in range(g.vcount())]
    >>> g.es["weight"] = [4, 4, 5, 5, 1]    # add an edge attribute
    >>> graph_dict = export_graph(g)
    >>> pprint(graph_dict)
    {'attributes': {'bipartite': False,
                    'directed': False,
                    'e_attrs': ['weight'],
                    'v_attrs': ['name', 'docnum']},
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


def read_json(data, filename=None):
    """ read,parse and return a :class:`Iggrap.Graph` from json data or file
    :param data: deserialized json data
    :param filename: path to a file
    
    G default is undirected 
    
    graph format:
        {
          attributes: { # graph attributes
            v_attrs: [], # vertex attrs names , otype ??
            e_attrs: [], # edges attrs names 
            
            directed: True/False,   # default = False
            bipartite: True/False,  # default = False
            
            key:value, ... # any pair of key, value
          },
          
          vs: [ # vertices list
            { # vertex
              _id: id,    # protected vertex id should not be editable 
              key:value,  # any pair of key value may match a type 
            }, ...
          ],
          
          es: [ # edge list
            { # edge
              s: source vid,
              t: target vid, 
              key: value, ...
            }, ...
          ],
        }
    """
    g_attrs = data['attributes']
    v_attrs = g_attrs.pop('v_attrs')
    e_attrs = g_attrs.pop('e_attrs')
    
    directed = g_attrs.get('directed', False)

    builder = GraphBuilder(directed=directed)
    
    builder.declare_vattr(v_attrs)
    builder.declare_eattr(e_attrs)
    
    builder.reset()
    
    print builder._vertex_attrs_name
    
    builder.set_gattrs(**g_attrs)
    
    for v in data['vs']:
        vid = builder.add_get_vertex(v['_id'])
        for attr in v_attrs:
            print vid, attr, v
            builder.set_vattr(vid, attr, v[attr])
    
    for e in data['es']:
        eid = builder.add_get_edge(e['s'],e['t'])
        for attr in v_attrs:
            builder.set_vattr(vid, attr, v[attr])
    
    return builder.create_graph()
        
    


    
    
    
class GraphBuilder(object):
    """ Abstract class to build a igraph graph object by parsing a source.

    You just need to implement the _parse() methode.
    
    - in the constructer you need to declare edge and vertex attributes using self.declare_eattr() and self.declare_vattr()

    builder = GraphBuilder()
    builder.declare_vattr(...)
    buidler.reset()
    #parsing...
    builder.add_get_vertex(...)
    # create the igraph graph
    graph = builder.create_graph()
    
    """
    def __init__(self, directed = False):
        self._directed = directed
        
        self._graph_attrs = {}
        
        self._vertex_attrs_name = [] # not reseted
        self._vertices = {}
        self._vertex_attrs = {}

        self._edges_attrs_name = [] # not reseted
        self._edges = {}
        self._edge_attrs = {}

        self._edge_list = []
        
    def reset(self):
        self._vertices = {}
        self._vertex_attrs = {}

        for att in self._vertex_attrs_name:
            self._vertex_attrs[att] = []

        self._edges = {}
        self._edge_attrs = {}

        for att in self._edges_attrs_name:
            self._edge_attrs[att] = []
        # removes edges 
        self._edge_list = []

    def set_gattrs(self, **kwargs):
        """ Set the graph attribut *attr_name* """
        for attr_name, value in kwargs.iteritems():
            self._graph_attrs[attr_name] = value

    ####### Vertices ########
    def add_get_vertex(self, vident):
        """ Add the vertex *vident* if not already present.
        
        @param vident: the identifier of the vertex (will be a key in a dict)
        @return: the id of the vertex in the graph
        """
        if vident not in self._vertices:
            # add the vertex
            self._vertices[vident] = len(self._vertices)
            # ajout empty attr
            for attr_list in self._vertex_attrs.itervalues():
                attr_list.append(None)
        return self._vertices[vident]

    def declare_vattr(self, attrs_name):
        """ Declare attributes of graph's vertices.
        @param attrs_name: <str> or [<str>, ... ] names of vertex attributes
        """
        assert len(self._vertices) == 0, "You should declare attributes before parsing."
        if isinstance(attrs_name, list):
            for attrs_n in attrs_name:
                self.declare_vattr(attrs_n)
        else:
            assert attrs_name not in self._vertex_attrs_name
            self._vertex_attrs_name.append(attrs_name)

    def set_vattr(self, vid, attr_name, value):
        """ Set the attribut *attr_name* of the vertex *vid*
        """
        self._vertex_attrs[attr_name][vid] = value

    def get_vattr(self, vid, attr_name, default=None):
        """ Get the attribut *attr_name* of the vertex *vid*
        """
        val = self._vertex_attrs[attr_name][vid]
        return val if val != None else default
    
    def append_vattr(self, vid, attr_name, value):
        """ Add the *value* to the vertex attribut *attr_name* for the vertex *vid* """
        if not self._vertex_attrs[attr_name][vid]: self._vertex_attrs[attr_name][vid] = [value]
        else: self._vertex_attrs[attr_name][vid].append(value)

    def incr_vattr(self, vid, attr_name, inc=1):
        """ Increment (by the value *inc*) the value of the attributes
        *attr_name* for the vertex *vid* """
        _val = self.get_vattr(vid, attr_name, 0) + inc
        self.set_vattr(vid, attr_name, _val)
        return _val

    ####### Edges ########
    def add_get_edge(self, vid_from, vid_to):
        """ Add the edges if not already present.
        Note: if the graph is set to be undirected (in the __init__) then the 
        vertex ids *vid_from* and *vid_to* may be swapped.
        
        @param vid_from: source of the edge
        @param vid_to: target of the edge
        @return: the id of the edges in the graph
        """
        if self._directed: key = (vid_from, vid_to)
        else: key = (min(vid_from, vid_to), max(vid_from, vid_to))
        
        if key not in self._edges:
            self._edges[key] = len(self._edges)
            self._edge_list.append(key)
            for attr_list in self._edge_attrs.itervalues():
                attr_list.append(None)
        return self._edges[key]

    def declare_eattr(self, attrs_name):
        """ Declare attributes of graph's edges
        @params attrs_name: <str> or [<str>, ... ] names of edge attributes
        """
        assert len(self._edges) == 0, "You should declare attributes before parsing."
        if isinstance(attrs_name, list) :
            for attr_n in attrs_name:
                self.declare_eattr(attr_n)
        else:
            assert attrs_name not in self._edges_attrs_name
            self._edges_attrs_name.append(attrs_name)

    def set_eattr(self, eid, attr_name, value):
        """ Set the attribut *attr_name* of the edge *eid*
        """
        self._edge_attrs[attr_name][eid] = value

    def append_eattr(self, eid, attr_name, value):
        """ Append *value* to the _list_ attribut *attr_name* (for the edge *eid*)
        """
        if not self._edge_attrs[attr_name][eid]: self._edge_attrs[attr_name][eid] = [value]
        else: self._edge_attrs[attr_name][eid].append(value)

    def get_eattr(self, eid, attr_name, default=None):
        """ Get the attribut *attr_name* of the edge *eid*
        """
        val = self._edge_attrs[attr_name][eid]
        return val if val != None else default

    def incr_eattr(self, eid, attr_name, inc=1):
        """ Increment (by the value *inc*) the value of the attributes
        *attr_name* for the edge *eid* """
        _val = self.get_eattr(eid, attr_name, 0) + inc
        self.set_eattr(eid, attr_name, _val)
        return _val

    def _parse(self, *args, **kargs):
        """ Parse the 'source' and build the edge and vertex list, should be
        overide in a inherited class.
        """
        raise NotImplementedError("Subclasses should implement this!")
    
    def build_graph(self, *args, **kargs):
        """ Build the graph by using *_parse* method.
        The parameters are passed to *_parse*.

        @return the igraph graph
        """
        self.reset()
        self._parse( *args, **kargs)
        return self.create_graph()
    
    def create_graph(self):
        graph = ig.Graph(n = len(self._vertices),
                         edges = self._edge_list,
                         directed = self._directed, 
                         graph_attrs  = self._graph_attrs,
                         vertex_attrs = self._vertex_attrs,
                         edge_attrs   = self._edge_attrs)
        return graph



#TODO: from optionable ?
class AbstractGraphBuilder(Optionable, GraphBuilder):
    def __init__(self, name, directed=False):
        
        Optionable.__init__(self, name)
        GraphBuilder.__init__(self, directed)

    def __call__(self, docs, *args, **kargs):
        graph = self.build_graph(docs, *args, **kargs)
        return graph

