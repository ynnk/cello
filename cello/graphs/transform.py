#-*- coding:utf-8 -*-
""" :mod:`cello.graphs.transform`
==============================
"""
import logging

import igraph as ig
import numpy as np

from cello.pipeline import Composable, Optionable
from cello.types import Text, Numeric, Boolean

from cello.graphs import EDGE_WEIGHT_ATTR
from cello.graphs.prox import prox_markov_dict
from cello.graphs.builder import GraphBuilder

_logger = logging.getLogger("cello.graphs.transform")


class MergeGraphs(Composable):
    """ Merge a list of graph into one.
    
    By default no vertices are merged (each vertex in each graph is keeped).
    However one can specify a vertex 'hash' function (`vertex_id`) that is used
    to identify vertices. If two vertices have the same 'vertex_id' they will 
    be merged.
    
    If we have two graphs like:
    
    >>> import igraph as ig
    >>> g1 = ig.Graph.Formula("a--b--c--a")
    >>> g3 = ig.Graph.Formula("a--B--C--a")

    is is possible to merge it with:

    >>> merger = MergeGraphs(vertex_id=lambda graph, vtx: vtx["name"])

    that give:

    >>> g = merger([g1, g3])
    >>> print(g.summary(verbosity=1))
    IGRAPH UN-- 5 6 -- 
    + attr: name (v)
    + edges (vertex names):
    a--b, a--c, b--c, a--B, a--C, B--C

    This composant is usefull when you have different graph builders that work
    from a same input.

    To illustrate it, we can take the two following simple (and useless) graph
    builders:

    >>> @Composable
    ... def lower_seq(string):
    ...     letters = [letter for letter in string if letter.islower()]
    ...     return ig.Graph.Formula("--".join(letters))
    >>> @Composable
    ... def upper_seq(string):
    ...     letters = [letter for letter in string if letter.isupper()]
    ...     return ig.Graph.Formula("--".join(letters))

    They build graphs from a sequence of char, taking into acount only upper or
    lower chars. Here is an exemple:

    >>> g1 = upper_seq("gBrIaphG")
    >>> print(g1.summary(verbosity=1))
    IGRAPH UN-- 3 2 -- 
    + attr: name (v)
    + edges (vertex names):
    B--I, I--G
    >>> g2 = lower_seq("gBrIaphG")
    >>> print(g2.summary(verbosity=1))
    IGRAPH UN-- 5 4 -- 
    + attr: name (v)
    + edges (vertex names):
    g--r, r--a, a--p, p--h

    We can now build a meta composant that use this two graph builders and then
    merge it in one graph.

    >>> gbuilder = (upper_seq & lower_seq) | MergeGraphs()

    This component can be used this way:

    >>> g = gbuilder("gBrIaphG")
    >>> print(g.summary(verbosity=1))
    IGRAPH UN-- 8 6 -- 
    + attr: name (v)
    + edges (vertex names):
    B--I, I--G, g--r, r--a, a--p, p--h

    """
    def __init__(self, name=None, vertex_id=None):
        """
        :param vertex_id: function to identify vertices
        :type vertex_id: (graph, vertex) -> str
        """
        super(MergeGraphs, self).__init__(name=name)
        if vertex_id is None:
            vertex_id = lambda graph, vtx: "%s-%s" % (hash(graph), vtx.index)
        self.vertex_id = vertex_id

    def __call__(self, graph_list):
        vertex_id = self.vertex_id
        # create the graph builder
        gbuilder = GraphBuilder(directed=False) #TODO: directed ?
        # declar attrs
        for graph in graph_list:
            # vtx_attr
            for vattr in graph.vs.attributes():
                gbuilder.declare_vattr(vattr)
            # edge_attr
            for eattr in graph.es.attributes():
                gbuilder.declare_eattr(eattr)
        #
        gbuilder.reset()
        # build the vertices of the merged graph
        for graph in graph_list:
            for vtx in graph.vs:
                vid = vertex_id(graph, vtx)
                vgid = gbuilder.add_get_vertex(vid)
                # add attributes
                for vattr, val in vtx.attributes().iteritems():
                    gbuilder.set_vattr(vgid, vattr, val)
        #
        # build the edges
        for graph in graph_list:
            for edge in graph.es:
                sid = vertex_id(graph, graph.vs[edge.source])
                sgid = gbuilder.add_get_vertex(sid)
                tid = vertex_id(graph, graph.vs[edge.target])
                tgid = gbuilder.add_get_vertex(tid)
                eid = gbuilder.add_get_edge(sgid, tgid)
                # add attributes
                for eattr, val in edge.attributes().iteritems():
                    gbuilder.set_eattr(eid, eattr, val)
                    #TODO : how to deal with conflict ?
        #
        # Creates and returns the graph
        return gbuilder.create_graph()


class Weight(Optionable):
    """ Add/Override ``weight`` attribute

    >>> import igraph as ig
    
    >>> graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> graph.es["weight"] = [1, 2, 3, 4, 1]
    >>> weight = Weight(weight="weight")
    >>> graph = weight(graph, is_weighted = True)
    >>> graph.es["weight"]
    [1, 2, 3, 4, 1]
    
    >>> graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> graph.es["wgt"] = [1, 2, 3, 4, 1]
    >>> weight = Weight(weight="wgt")
    >>> graph = weight(graph, is_weighted = True)
    >>> graph.es["weight"]
    [1, 2, 3, 4, 1]
    
    >>> graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> graph.es["weight"] = [1, 2, 3, 4, 1]
    >>> weight = Weight()
    >>> graph = weight(graph, is_weighted = True)
    >>> graph.es["weight"]
    [1.0, 1.0, 1.0, 1.0, 1.0]
    
    >>> graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> graph.es["weight"] = [1, 2, 3, 4, 1]
    >>> weight = Weight()
    >>> graph = weight(graph, is_weighted = False)
    >>> graph.es["weight"]
    [1.0, 1.0, 1.0, 1.0, 1.0]
    
    >>> graph = ig.Graph.Formula("a--b--c--d, b--d, b--e")
    >>> weight = Weight()
    >>> graph = weight(graph, is_weighted = True)
    >>> graph.es["weight"]
    [1.0, 1.0, 1.0, 1.0, 1.0]
    """
    def __init__(self, weight=None, name=None):
        """
        :attr graph: global graph from which subgraph will be extracted
        :attr is_weighted: boolean to know weither the subgraph weighted or no : if False then graph.es[weight]=1.0
        :attr weight: name of the edges' ``weight`` attribute  when is_weighted == True : if weight = None then graph.es[weight]=1.0
        :attr name: name of the component
        """
        super(Weight, self).__init__(name=name)
        
        self.add_option("is_weighted", Boolean(default=True, help="is the graph weighted?"))
        
        self._weight = weight

    def __call__(self, graph, is_weighted=None):

        if is_weighted==True and isinstance(self._weight, str) and self._weight in graph.edge_attributes() : 
            graph.es["weight"] = graph.es[self._weight]
        else :
            graph.es["weight"] = 1.
        
        return graph


class EdgeAttr(Composable):
    """ Add one or more attributes to the edges of the graph

    >>> g = ig.Graph.Formula("a--B, a--C, a--D, C--f, D--f")
    >>> edge_label = lambda graph, edg: '-'.join(graph.vs[[edg.source, edg.target]]['name'])
    >>> add_attr = EdgeAttr(weight=2.0, label=edge_label)
    >>> g = add_attr(g)
    >>> g.es['weight']
    [2.0, 2.0, 2.0, 2.0, 2.0]
    >>> g.es['label']
    ['a-B', 'a-C', 'a-D', 'C-f', 'D-f']
    """
    def __init__(self, name=None, **kwargs):
        super(EdgeAttr, self).__init__(name=name)
        self._eattrs = kwargs

    def __call__(self, graph):
        for attr, value in self._eattrs.iteritems():
            if callable(value):
                graph.es[attr] = [value(graph, edg) for edg in graph.es]
            else:
                graph.es[attr] = value
        return graph


def bipartit_linw(graph, edge):
    """ Ad-Hoc method to weight a bipartite (tag-document) graph

    Linear weight according to nb of neighbors ot the tag compared to the
    total nuber of documents:
     * a tag present in only 1 document has small edge weight
     * a tag present in all documents has small edge weight
     * optimal (=1) is form nb_doc/4.
    
    Here is an ascii art plot ::
    
            1-|     *,
              |   / ! \,
        wgt   |  /  !   \, 
              | /   !     \,
            0-|/____!_______\,
              0   nb_opt   nb_doc
             nb of neigh of the tag
     
    This method 'seems' to work prety well but can clearly be improved !
     
    It sould be used with :class:`EdgeAttr` :
    
    >>> weighter = EdgeAttr(weight=bipartit_linw)
    >>> # then at run time
    >>> g = ig.Graph.Formula("a:b--B:C:D, c:d:e:f:g--C, h--D")
    >>> g.vs["type"] = [v["name"].islower() for v in g.vs]
    >>> g = weighter(g)
    >>> ["%s-%s w:%1.3f" % (g.vs[e.source]["name"], g.vs[e.target]["name"], e["weight"]) for e in g.es]
    ['a-B w:1.000', 'a-C w:0.167', 'a-D w:0.833', 'b-B w:1.000', 'b-C w:0.167', 'b-D w:0.833', 'C-c w:0.167', 'C-d w:0.167', 'C-e w:0.167', 'C-f w:0.167', 'C-g w:0.167', 'D-h w:0.833']
    
    """
    # get the doc (top) and tag (bot) vertex of the edge
    source, target = graph.vs[edge.source], graph.vs[edge.target]
    if source["type"]:
        top, bot = source, target
    else:
        top, bot = target, source
    # compute basic values
    nb_vois_tag = 1.*len(bot.neighbors())
    nb_doc = 1.*len(graph.vs.select(type=True))
    # Optiomal number if neighbours :
    nb_opt = nb_doc/4.
    #print top, bot
    #print top["name"], bot["name"]
    #print nb_vois_tag, nb_doc, min(nb_vois_tag/nb_opt, 1 - (nb_vois_tag-nb_opt)/(nb_doc-nb_opt))
    return min(nb_vois_tag/nb_opt, 1 - (nb_vois_tag-nb_opt)/(nb_doc-nb_opt))


class VtxAttr(Composable):
    """ Add one or more attributes to the vertices of the graph
    
    >>> g = ig.Graph.Formula("a--B, a--C, a--D, C--f, D--f")
    >>> add_attr = VtxAttr(score=1, type=lambda graph, vtx: vtx['name'].islower())
    >>> g = add_attr(g)
    >>> g.vs["score"]
    [1, 1, 1, 1, 1]
    >>> g.vs["type"]
    [True, False, False, False, True]
    """
    def __init__(self, name=None, **kwargs):
        super(VtxAttr, self).__init__(name=name)
        self._vattrs = kwargs

    def __call__(self, graph):
        for attr, value in self._vattrs.iteritems():
            if callable(value):
                graph.vs[attr] = [value(graph, vtx) for vtx in graph.vs]
            else:
                graph.vs[attr] = value
        return graph


class TrueInFirst(Composable):
    """ Permute bigraph vertices to move True vertices in first places.

    >>> true_in_first = TrueInFirst()
    >>> g = ig.Graph.Formula("a:b:c--A:B:C:D, d--D:E, c:d--F")
    >>> g.vs["type"] = [vtx["name"].islower() for vtx in g.vs]
    >>> g.vs["name"]
    ['a', 'b', 'c', 'A', 'B', 'C', 'D', 'd', 'E', 'F']
    >>> ng = true_in_first(g)
    >>> ng.vs["name"]
    ['a', 'b', 'c', 'd', 'A', 'B', 'C', 'D', 'E', 'F']
    """
    def __init__(self, name=None):
        super(TrueInFirst, self).__init__(name=name)

    def __call__(self, bigraph):
        new_ids = {vtx.index: vid for vid, vtx in enumerate(bigraph.vs.select(type=True))}
        nb_true = len(new_ids)
        new_ids.update({vtx.index: nb_true+vid for vid, vtx in enumerate(bigraph.vs.select(type_ne=True))})
        new_order = [new_ids[vid] for vid in xrange(bigraph.vcount())]
        bigraph_true_first = bigraph.permute_vertices(new_order)
        return bigraph_true_first


class SymFalseBigraph(Optionable):
    """ Symetrise a "false-bipartite" graph, i.e. an unipartite graph considered
    as a bipartite one.

    If you have the following bigraph:

    >>> import igraph as ig
    >>> g = ig.Graph.Formula("A--b, B--c:d, D--a")
    >>> g.vs["type"] = [vtx["name"].isupper() for vtx in g.vs]
    >>> print(g.summary(verbosity=2))
    IGRAPH UN-T 7 4 -- 
    + attr: name (v), type (v)
    + edges (vertex names):
    A--b, B--c, B--d, D--a

    each vertex is present either with a lower name or a upper name (or both).

    >>> # you cat use the following 'symetriser'
    >>> sym = SymFalseBigraph(
    ...     vtx_true_hash=lambda vtx: vtx["name"].lower(),
    ...     vtx_false_hash=lambda vtx: vtx["name"]
    ... )
    >>> g = sym(g)
    >>> print(g.summary(verbosity=2))
    IGRAPH UN-T 7 10 -- 
    + attr: name (v), type (v)
    + edges (vertex names):
    A -- b, d, a
    b -- A, B, D
    B -- b, c, d, a
    c -- B
    d -- A, B, D
    D -- b, d, a
    a -- A, B, D

    One can see that now there is an edge between lower and uper version of each
    vertex. Also there is now an edge between 'a' and 'B' (for exemple) because
    there is an edge between 'A' and 'b' in the initial graph.

    """
    def __init__(self, name=None, vtx_true_hash=None, vtx_false_hash=None):
        super(SymFalseBigraph, self).__init__(name=name)
        # hash to identify type True vertices
        if vtx_true_hash is None:
            vtx_true_hash = lambda vtx: vtx["label"]
        self.vtx_true_hash = vtx_true_hash
        # hash to identify type False vertices
        if vtx_false_hash is None:
            vtx_false_hash = lambda vtx: vtx["label"]
        self.vtx_false_hash = vtx_false_hash

    @Optionable.check
    def __call__(self, bigraph):
        vtx_false_hash = self.vtx_false_hash
        vtx_true_hash = self.vtx_true_hash
        new_edges = []
        # get id of vertices from there 'hash'
        true_by_hash = {vtx_true_hash(vtx): vtx.index for vtx in bigraph.vs.select(type=True)}
        false_by_hash = {vtx_false_hash(vtx): vtx.index for vtx in bigraph.vs.select(type=False)}
        #
        # ETAPE 1: self loops
        # pour tout les True (doc) : ajout le lien sym si autre existe
        for vtx_doc_hash, vtx_doc_index in true_by_hash.iteritems():
            if vtx_doc_hash in false_by_hash:
                new_edges.append((vtx_doc_index, false_by_hash[vtx_doc_hash]))
        #
        # ETAPE 2 : symetrisation
        # pour tout les True (doc) :
        for vtx_doc_hash, vtx_doc_index in true_by_hash.iteritems():
            if vtx_doc_hash not in false_by_hash:
                # this document is not linked by any other...
                # so it can't make in link to the others
                continue
            # pour tous les liens sortants, ajoute le lien entrant dans l'autre sens
            for neith in bigraph.neighbors(vtx_doc_index):
                vtx_neith_hash = vtx_false_hash(bigraph.vs[neith])
                if vtx_neith_hash in true_by_hash:
                    new_edges.append((true_by_hash[vtx_neith_hash], false_by_hash[vtx_doc_hash]))
        self._logger.info("Add %d edges" % len(new_edges))
        bigraph.add_edges(new_edges)
        return bigraph


class GraphProjection(Optionable):
    """ Project a bipartite graph to an unipartite one

    >>> projection = GraphProjection()
    >>> projection.print_options()
    proj_wgt (Text, default=p, in: {no, count, p, pmin, pmax, pavg, confl}): projection weighting method

    .. Warning:: The bipartite graph should have True vertices in first in
        vertex sequence, if not use  :class:`TrueInFirst`:.

    This could be used without weights on original graph:

    >>> g = ig.Graph.Formula("a:b:c--A:B:C:D, d--D:E, c:d--F")
    >>> g.vs["type"] = [vtx["name"].islower() for vtx in g.vs]

    As the graph do not have True vertices in first we have to use :class:`TrueInFirst`:

    >>> projection = TrueInFirst() | GraphProjection()

    One can then compute a projection without weights:

    >>> gp = projection(g, proj_wgt='no')
    >>> gp.vs["name"]
    ['a', 'b', 'c', 'd']
    
    Note that edges always have weight attribute:
    
    >>> gp.es["weight"]
    [1, 1, 1, 1, 1, 1]
	>>>  # also note that no loops are created
    >>> gp.is_loop()
    [False, False, False, False, False, False]

    One can also use the weight to count the number of commun neighbors in the
    original bipartite graph:
    
    >>> gp = projection(g, proj_wgt='count')
    >>> gp.es["weight"]
    [4, 4, 1, 4, 1, 2]


    For other projection weighting we need to add a weight on the graph

    >>> add_weight = EdgeAttr(weight=1.0)
    >>> g = add_weight(g)
    >>> g.es["weight"]
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]


    Then different weights are possible (see :meth:`GraphProjection.bigraph_projection`):
    
    >>> gp = projection(g, proj_wgt='p')
    >>> gp.es["weight"]
    [1.25, 1.25, 0.25, 1.25, 0.25, 0.7500000000000001]
    >>> gp = projection(g, proj_wgt='pavg')
    >>> gp.es["weight"]
    [0.3125, 0.28125, 0.07291666666666666, 0.28125, 0.07291666666666666, 0.2]
    >>> gp = projection(g, proj_wgt='confl')
    >>> gp.es["weight"]
    [0.5555555555555556, 0.5, 0.25, 0.5, 0.25, 0.4444444444444445]
    """
    def __init__(self, name=None):
        """ Projection of a bipartite graph to a unipartite graph
        """
        Optionable.__init__(self, name=name)
        self.add_option("proj_wgt", Text(default='p', vtype=str,
             help=u"projection weighting method",
             choices=['no', 'count', 'p', 'pmin', 'pmax', 'pavg', 'confl']))

    @Optionable.check
    def __call__(self, graph, proj_wgt=None):
        # The projection work only because:
        #  - documents are the first vertices of the graph
        #  - the projection fct do not change the vertices order
        # this two points are checked with following assert
        if __debug__:
            docids = [vtx.index for vtx in graph.vs.select(type=True)]
            assert len(docids) == 0 or sorted(docids) == range(max(docids) + 1), \
                "Documents should be the first veritces of the graph"
        if graph.vcount() == 0:
            pgraph = graph.copy()
        else:
            pgraph = GraphProjection.bigraph_projection(graph, proj_wgt, wgt_attr=EDGE_WEIGHT_ATTR)
        if __debug__ and "_doc" in graph.vs.attributes():
            assert pgraph.vs["_doc"] == graph.vs.select(type=True)["_doc"]
        return pgraph

    @staticmethod
    def bigraph_projection(graph, weight=None, wgt_attr=EDGE_WEIGHT_ATTR):
        """ Projection of a bipartite graph
    
        .. note:: this method is static so it may be use independently

        weight:
            - 'count': number of neighbors in commun
            - 'p': 
                :math:`w(u, v) = p(u\\rightarrow v, t=2) . deg(u) = p(v \\rightarrow u, t=2) . deg(v)`
            - 'confl': 
                :math:`w(u, v) = \\frac{ p(u\\rightarrow v, t=2) }{p(u \\rightarrow v, t=2) + \\pi_v} \\quad`
                avec 
                :math:`\\quad \\pi_v = \\frac{deg(v)}{ \\sum_j deg(j)}`
            - 'pmin': 
                :math:`w(u, v) = \\min\\big(p(u\\rightarrow v, t=2), \quad p(v \\rightarrow u, t=2) \\big )`
            - 'pmax':  
                :math:`w(u, v) = \\max\\big(p(u\\rightarrow v, t=2), \quad p(v \\rightarrow u, t=2) \\big )`
            - 'pavg':
                :math:`w(u, v) = \\frac{1}{2} . \\big ( p(u\\rightarrow v, t=2) + p(v \\rightarrow u, t=2)\\big )`
                - else: no weight
        """
        multiplicity = True if weight == "count" else False
        pg, _ = graph.bipartite_projection(types="type", multiplicity=multiplicity, probe1=0)
        if weight in ["p", "pmin", "pmax", "pavg", "confl"]:
            P = [prox_markov_dict(graph, [vid.index], length=2, weight=wgt_attr, add_loops=False) for vid in pg.vs]
            if weight == "p":
                pwgt = lambda a, b: P[a].get(b, 0.) * graph.degree(a)
            elif weight == "confl":
                degtot = 1. * sum(graph.vs.select(type=True).degree())
                pwgt = lambda a, b: P[a].get(b, 0.) / ( P[a].get(b, 0.) + graph.degree(b)/degtot )
            elif weight == "pmin":
                pwgt = lambda a, b: min(P[a].get(b, 0.), P[b].get(a, 0.))
            elif weight == "pmax":
                pwgt = lambda a, b: max(P[a].get(b, 0.), P[b].get(a, 0.))
            elif weight == "pavg":
                pwgt = lambda a, b: (P[a].get(b, 0.) + P[b].get(a, 0.)) / 2.
            pg.es[wgt_attr] = [pwgt(edg.source, edg.target) for edg in pg.es]
        elif weight == "count":
            pass
        else:
            pg.es[wgt_attr] = 1

        # clear nul edges.keys
        null_edges = [e.index for e in pg.es if e[wgt_attr] - 1e-6 <= 0]
        _logger.info("Deletion of %d null edges" % (len(null_edges)))
        
        pg.delete_edges(null_edges)
        return pg


class WeightByConfluence(Optionable):
    """ Normalise edge weights using the confluence.
    
    >>> weighter = WeightByConfluence()
    >>> weighter.print_options()
    wlength (Numeric, default=3): length of the random walks

    >>> g = ig.Graph.Formula("a--b:c:d:e, e--f")
    >>> g.es["weight"] = [1, 2, 1, 1, 2]
    >>> g = weighter(g, wlength=1)
    >>> g.es["weight"]
    [0.625, 0.625, 0.625, 0.42553191489361708, 0.7142857142857143]

    >>> g = ig.Graph.Formula("a--b:c:d:e, e--f")
    >>> g.es["weight"] = [1, 2, 1, 1, 2]
    >>> g = weighter(g, wlength=3)
    >>> g.es["weight"]
    [0.55408753096614372, 0.55408753096614372, 0.55408753096614372, 0.37079233557742103, 0.66260543580131204]

    >>> g = ig.Graph.Formula("a--b:c:d:e, e--f")
    >>> g.es["weight"] = [1, 2, 1, 1, 2]
    >>> #HACK: strange call to avoid the check on option (wlength can't be higher than 10)
    >>> g = WeightByConfluence.__call__._no_check(weighter, g, wlength=100)
    >>> g.es["weight"]
    [0.47801147996233123, 0.47801147996233123, 0.47801147996233123, 0.4780114630482894, 0.4972375921723784]
    """
    def __init__(self, name=None):
        super(WeightByConfluence, self).__init__(name=name)
        self.add_option("wlength", Numeric(default=3, min=1, max=10,
            help="length of the random walks"))
        #TODO: add an option tu remove the edge before to compute the confl
        #TODO; add param to configure the edge attr to use

    @Optionable.check
    def __call__(self, graph, wlength=None):
        assert not graph.is_directed() #TODO: manage directed graph

        # compute total weight
        weigths = graph.es[EDGE_WEIGHT_ATTR]
        wtot = sum(weigths)
        # add weight of loosp
        wtot += graph.vcount()

        ## calcul la proba limite de chaque sommet, + 1 for add_loops
        # weight de chaque somment:
        limits = np.fromiter(
            (sum(weigths[inc_edge] for inc_edge in graph.incident(vtx)) + 1 for vtx in graph.vs),
            np.float, count=graph.vcount()
        )
        # normalised
        limits = limits / limits.sum()

        cweight = np.zeros(graph.ecount())
        # pour chaque sommet
        for vtx in graph.vs:
            # calcul ligne prox
            lprox = prox_markov_dict(
                graph,
                [vtx.index],
                wlength,
                weight=weigths,
                add_loops=True,
                loops_weight=None, # then 1 on each loop
            )
            # pour chaque voisin,
            for vois in graph.neighbors(vtx):
                # calcul
                limit = limits[vois]
                # update le score
                eid = graph.get_eid(vtx.index, vois)
                cweight[eid] = lprox.get(vois, 0.) / (limit + lprox.get(vois, 0.))

        # update the weights
        graph.es[EDGE_WEIGHT_ATTR] = cweight
        return graph

