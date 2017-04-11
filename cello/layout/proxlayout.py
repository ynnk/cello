#-*- coding:utf-8 -*-
""" :mod:`cello.layout.proxlayout`
==================================

Set of 'prox' graphs layout, moslty based on igraph layouts
"""

import igraph as ig

from reliure import Optionable, Composable
from reliure.types import Numeric, Boolean

from cello.graphs import prox
from cello.graphs import EDGE_WEIGHT_ATTR
from cello.layout.transform import ReducePCA, ReduceRandProj, ReduceMDS, normalise


class ProxLayout(Optionable):
    """ Returns a n*n layout computed with short length random walks
    
    .. Note:: Don't use this component directly, you need to reduce dimention to
        have a usable 2D or 3D layout.
    
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f")
    >>> layout = ProxLayout()
    >>> layout(g)
    <Layout with 5 vertices and 5 dimensions>
    
    >>> import cello.graphs
    >>> g.es[cello.graphs.EDGE_WEIGHT_ATTR] = [10, 10, 1, 1]
    >>> layout_wgt = ProxLayout(weighted=True)
    >>> layout_wgt(g)
    <Layout with 5 vertices and 5 dimensions>
    """
    def __init__(self, name="prox_layout", weighted=False):
        """
        :param weighted: whether to use the weight of the graph, is True the edge
            attribute `cello.graphs.EDGE_WEIGHT_ATTR` is used.
        :type weighted: boolean
        """
        super(ProxLayout, self).__init__(name=name)
        self.add_option("length", Numeric(default=3, min=1, max=50, help="Random walks length"))
        self.add_option("add_loops", Boolean(default=True, help="Wether to add self loop on all vertices"))
        self.weighted = weighted

    @Optionable.check
    def __call__(self, graph, length=None, add_loops=None):
        weight = None
        if self.weighted:
            weight = EDGE_WEIGHT_ATTR
        #TODO: manage loops weight !
        coords = [prox.prox_markov_list(graph, [vtx.index], weight=weight, length=length, add_loops=add_loops) \
                        for vtx in graph.vs]
        return ig.Layout(coords, dim=len(coords))


def ProxLayoutPCA(name="ProxLayoutPCA", dim=3, weighted=False):
    """ Std Prox layout
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts
    :param weighted: whether to use the weight of the graph, is True the edge
        attribute `cello.graphs.EDGE_WEIGHT_ATTR` is used.

    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f")
    >>> layout = ProxLayoutPCA(dim=2)
    >>> layout.name
    'ProxLayoutPCA'
    >>> layout(g)
    <Layout with 5 vertices and 2 dimensions>
    """
    layout_cpt = ProxLayout(name=name, weighted=weighted) | ReducePCA(dim=dim) | normalise
    layout_cpt.name = name
    return layout_cpt


def ProxLayoutRandomProj(name="ProxLayoutRandomProj", dim=3):
    """ Prox layout with a random projection to reduce dimentions
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts
    
    
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f")
    >>> layout = ProxLayoutRandomProj(dim=3)
    >>> layout.name
    'ProxLayoutRandomProj'
    >>> layout(g)
    <Layout with 5 vertices and 3 dimensions>
    """
    layout_cpt = ProxLayout() | ReduceRandProj(dim=dim) | normalise
    layout_cpt.name = name
    return layout_cpt



def ProxLayoutMDS(name="ProxLayoutMDS", dim=3, weighted=False):
    """ Std Prox layout
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts
    :param weighted: whether to use the weight of the graph, is True the edge
        attribute `cello.graphs.EDGE_WEIGHT_ATTR` is used.
    """
    layout_cpt = ProxLayout(name=name, weighted=weighted) | ReduceMDS(dim=dim) | normalise
    layout_cpt.name = name
    return layout_cpt

class ProxBigraphLayout(Optionable):
    """ Returns a n*n layout computed with short length random walks
    
    .. Note:: Don't use this component directly, you need to reduce dimention to
        have a usable 2D or 3D layout. See: :class:`ProxBigraphLayoutPCA` or 
        :class:`ProxBigraphLayoutRandomProj`.
    
    >>> g = ig.Graph.Formula("A--a, A--b, A--c, B--b, B--f")
    >>> g.vs['type'] = [vtx['name'].isupper() for vtx in g.vs]
    
    >>> layout = ProxBigraphLayout()
    >>> layout(g, length=1)
    <Layout with 6 vertices and 6 dimensions>

    Works also with weighted graph:

    >>> import cello.graphs
    >>> g.es[cello.graphs.EDGE_WEIGHT_ATTR] = [10, 10, 1, 1, 10]
    >>> layout_wgt = ProxBigraphLayout(weighted=True)
    >>> layout_wgt(g)
    <Layout with 6 vertices and 6 dimensions>
    """
    def __init__(self, name=None, weighted=False):
        """
        :param weighted: whether to use the weight of the graph, is True the edge
            attribute `cello.graphs.EDGE_WEIGHT_ATTR` is used.
        :type weighted: boolean
        """
        super(ProxBigraphLayout, self).__init__(name=name)
        self.add_option("length", Numeric(default=3, min=1, max=50, help="Random walks length"))
        self.weighted = weighted

    @Optionable.check
    def __call__(self, graph, length=None, add_loops=None):
        assert "type" in graph.vs.attributes()
        weight = None
        if self.weighted:
            weight = EDGE_WEIGHT_ATTR

        coords = []
        for vtx in graph.vs:
            v_length = length - (length % 2) if vtx["type"] else length - ( length % 2 ) + 1
            pline = prox.prox_markov_list(graph, [vtx.index], length=v_length, add_loops=False, weight=weight)
            coords.append(pline)
        return ig.Layout(coords)


def ProxMDSSugiyamaLayout(name="ProxMDSSugiyama", dim=3, weighted=False):
    """
    layout for graph with partial order, combine Sugiyama for Z and ProxMDS for (x,y)
    """
    
    @Composable
    def computeLayout(graph):
        ranks = [x[1] for x in graph.layout_sugiyama()[:len(graph.vs)]]
        prox_coords = ProxLayoutMDS(dim=dim-1)(graph)
        return ig.Layout([ prox_coords[i] + [rank] for i, rank in enumerate(ranks)], dim=dim)

    computeLayout.name = name
    return computeLayout


def ProxBigraphLayoutPCA(name="ProxBigraphLayoutPCA", dim=3, weighted=False):
    """ Std Prox layout for bipartite graphs
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts
    :param weighted: whether to use the weight of the graph, is True the edge
        attribute `cello.graphs.EDGE_WEIGHT_ATTR` is used.

    >>> g = ig.Graph.Formula("A--a, A--b, A--c, B--b, B--f")
    >>> g.vs['type'] = [vtx['name'].isupper() for vtx in g.vs]

    >>> layout = ProxBigraphLayoutPCA(dim=3)
    >>> layout(g)
    <Layout with 6 vertices and 3 dimensions>
    """
    layout_cpt = ProxBigraphLayout(weighted=weighted) | ReducePCA(dim=dim) | normalise
    layout_cpt.name = name
    return layout_cpt


def ProxBigraphLayoutRandomProj(name="ProxLayoutBigraphPCA", dim=3):
    """ Prox layout with a random projection to reduce dimentions
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts
    
    >>> g = ig.Graph.Formula("A--a, A--b, A--c, B--b, B--f")
    >>> g.vs['type'] = [vtx['name'].isupper() for vtx in g.vs]

    >>> layout = ProxBigraphLayoutRandomProj(dim=2)
    >>> layout(g)
    <Layout with 6 vertices and 2 dimensions>
    """
    layout_cpt = ProxBigraphLayout() | ReduceRandProj(dim=dim) | normalise
    layout_cpt.name = name
    return layout_cpt


class ProxGlobalLayout(ProxLayout):
    """ Prox Layout on the 'global' graph
    
    .. Warning:: THIS SHOULD BE UPDATED !
    """
    def __init__(self, global_graph, name='ProxGlobalLayout'):
        raise NotImplementedError("this should be updated...")
        super(ProxGlobalLayout, self).__init__(name=name)
        self.global_graph = global_graph

    def __call__(self, subgraph, **kwargs):
        """Compute a n-dimension layout for the given subgraph according to the
        result of random walks in the given graph.
        """
        raise NotImplementedError("this should be updated...")
        neighbors_fct = lambda g, vid: ( [vid] if True else [] ) + g.neighbors(vid)
        coords = []

        assert "kgraph_id" in subgraph.vertex_attributes(), "There is no global vertex id on subgraph vertices."
        # sur le "kgraph" seulement ie le global
        pzlist = subgraph.vs["kgraph_id"]
        graph = self.global_graph

        for gid in pzlist:
            pline = self.prox_func(graph, [gid], neighbors_fct, **kwargs )
            coords.append([pline.get(to_gid, .0) for to_gid in pzlist])

        return coords

