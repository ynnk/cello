#-*- coding:utf-8 -*-
""" :mod:`cello.graphs.prox`
===========================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

.. currentmodule:: cello.graphs.prox

Python version of Prox over igraph.

Here is a minimal exemple:

>>> import igraph as ig 
>>> graph = ig.Graph.Formula("a-b-c-d")   #TODO: avoir un minigraph a nous non depédendant de igraph
>>> prox_markov_dict(graph, [0], 2)
{0: 0.5, 2: 0.5}

On can also use a dict for `p0`:

>>> prox_markov_dict(graph, {0:1, 3:1}, 0)  # p0 is just normalized
{0: 0.5, 3: 0.5}
>>> prox_markov_dict(graph, {0:1, 3:1}, 1)
{1: 0.5, 2: 0.5}
>>> prox_markov_list(graph, {0:1, 3:1}, 1)
[0.0, 0.5, 0.5, 0.0]
>>> res = prox_markov_mtcl(graph, [0, 3], 1, 10)

Zachary :

>>> g = ig.Graph.Famous("Zachary")
>>> p4 = prox_markov_dict(g, [0], 4)
>>> len(p4)
34
>>> p4[0]
0.20139916513480394
>>> p4[2]
0.06625652318218955

"""
from random import randint
import numpy as np

import cello
from cello.graphs import IN, OUT, ALL


def normalise(p0):
    """ normalise p0 dict vector 
    
    >>> p0 = {0:1, 3:1}
    >>> normalise(p0)
    {0: 0.5, 3: 0.5}
    """
    vsum = 1.* np.sum(abs(val) for val in p0.itervalues())
    return {vid: val/vsum for vid, val in p0.iteritems()}


def sortcut(v_extract, vcount):
    """ Gets the first vcount vertex sorted by score from the list or dict of score

    >>> sortcut({45:0.2, 180:0.08, 20:0.12, 21:0.102, 255:0.85, 12:0.0021}, 3) 
    [(255, 0.85), (45, 0.2), (20, 0.12)]
    >>> sortcut([0.02, 0.12, 0.82, 0.001, 0.18], 3)
    [(2, 0.82), (4, 0.18), (1, 0.12)]


    :param v_extract: dict vertex_ids, value or list of values
    :param vcount: vertex count
    :return: a list of the form: [(vid1, score), (vid2, score), ...]
    """
    if type(v_extract) is list:
        v_extract = { i: v for i, v in enumerate(v_extract) }
    v_extract = v_extract.items() #  sparce prox_vect : [(id, prox_value)]
    v_extract.sort(key=lambda x: x[1], reverse=True) # sorting by prox.prox_markov
    v_extract = v_extract[:vcount]
    
    return v_extract


def spreading(graph, in_vect, mode, add_loops):
    """ Basic function: spread value of in_vect throw the graph g. 
    
    >>> graph = ig.Graph.Formula("a--b--c")
    >>> spreading(graph, {1:1}, mode=OUT, add_loops=True)
    
    
    :param graph: graph in igraph format
    :param in_vect: input vector, a python dictionary : {vertex_id:value, ...}
    :param mode: given to neighboors, consider OUT links, IN links our ALL for both
    :param add_loops: if True do as if every vertex hold a self loop
                     (force the graph to be reflexif)
    :param neighbors: function that override std graph.neighbors fct
        For `neighbors_fct` you can use :
        > neighbors_fct = lambda g, from_vertex : g.neighbors(from_vertex)
        > neighbors_fct = ig.Graph.neighbors
    :returns: output vector same format as in_vect.
    """
    vect = {}
    for vtx, value in in_vect.iteritems():
        neighborhood = graph.neighbors(vtx)
        if add_loops and not vtx in neighborhood:
            neighborhood.append(vtx)
        if len(neighborhood) > 0:
            pvalue = 1. * value / len(neighborhood)
            for neighbor in neighborhood:
                vect[neighbor] = vect.get(neighbor, 0.) + pvalue
    return vect


def spreading_wgt(g, in_vect, wgt=lambda i: 1., epsi=0, false_refl=False):
    """ Basic function : spread value of in_vect throw the graph g. (weighted version)
    
    :param g: graph in igraph format
    :param in_vect: input vector, a python dictionary : {vertex_id:value, ...}   
    :param weight: either str then the corresponding edge attribute is use as weight, or a list of weight (`|weight| == g.ecount()`)
    :param false_refl: if True do as if every vertex hold a self loop (reflexif graph)

    :returns: output vector same format as in_vect.
    """
    out_vect = {}
    for from_vertex, value in in_vect.iteritems():
        if value <= epsi : continue
        neighborhood = g.neighbors(from_vertex)
        if false_refl: neighborhood.append(from_vertex)
        wgts = [wgt(from_vertex, v) for v in neighborhood]
        tot = 1. * sum(wgts)
        if tot > 0:
            for i, neighbor in enumerate(neighborhood):
                out_vect[neighbor] = out_vect.get(neighbor, 0.) + value * wgts[i] / tot
    return out_vect

def vect_pzero(graph, p0):
    """ returns a normalised a p0 dict.

    :param p0: `dict` {vid:weight} or `list` [vid, vid, ... ] weight is then 1.
    """
    if isinstance(p0, dict):
        vect = normalise(p0)
    else : 
        if len(p0) == 0:
            p0 = range(graph.vcount()) # graph global
        vect = normalise({k:1.  for k in p0})
    return vect


def prox_markov_dict(graph, p0, length, mode=OUT, add_loops=False, weight=None,
                        neighbors=cello.graphs.neighbors):
    """ Generic prox implementation

    For `p0` : it is either a list of vertex idx or a dict of vertex associated 
    with starting weight.
    If it is a list of vertex idx (`[id_vertex1, id_vertex2, ...]`) then the walk 
    starts with equal probability on each of theses vertices.
    If it is a dict (`{id_vertex1:0.2, id_vertex2:0.5, ...}`) the the walk starts 
    on of theses vertices with a propability proportional to the associated score.
    
    :param graph: subclass of :class:`.AbstractGraph`
    :param p0: list of starting nodes (see above)
    :param length: random walk length
    :param _others_: see :func:`spreading`
    
    :returns: result vector, a python dictionary : `{vertex_id:value, ...}`
    """
    if weight is not None:  #FIXME
        raise NotImplementedError
    #FIXME: neighbors should be None by default
    #TODO: ajout du choix de la fct de `spreading` en param (il faut bien normalisé l'interface de spreading)
    vect = vect_pzero(graph, p0)
    for k in xrange(length):
        vect = spreading(graph, vect, mode, add_loops, weight, neighbors)
    return vect


def prox_markov_list(graph, p0, length, mode=OUT, add_loops=False, weight=None,
                        neighbors=cello.graphs.neighbors):
    vect = prox_markov_dict(graph, p0, length, mode, add_loops, weight, neighbors)
    return [vect.get(vidx, 0.) for vidx in xrange(graph.vcount())]


def prox_markov_mtcl(graph, p0, length, throws, mode=OUT, add_loops=False,
                        weight=None, neighbors=cello.graphs.neighbors):
    """ Prox 'classic' by an approximate method montecarlo with nb_throw throws

    :param g: graph in igraph format
    :param p0: list of starting nodes : [id_vertex1, id_vertex2, ...]
    :parma l: random walk length
    :param nb_throw: the number of throws in montecarlo process
    :param false_relf: if True do as if every vertex hold a self loop (reflexif graph)
    
    :returns: prox_vect, died: prox_vect is a python dictionary : {vertex_id:value, ...} AND died is the probability of dying during the random walks (the walker die when he has to do a step starting from a vertex without neighbors)
    """ 
    prox_vect = {} # le vecteur de proxemie approchée par montecarlo
    died = 0 # proba de mourir : on meurt qd on doit faire un pas a partir d'un sommet sans voisins
    #p0 = normalise(p0)
    
    if weight is not None:  #FIXME
        raise NotImplementedError
    for throw in xrange(throws) :
        neighborhood = vect_pzero(graph, p0).keys() # FIXME not weighted
        for j in xrange(length) :
            len_n = len(neighborhood)
            if len_n  > 0 :
                vtx = neighborhood[randint(0, len_n-1)]
                neighborhood = neighbors(graph, vtx, mode)
                if add_loops and not vtx in neighborhood:
                    neighborhood.append(vtx)
        
        len_n = len(neighborhood)
        if len_n > 0 :
            vtx = neighborhood[randint(0, len_n -1)]
            if prox_vect.has_key(vtx):
                prox_vect[vtx] = prox_vect[vtx] + 1
            else :
                prox_vect[vtx] = 1
        else :
            died = died+1
    if died != 0:
        died = 1. * died/throws
    for k in prox_vect.keys():
        prox_vect[k] = 1. * prox_vect[k] / throws
    return prox_vect #, died


################################################################################
# Prow weighted 




def prox_markov_wgt(g, p0, l=3, wgt=None, epsi=0, false_refl=False):
    """ Prox 'classic'
        
    :param g: graph in igraph format
    :param p0: list of starting nodes : [id_vertex1, id_vertex2, ...]
    :param l: random walk length
    :param wgt: weighting fuction, given a edge id return the weight of the edge 
    :param false_refl: if True do as if every vertex hold a self loop (reflexif graph)

    :returns: result vector, a python dictionary : {vertex_id:value, ...}
    """
    
    v0 = 1./len(p0)
    prox_vect = dict((id, v0) for id in p0)

    if not wgt: _spreading = lambda vect : spreading(g, vect, epsi, false_refl)
    else: _spreading = lambda vect : spreading_wgt(g, vect, wgt, epsi, false_refl)

    for k in range(l):
        prox_vect = _spreading(prox_vect)
    return prox_vect


def confluence(graph, vtxa, vtxb, length=3, add_loops=True, remove_edge=False, 
            prox_markov_list=prox_markov_list, neighbors=cello.graphs.neighbors):
    """ Compute the confluence
    use prox_markov_list_c
    
    :param remove_edge: wheter to remove edge before computing similarity of an edge.
    """
    assert not graph.is_directed()
    
    # FIXME 
    
    if remove_edge:
        raise NotImplementedError
    if not add_loops:
        raise NotImplementedError
        
    # default MODE is OUT
    # neighbors is not used 
    
    sim = prox_markov_list(graph, [vtxa], length=length, add_loops=add_loops)[vtxb]
    degree = np.array(graph.degree(), dtype=float) + 1.
    lsum = degree.sum()
    limit = (graph.degree(vtxb) + 1.) / lsum
    sim_init = sim
    sim /= (sim + limit)
    assert sim<=1., "cfl: %1.3f prox: %1.4f  limit=%1.5f  lsum: %1.6f" % (sim, sim_init, limit, lsum)
    return sim


def confluence_simple(g, p0, length=3 , method=prox_markov_dict, neighbors=cello.graphs.neighbors):
    pm = method(g, p0, length=length, neighbors=neighbors )
    conf =  { k: 1.*v / (v+(1.*len(neighbors(g,k))/(2*g.ecount()))) for k,v in pm.iteritems()}
    return conf 

