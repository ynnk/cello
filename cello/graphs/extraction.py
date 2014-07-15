#-*- coding:utf-8 -*- 
""" :mod:`cello.graphs.extraction`
==================================
.. currentmodule:: cello.graphs.extraction

Vertex extraction classes

Should return a v_extract list: `[(id, score), ...]`

here is an usage example:

>>> from cello.providers.igraphGraph import IgraphGraph
>>> global_graph = IgraphGraph.Famous("Zachary")
>>> markov_glbl = ProxMarkovExtractionGlobal(global_graph) | VertexIds()
>>> mtcl_glbl = ProxMtclExtractionGlobal(global_graph) | VertexIds()

These two components can be used this way:

>>> markov_glbl([1], vcount=5, length=3, add_loops=False)
[0, 2, 3, 13, 7]
>>> import random; random.seed(0) #for testing purpose
>>> mtcl_glbl([1, 2], vcount=3, length=3, throws=10000, add_loops=False)
[0, 1, 3]

"""
import re

from cello.exceptions import CelloPlayError
from cello.types import Numeric, Text, Boolean
from cello.pipeline import Composable, Optionable
from cello.graphs import prox, IN, OUT, ALL, neighbors

class VertexIds(Optionable):
    """ Extract only vertex ids from a list of `[(vid, score), ...]`
    
    >>> vtxid = VertexIds()
    >>> vtxid([(21, 1.), (541, .8), (2, .45)])
    [21, 541, 2]
    """
    def __init__(self, name=None):
        super(VertexIds, self).__init__(name=name)
    
    def __call__(self, vect):
        return [vid for vid, _ in vect]


class VtxMatch(Optionable):
    """ Extract a list of weighted vertex ids from a query string
    
    >>> import igraph as ig
    >>> # A graph with, for each vertex, an uniq 'name' and a not uniq 'label'
    >>> global_graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> global_graph.vs["label"] = ["1", "1", "2", "2", "3"]
    >>> # we build the match component:
    >>> match = VtxMatch(global_graph, attr_list=[u"name", u"label"], default_attr=u"name")
    >>> # one can see the availables options 
    >>> match.print_options()
    default_attr (Text, default=name, in: {name, label}): default search attribute

    Then one can use it at query time:

    >>> match("a")      # by default attr "name" is used
    {0: 1.0}
    >>> match("a ; a")
    {0: 2.0}
    >>> match("a ; a;a;a")
    {0: 4.0}
    >>> match("a:5.5")
    {0: 5.5}
    >>> match("a; d", default_attr=u"name") # it is also possible to set the default_attr used for searching vtx
    {0: 1.0, 3: 1.0}
    >>> match("a; d:3", default_attr=u"name")
    {0: 1.0, 3: 3.0}
    >>> match("a; d:-3", default_attr=u"name")
    {0: 1.0, 3: -3.0}
    >>> match("a; d:-3", default_attr=u"name")
    {0: 1.0, 3: -3.0}
    >>> match("1", default_attr=u"label")    #Note: if more than one vtx have the given attr value the all are returned
    {0: 1.0, 1: 1.0}
    >>> match("1;1;1;1", default_attr=u"label")
    {0: 4.0, 1: 4.0}
    >>> match("2:5.5", default_attr=u"label")
    {2: 5.5, 3: 5.5}
    >>> match("1; 3", default_attr=u"label")
    {0: 1.0, 1: 1.0, 4: 1.0}
    >>> match("1; 3:3", default_attr=u"label")
    {0: 1.0, 1: 1.0, 4: 3.0}
    >>> match("1; 3:-3", default_attr=u"label")
    {0: 1.0, 1: 1.0, 4: -3.0}
    >>> match("1:-2; 3:-3", default_attr=u"label")
    {0: -2.0, 1: -2.0, 4: -3.0}
    >>> match("1")    #Note: if more than one vtx have the given attr value the all are returned
    {0: 1.0, 1: 1.0}
    >>> match("1;1;1;1")
    {0: 4.0, 1: 4.0}
    >>> match("2:5.5")
    {2: 5.5, 3: 5.5}
    >>> match("1; 3")
    {0: 1.0, 1: 1.0, 4: 1.0}
    >>> match("1; 3:3")
    {0: 1.0, 1: 1.0, 4: 3.0}
    >>> match("1; 3:-3")
    {0: 1.0, 1: 1.0, 4: -3.0}
    >>> match("1:-2; 3:-3")
    {0: -2.0, 1: -2.0, 4: -3.0}
    
    This component can also throw some :class:`.CelloPlayError` if vertices are
    not found:
    
    >>> match("bp")
    Traceback (most recent call last):
    ...
    CelloPlayError: Vertex's name 'bp' not found; Vertex's label 'bp' not found
    
    >>> match("bp;lj")
    Traceback (most recent call last):
    ...
    CelloPlayError: Vertices' names 'bp and lj' not found; Vertices' labels 'bp and lj' not found
    
    >>> match("bp;1")
    Traceback (most recent call last):
    ...
    CelloPlayError: Vertices' names 'bp and 1' not found; Vertex's label 'bp' not found
    
    >>> match("a;1")
    Traceback (most recent call last):
    ...
    CelloPlayError: Vertex's name '1' not found; Vertex's label 'a' not found
    """
    #TODO add test an suport for str/unicode

    re_split_score = re.compile(r"(?: *\; *)?(?:([^:\;]*[^:\; ]+)(?: *: *)?(\-?\d+(?:\.\d+)?)?)", re.UNICODE)
    @staticmethod
    def split_score(query):
        u""" Split a input query (with some score), see above exemples for usage

        >>> VtxMatch.split_score(u"être")
        [(u'\\xeatre', u'')]
        >>> VtxMatch.split_score(u"peler:0.2 ; courir:0.4")
        [(u'peler', u'0.2'), (u'courir', u'0.4')]
        >>> VtxMatch.split_score(u"été:0.2 ; être:14")   
        [(u'\\xe9t\\xe9', u'0.2'), (u'\\xeatre', u'14')]
        >>> VtxMatch.split_score(u"avoir l'air: 0.2 ; rire jaune ; chanter :2")
        [(u"avoir l'air", u'0.2'), (u'rire jaune', u''), (u'chanter', u'2')]
        """
        return VtxMatch.re_split_score.findall(query)

    def __init__(self, global_graph, attr_list, default_attr, name=None):
        super(VtxMatch, self).__init__(name=name)
        self.add_option("default_attr", Text(default=default_attr, choices=attr_list, help="default search attribute"))
        self.global_graph = global_graph
        self._vattr_list = attr_list
        self._index = {}
        # build the indices, for each attr
        for attr in attr_list:
            self._index[attr] = {}
            for vtx in global_graph.vs:
                if self._index[attr].has_key(vtx[attr]):
                    self._index[attr][vtx[attr]].append(vtx.index)
                else:
                    self._index[attr][vtx[attr]] = [vtx.index]
        #RMQ: construire un index comme ca n'est pas pertinant pour les graphes non stocké en RAM
        # est-ce que l'on incorpore "select" dans AbstractGraph ?
        # ALIRE: http://permalink.gmane.org/gmane.comp.science.graph.igraph.general/2722

    @Optionable.check
    def __call__(self, query, default_attr=None):
        pzero = {}
        attr_list = []
        #get the default attribute position in list
        attr_idx = self._vattr_list.index(default_attr)
        #if attr_idx is not the first one, rebuild attr_list with default at first position
        if attr_idx > 0 : 
            attr_list = [default_attr]
            attr_list.extend(self._vattr_list[0:attr_idx])
            attr_list.extend(self._vattr_list[attr_idx+1:len(self._vattr_list)])
        else :
            attr_list= self._vattr_list
        
        missing_nodes = {}
        for attr in attr_list : 
            for name, score in VtxMatch.split_score(query) :
                if name not in self._index[attr] :
                    if missing_nodes.has_key(attr) : 
                        missing_nodes[attr].append(name)
                    else : 
                        missing_nodes[attr] = [name]
#                    raise CelloPlayError("Vertex '%s' not found !" % name) #TODO i18n
                else :
                    score = 1. if len(score) == 0 else float(score)
                    for vid in self._index[attr][name] : 
                        pzero[vid] = pzero.get(vid, 0.) + score
            if missing_nodes.has_key(attr) == False : break #if no missing nodes for the attribute, break the loop
                
        if len(missing_nodes) == len(attr_list) :
            print len(missing_nodes)
            str_err_list = []
            str_err = ""
            
            for key, val in missing_nodes.items() :
            
                if (len(val)>1) : 
                    str_err_temp = "Vertices' %ss '%s' not found" % (key, " and ".join(val))
                else : 
                    str_err_temp = "Vertex's %s '%s' not found" % (key, val[0])
                    
                str_err_list.append(str_err_temp)
            
            str_err = "; ".join(str_err_list)
            
            raise CelloPlayError("%s" % str_err) #TODO i18n
                        
        return pzero


#TODO; NeighborsExtractGlobal


class ProxExtractGlobal(Optionable):
    """ Extract vertices of a graph from an inital set of vertices.
    """
    def __init__(self, global_graph, prox_func, name=None):
        """
        :param global_graph: a subclass of :class:`.AbstractGraph`
        :param prox_func: curryfied function for prox. Only `graph`, `pzero`,
            and `length` will be passed a argument to the fuction. If one wants
            to modified the named argument you want passed a lamdba with all
            named arguments setted.

        Here is an example of usable prox fct:

        >>> def prox_func(graph, pzero, length):
        ...     return prox.prox_markov_dict(graph, pzero, length, mode=OUT,
        ...         add_loops=False, weight=None)
        """
        super(ProxExtractGlobal, self).__init__(name=name)
        self.add_option("vcount", Numeric(default=10, help="max vertex count"))
        self.add_option("length", Numeric(default=3, help="random walk length"))
        self.add_option("add_loops", Boolean(default=True, help="virtualy add loops on each vertex"))
        self.prox_func = prox_func
        self.global_graph = global_graph

    @Optionable.check
    def __call__(self, pzero, vcount=None, length=None, add_loops=None, **kwargs):
        kwargs["add_loops"] = add_loops
        v_extract = self.prox_func(self.global_graph, pzero, length, **kwargs)
        v_extract = prox.sortcut(v_extract, vcount) # limit 
        return v_extract


class ProxMarkovExtractionGlobal(ProxExtractGlobal):
    """
    Here is an usage example:

    >>> import igraph as ig
    >>> global_graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> xtrct_markov = ProxMarkovExtractionGlobal(global_graph)
    >>> # then at query time:
    >>> xtrct_markov([4], length=3, vcount=2, add_loops=False)
    [(1, 0.75), (2, 0.125)]
    >>> xtrct_markov([4], length=1, vcount=10, add_loops=True)
    [(1, 0.5), (4, 0.5)]
    """
    def __init__(self, global_graph, name=None):
        super(ProxMarkovExtractionGlobal, self).__init__(global_graph, prox.prox_markov_dict, name=name)


class ProxMtclExtractionGlobal(ProxExtractGlobal):
    """
    Here is an usage example:

    >>> import igraph as ig
    >>> global_graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> xtrct_markov_mtcl = ProxMtclExtractionGlobal(global_graph)
    >>> # then at query time:
    >>> import random; random.seed(0) #for testing purpose
    >>> xtrct_markov_mtcl([4], length=2, vcount=3, throws=200, add_loops=False)
    [(2, 0.31), (3, 0.27), (4, 0.24)]
    """
    def __init__(self, global_graph, name=None):
        super(ProxMtclExtractionGlobal, self).__init__(global_graph, prox.prox_markov_mtcl, name=name)
        self.add_option("throws", Numeric(default=500, help="The number of throws in montecarlo process"))


#RMQ: les extracts non "global" sont en fait des pipeline: Prox() | sortcut
# A condition que Prox soit un optionable 

class ProxExtract(Optionable):
    def __init__(self, prox_func, name=None):
        """
        :param prox_func: curryfied function for prox. Only `graph`, `pzero`,
            and `length` will be passed a argument to the fuction. If one wants
            to modified the named argument you want passed a lamdba with all
            named arguments setted.

        Here is an example of usable prox fct:

        >>> def prox_func(graph, pzero, length): 
        ...     return prox.prox_markov_dict(graph, pzero, length, mode=OUT, 
        ...         add_loops=False, weight=None)
        """
        super(ProxExtract, self).__init__(name=name)
        self.add_option("vcount", Numeric(default=10, help="max vertex count"))
        self.add_option("length", Numeric(default=3, help="random walk length"))
        self.prox_func = prox_func

    @Optionable.check
    def __call__(self, graph, pzero, vcount=None, length=None, **kwargs):
        """
        :param graph: a subclass of :class:`.AbstractGraph`
        :param pzero: list of vertex id, or dictionary `{vid: score}`
        """
        v_extract = self.prox_func(graph, pzero, length, **kwargs)
        v_extract = prox.sortcut(v_extract, vcount) # limit 
        return v_extract


class ProxMarkovExtraction(ProxExtract):
    """
    Here is an usage example:

    >>> xtrct_markov = ProxMarkovExtraction()
    >>> # then at query time:
    >>> import igraph as ig
    >>> graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> xtrct_markov(graph, [0], length=2, vcount=3)
    [(0, 0.25), (2, 0.25), (3, 0.25)]
    """
    def __init__(self, name=None):
        super(ProxMarkovExtraction, self).__init__(prox.prox_markov_dict, name=name)


class ProxMonteCarloExtraction(ProxExtract):
    """
    Here is an usage example:

    >>> xtrct_markov_mtcl = ProxMonteCarloExtraction()
    >>> # then at query time:
    >>> import igraph as ig
    >>> graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> import random; random.seed(0) #for testing purpose
    >>> xtrct_markov_mtcl(graph, [0], length=2, vcount=3, throws=2000)
    [(2, 0.2785), (3, 0.2505), (4, 0.2495)]
    """
    def __init__(self, name=None):
        super(ProxMonteCarloExtraction, self).__init__(prox.prox_markov_mtcl, name=name)
        self.add_option("throws", Numeric(default=500, help="The number of throws in montecarlo process"))




# FIXME Untested 
def extract_bipartite(graph, p0, length, vcount, mode=OUT, add_loops=False, 
                        weight=None, neighbors=neighbors):
    """ neighborhood of a list of vertices in a bipartite graph

    :param pzero: list of starting vertices (ids)
    :param l: length of the random walk use to compute the neighborhood
    :param neighbors_fct: (optional) function that return, for a given graph and a given vertex id, the neighbors of the vertexs

    :returns: a list of the form: [(vid1, score), (vid2, score), ...]
    """
    # prox curryfication 
    prox_method = lambda _length : prox.prox_markov_dict(graph, p0, _length)
    
    v_extract = prox_method(length)
    v_extract.update(prox_method(length+1))
    
    v_extract = v_extract.items() #  sparce prox_vect : [(id, prox_value)]
    v_extract.sort(key=lambda x: x[1], reverse=True) # sorting by prox.prox_markov
    v_extract = v_extract[:vcount]
    
    return v_extract

