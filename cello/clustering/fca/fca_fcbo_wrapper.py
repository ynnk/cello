#!/usr/bin/env python
#-*- coding:utf-8 -*-

__author__ = "Emmanuel Navarro <navarro@irit.fr>"

import sys
import os
import logging
_logger = logging.getLogger("cello.grahs.fca.fca_fcbo")

import subprocess
from tempfile import NamedTemporaryFile

import random

import igraph as ig

def _extent(bigraph, intent, obj_type=True):
    """Return the extent of a concept according to this intent"""
    if len(intent):
        intent_iter = iter(intent)
        first_vtx = intent_iter.next()
        assert 0 <= first_vtx < bigraph.vcount(), "vtx id '%d' is not a valid vertex index" % first_vtx
        extent = set(bigraph.neighbors(first_vtx))
        for prop in intent_iter:
            extent.intersection_update(bigraph.neighbors(prop))
    else:
        extent = [vtx.index for vtx in bigraph.vs.select(type=obj_type)]
    return extent

def fcbo(bigraph, min_support=1, obj_type=True, delete_files=True, fcbo_exec=None):
    """ Call FCBO formal concept analysis program
    
    @see: http://fcalgs.sourceforge.net/
    """
    # check exec file
    if fcbo_exec is None:
        fcbo_exec = os.path.dirname(__file__) + "/../../../misc/fca/fcbo-ins/fcbo-static-linux-x86_64"
    if not os.path.isfile(fcbo_exec):
        raise ValueError("Could not found the FCBO exec file : %s doesn't exist" % fcbo_exec)
    if bigraph.ecount() == 0:
        _logger.warn("Graph with no edges")
        return []
    # creation du fichier input
    tmp_input = NamedTemporaryFile(mode='w', prefix='fcbo_wrapper_', delete=False)
    tmp_input_name = tmp_input.name
    try:
        # remplisage du fichier input
        for obj in bigraph.vs.select(type=obj_type):
            voisins = " ".join( "%s" % prop.index for prop in obj.neighbors() )
            tmp_input.write("%s\n" % (voisins))
        tmp_input.close()
        # calcul des concepts, lecture sur stdout
        cmd = [fcbo_exec]
        cmd += ["-S%d" % min_support]
        cmd += [tmp_input_name]
        fcbo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        intents = []
        for lconcept in fcbo.stdout.xreadlines():
            lconcept = lconcept.strip()
            if not len(lconcept): continue
            intents.append(set(int(attr) for attr in lconcept.split()))
    finally:
        # suppression du fichier input
        os.remove(tmp_input_name)
    # completion des concepts
    concepts = [(_extent(bigraph, intent, obj_type=obj_type), intent) for intent in intents]
    return concepts

def main():
    fcbopath = os.path.dirname(__file__) + "/../../../misc/fca/fcbo-ins/fcbo-static-linux-x86_64"
    gtest = ig.Graph.Formula("A:B:C:D-a:b:c:d:e:f,A-g:h")
    gtest.vs["type"] = [v["name"].isupper() for v in gtest.vs]
    concepts = fcbo(gtest, fcbo_exec=fcbopath)
    print("concepts :")
    for extent, intent in concepts:
        extent_str = ",".join(gtest.vs[vid]["name"] for vid in extent)
        intent_str = ",".join(gtest.vs[vid]["name"] for vid in intent)
        print("%s - %s" % (extent_str, intent_str))

if __name__ == '__main__':
    sys.exit(main())


