#-*- coding:utf-8 -*- 



"""
:mod:`cello.graphs.extraction`
Extraction classes
Should return a v_extract {id: score}

.. currentmodule:: cello.graphs.extraction
    
    Extraction:
    >>> from cello.providers.igraphGraph import IgraphGraph
    >>> g = IgraphGraph.Famous("Zachary")
    >>> markov = ProxMarkovExtraction() | VertexIds()
    >>> mtcl = ProxMonteCarloExtraction() | VertexIds()
    
    >>> markov(g, [], vcount=5, length=3)
    [33, 0, 32, 2, 1]
    
    >>> mtcl(g, [], vcount=3, length=3, throws=10000)
    [33, 0, 32]
"""

from cello.types import Numeric, Text
from cello.pipeline import Optionable
from cello.graphs import prox, IN, OUT, ALL, neighbors

class VertexIds(Optionable):
    def __init__(self, name=None):
        super(VertexIds, self).__init__(name=name)
    
    def __call__(self, vect):
        return [vid for vid, _ in vect]

class ProxExtract(Optionable):
    def __init__(self, prox_func, name=None):
        """ 
        :param prox_func: curryfied function for prox.
            Only graph, pzero, length will be passed a argument to the fuction.
            If One wants to modified the named argument you want passed a lamdba
            with all named arguments set.
            example:
            def prox_func(graph, pzero, length): 
                return prox.prox_markov_dict(graph, pzero, length, mode=OUT, 
                    add_loops=False, weight=None, neighbors=AbstractGraph.neighbors)
        """
        super(ProxExtract, self).__init__(name=name)
        self.add_option("vcount", Numeric(default=10, help="max vertex count"))
        self.add_option("length", Numeric(default=3, help="random walk length"))
        self.prox_func = prox_func
        
    @Optionable.check
    def __call__(self, graph, pzero, vcount=None, length=None):
        v_extract = self.prox_func(graph, pzero, length)
        v_extract = prox.sortcut(v_extract, vcount) # limit 
        return v_extract   
    
class ProxMarkovExtraction(ProxExtract):
    def __init__(self, name=None):
        ProxExtract.__init__(self, prox.prox_markov_dict, name=name )
        
class ProxMonteCarloExtraction(Optionable):
    def __init__(self, name=None, vcount=10, length=3, throws=10):
        Optionable.__init__(self, name=name)
        self.add_option("vcount", Numeric(default=vcount, help="max vertex count"))
        self.add_option("length", Numeric(default=length, help="random walk length"))
        self.add_option("throws", Numeric(default=throws, help="The number of throws in montecarlo process"))

    @Optionable.check
    def __call__(self, graph, pzero, vcount=None, length=None, throws=None  ):
        v_extract = prox.prox_markov_mtcl(graph, pzero, length, throws)
        v_extract = prox.sortcut(v_extract, vcount) # limit 
        return v_extract   


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

