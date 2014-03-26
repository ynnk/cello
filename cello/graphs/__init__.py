#-*- coding:utf-8 -*-
""" :mod:`cello.graphs`
=======================
"""

import igraph as ig

from cello.pipeline import Optionable

EDGE_WEIGHT_ATTR = "weight"

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
        vid = random.choice(xrange(self.graph.vcount()))
    # return attr or vid
    if attr is not None:
        return self.graph.vs[vid][attr]
    else:
        return vid

class GraphBuilder(object):
    """ Abstract class to build a igraph graph object by parsing a source.

    You just need to implement the _parse() methode.
    
    - in the constructer you need to declare edge and vertex attributes using self.declare_eattr() and self.declare_vattr()
    - 
    
    """
    def __init__(self, directed = False):
        self._directed = directed
        self._graph_attrs = {}
        self._vertex_attrs_name = []
        self._edges_attrs_name = []
        self._init_internal_graph_repr()

    def set_gattr(self, attr_name, value):
        """ Set the graph attribut *attr_name* """
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

    ####
    def _init_internal_graph_repr(self):
        self._vertices = {}
        self._vertex_attrs = {}
        for att in self._vertex_attrs_name:
            self._vertex_attrs[att] = []

        self._edges = {}
        self._edge_list = []
        self._edge_attrs = {}
        for att in self._edges_attrs_name:
            self._edge_attrs[att] = []

    #######
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
        self._init_internal_graph_repr()
        self._parse( *args, **kargs)
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

