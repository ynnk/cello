#-*- coding:utf-8 -*-

import igraph
import random
from cello.graphs import AbstractGraph, random_vertex

class IgraphGraph( AbstractGraph, igraph.Graph):
    
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

    
    def random_vertex(self, attr=None, from_edges=False):
        """ return a random vertex of the given graph

        :param attr: if not None return the attribute 'attr' of the random vertex, instead of the id (of the random vertex).
        :param from_edges: if True get an edges by random and then pick one of the ends of the edge by random
        
        >>> import random ; random.seed(1) # fix the random seed to test purpose
        >>> g = IgraphGraph.Formula("a--b, a--c, a--d, a--f, d--f")
        >>> random_vertex(g)
        0
        >>> random_vertex(g, attr='name')
        'f'
        >>> random_vertex(g, attr='name')
        'd'
        >>> random_vertex(g, from_edges=True)
        0
        >>> random_vertex(g, attr='name', from_edges=True)
        'd'
        >>> random_vertex(g, attr='name', from_edges=True)
        'a'
        """
        
        if from_edges:
            # random edge
            es = random.choice(self.es)
            vid = random.choice([es.source, es.target])
        else:
            # random node
            vid = random.choice(xrange(self.vcount()))
        # return attr or vid
        if attr is not None:
            return self.vs[vid][attr]
        else:
            return vid
            