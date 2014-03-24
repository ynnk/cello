#-*- coding:utf-8 -*-
""" :mod:`cello.layout.prox`
=============================

Set of 'prox' graphs layout, moslty based on igraph layouts
"""

import igraph as ig
import cprox

from cello.types import Numeric, Boolean
from cello.pipeline import Optionable, Composable

from cello.layout.transform import ReducePCA, ReduceRandProj, normalise

class ProxLayout(Optionable):
    """ Returns a n*n layout computed with short length random walks
    
    .. Note:: Don't use this component directly, you need to reduce dimention to
        have a usable 2D or 3D layout.
    
    >>> layout = ProxLayout()
    >>> import igraph as ig
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f")
    >>> layout(g)
    <Layout with 5 vertices and 5 dimensions>
    """
    def __init__(self, name="prox_layout"):
        super(ProxLayout, self).__init__(name=name)
        self.add_option("length", Numeric(default=3, min=1, max=50, help="Random walks length"))
        self.add_option("add_loops", Boolean(default=True, help="Wether to add self loop on all vertice"))

    @Optionable.check
    def __call__(self, graph, length=None, add_loops=None):
        coords = [cprox.prox_markov_list_c(graph, [vtx.index], length=length, add_loops=add_loops) \
                        for vtx in graph.vs]
        return ig.Layout(coords)


def ProxLayoutPCA(name="prox_layout_PCA", dim=3):
    """ Std Prox layout
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts

    >>> layout = ProxLayoutPCA(dim=2)
    >>> import igraph as ig
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f")
    >>> layout(g)
    <Layout with 5 vertices and 2 dimensions>
    """
    layout_cpt = ProxLayout() | ReducePCA(dim=dim) | normalise
    layout_cpt.name = name
    return layout_cpt


def ProxLayoutRandomProj(name="prox_layout_PCA", dim=3):
    """ Prox layout with a random projection to reduce dimentions
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts
    
    
    >>> layout = ProxLayoutRandomProj(dim=3)
    >>> import igraph as ig
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f")
    >>> layout(g)
    <Layout with 5 vertices and 3 dimensions>
    """
    layout_cpt = ProxLayout() | ReduceRandProj(dim=dim) | normalise
    #TODO: on ajoute un truc du genre:
    #layout_cpt |= maybe(Shaker(), default=True, help="'Shake' the layout to ensure no overlaping vertices")
    layout_cpt.name = name
    return layout_cpt


class ProxBigraphLayout(Optionable):
    """ Returns a n*n layout computed with short length random walks
    
    .. Note:: Don't use this component directly, you need to reduce dimention to
        have a usable 2D or 3D layout. See: :class:`ProxBigraphLayoutPCA` or 
        :class:`ProxBigraphLayoutRandomProj`.
    
    >>> import igraph as ig
    >>> g = ig.Graph.Formula("A--a, A--b, A--c, B--b, B--f")
    >>> g.vs['type'] = [vtx['name'].isupper() for vtx in g.vs]
    
    >>> layout = ProxBigraphLayout()
    >>> layout(g, length=1)
    <Layout with 6 vertices and 6 dimensions>
    """
    def __init__(self, name='prox_bigraph_layout'):
        super(ProxBigraphLayout, self).__init__(name=name)
        self.add_option("length", Numeric(default=3, min=1, max=50, help="Random walks length"))

    @Optionable.check
    def __call__(self, graph, length=None, add_loops=None):
        assert "type" in graph.vs.attributes()

        coords = []
        for vtx in graph.vs:
            v_length = length - (length % 2) if vtx["type"] else length - ( length % 2 ) + 1
            pline = cprox.prox_markov_list_c(graph, [vtx.index], length=v_length, add_loops=False)
            coords.append(pline)
        return ig.Layout(coords)


def ProxBigraphLayoutPCA(name="prox_bigraph_layout_PCA", dim=3):
    """ Std Prox layout for bipartite graphs
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts

    >>> import igraph as ig
    >>> g = ig.Graph.Formula("A--a, A--b, A--c, B--b, B--f")
    >>> g.vs['type'] = [vtx['name'].isupper() for vtx in g.vs]

    >>> layout = ProxBigraphLayoutPCA(dim=3)
    >>> layout(g)
    <Layout with 6 vertices and 3 dimensions>
    """
    layout_cpt = ProxBigraphLayout() | ReducePCA(dim=dim) | normalise
    layout_cpt.name = name
    return layout_cpt


def ProxBigraphLayoutRandomProj(name="prox_layout_PCA", dim=3):
    """ Prox layout with a random projection to reduce dimentions
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts
    
    >>> import igraph as ig
    >>> g = ig.Graph.Formula("A--a, A--b, A--c, B--b, B--f")
    >>> g.vs['type'] = [vtx['name'].isupper() for vtx in g.vs]

    >>> layout = ProxBigraphLayoutRandomProj(dim=2)
    >>> layout(g)
    <Layout with 6 vertices and 2 dimensions>
    """
    layout_cpt = ProxLayout() | ReduceRandProj(dim=dim) | normalise
    #TODO: on ajoute un truc du genre:
    #layout_cpt |= maybe(Shaker(), default=True, help="'Shake' the layout to ensure no overlaping vertices")
    layout_cpt.name = name
    return layout_cpt


class ProxGlobalLayout(ProxLayout):
    """ Prox Layout on the 'global' graph
    
    .. Warning:: THIS SHOULD BE UPDATED !
    """
    def __init__(self, global_graph, name='prox_layout_global'):
        raise NotImplementedError("this should be updated...")
        super(ProxGlobalLayout, self).__init__(name=name)
        self.global_graph = global_graph

    def __call__(self, subgraph, shake=False, **kwargs):
        """Compute a n-dimention layout for the given subgraph according to the
        result of random walks in the given graph.
        """
        raise NotImplementedError("this should be updated...")
        neighbors_fct = lambda g, vid: ( [vid] if True else [] ) + g.neighbors(vid)
        coords = []

        assert "kgraph_id" in subgraph.vertex_attributes(), "There is no global vertex id on subgraph vertices."
        # sur le "kgraph" seulement ie le global
        pzlist = subgraph.vs["kgraph_id"]
        graph = self._kgraph.graph

        for gid in pzlist:
            pline = self.prox_func(graph, [gid], neighbors_fct, **kwargs )
            coords.append([pline.get(to_gid, .0) for to_gid in pzlist])

        return coords

