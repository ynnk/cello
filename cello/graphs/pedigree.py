#-*- coding:utf-8 -*-

import igraph
import numpy as np
import StringIO

# from enavarro http://enavarro.me/

opt_default = { "n":True,
                "m":True,
                "<k>":True,         # average degree (in case of directed graph, it's average OUT degree)
                "<k_in>":True,         # average degree (in case of directed graph, it's average OUT degree)

                "directed":True,
                "mutuals":True,     # for directed graph, number of edges (a->b) that have a mutual edge (b->a)
                "loops":True,       # number of self loops
                "single":True,      # number of vertices without neighbors
                "reflexif":True,    # boolean, True if loops == n (a selfloop per vertex)
                "multiples":False,   # Number of multiple edges (long to compute)
                "simple":True,      # simple means no loop and no mulitple edge

                "ncc":True,         # nomber of connected components

                "C":True,           # Global clustering coef
                "rho":True,         # degree correlation

                "dd_plot":False,     # plot the degree distribution
                "a":True,           # power law fit, out degree used by default
                "r2":True,
                "dd_plot_in": False,     # plot the degree distribution
                "a_in":True,
                "r2_in":True,

                # Largest Connected Component
                "LCC":True,        # Compute figures on LCC (should be True for following options)
                "n_lcc":True,
                "m_lcc":True,
                "<k>_lcc":False,
                "C_lcc":False,
                "rho_lcc":False,    # degree correlation
                "L_lcc":True,
    
                "dd_plot_lcc":False,
                "a_lcc":False,
                "r2_lcc":False,
                # global plot flag
                "no_plot":True,
            }

strf4 = lambda val: "%1.4f"%val
strf3 = lambda val: "%1.3f"%val
strf2 = lambda val: "%1.2f"%val
str2bool = lambda val: val.lower() in ["yes", "true", "t", "1"]

# graph pedigree
opt_ordre_cast_cmt = [   
                #("Name", value-->texte, texte-->value, "comment")
                ("n", str, int, " = |V|, number of vertices"),
                ("m", str, int, " = |E|, number of edges"),
                ("<k>", strf4, float," average degree (in case of directed graph, it's average of OUT degree)"),

                ("directed", str, str2bool, "True if the graph is directed"),
                ("mutuals", str, int,   "for directed graph, number of edges (a->b) that have a mutual edge (b->a)"),
                ("loops", str, int,     "number of self loops"),
                ("single", str, int,    "number of vertices without neighbors"),
                ("reflexif", str, str2bool, "True if loops == n (ie. a selfloop per vertex)"),
                ("multiples", str, int, "Number of multiple edges (long to compute)"), 
                ("simple", str, str2bool,   "True if NO loop and NO mulitple edge"),

                ("ncc", str, int,       "number of connected components"),

                ("C", strf4, float,     "Global clustering coef."),
                ("rho", strf4, float,   "degree correlation"),

                ("dd_plot", str, str,   "Path to the degree distribution plot"),
                ("a", strf4, float,     ""),
                ("r2", strf4, float,    ""),
                ("dd_plot_in", str, str,   "Path to the degree distribution plot (in degree)"),
                ("a_in", strf4, float,     ""),
                ("r2_in", strf4, float,    ""),

                # Largest Connected Component
                ("n_lcc", str,     int,  ""),
                ("m_lcc", str,     int,  ""),
                ("<k>_lcc", strf4, float,""),
                ("C_lcc", strf4, float,  ""),
                ("rho_lcc", strf4, float,   "degree correlation on lcc"),
                ("L_lcc", strf4, float,  ""),
    
                ("dd_plot_lcc", str, str, ""),
                ("a_lcc", strf4, float, ""),
                ("r2_lcc", strf4, float,""),
            ]

def compute(g, opt={}):
    """ Calcul le pedigree du graph g.

    @param g: le graph (object igraph.Graph)
    @param opt: dictionaire indiquant les valeurs a calculer, le dictionaire fournis met a jour les valeurs par defaut indiqué dans opt_default.

    @return: le pedigree cad un dictionaire
    """
    # Update des options par defaut par celles fournies
    _opt = opt
    opt = opt_default.copy()
    opt.update(_opt)

    p = {}
    
    def pset(key, value):
        if not key in opt:
            warnings.warn("The key '%s' doesn't exist !")
        if key in opt and opt[key]: p[key] = value
    
    pset("n", g.vcount())
    pset("m", g.ecount())
    pset("<k>", np.mean(g.degree(mode=igraph.OUT)))
    
    pset("directed", g.is_directed())
    pset("mutuals", len([1 for e in g.is_mutual() if e]))

    if opt["loops"] or opt["reflexif"]:
        nloops = len([1 for l in g.is_loop() if l])
    pset("loops", nloops)
    pset("reflexif", nloops == g.vcount())

    pset("single", len(g.vs.select(lambda v: g.degree(v.index) == 0)))
    
    pset("multiples", len([1 for e in g.is_multiple() if e]))
    pset("simple", g.is_simple())
    
    # C Global
    pset("C", g.transitivity_undirected())
    # Correlation des degrées
    pset("rho", g.assortativity_degree())
    
    cc = []
    if opt["ncc"] or opt["LCC"]: cc = g.clusters(mode=igraph.WEAK)
    pset("ncc", len(cc))


    if  opt["no_plot"] == False:

        if opt["dd_plot"] or opt["a"] or opt["r2"]:
            plot_title = "Degree Distribution" if opt["dd_plot"] else None
            a, r2, plot_fname = fit_power_law(g, plot_title, plot_fname=None, only_loglog=False, mode=igraph.OUT)
            pset("a", a)
            pset("r2", r2)
            pset("dd_plot", plot_fname)
            if g.is_directed():
                plot_title = "Degree Distribution (in)" if opt["dd_plot"] else None
                a, r2, plot_fname = fit_power_law(g, plot_title, plot_fname=None, only_loglog=False, mode=igraph.IN)
                pset("a_in", a)
                pset("r2_in", r2)
                pset("dd_plot_in", plot_fname)

    if opt["LCC"]:
        lcc = cc.giant()
        
        pset("n_lcc", lcc.vcount())
        pset("m_lcc", lcc.ecount())
        #pset("<k>", np.mean(lcc.degree(mode=igraph.OUT)))
        
        pset("C_lcc", lcc.transitivity_undirected())
        # Correlation des degrées
        pset("rho_lcc", lcc.assortativity_degree())

        pset("L_lcc", lcc.average_path_length())

        if  opt["no_plot"] == False:
            if opt["dd_plot_lcc"] or opt["a_lcc"] or opt["r2_lcc"]:
                plot_title = "Degree Distribution (on LCC)" if opt["dd_plot_lcc"] else None
                a_lcc, r2_lcc, plot_fname_lcc = fit_power_law(g, plot_title, plot_fname=None, only_loglog=False)
                pset("a_lcc", a)
                pset("r2_lcc", r2)
                pset("dd_plot_lcc", plot_fname_lcc)
    return p




def to_str(p):
    out = StringIO.StringIO()
    for key, cast, _, cmt in opt_ordre_cast_cmt :

        if not p.has_key(key):
            continue
            
        out.write("%12s = %6s\t\t# %s\n"%(key, cast(p[key]), cmt))
        
    return out.getvalue()
    