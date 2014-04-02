#-*- coding:utf-8 -*-
""" :mod:`cello.graphs.builder`
==============================


"""
import logging

import igraph as ig

from cello.pipeline import Optionable

class GraphBuilder(object):
    """ Abstract class to build a igraph graph object by parsing a source.

    This class may be use in two way : either direclty or by inheritage.
    
    If you use it by inheritage you need to implement the :func:`_parse` method.
    
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
        """ Create the graph it self and return it
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
    """ Build bipartite graph from a list of documents: documents are conncted
    to vertices built from one (or more) document field.
    
    A top vertex (type=True) is created for each document (document-vertex) and
    a bottom vertex (type=False) is created for each different object in
    indicated document fields (object-vertex).

    Document-vertices are connected to object-vertices they contains in indicated fields.

    Objects attributes (attributes associated to each object in a vector field)
    can eihter :
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
    {'TF_RD': 13, 'title': None, '_doc': None, 'label': 'cat', 'df_RD': 2, 'type': False}
    >>> [vtx['_doc'].docnum for vtx in cat_vtx.neighbors()]
    ['un', 'trois']
    
    and then an edge:
    
    >>> edge = g.es[g.get_eid(cat_vtx.index, doc_un_vtx.index)]
    >>> edge.attributes()
    {'tf': 2}
    """
    
    def __init__(self, fields, field_vtx, doc_vtx=None, field_edge=None, other_field_vtx=None, name=None):
        """ Create the bigraph builder
        
        :param fields: the name of the fields used to create the graph
        :type fields: list of str
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

