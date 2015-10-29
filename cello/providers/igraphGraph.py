#-*- coding:utf-8 -*-
""" :mod:`cello.providers.igraphGraph`
=====================================
"""
from builtins import range

import igraph
import random
from cello.graphs import AbstractGraph, random_vertex

class IgraphGraph(AbstractGraph, igraph.Graph):

    def __init__(self, *args, **kwargs ):
        AbstractGraph.__init__( self, *args, **kwargs)
        igraph.Graph.__init__( self, *args, **kwargs)

    @classmethod
    def Read(cls, *args, **kwargs):
        g = igraph.read(*args, **kwargs)
        cls.convert_from_igraph(g)
        return g

    @classmethod
    def convert_from_igraph(cls, obj):
        obj.__class__ = cls

    #Note: for ramdom seed for py3 see http://stackoverflow.com/questions/11929701/why-is-seeding-the-random-generator-not-stable-between-versions-of-python/11929775#11929775
    # however it is not enought and random.choice behave differently in PY2 and 3
    def random_vertex(self, attr=None, from_edges=False):
        """ return a random vertex of the given graph

        :param attr: if not None return the attribute 'attr' of the random vertex, instead of the id (of the random vertex).
        :param from_edges: if True get an edges by random and then pick one of the ends of the edge by random
        
        :hide:
            >>> # set the random seed to test purpose
            >>> import random, six
            >>> if six.PY3: random.seed(2, version=1)
            >>> if six.PY2: random.seed(1)

        >>> g = IgraphGraph.Formula("a--b, a--c, a--d, a--f, d--f")
        >>> random_vertex(g) in range(g.vcount())
        True
        >>> random_vertex(g, attr='name') in g.vs["name"]
        True
        >>> random_vertex(g, attr='name') in g.vs["name"]
        True
        >>> random_vertex(g, from_edges=True) in range(g.vcount())
        True
        >>> random_vertex(g, attr='name', from_edges=True) in g.vs["name"]
        True
        >>> random_vertex(g, attr='name', from_edges=True) in g.vs["name"]
        True
        """
        if from_edges:
            # random edge
            es = random.choice(self.es)
            vid = random.choice([es.source, es.target])
        else:
            # random node
            vid = random.choice(range(self.vcount()))
        # return attr or vid
        if attr is not None:
            return self.vs[vid][attr]
        else:
            return vid
            
