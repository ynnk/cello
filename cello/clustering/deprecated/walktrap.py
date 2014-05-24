# -*- coding: utf-8 -*-
""" 
"""
from operator import itemgetter
from math import sqrt
from numpy import zeros
import igraph

from cello.graphs.prox import prox_markov_dict

################################################################################

# calcul de la modularité, 
#XXX: doit sortir d'ici, rien a faire dans ce fichier .py
def bimodularity(g, membership, wgt = None):
    """ Compute the modularity in a bipartit graph.
    @see: Michael J Barber, “Modularity and community detection in bipartite networks” 0707.1616 (Juillet 11, 2007), doi:doi:10.1103/PhysRevE.76.066102, http://arxiv.org/abs/0707.1616.
    """
    nb_c = max(membership) + 1 

    com = [{'top':[], 'bot':[]} for _ in xrange(int(nb_c))]
    for v, c in enumerate(membership):
        c = int(c)
        if g.vs[v]["type"]: com[c]['top'].append(v)
        else: com[c]['bot'].append(v)
    
    top = [v for v in g.vs if v["type"]]
    bot = [v for v in g.vs if not v["type"]]

    #for vs in com: print vs
    if wgt == None :
        m = float(g.ecount())
        _a = lambda i, j : 1. if g.are_connected(i, j) else 0.
        _p = lambda i, j : g.degree(i, type=igraph.OUT) * g.degree(j, type=igraph.OUT) / m
    else:
        wgt_by_top = dict( (v.index, {}) for v in top )
        wgt_by_bot = dict( (v.index, {}) for v in bot )
        for e in g.es:
            id_top, id_bot = (e.source, e.target) if g.vs[e.source]["type"] \
                        else (e.target, e.source)
            wgt_by_top[id_top][id_bot] = wgt[e.index]
            wgt_by_bot[id_bot][id_top] = wgt[e.index]

        deg_top = dict((v.index, sum(wgt_by_top[v.index].values())) for v in top)
        deg_bot = dict((v.index, sum(wgt_by_bot[v.index].values())) for v in bot)
        m = sum(deg_bot.values())
        m2 = sum(deg_top.values())
        assert abs(m - m2) < 1e-5
        _a = lambda i, j : wgt_by_top[i][j] if g.are_connected(i, j) else 0.
        _p = lambda i, j : deg_top[i] * deg_bot[j] / m 

        #print [[_a(i, j) - _p(i, j) for i in vs['top'] for j in vs['bot']] for vs in com]
    #for c, vs in enumerate(com):
    #    for i in vs['top']:
    #        for j in vs['bot']:
    #            print _a(i, j)
    #            print deg_top[i],  deg_bot[j], deg_top[i] * deg_bot[j], m
    #            assert _p(i, j) <= 1., "p > 1 - %1.4f"%(_p(i, j))
                #print c, i, j, _a(i, j) - _p(i, j), _a(i, j), _p(i, j), \
                #    deg_top[i] * deg_bot[j], \
                #    deg_top[i],  deg_bot[j], m 

    q = sum([sum([_a(i, j) - _p(i, j) for i in vs['top'] for j in vs['bot']]) for vs in com])

    return q / m

def bimodularity_local(g, subset):
    """ Compute the modularity for one community
    """
    subtop = [v for v in subset if g.vs[v]["type"]]
    subbot = [v for v in subset if not g.vs[v]["type"]]

    m = float(g.ecount())
    a, e = 0., 0.

    e = sum([1. for vt in subtop for vb in subbot if g.are_connected(vt, vb)])
    a = float(sum([k*d for k in g.degree(subtop, type=igraph.OUT) \
                       for d in g.degree(subbot, type=igraph.OUT)]))
    return (e  - a / m )/ m


def cut_diag(g, merges, q_local):
    """
    """
    nb_v = g.vcount()

    def _members(merges, i):
        if i <= len(merges):
            return [i]
        else:
            suns = merges[i - len(merges) - 1]
            return _members(merges, suns[0]) + _members(merges, suns[1])

    def _best_cut(merges, c_id):
        C = _members(merges, c_id)
        ql = q_local(g, C)
        if c_id <= len(merges):
            return ql, [C]
        else:
            suns = merges[c_id - len(merges) - 1]
            q1, sC1 = _best_cut(merges, suns[0])
            q2, sC2 = _best_cut(merges, suns[1])
            if q1 + q2 > ql:
                return q1+q2, sC1 + sC2
            else:
                return ql, [C]
        return q, s

    q, C = _best_cut(merges, nb_v+len(merges)-1)
    m = [0]*g.vcount()
    for c, nodes in enumerate(C):
        for n in nodes: m[n] = c
    return q, m


################################################################################
def walktrap_bigraph(graph, l_docs, l_terms, wgt=None, cut_type="modularity"):
    """ WalkTrap community detection method, but adapted for bipartite graph.
        1. Compute geometry of the bigraph using prox
        2.
    """
    # clustering hierarchique par dessus numpy
    import hcluster

    if not  cut_type in ["modularity", "max", "cc", "fixed", "fixed_V2"]:
        raise ValueError, "Option cut_type : %s didn't exist !"%cut_type 
    #   ========================================================
    #   = Document’s and label’s geometry computation 
    #   
    #   =     in       : L ∪ RD                      : document and label sets 'v_extract'
    #   =     out      : {FG (u) ∈ Rn , ∀u ∈ L ∪ RD} : geometrical coordinates  [][]
    #   =     resources: Gt                          : thematic bipartite graph
    #   ========================================================

    # liste des documents a prendre en considération
    ids_docs = [v.index for v in graph.vs.select(type=True)]
    # liste des labels a prendre en considération
    # union des labels de chaque document
    ids_labels = [v.index for v in graph.vs.select(type=False)]
    
    if type(wgt) == str:
        assert wgt in graph.es.attribute_names(), "'%s' is not an edge attribute !" % wgt
        wgt = graph.es[wgt]
    #print "WGTTT", wgt
    
    if wgt and len(wgt) != 0:
        assert type(wgt) == list, "The weight should be of type list or str (not %s)" % type(wgt)
        assert len(wgt) == graph.ecount(), "Incorect weight list"
        wgt_fct = lambda u, v: wgt[graph.get_eid(u, v)]
    else:
        wgt_fct = lambda u, v: 1.
    
    # cacul des lignes de proxemie
    # Utilisation de generateur pour ne pas chargé inutilement la mémoire (le calcul n'est effectuer que lors de la lecture)
    M_docs  = (prox_markov_wgt(graph, [vid], l=l_docs, wgt=wgt_fct, epsi=0, false_refl=False) for vid in ids_docs)
    M_terms = (prox_markov_wgt(graph, [vid], l=l_terms, wgt=wgt_fct, epsi=0, false_refl=False) for vid in ids_labels)
    # construit la matrice : (docs+terms)*docs
    #     d1, d2, d3, ..., dk
    #  d1  x   x   x        x
    #  dk  x   x   x        x
    #  t1  x   x   x        x
    #  t2  x   x   x        x
    #  t3  x   x   x        x
    #   
    #  tn  x   x   x        x
    matrix =  [[l_prox.get(vid, 0) for vid in ids_docs] for l_prox in M_docs]
    matrix += [[l_prox.get(vid, 0) for vid in ids_docs] for l_prox in M_terms]
    
    #   ========================================================
    #   = Clustering 
    #   ========================================================
    
    id2ig = lambda x: ids_docs[x] if x < len(ids_docs) \
                   else ids_labels[x-len(ids_docs)] if x - len(ids_docs) < len(ids_labels) \
                   else x

    #   calcul du dendrogramme
    Z = hcluster.linkage(matrix,  method='ward', metric='euclidean')
    #   dendrogramme liste de merges de type array numpy  
    merges = [ [id2ig(int(i[0])), id2ig(int(i[1]))] for i in Z[:, 0:2]]
    #print "Graph  len %s"%(graph.vcount())
    #print "Matrix len %s"%(len(matrix))
    #print "Merges len %s"%(len(merges))
    
    membership = []
    if cut_type == "modularity" :
        q_max = -100
        for s in range(len(merges)):
            com = igraph.community_to_membership(merges, graph.vcount(), s)
            q = bimodularity(graph, com, wgt)
            if q > q_max:
                membership = com
                q_max = q

    elif cut_type == "max":
        q, membership = community.cut_diag(graph, merges, q_local=bimodularity_local)
    
    elif cut_type == "fixed":
        membership = igraph.community_to_membership(merges, graph.vcount(), cut_level)
    
    elif cut_type == "cc":
        membership = graph.clusters().membership
    
    return igraph.VertexClustering(graph, membership);
    
