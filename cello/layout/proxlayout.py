#-*- coding:utf-8 -*-
""" :mod:`cello.layout.proxlayout`
==================================

Set of 'prox' graphs layout, moslty based on igraph layouts
"""

import igraph as ig

from cello.types import Numeric, Boolean
from cello.pipeline import Optionable, Composable

from cello.graphs import prox
from cello.layout.transform import ReducePCA, ReduceRandProj, normalise

class ProxLayout(Optionable):
    """ Returns a n*n layout computed with short length random walks
    
    .. Note:: Don't use this component directly, you need to reduce dimention to
        have a usable 2D or 3D layout.
    
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f")
    >>> layout = ProxLayout()
    >>> layout(g)
    <Layout with 5 vertices and 5 dimensions>
    """
    def __init__(self, name="prox_layout"):
        super(ProxLayout, self).__init__(name=name)
        self.add_option("length", Numeric(default=3, min=1, max=50, help="Random walks length"))
        self.add_option("add_loops", Boolean(default=True, help="Wether to add self loop on all vertices"))

    @Optionable.check
    def __call__(self, graph, length=None, add_loops=None):
        coords = [prox.prox_markov_list(graph, [vtx.index], length=length, add_loops=add_loops) \
                        for vtx in graph.vs]
        return ig.Layout(coords)


def ProxLayoutPCA(name="prox_layout_PCA", dim=3):
    """ Std Prox layout
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts

    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f")
    >>> layout = ProxLayoutPCA(dim=2)
    >>> layout(g)
    <Layout with 5 vertices and 2 dimensions>
    """
    layout_cpt = ProxLayout() | ReducePCA(dim=dim) | normalise
    layout_cpt.name = name
    return layout_cpt


def ProxLayoutRandomProj(name="prox_layout_Random_Proj", dim=3):
    """ Prox layout with a random projection to reduce dimentions
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts
    
    
    >>> g = ig.Graph.Formula("a--b, a--c, a--d, a--f")
    >>> layout = ProxLayoutRandomProj(dim=3)
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
            pline = prox.prox_markov_list(graph, [vtx.index], length=v_length, add_loops=False)
            coords.append(pline)
        return ig.Layout(coords)


def ProxBigraphLayoutPCA(name="prox_bigraph_layout_PCA", dim=3):
    """ Std Prox layout for bipartite graphs
    
    :param name: name of the component
    :param dim: number of dimentions of the output layouts

    >>> g = ig.Graph.Formula("A--a, A--b, A--c, B--b, B--f")
    >>> g.vs['type'] = [vtx['name'].isupper() for vtx in g.vs]

    >>> layout = ProxBigraphLayoutPCA(dim=3)
    >>> layout(g)
    <Layout with 6 vertices and 3 dimensions>
    """
    layout_cpt = ProxBigraphLayout() | ReducePCA(dim=dim) | normalise
    layout_cpt.name = name
    return layout_cpt


def ProxBigraphLayoutRandomProj(name="prox_layout_bigraph_PCA", dim=3):
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


def layout_bipartite(subgraph, graph, l, neighbors_fct=None):
    """Compute a n-dimention layout for the given bipartite subgraph according
    to the result of random walks in the given graph (also bipartite).
    
    TODO
    """
    assert "globalIndex" in subgraph.vertex_attributes()
    assert "type" in subgraph.vertex_attributes()
    
    if neighbors_fct is None:
        neighbors_fct = lambda g, vid: g.neighbors(vid)
    
    global_idx = subgraph.vs["globalIndex"]
    pzlist = [gid  if graph.vs[gid]["type"] else -1 for gid in global_idx]
    
    layout = []
    for vid, gid in enumerate(global_idx):
        length = l - (l%2) if graph.vs[gid]["type"] else l - (l%2) + 1
        pline = prox.prox_markov_dict(graph, [gid], l=length,  neighbors_fct=neighbors_fct)
        layout.append([pline.get(to_gid, .0) for to_gid in pzlist])
        
    return layout


