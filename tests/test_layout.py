#-*- coding:utf-8 -*-
import igraph as ig


def test_ByConnectedComponent():
    from cello.layout.simple import KamadaKawaiLayout
    from cello.layout.transform import ByConnectedComponent

    basic_layout = KamadaKawaiLayout(dim=3)
    merge_layout = ByConnectedComponent(basic_layout)
    
    graph = ig.Graph.Formula("a--b--c, d--e")
    layout = merge_layout(graph)
    assert len(layout) == len(graph.vs)
    assert layout.dim == 3
    
    graph = ig.Graph.Formula("a, b, c, d")
    layout = merge_layout(graph)
    assert len(layout) == len(graph.vs)
    assert layout.dim == 3
    
    graph = ig.Graph.Formula("a")
    layout = merge_layout(graph)
    assert len(layout) == len(graph.vs)
    assert layout.dim == 3
