#!/usr/bin/env python
#-*- coding:utf-8 -*-
__author__ = "Emmanuel Navarro <navarro@irit.fr>"
__copyright__ = "Copyright (c) 2011 Emmanuel Navarro"
__license__ = "GPL"
__version__ = "0.1"
__cvsversion__ = "$Revision: $"
__date__ = "$Date: $"

import igraph as ig

def weighted_linegraph(g, alpha=1, wgt_attr="weight"):
    """ Compute a weighted linegraph
    """
    assert g.is_directed()
    
    lg = g.linegraph()
    print "Graph:     |V|=%4d, |E|=%4d,  directed:%s"%(g.vcount(), g.ecount(), g.is_directed())
    print "LineGraph: |V|=%4d, |E|=%4d,  directed:%s"%(lg.vcount(), lg.ecount(), lg.is_directed())

    def wgt(ee):
        es = g.es[ee.source]
        et = g.es[ee.target]
        a, b  = es.source, es.target
        bp, c  = et.source, et.target
        assert b == bp
        ac = g.are_connected(a, c) if not a == c else 1
        return alpha + (1-alpha)*ac

    lg.es[wgt_attr] = [wgt(ee) for ee in lg.es]
    
    if __debug__:
        for ve in lg.vs:
            ve = ve.index
            assert lg.degree(ve) > 0, "degree of %d (%d->%d) is zero"%(ve, g.es[ve].source, g.es[ve].target)
            #wsum = sum([lg.es[ee_idx]["weight"] for ee_idx in lg.adjacent(ve, type=ig.OUT)])
            #assert fequals(wsum, 1), \
            #        "Vertex %d (%d->%d): sum equals %1.3f rather 1."%(ve, g.es[ve].source, g.es[ve].target, wsum)
            
    return lg

def undirected_weighted_linegraph(g, weight="D", wgt_attr="weight"):
    """ Compute linegraph

    @param weight: C, D or E
    """
    assert not g.is_directed(), "The graph should not be directed"
    
    lg = g.linegraph()
    print "G:        |V|=%4d, |E|=%4d,  directed:%s"%(g.vcount(), g.ecount(), g.is_directed())
    print "un-d. LG: |V|=%4d, |E|=%4d,  directed:%s"%(lg.vcount(), lg.ecount(), lg.is_directed())
    print "weight: %s" % weight
    
    if weight == "C":
        wgt = lambda e: 1.
    elif weight == "D":
        def wgt(ee):
            es, et = g.es[ee.source], g.es[ee.target]
            assert not es == et
            a, b  = es.source, es.target
            c, d  = et.source, et.target
            if a == c or a == d:   k = g.degree(a)
            elif b == c or b == d: k = g.degree(b)
            else: raise AssertionError, "Pb: %s-%s and %s-%s are linked in the line graph !" % (a,b,c,d)
            return 1. / float(k-1)
    #elif weight == "E":
        #wgt = lambda e: 1.
    else:
        raise IOError, "Unknow weight function (%s)" % weight
    #
    lg.es[wgt_attr] = [wgt(ee) for ee in lg.es]
    #
    if __debug__:
        for ve in lg.vs: #OR for ve in g.es:
            ve = ve.index
#            print g.degree(g.es[ve].source), g.degree(g.es[ve].target)
            v1_deg_ok = g.degree(g.es[ve].source) > 1
            v2_deg_ok = g.degree(g.es[ve].target) > 1
            if v1_deg_ok or v2_deg_ok:
                assert lg.degree(ve) > 0, "degree of %d (%d->%d) is zero"%(ve, g.es[ve].source, g.es[ve].target)
            wsum = sum([lg.es[ee_idx]["weight"] for ee_idx in lg.incident(ve)])
            if weight == "D":
                if v1_deg_ok and v2_deg_ok:
                    assert abs(wsum - 2.) < 1e-10, \
                        "Vertex %d (%d-%d): sum equals %1.3f rather 2."%(ve, g.es[ve].source, g.es[ve].target, wsum)
                elif v1_deg_ok or v2_deg_ok:
                    assert abs(wsum - 1.) < 1e-10, \
                        "Vertex %d (%d-%d): sum equals %1.3f rather 1."%(ve, g.es[ve].source, g.es[ve].target, wsum)
                else:
                    assert wsum == 0
    return lg


def ecluster_2_vcover(g, eclusters, fmain=False, fsmall=0, type_use=ig.IN):
    """ Transforme un partitionement des aretes en un recouvrement des sommets

    @param fsmall: keep only community of *strictly* more than the given number of vertices
    """
    cover = []
    membership = [{} for _ in range(g.vcount())]
    for cid, eids in enumerate(eclusters):
        #sys.stdout.write("%d: "%(cid))
        com = {}
        for eid in eids:
            #sys.stdout.write(" eid:%d"%eid)
            #sys.stdout.flush()
            vsource = g.es[eid].source
            vtarget = g.es[eid].target
            #sys.stdout.write(" %d->%d"%(vsource, vtarget))
            
            if type_use == ig.OUT or type_use == ig.ALL:
                # ajout le sommet *source* dans le cluster
                com[vsource] = com.get(vsource, 0) + 1 # inc. nb de fois le sommet "est" ajouté dans le cluster
                membership[vsource][cid] = membership[vsource].get(cid, 0) + 1
            if type_use == ig.IN  or type_use == ig.ALL:
                # ajout le sommet *target* dans la cluster
                com[vtarget] = com.get(vtarget, 0) + 1# inc. nb de fois le sommet "est" ajouté dans le cluster
                membership[vtarget][cid] = membership[vtarget].get(cid, 0) + 1
            #sys.stdout.flush()
        cover.append(com)
        #sys.stdout.write(" | "+ " ".join(["%d(%d)"%(vid, nb) for vid, nb in com.items()]) + "\n")
    # cover = [{1:34, 2:3}, {2:4, 4:6}]
    
    # seulements les com qui sont principale pour au moins un de leur sommet
    
    debug = False
    if debug:
        c_is_main = lambda cid, c: sum([membership[vid][cid] == max(membership[vid].values()) for vid in c])
        print("-->vid(nbcom): % aretes ds chaque com")
        for vid, vcom in enumerate(membership):
            print "-->%d(%d): "%(vid, len(vcom)) + \
               " - ".join(["%1.2f"%(nb_edges/float(g.degree(vid, type_use)))  for cid, nb_edges in vcom.iteritems()])
            
        print "***----***"       
        print("->com.(size, nb_main_vertices): % aretes de chaque sommet")
        for cid, c in enumerate(cover):
            print "->%d(%d,%s): "%(cid, len(c), "M"*c_is_main(cid, c.keys())) +\
               " - ".join(["%1.2f"%(nb_edges/float(g.degree(vid, type_use)))  for vid, nb_edges in c.iteritems()])
    
    if fmain:
        c_is_main = lambda cid, c: sum([membership[vid][cid] == max(membership[vid].values()) for vid in c])
        cover = [c.keys() for cid, c in enumerate(cover) if c_is_main(cid, c.keys())]
    else:
        cover = [c.keys() for c in cover]
    
    # filter too small communities
    if fsmall > 0: cover = [c for c in cover if len(c) > fsmall]
    return cover 

