#-*- coding:utf-8 -*-
""" :mod:`cello.utils.prox`
===========================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

Python version of Prox over igraph :

>>> import igraph as ig
>>> g = ig.Graph.Famous("Zachary")
>>> p4 = prox_markov(g, [0], l=4)
>>> len(p4)
34
>>> p4[0]
0.20139916513480394
>>> p4[2]
0.06625652318218955

.. currentmodule:: cello.utils.prox

.. autosummary::
    prox_markov
    
"""
from random import randint

import igraph as ig

#{ Prox on graph in igraph object
def spreading(g, in_vect, neighbors_fct):
    """ spread value of in_vect throw the graph g.
    
    
    :param g: graph in igraph format
    :param in_vect: input vector, a python dictionary : {vertex_id:value, ...}
    :param neighbors_func: a function to retrieve nodes neighbors list
    
    :returns: output vector same format as in_vect.
    """
    out_vect = {}
    for from_vertex, value in in_vect.iteritems():
        neighborhood = neighbors_fct(g, from_vertex)
        if len(neighborhood) > 0:
            a = 1. * value / len(neighborhood) 
            for neighbor in neighborhood:
                out_vect[neighbor] = out_vect.get(neighbor, 0.) + a
    return out_vect


def prox_markov(g, p0, neighbors_fct=ig.Graph.neighbors, l=3):
    """ Prox 'classic'
    
    For `neighbors_fct` you can use :
    
    >>> neighbors_fct = lambda g, from_vertex : g.neighbors(from_vertex)
    >>> neighbors_fct = ig.Graph.neighbors
    
    :param g: graph in igraph format
    :param p0: list of starting nodes: [id_vertex1, id_vertex2, ...] or dict of starting node {(id, weight) , ... }. Giving a list as pzero will set initial vector to v0 = 1./len(p0).
    :param neighbors_func: a function to retrieve nodes neighbors list takes a graph and from_vertex as arguments 
    
    :param l: random walk length
    
    :returns: result vector, a python dictionary : {vertex_id:value, ...}
    """
    
    if isinstance(p0, dict):
        assert sum(p0.itervalues()) -1 < 1e-5, "Your initial vector is not normalized"
        prox_vect = p0
    else : 
        v0 = 1./len(p0)
        prox_vect = dict((id, v0) for id in p0)
    
    for k in range(l):
        prox_vect = spreading(g, prox_vect, neighbors_fct)
    return prox_vect

def prox_markov_mtcl(g, p0, neighbors_fct = ig.Graph.neighbors, l=3, nb_throw=10):
    """ Prox 'classic' by an approximate method montecarlo with nb_throw throws

    :param g: graph in igraph format
    :param p0: list of starting nodes : [id_vertex1, id_vertex2, ...]
    :parma l: random walk length
    :param nb_throw: the number of throws in montecarlo process
    :param false_relf: if True do as if every vertex hold a self loop (reflexif graph)
    
    :returns: prox_vect, died: prox_vect is a python dictionary : {vertex_id:value, ...} AND died is the probability of dying during the random walks (the walker die when he has to do a step starting from a vertex without neighbors)
    """ 
    prox_vect={} # le vecteur de proxemie approchée part montecarlo
    died=0 # proba de mourir : on meurt qd on doit faire un pas a partir d'un sommet sans voisins

    for throw in range(nb_throw) :
        neighborhood = p0
        for j in range(l) :
            if len(neighborhood) > 0 :
                s = neighborhood[randint(0, len(neighborhood)-1)]
                neighborhood = neighbors_fct(g,s)
        if len(neighborhood) > 0 :
            s = neighborhood[randint(0, len(neighborhood)-1)]
            if prox_vect.has_key(s):
                prox_vect[s] = prox_vect[s] +1
            else :
                prox_vect[s] = 1
        else :
            died = died+1
    if died != 0:
        died = 1. * died/nb_throw
    for k in prox_vect.keys():
        prox_vect[k] = 1. * prox_vect[k] / nb_throw
    return prox_vect #, died


################################################################################
# Prow weighted 


def spreading_wgt(g, in_vect, wgt=lambda i: 1., epsi=0, false_refl=False):
    """ Basic function : spread value of in_vect throw the graph g. (weighted version)
    
    :param g: graph in igraph format
    :param in_vect: input vector, a python dictionary : {vertex_id:value, ...}   
    :param wgt: weighting fuction, given a edge id return the weight of the edge 
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


def prox_markov_wgt(g, p0, length=3, wgt=None, epsi=0, false_refl=False):
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

    for k in range(length):
        prox_vect = _spreading(prox_vect)
    return prox_vect


def confluence(g, p0, neighbors_fct = ig.Graph.neighbors, l=3 , method=prox_markov):
    pm = method(g, p0, neighbors_fct = neighbors_fct, l=l )
    conf =  { k: 1.*v / (v+(1.*len(neighbors_fct(g,k))/(2*g.ecount()))) for k,v in pm.iteritems()}
    #~ print conf
    return conf 


################################################################################

def sortcut( v_extract, nnodes ):
    """ Return the neighborhood of a list of vertices by using prox.

    :param pzero: list of starting vertices (ids)
    :param l: length of the random walk use to compute the neighborhood
    :param neighbors_fct: (optional) function that return, for a given graph and a given vertex id, the neighbors of the vertexs
    :return: a list of the form: [(vid1, score), (vid2, score), ...]
    """
    v_extract = v_extract.items() #  sparce prox_vect : [(id, prox_value)]
    v_extract.sort(key=lambda x: x[1], reverse=True) # sorting by prox.prox_markov
    v_extract = v_extract[:nnodes]
    
    return v_extract



def neighborhood_bipartite(graph, pzero, l, nnodes, neighbors_fct=None):
    """ neighborhood of a list of vertices in a bipartite graph

    :param pzero: list of starting vertices (ids)
    :param l: length of the random walk use to compute the neighborhood
    :param neighbors_fct: (optional) function that return, for a given graph and a given vertex id, the neighbors of the vertexs

    :returns: a list of the form: [(vid1, score), (vid2, score), ...]
    """
    if neighbors_fct is None:
        neighbors_fct = lambda g, vid: g.neighbors(vid)
    
    v_extract = prox_markov(graph, pzero, l=l, neighbors_fct=neighbors_fct)
    v_extract.update(prox_markov(graph, pzero, l=l+1, neighbors_fct=neighbors_fct))
    
    v_extract = v_extract.items() #  sparce prox_vect : [(id, prox_value)]
    v_extract.sort(key=lambda x: x[1], reverse=True) # sorting by prox.prox_markov
    v_extract = v_extract[:nnodes]
    
    return v_extract


################################################################################



# TODO rien a faire la 
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
        pline = prox_markov(graph, [gid], l=length,  neighbors_fct=neighbors_fct)
        layout.append([pline.get(to_gid, .0) for to_gid in pzlist])
        
    return layout


