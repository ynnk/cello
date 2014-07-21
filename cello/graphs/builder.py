#-*- coding:utf-8 -*-
""" :mod:`cello.graphs.builder`
==============================

inheritance diagrams
--------------------

.. inheritance-diagram:: GraphBuilder OptionableGraphBuilder DocumentFieldBigraph

Class
-----
"""
import logging

import igraph as ig

from cello.pipeline import Optionable, Composable


class Subgraph(Composable):
    """ Build a local graph by extracting a subgraph from a global one

    >>> import igraph as ig
    >>> global_graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> subgraph_builder = Subgraph(global_graph)
    >>> # then at run time
    >>> graph = subgraph_builder([0,1,3])
    >>> print(graph.summary(1))
    IGRAPH UN-- 3 2 -- 
    + attr: gid (v), name (v)
    + edges (vertex names):
    a--b, b--d
    >>> graph.vs["gid"]
    [0, 1, 3]
    >>> [vtx.index for vtx in graph.vs]
    [0, 1, 2]

    If the input is a list of tupple `[(vid, score), ...]` then the score is stored
    on an vertex attribute

    >>> subgraph_builder = Subgraph(global_graph, score_attr="prox")
    >>> # then at run time
    >>> graph = subgraph_builder([(0, 0.02), (1, 0.0015), (3, 0.00102)])
    >>> graph.vs["gid"]
    [0, 1, 3]
    >>> graph.vs["prox"]
    [0.02, 0.0015, 0.00102]

    It also work with larger graph:

    >>> global_graph = ig.Graph.Tree(200, 3)
    >>> global_graph.vs["name"] = [str(i) for i in range(global_graph.vcount())]
    >>> subgraph_builder = Subgraph(global_graph)
    >>> graph = subgraph_builder([0, 152, 42])
    >>> graph.vs["name"]
    ['0', '42', '152']
    >>> graph.vs["gid"]
    [0, 42, 152]

    It is possible to keep in the subgraph the degree of each vertex in the
    global graph:

    >>> import random; random.seed(0)
    >>> global_graph = ig.Graph.Erdos_Renyi(400, 0.6)
    >>> subgraph_builder = Subgraph(global_graph, gdeg_attr="gdeg")
    >>> graph = subgraph_builder([0,3,2])
    >>> graph.vs["gid"]
    [0, 2, 3]
    >>> graph.vs["gdeg"]
    [257, 258, 243]
    >>> global_graph.degree(graph.vs["gid"])
    [257, 258, 243]

    Not that a attribute "gid" will be added to the global graph at init time

    >>> global_graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> subgraph_builder = Subgraph(global_graph)
    >>> global_graph.vs["gid"]
    [0, 1, 2, 3, 4]

    """
    def __init__(self, graph, score_attr="score", gdeg_attr=None, name=None):
        """
        :attr graph: global graph from which subgraph will be extracted
        :attr score_attr: vertex attribute used to store incomming score
        :attr gdeg_attr: vertex attribute used to store global degree of each
            vertices. In None global degree isn't stored.
        :attr name: name of the component
        """
        super(Subgraph, self).__init__(name=name)
        self._graph = graph
        # add global id to the graph
        self._graph.vs["gid"] = range(self._graph.vcount())
        self._score_attr = score_attr
        self._gdeg_attr = gdeg_attr

    def __call__(self, vids):
        scores = None
        if len(vids) != 0 and isinstance(vids[0], tuple):
            scores = [score for vid, score in vids]
            vids = [vid for vid, score in vids]
        subgraph = self._graph.subgraph(vids)
        assert subgraph.vcount() == len(vids)
        if scores is not None:
            subgraph.vs[self._score_attr] = scores
        if self._gdeg_attr is not None:
            gids = subgraph.vs["gid"]
            subgraph.vs[self._gdeg_attr] = self._graph.degree(gids)
        #for i, vtx in enumerate(subgraph.vs):
        #    print vtx["label"], self._graph.vs[vids[i]]["label"]
        #    assert vtx[self._gdeg_attr] == self._graph.degree(vtx["gid"])
        return subgraph


class GraphBuilder(object):
    """ Abstract class to build a igraph graph object by parsing a source.

    This class may be use in two way : either direclty or by inheritage.

    If you use it by inheritage you need to implement the :func:`_parse` method
    and then you can call :func:`.build_graph`:

    >>> builder = GraphBuilder()
    >>> builder.build_graph()
    Traceback (most recent call last):
    ...
    NotImplementedError: Subclasses should implement this!

    Note that all arguments given to :func:`.build_graph`: are given to
    :func:`_parse` method

    See for instance :class:`.DocumentFieldBigraph`.


    If you use it directly you can use it this way, first setup the builder
    with vertex and edge attributes:

    >>> builder = GraphBuilder()
    >>> builder.declare_vattr('name')
    >>> builder.declare_eattr('weight')

    and then add vertice and edges:

    >>> builder.reset()         # reset 
    >>> aid = builder.add_get_vertex("a")
    >>> bid = builder.add_get_vertex("b")
    >>> builder.set_vattr(aid, 'name', 'A')
    >>> builder.set_vattr(bid, 'name', 'B')
    >>> eid = builder.add_get_edge(aid, bid)
    >>> builder.set_eattr(eid, 'weight', 42)
    
    before to create the igraph graph it self:

    >>> graph = builder.create_graph()
    >>> print(graph.summary())
    IGRAPH UNW- 2 1 -- 
    + attr: name (v), weight (e)
    """
    def __init__(self, directed = False):
        self._directed = directed
        # graph attr
        self._graph_attrs = {}
        # vtx attrs
        self._vertex_attrs_name = [] # not reseted
        self._vertices = {}
        self._vertex_attrs = {}
        # edges and edges attrs
        self._edges_attrs_name = [] # not reseted
        self._edges = {}
        self._edge_attrs = {}
        self._edge_list = []

    def reset(self):
        """ Clear the internal data, should be call before to build a new graph
        """
        # vertices
        self._vertices = {}
        self._vertex_attrs = {}
        for att in self._vertex_attrs_name:
            self._vertex_attrs[att] = []
        # edges
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

        :param vident: the identifier of the vertex (will be a key in a dict)
        :return: the id of the vertex in the graph
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

        It add it only of if it has not yet be declared :

        >>> builder = GraphBuilder()
        >>> builder.declare_vattr('name')
        >>> builder.declare_vattr('name')
        >>> builder.reset()
        >>> builder.create_graph().vs.attributes()
        ['name']

        :param attrs_name: names of vertex attributes
        :type attrs_name: str or list of str
        """
        assert len(self._vertices) == 0, "You should declare attributes before parsing."
        if isinstance(attrs_name, list):
            for attrs_n in attrs_name:
                self.declare_vattr(attrs_n)
        else:
            # add it only if it doesn't already exist
            if attrs_name not in self._vertex_attrs_name:
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

        :param vid_from: source of the edge
        :param vid_to: target of the edge
        :return: the id of the edges in the graph
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

        It add it only of if it has not yet be declared :

        >>> builder = GraphBuilder()
        >>> builder.declare_eattr('weight')
        >>> builder.declare_eattr('weight')
        >>> builder.reset()
        >>> builder.create_graph().es.attributes()
        ['weight']

    
        :params attrs_name: names of edge attributes
        :type  attrs_name: str or list of str
        """
        assert len(self._edges) == 0, "You should declare attributes before parsing."
        if isinstance(attrs_name, list) :
            for attr_n in attrs_name:
                self.declare_eattr(attr_n)
        else:
            if attrs_name not in self._edges_attrs_name:
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
        """ Build the graph by using :func:`_parse` method.
        The parameters are passed to :func:`_parse`.

        :returns: the graph
        :rtype: :class:`igraph.Graph`
        """
        self.reset()
        self._parse( *args, **kargs)
        return self.create_graph()
    
    def create_graph(self):
        """ Create the graph it self and return it
        
        :returns: the graph
        :rtype: :class:`igraph.Graph`
        """
        graph = ig.Graph(n=len(self._vertices),
                         edges=self._edge_list,
                         directed=self._directed, 
                         graph_attrs=self._graph_attrs,
                         vertex_attrs=self._vertex_attrs,
                         edge_attrs=self._edge_attrs)
        return graph


class OptionableGraphBuilder(Optionable, GraphBuilder):
    """ Optionable graph builder
    """
    def __init__(self, name=None, directed=False):
        Optionable.__init__(self, name)
        GraphBuilder.__init__(self, directed)

    def __call__(self, docs, *args, **kargs):
        graph = self.build_graph(docs, *args, **kargs)
        return graph


class DocumentFieldBigraph(OptionableGraphBuilder):
    """ Build bipartite graph from a list of documents: documents are connected
    to vertices built from one (or more) document field.
    
    A top vertex (type=True) is created for each document (document-vertex) and
    a bottom vertex (type=False) is created for each different object in
    indicated document fields (object-vertex).

    Document-vertices are connected to object-vertices they contains in indicated fields.

    Objects attributes (attributes associated to each object in a vector field)
    can either :

        * be ignored,
        * be copied as edge attribute between a document and an object (weight for ex.),
        * be transformed as object vertex attribute.

    The vertex attribute '`_doc`' contains for each document-vertex a reference
    to original :class:`.Doc` object.
    
    Given the following sample list of documents:
    
    >>> from cello.schema import Doc, Schema
    >>> from cello.types import Text, Numeric
    >>> schema = Schema(
    ...    title=Text(vtype=str),
    ...    terms=Text(vtype=str, multi=True, attrs={'tf': Numeric(default=1)})
    ... )
    >>> d1 = Doc(schema=schema, docnum='un', title='doc one !')
    >>> d1.terms.add('cat', tf=2)
    >>> d1.terms.add('dog', tf=10)
    >>> d1.terms.add('kiwi', tf=2)
    >>> d2 = Doc(schema=schema, docnum='deux', title='doc two !')
    >>> d2.terms.add('dog', tf=9)
    >>> d3 = Doc(schema=schema, docnum='trois', title='doc three !')
    >>> d3.terms.add('cat', tf=11)
    >>> d3.terms.add('mouse', tf=5)
    >>> doclist = [d1, d2, d3]
    
    one can create a graph builder like this:
    
    >>> gbuilder = DocumentFieldBigraph(
    ...                     fields=["terms"],
    ...                     field_vtx='label',
    ...                     doc_vtx=["title"],
    ...                     field_edge=["tf"],
    ...                     other_field_vtx=[
    ...                         ("tf", 0, lambda prev, new: prev+new, "TF_RD"),
    ...                         ("tf", 0, lambda prev, new: prev+1, "df_RD")
    ...                     ]
    ... )
    
    and then use it this way:
    
    >>> g = gbuilder(doclist)
    >>> len(g.vs.select(type=True))
    3
    >>> len(g.vs.select(type=False))
    4
    
    Here is an exemple of document-vertex:
    
    >>> doc_un_vtx = g.vs.select(lambda vtx: vtx['_doc'] is not None and vtx['_doc'].docnum == 'un')[0]
    >>> doc_un_vtx["title"]
    'doc one !'

    Here is an exemple of object-vertex:
    
    >>> cat_vtx = g.vs.select(label='cat')[0]
    >>> cat_vtx.attributes()
    {'TF_RD': 13, 'title': None, '_doc': None, 'label': 'cat', 'df_RD': 2, '_source': 'terms', 'type': False}
    >>> [vtx['_doc'].docnum for vtx in cat_vtx.neighbors()]
    ['un', 'trois']

    note that for each object-vertex there is a '_source' attr that indicate the name of the document field where the vertex cam's from :
    >>> cat_vtx["_source"]
    'terms'


    and then an edge:
    
    >>> edge = g.es[g.get_eid(cat_vtx.index, doc_un_vtx.index)]
    >>> edge.attributes()
    {'tf': 2}
    """
    
    def __init__(self, fields, field_vtx, doc_vtx=None, field_edge=None, other_field_vtx=None, name=None):
        """ Create the bigraph builder
        
        :param fields: the name of the fields used to create the graph
        :type fields: list of str field should be a `:.VectorField:`
        :param field_vtx: the name of vertex attribute where the fields value
            will be stored.
        :type field_vtx: str
        :param doc_vtx: list of the document field to copy as vertex attribute
        :type doc_vtx: list of str
        :param field_edge: list of the field attibutes to copy as vertex attribute
        :type field_edge: list of str
        :param other_field_vtx: indicate how to transform field attribute to
            vertex attribute. It is a 4-tuple `(origin attr name, initial value,
            merge function, output vertex attribute name)`
        :type other_field_vtx: list of 4-tuple
        
        """
        super(DocumentFieldBigraph, self).__init__(name=name, directed=False)
        #TODO add bipartite attribute
        self.field_vtx = field_vtx
        self.doc_vtx = doc_vtx or []
        self.field_edge = field_edge or []
        self.other_field_vtx = other_field_vtx or []
        # the document fields tu use
        self.field_names = fields
        # declare std attributs
        self.declare_vattr("type")
        self.declare_vattr("_source")
        self.declare_vattr("_doc")
        self.declare_vattr(self.field_vtx)
        # declare user selected attr
        for doc_attr in self.doc_vtx:
            self.declare_vattr(doc_attr)
        for edge_attr in self.field_edge:
            self.declare_eattr(edge_attr)
        for rule in self.other_field_vtx:
            if len(rule) != 4:
                raise ValueError("field_vtx should be a list of 4-tupple")
            _, _, merge, out_attr = rule
            if not callable(merge):
                raise ValueError("The merge function is not callable")
            self.declare_vattr(out_attr)

    def _parse(self, docs):
        field_names = self.field_names
        field_vtx = self.field_vtx
        doc_vtx = self.doc_vtx
        field_edge = self.field_edge
        other_field_vtx = self.other_field_vtx
        # first add all documents
        for doc in docs:
            doc_gid = self.add_get_vertex((True, doc.docnum))
            self.set_vattr(doc_gid, "type", True)
            self.set_vattr(doc_gid, "_doc", doc)
            self.set_vattr(doc_gid, "_source", None)
            self.set_vattr(doc_gid, field_vtx, None)
            for doc_attr in doc_vtx:
                self.set_vattr(doc_gid, doc_attr, doc[doc_attr])
        # then for each document add the object-vertices and edges
        for doc in docs:
            doc_gid = self.add_get_vertex((True, doc.docnum))
            for field in field_names:
                termset = doc[field]
                for term in termset:
                    term_gid = self.add_get_vertex((False, term))
                    self.set_vattr(term_gid, "type", False)
                    self.set_vattr(term_gid, "_doc", None)
                    self.set_vattr(term_gid, "_source", field)
                    self.set_vattr(term_gid, field_vtx, term)
                    # add / merge score
                    for source_attr, init, merge, dest_attr in other_field_vtx:
                        val = termset.get_attr_value(term, source_attr)
                        prec_val = self.get_vattr(term_gid, dest_attr) or init
                        self.set_vattr(term_gid, dest_attr, merge(prec_val, val))
                    # add edge with score
                    eid = self.add_get_edge(doc_gid, term_gid)
                    for edge_attr in field_edge:
                        val = termset.get_attr_value(term, edge_attr)
                        self.set_eattr(eid, edge_attr, val)

