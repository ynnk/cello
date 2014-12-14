#-*- coding:utf-8 -*-
""" :mod:`cello.layout.simple`
=============================

Set of basic graphs layout, moslty based on igraph layouts
"""

import igraph as ig

from cello.types import Numeric, Boolean
from cello.pipeline import Optionable, Composable
from cello.layout.transform import normalise

class KamadaKawaiLayout(Composable):
    """ Kamada Kawai layout
    
    >>> g = ig.Graph.Formula("a--b, a--c, a--d")
    >>> layout = KamadaKawaiLayout(dim=2)
    >>> layout(g)
    <Layout with 4 vertices and 2 dimensions>
    """
    def __init__(self, name="kamada_kawai", dim=3):
        """ Build the layout component
        
        :param name: mane of the component
        :param dim: the number of dimention of the output layouts (2 or 3)
        """
        super(KamadaKawaiLayout, self).__init__(name=name)
        assert dim == 2 or dim == 3
        self.dimensions = dim

    def __call__(self, graph):
        return normalise(graph.layout_kamada_kawai(dim=self.dimensions))

class FruchtermanReingoldLayout(Composable):
    """ Fruchterman Reingold layout
    
    >>> g = ig.Graph.Formula("a--b, a--c, a--d")
    >>> layout = FruchtermanReingoldLayout(dim=3)
    >>> layout(g)
    <Layout with 4 vertices and 3 dimensions>
    """
    def __init__(self, name="fruchterman_reingold", dim=3):
        """ Build the layout component
        
        :param name: mane of the component
        :param dim: the number of dimention of the output layouts (2 or 3)
        """
        super(FruchtermanReingoldLayout, self).__init__(name=name)
        assert dim == 2 or dim == 3
        self.dimensions = dim

    def __call__(self, graph):
        return graph.layout_fruchterman_reingold(dim=self.dimensions)


class RandomLayout(Composable):
    """ Random layout
    
    >>> g = ig.Graph.Formula("a--b, a--c, a--d")
    >>> layout = RandomLayout(dim=2)
    >>> layout(g)
    <Layout with 4 vertices and 2 dimensions>
    """
    def __init__(self, name="random_layout", dim=3):
        """ Build the layout component
        
        :param name: mane of the component
        :param dim: the number of dimention of the output layouts (2 or 3)
        """
        super(RandomLayout, self).__init__(name=name)
        assert dim == 2 or dim == 3
        self.dimensions = dim

    def __call__(self, graph):
        return graph.layout_random(dim=self.dimensions)


class GridLayout(Optionable):
    """ Grid layout
    
    >>> g = ig.Graph.Formula("a--b, a--c, a--d")
    >>> layout = GridLayout()
    >>> layout(g, 1, 2)
    <Layout with 4 vertices and 3 dimensions>
    """
    def __init__(self, name="grid_layout", dim=3):
        """ Build the layout component
        
        :param name: mane of the component
        :param dim: the number of dimention of the output layouts (2 or 3)
        """
        super(GridLayout, self).__init__(name=name)
        self.add_option("width", Numeric(default=0,
            help="""Number of vertices in a single row of the layout.
            Zero means that the height should be determined automatically."""))
        self.add_option("height", Numeric(default=0,
            help="""Number of vertices in a single column of the layout.
            Zero means that the height should be determined automatically."""))
        assert dim == 2 or dim == 3
        self.dimensions = dim

    def __call__(self, graph, width=0, height=0):
        return graph.layout_grid(width=width, height=height, dim=self.dimensions)

