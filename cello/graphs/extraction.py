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

from reliure import Composable, Optionable
from reliure.types import Numeric, Text, Boolean
from reliure.exceptions import ReliurePlayError

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
    >>> match("")
    {}
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
    
    >>> #Test case sensitivity
    >>> match = VtxMatch(global_graph, attr_list=[u"name", u"label"], default_attr=u"name", case_sensitive=False)
    >>> match("a")
    {0: 1.0}
    >>> match("A")
    {0: 1.0}
    >>> match = VtxMatch(global_graph, attr_list=[u"name", u"label"], default_attr=u"name")
    >>> match("A")
    Traceback (most recent call last):
    ...
    ReliurePlayError: Vertex's name 'A' not found; Vertex's label 'A' not found
    >>> match("a")
    {0: 1.0}


    This component can also throw some :class:`.ReliurePlayError` if vertices are
    not found:

    >>> match("bp")
    Traceback (most recent call last):
    ...
    ReliurePlayError: Vertex's name 'bp' not found; Vertex's label 'bp' not found
    
    >>> match("bp;lj")
    Traceback (most recent call last):
    ...
    ReliurePlayError: Vertices' names 'bp and lj' not found; Vertices' labels 'bp and lj' not found

    >>> match("bp;1")
    Traceback (most recent call last):
    ...
    ReliurePlayError: Vertices' names 'bp and 1' not found; Vertex's label 'bp' not found

    >>> match("a;1")
    Traceback (most recent call last):
    ...
    ReliurePlayError: Vertex's name '1' not found; Vertex's label 'a' not found
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

    def __init__(self, global_graph, attr_list, default_attr, case_sensitive=True, name=None):
        """
        :attr global_graph: the graph to search vertices in
        :attr attr_list: list of the vtx attributes used to identify vertices
        :attr default_attr: the one used by default (should be in `attr_list`)
        :arre case_sensitive: is the search case_sensitive
        """
        super(VtxMatch, self).__init__(name=name)
        self.add_option("default_attr", Text(default=default_attr, choices=attr_list, help="default search attribute"))
        self.global_graph = global_graph
        self._vattr_list = attr_list
        self._index = {}
        
        self._case_sensitive = case_sensitive
        
        # build the indices, for each attr
        for attr in attr_list:
            self._index[attr] = {}
            for vtx in global_graph.vs:
                
               #Manage the case sentivity
                if self._case_sensitive: 
                    vtx_label = vtx[attr]
                else:
                    vtx_label = vtx[attr].lower()
                    
                if vtx_label in self._index[attr]:
                    self._index[attr][vtx_label].append(vtx.index)
                else:
                   self._index[attr][vtx_label] = [vtx.index]
        
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
        if attr_idx > 0:
            attr_list = [default_attr]
            attr_list.extend(self._vattr_list[0:attr_idx])
            attr_list.extend(self._vattr_list[attr_idx+1:len(self._vattr_list)])
        else:
            attr_list= self._vattr_list

        missing_nodes = {}
        for attr in attr_list:
            # for each attributes
            for name, score in VtxMatch.split_score(query):
                # for each term in the query
                if not self._case_sensitive:
                    name = name.lower()
                # does we have it in the attr ?
                if name not in self._index[attr]:
                    # not found !
                    if attr in missing_nodes:
                        missing_nodes[attr].append(name)
                    else:
                        missing_nodes[attr] = [name]
                else:
                    # found !
                    score = 1. if len(score) == 0 else float(score)
                    for vid in self._index[attr][name]:
                        pzero[vid] = pzero.get(vid, 0.) + score
            #if no missing nodes for the attribute, break the loop
            if not attr in missing_nodes:
                break

        # if we have missing nodes for all attributes... then error !
        if len(missing_nodes) == len(attr_list):
            str_err_list = []
            str_err = ""
            for key, val in missing_nodes.items():
                if len(val) > 1:
                    str_err_temp = "Vertices' %ss '%s' not found" % (key, " and ".join(val))
                else:
                    str_err_temp = "Vertex's %s '%s' not found" % (key, val[0])
                str_err_list.append(str_err_temp)
            str_err = "; ".join(str_err_list)
            raise ReliurePlayError("%s" % str_err) #TODO i18n

        return pzero


#TODO; NeighborsExtractGlobal


class ProxExtractGlobal(Optionable):
    """ Extract vertices of a graph from an inital set of vertices.
    """
    def __init__(self, global_graph, prox_func, default_mode=OUT, weight=None, loops_weight=None, name=None):
        """
        :param global_graph: a subclass of :class:`.AbstractGraph`
        :param prox_func: curryfied function for prox. Only `graph`, `pzero`,
            and `length` will be passed a argument to the fuction. If one wants
            to modified the named argument you want passed a lamdba with all
            named arguments setted.
        :param default_mode: default mode for the random walk (useful only if the graph is directed)
        :param weight: if None the graph is not weighting, else it could be:
            a str corresponding to an edge attribute to use as weight,
            or a list of weight (`|weight| == graph.ecount()`),
            or a callable `lambda graph, source, target: wgt`
        :param loops_weight: only if `add_loops`, weight for added loops, it may be :
            a str corresponding to a vertex attribute,
            or a list of weight (`|loops_weight| == graph.vcount()`),
            or a callable `lambda graph, vid, mode, weight: wgt`


        Here is an example of usable prox fct:

        >>> def prox_func(graph, pzero, length):
        ...     return prox.prox_markov_dict(graph, pzero, length, mode=OUT,
        ...         add_loops=False, weight=None)
        """
        super(ProxExtractGlobal, self).__init__(name=name)
        
        self.add_option("vcount", Numeric(default=10, help="max vertex count"))
        self.add_option("length", Numeric(default=3, help="random walk length"))
        self.add_option("add_loops", Boolean(default=True, help="virtualy add loops on each vertex"))
        
        
        self._modes = {
            "text_to_num": {"IN":IN, "OUT":OUT, "ALL":ALL},
            "num_to_text": {IN:u"IN", OUT:u"OUT", ALL:u"ALL"}
            }

        self.add_option("mode", Text(default=self._modes["num_to_text"][default_mode], choices=[u"IN", u"OUT", u"ALL"], help="edges to walk on from a vertex"))
        
        self._wgt = weight
        if weight is not None : 
            self.add_option("is_wgt", Boolean(default=True, help="consider graph weight?"))
        self.prox_func = prox_func
        self.global_graph = global_graph
        self._loops_weight= loops_weight

    @Optionable.check
    def __call__(self, pzero, vcount=None, length=None, add_loops=None, mode=None, is_wgt=None, **kwargs):
        kwargs["add_loops"] = add_loops
        kwargs["loops_weight"] = self._loops_weight
        kwargs["mode"] = self._modes["text_to_num"][mode]
        
        if self._wgt is not None and is_wgt == True:
            kwargs["weight"] = self._wgt
            
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
    >>> # in case of empty p0, :
    >>> xtrct_markov([], length=3, vcount=2, add_loops=False)
    [(1, 0.5250000000000001), (2, 0.17500000000000002)]
    >>> xtrct_markov([4], length=3, vcount=0, add_loops=False)
    []
    >>> xtrct_markov([4], length=1, vcount=10, add_loops=True)
    [(1, 0.5), (4, 0.5)]
    >>> global_graph = ig.Graph.Formula("a-->b-->c")
    >>> xtrct_markov = ProxMarkovExtractionGlobal(global_graph)
    >>> xtrct_markov([1], length=1, vcount=10, add_loops=False)
    [(2, 1.0)]
    >>> xtrct_markov([1], length=1, vcount=10, add_loops=False, mode=u"IN")
    [(0, 1.0)]
    >>> xtrct_markov([1], length=1, vcount=10, add_loops=False, mode=u"ALL")
    [(0, 0.5), (2, 0.5)]
    >>> # one ca also start from no vertices, then you start from all
    >>> xtrct_markov([], length=1, vcount=10, add_loops=False, mode=u"ALL") 
    [(1, 0.6666666666666666), (0, 0.16666666666666666), (2, 0.16666666666666666)]
    >>> # test of the weight
    >>> global_graph = ig.Graph.Formula("a-->b-->c")
    >>> global_graph.es["wgt"] = [3, 1]
    >>> xtrct_markov = ProxMarkovExtractionGlobal(global_graph, weight = "wgt")
    >>> xtrct_markov([1], length=1, vcount=10, add_loops=False, mode=u"ALL") 
    [(0, 0.75), (2, 0.25)]
    >>> xtrct_markov([1], length=1, vcount=10, add_loops=True, mode=u"ALL") 
    [(0, 0.5), (1, 0.3333333333333333), (2, 0.16666666666666666)]
    
    """
    def __init__(self, global_graph, default_mode=OUT, weight=None, loop_weight=None, name=None):
        super(ProxMarkovExtractionGlobal, self).__init__(global_graph, prox.prox_markov_dict, default_mode, weight, loop_weight, name=name)


class ProxMtclExtractionGlobal(ProxExtractGlobal):
    """
    Here is an usage example:

    >>> import igraph as ig
    >>> global_graph = ig.Graph.Formula("a,b,c,d,e,a--b--c--d, b--d, b--e")
    >>> xtrct_markov_mtcl = ProxMtclExtractionGlobal(global_graph)
    >>> # then at query time:
    >>> xtrct_markov_mtcl([4], length=2, vcount=3, throws=200, add_loops=False)  # doctest:+ELLIPSIS
    [(2, ...), (3, ...), (4, ...)]
    """
    def __init__(self, global_graph, name=None):
        super(ProxMtclExtractionGlobal, self).__init__(global_graph, prox.prox_markov_mtcl, name=name)
        self.add_option("throws", Numeric(default=500, help="The number of throws in montecarlo process"))


class ProxMarkovExtractionGlobalBigraph(Optionable):
    """ According to an initial distribution of weight over some vertices of
    the graph extract a given number of vertices by two random walks : one of
    odd length one of even lenght.
    
    >>> # a global graph is needed to build the extractor
    >>> import igraph as ig
    >>> g = ig.Graph.Formula("a:b:c--A:B:C:D, d--D:E, c:d--F")
    >>> g.vs["type"] = [vtx["name"].islower() for vtx in g.vs]
    >>> g.vs["name"] # to see corespondance between id and name
    ['a', 'b', 'c', 'A', 'B', 'C', 'D', 'd', 'E', 'F']
    >>> extract = ProxMarkovExtractionGlobalBigraph(g)
    >>> extract.print_options()
    half_length (Numeric, default=2): Two walks will be computed one of lenght t*2-1 one of lenght t*2
    odd_count (Numeric, default=15): Number of vertices to keep with the *odd* lenght walk
    even_count (Numeric, default=35): Number of vertices to keep with the *even* lenght walk

    One can then use it:
    
    >>> extract({0:1.}, half_length=1, odd_count=4, even_count=0)
    [(3, 0.25), (4, 0.25), (5, 0.25), (6, 0.25)]
    >>> extract({0:1.}, half_length=1, odd_count=0, even_count=20)
    [(0, 0.3125), (1, 0.3125), (2, 0.3125), (7, 0.0625)]
    >>> extract({0:1.}, half_length=1, odd_count=20, even_count=20)
    [(3, 0.25), (4, 0.25), (5, 0.25), (6, 0.25), (0, 0.3125), (1, 0.3125), (2, 0.3125), (7, 0.0625)]
    """
    def __init__(self, graph, name=None):
        super(ProxMarkovExtractionGlobalBigraph, self).__init__(name=name)
        self.add_option("half_length", Numeric(
            min=0, max=20, default=2,
            help="Two walks will be computed one of length t*2-1 one of lenght t*2"
        ))
        self.add_option("odd_count", Numeric(
            min=0, default=15,
            help="Number of vertices to keep with the *odd* length walk"
        ))
        self.add_option("even_count", Numeric(
            min=0, default=35,
            help="Number of vertices to keep with the *even* length walk"
        ))
        # create the the basic extractor
        self.extrator = ProxMarkovExtractionGlobal(graph)

    @Optionable.check
    def __call__(self, pzero, half_length=None, odd_count=None, even_count=None):
        #TODO: assert pzero only on one kind of vtx
        odd_vect = self.extrator(pzero, length=half_length*2-1, vcount=odd_count, add_loops=False)
        even_vect = self.extrator(pzero, length=half_length*2, vcount=even_count, add_loops=False)
        odd_vect.extend(even_vect)
        return odd_vect


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

