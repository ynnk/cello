#!/usr/bin/env python
#-*- coding:utf-8 -*-

__author__ = "Emmanuel Navarro <navarro@irit.fr>"
__copyright__ = "Copyright (c) 2009 Emmanuel Navarro"
__license__ = "GPL"
__version__ = "0.1"
__cvsversion__ = "$Revision: $"
__date__ = "$Date: $"

import sys
import os

from subprocess import Popen
from tempfile import mkdtemp

import random

import igraph as ig



def _read_cover(filename):
    """ Read cover file (on line by cluster)
    """
    cover = []
    with open(filename, "r") as coverfile:
        for cluster_id, cluster_line in enumerate(coverfile.xreadlines()):
            if cluster_line.strip().startswith("#"): continue
            cluster_vids = [int(vid) for vid in cluster_line.strip().split(" ")]
            cover.append(cluster_vids)
    return cover

#------------------------------------------------------------------------------#
BASE_CLUSTERING_DIR = os.path.dirname(__file__)

#------------------------------------------------------------------------------#
OSLOM_CMD_UD = "../../../misc/clustering/OSLOM2/oslom_undir"
OSLOM_CMD_D =  "../../../misc/clustering/OSLOM2/oslom_dir"

OSLOM_GRAPHNAME = "graph.elist"
OSLOM_COMFILE = "tp"
OSLOM_LOG_FILE = "oslom_run.log"
OSLOM_TMP_DIR_PRE = "tmp_oslom_"

def check_oslom():
    filedir = os.path.dirname(os.path.abspath(__file__))
    return os.path.isfile(os.path.join(filedir, OSLOM_CMD_UD)) \
            and os.path.isfile(os.path.join(filedir, OSLOM_CMD_D))

def oslom(graph, weights=None, delete_files=True):
    """ Call to the OSLOM application
    """
    jdir = os.path.join
    # create tmp working dir
    workdir = mkdtemp(prefix=OSLOM_TMP_DIR_PRE, dir="/tmp/")
    
    # graph file writing
    if weights:
        graph.write_ncol(jdir(workdir, OSLOM_GRAPHNAME), names=None, weights=weights)
    else:
        graph.write_edgelist(jdir(workdir, OSLOM_GRAPHNAME))

    filedir = os.path.dirname(os.path.abspath(__file__))
    if not graph.is_directed(): cmd = [os.path.join(filedir, OSLOM_CMD_UD)]
    else: cmd = [os.path.join(filedir, OSLOM_CMD_D)]
    cmd += ["-f", OSLOM_GRAPHNAME]
    cmd += ["-w"] if weights else ["-uw"]
    cmd += ["-hr", "0"]
    cmd += ["-seed", "%s"%random.randint(0,2e8)]

    logfilename = jdir(workdir, OSLOM_LOG_FILE)
    with open(logfilename, "w") as logfile:
        print("DIR:%s CMD:%s" % (workdir, " ".join(cmd)))
        print("File: %s" % __file__)
        cmd_run = Popen(cmd, stdout=logfile, stderr=logfile, cwd=workdir)
        return_code = cmd_run.wait()
    # error ?
    if return_code != 0:
        raise IOError, "Error code : %d (errors in: %s)" % (return_code, logfilename)

    # result reading
    cover = _read_cover(jdir(workdir, OSLOM_COMFILE))

    # cleaning tmp files
    if delete_files:
        os.remove(jdir(workdir, OSLOM_GRAPHNAME))
        os.remove(jdir(workdir, OSLOM_LOG_FILE))
        try: os.remove(jdir(workdir, OSLOM_COMFILE))
        except OSError: pass
        contenu = os.listdir(jdir(workdir, OSLOM_GRAPHNAME + "_oslo_files"))
        for subfile in contenu: os.remove(jdir(workdir, OSLOM_GRAPHNAME + "_oslo_files", subfile))
        os.rmdir(jdir(workdir, OSLOM_GRAPHNAME + "_oslo_files"))
        os.removedirs(workdir)
    return ig.VertexCover(graph, cover)

#------------------------------------------------------------------------------#
#COPRA_JAR = os.path.dirname(__file__) + "../copra/copra.jar"
COPRA_JAR = "../copra/copra.jar"
COPRA_GRAPHNAME = "graph.elist"
COPRA_LOG_FILE = "copra_run.log"
COPRA_TMP_DIR_PRE = "tmp_copra_"

def copra(graph, repeat=10, v=1, delete_files=True):
    """ Call to the copra java application
    see  http://www.cs.bris.ac.uk/~steve/networks/software/copra.html
    """
    jdir = os.path.join
    # create tmp working dir
    workdir = mkdtemp(prefix=COPRA_TMP_DIR_PRE, dir="./")

    # graph file writing
    graph.write_edgelist(jdir(workdir, COPRA_GRAPHNAME))

    # cobra execution
    # cmd example:
    # java -cp ./copra/copra.jar COPRA gtest/papillon_v5.elist -v 2 -repeat 20 -mo
    cmd =  ["java"]
    cmd += ["-cp", COPRA_JAR, "COPRA"]
    cmd += [COPRA_GRAPHNAME]
    cmd += ["-repeat", str(repeat), "-mo"]
    cmd += ["-vs", "1", "3"]

    with open(jdir(workdir, COPRA_LOG_FILE), "w") as logfile:
        print workdir, cmd
        cmd_run = Popen(cmd, stdout=logfile, cwd=workdir)
        return_code = cmd_run.wait()
    # error ?
    if return_code != 0:
        raise IOError, "Error code : %d" % return_code

    # result reading
    cover = _read_cover(jdir(workdir, "best-clusters-" + COPRA_GRAPHNAME))

    # cleaning tmp files
    if delete_files:
        os.remove(jdir(workdir, COPRA_GRAPHNAME))
        os.remove(jdir(workdir, COPRA_LOG_FILE))
        try: os.remove(jdir(workdir, "clusters-" + COPRA_GRAPHNAME))
        except OSError: pass
        try: os.remove(jdir(workdir, "best-clusters-" + COPRA_GRAPHNAME))
        except OSError: pass
        os.removedirs(workdir)
    return ig.VertexCover(graph, cover)


#------------------------------------------------------------------------------#
#COPRA_JAR = os.path.dirname(__file__) + "../copra/copra.jar"
MOSES_CMD = "../moses/moses-binary-linux-x86-64"
MOSES_GRAPHNAME = "graph.elist"
MOSES_COMFILE = "result.com"
MOSES_LOG_FILE = "moses_run.log"
MOSES_TMP_DIR_PRE = "tmp_moses_"

def moses(graph, delete_files=True):
    """ Call to the MOSES application
    see http://clique.ucd.ie/moses
    """
    jdir = os.path.join
    # create tmp working dir
    workdir = mkdtemp(prefix=MOSES_TMP_DIR_PRE, dir="./")

    # graph file writing
    graph.write_edgelist(jdir(workdir, MOSES_GRAPHNAME))

    # cobra execution
    # cmd example:
    # java -cp ./copra/copra.jar COPRA gtest/papillon_v5.elist -v 2 -repeat 20 -mo
    cmd =  [MOSES_CMD]
    cmd += [MOSES_GRAPHNAME]
    cmd += [MOSES_COMFILE]

    with open(jdir(workdir, MOSES_LOG_FILE), "w") as logfile:
        print workdir, cmd
        cmd_run = Popen(cmd, stdout=logfile, cwd=workdir)
        return_code = cmd_run.wait()
    # error ?
    if return_code != 0:
        raise IOError, "Error code : %d" % return_code

    # result reading
    cover = _read_cover(jdir(workdir, MOSES_COMFILE))

    # cleaning tmp files
    if delete_files:
        os.remove(jdir(workdir, MOSES_GRAPHNAME))
        os.remove(jdir(workdir, MOSES_LOG_FILE))
        try: os.remove(jdir(workdir, MOSES_COMFILE))
        except OSError: pass
        os.removedirs(workdir)
    return ig.VertexCover(graph, cover)


if __name__ == '__main__':
    #g = ig.Graph(n=6, edges=[(0,1),(0,5),(1,2),(1,5),(2,3),(2,4),(3,4)])
    g1 = ig.Graph.Erdos_Renyi(100,0.2)
    g2 = ig.Graph.Erdos_Renyi(100,0.2)
    g = g1 + g2
    cover = oslom(g, delete_files=True)
    #cover = moses(g, delete_files=False)
    #cover = copra(g, repeat=20, delete_files=True)
    print cover
    sys.exit()


