#-*- coding:utf-8 -*-
""" Set of Layout Optionable classes

G{classtree AbstractLayout}
"""
__author__ = "Emmanuel Navarro <navarro@irit.fr>"
__copyright__ = "Copyright (c) 2011 Emmanuel Navarro"
__license__ = "GPL"
__version__ = "0.1"
__cvsversion__ = "$Revision: $"
__date__ = "$Date: $"

import logging
import warnings
import  igraph as ig
import numpy as np

from matplotlib.mlab import PCA

from cello.exceptions import CelloError
from cello.graphs import prox
from cello.pipeline import Optionable
from cello.types import Boolean, Numeric, Text

_logger = logging.getLogger("cello.graphs.layout")

def cluster_colors(n_clusts):
    """ Helper, computes a set of colors for n clusters using hsv colors """ 
    colors = []
    for i in xrange(n_clusts):
        colors.append( hsvToRgb((1.*i / n_clusts * 360), 0.4, 0.8) )
    return colors

def hsvToRgb(h,s,v):
    """ return a float rgb tuple as color
    http://en.wikipedia.org/wiki/HSL_and_HSV#Converting_to_RGB
    @ param h: hue float [0,360]
    @ param s: saturation float [0,1]
    @ param v: value float [0,1]
    @ return (r,g,b) with r in [0,1.], g in [0,1.] and b in [0,1.]
    """
    import math
    hi = math.floor((h/60) % 6);
    f = (h / 60) - hi
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    _rgbs = {
         0: (v,t,p),
         1: (q,v,p),
         2: (p,v,t),
         3: (p,q,v),
         4: (t,p,v),
         5: (v,p,q)
    }
    return _rgbs[hi]


def pca(mat_input, out_dim):
    """ Process a PCA
    """
    # process warnings as an error
    with warnings.catch_warnings():
        warnings.filterwarnings('error')
        try :
            mat = np.array(mat_input)
            # normalisation
            mat = mat / np.sqrt((mat**2).sum(1))[:, np.newaxis]
            # centrage
            mat = mat - mat.mean(0)
            # pca
            mypca = PCA(mat)
            result = mypca.Y[:, :out_dim].tolist()
        except np.linalg.LinAlgError as e  : # uniform matrix
            _logger.info("pca() np.linalg.LinAlgError : %s \n %s" %(e, mat_input))
            result = pca(mat + np.identity(len(mat_input)), out_dim)
        except Warning as warn: # catch warnings as error
            _logger.warn('pca() %s ' % warn)
            if len(mat_input) <= 3 :
                result = np.identity(len(mat_input)).tolist()
            else :
                result = pca(np.identity(len(mat_input)).tolist(), out_dim)
    return result

def random_proj(coords, out_dim):
    """calcul des coordonnées effectué selon a méthode Random Projection (3D) """
    import scipy as sc
    mat_r = sc.rand(len(coords), out_dim)
    proj=[]
    for coord in coords:
        x = y = z = 0
        for i,v in enumerate(coord):
            x += v * mat_r[i][0] 
            y += v * mat_r[i][1]
            z += v * mat_r[i][2]
        proj.append([x, y, z])
    return proj

def to_layout(coords, dimensions=3, shaking=False):
    """ Transform a list of positions (list) into an igraph layout
    It also does the following:
     * add empty dimension to ensure to have at least *dimensions* dimensions
     * normalise the coords between -0.5 and 0.5
     * if *shaking*, make sure that there is no point too close
    """
    # Force the layout to have enough dimensions
    if len(coords[0]) < dimensions:
        multi = dimensions - len(coords[0])
        coords = [ c + [0.]* multi for c in coords ]
    elif len(coords[0]) > dimensions:
        raise ValueError("The given layout has too many dimensions")
    # create igraph.Layout object
    layout = ig.Layout(coords)
    # normalise
    layout = normalise(layout)
    # shake
    if shaking:
        layout = shake(layout)
    return layout

def normalise(layout):
    """ Normalize an igraph.Layout,
    all values are between -0.5 and 0.5
    """
    layout.fit_into([1.] * layout.dim)
    layout.center([0.] * layout.dim)
    return layout

def shake(layout, kelastic=0.3):
    """ shakes coords

    layout: initial layout, should be normalised
    kelastic: coeficient d'elasticité
        force = kelastic * dlen
    """
    from scipy.spatial.distance import pdist, squareform
    iter_max = 50  # try to keep low

    layout_mat = np.array(layout.coords)
    nbs, nbdim = layout_mat.shape       # nb objets, nb dimension de l'espace
    deplacements = np.zeros((nbs, nbdim))  # matrice des déplacement élémentaires
    # on calcul la taille des spheres,
    # l'heuristique c'est que l'on puisse mettre 10 spheres sur la largeur du layout
    # le layout fait 1 de large
    size_elem = 1./10.
    sizes = size_elem * np.ones((nbs)) # a pseudo sphere size

    # calcul la matrice des distances minimales entre sommets
    dists_min = (sizes[:,None] + sizes[None, :]) / 2
    dists_min -= np.diag(dists_min.diagonal()) # diagonal = 0

    chevauchement = True # est-ce qu'il y a chevauchement entre les spheres ?
    nb_iter = 0
    while nb_iter < iter_max and chevauchement:
        nb_iter += 1
        # calcul des distances entre les spheres
        dists = pdist(layout_mat, 'euclidean')
        dists = squareform(dists, force='tomatrix')
        # si tout les distances sont sup a distance min
        chevauchement = (dists < dists_min).any()
        if not chevauchement:
            break
        # calcul des vecteurs de deplacement de chaque sphere (= somme des forces qui s'exerce sur chaque sommet)
        deplacements[:, :] = 0 # raz
        for source in xrange(nbs):
            for dest in xrange(source+1, nbs):
                if dists[source, dest] < dists_min[source, dest]:
                    # vecteur de deplacement de source vers dest
                    vect_depl = layout_mat[dest] - layout_mat[source]
                    # deplacement aléatoire si chevauchement parfait
                    vnorm = np.linalg.norm(vect_depl)
                    if vnorm < 1e-10:
                        vect_depl = np.random.random(nbdim)
                        vnorm = np.linalg.norm(vect_depl)
                    vect_depl /= vnorm # normalisation
                    # force = prop a la difference entre dist min et dist réel
                    force = kelastic * (dists_min[source, dest] - dists[source, dest])
                    deplacements[source, :] += - force * vect_depl
                    deplacements[dest, :] -= - force * vect_depl
        # mise a jour des positions
        layout_mat += deplacements
    layout = ig.Layout(layout_mat.tolist())
    layout = normalise(layout)
    return layout


class ProxColors(Optionable):
    def __init__(self, kgraph, name='ProxColors'):
        Optionable.__init__(self, name)
        self.name = name
        self.kgraph = kgraph
        self.prox_func = prox.prox_markov;

    def __call__(self, graph):
        plines={}
        color_vertices = self.kgraph.color_vertices
        neighbors_fct = lambda g, _vid: ( [_vid] if True else [] ) + g.neighbors(_vid)
        # vertex id in global grah, color as (r,g,b)
        for gid, (r,g,b) in color_vertices:
            plines[gid] = self.prox_func(self.kgraph.graph, [gid], neighbors_fct )

        colors = []
        for idx, vid in enumerate(graph.vs["kgraph_id"]):
            cr,cg,cb = (0,0,0) # color in [0,1]
            for cgid, (r,g,b) in color_vertices:
                value = plines[cgid].get(vid, .0)
                cr += r * value
                cg += g * value
                cb += b * value
            maxRVB = float(max(cr, cg, cb))
            if maxRVB > 0 :
                cr, cg, cb = [int(255*u) for u in [cr/maxRVB , cg/maxRVB , cb/maxRVB]]
            colors.append((cr,cg,cb))
        graph.vs['prox_color'] = colors

def Layouts2D():
    return[KamadaKawaiLayout(), FruchtermanReingoldLayout(), ProxMarkovLayoutPCA2D()]


class AbstractLayout(Optionable):
    """ Abstract labelling object
    """
    def __init__(self, name):
        """
        @param name: name of layout method
        """
        Optionable.__init__(self, name)
        self._logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, graph, **kargs):
        """ Compute a layout for a graph

        @param graph: an igraph graph
        @return: an igraph layout object
        """
        raise NotImplementedError



class ProxLayout(AbstractLayout):
    def __init__(self, prox_func, kgraph=None, dimensions=3, name='prox_layout'):
        AbstractLayout.__init__(self, name=name)
        self.dimensions = dimensions
        self._kgraph = kgraph
        self.prox_func=prox_func
        self.add_option(
            "shake", 
            Boolean(default=True, 
                    help=u"'Shake' the layout to ensure no overlaping vertices"))

    def __call__(self, graph, shake=False, **kwargs):
        """Compute a n-dimention layout for the given subgraph according to the
        result of random walks in the given graph.
        """
        # prox geometry computation (layout in n>3 dimension)
        coords = self._layout(graph, **kwargs )
        _layout = to_layout(coords, dimensions=self.dimensions, shaking=shake)
        return _layout

    def _layout(self, subgraph, **kwargs):
        neighbors_fct = lambda g, vid: ( [vid] if True else [] ) + g.neighbors(vid)
        coords = []

        if self._kgraph is not None:
            assert "kgraph_id" in subgraph.vertex_attributes(), "There is no global vertex id on subgraph vertices."
            # sur le "kgraph" seulement ie le global
            pzlist = subgraph.vs["kgraph_id"]
            graph = self._kgraph.graph
        else:
            self._logger.info("layout computation on the local graph, KGraph not available")
            # sur le "subgraph" seulement
            pzlist = range(subgraph.vcount())
            graph = subgraph

        for gid in pzlist:
            pline = self.prox_func(graph, [gid], neighbors_fct, **kwargs )
            coords.append([pline.get(to_gid, .0) for to_gid in pzlist])

        return coords



class ProxMarkovLayout(ProxLayout):
    def __init__(self, kgraph=None, dimensions=3, name='prox_markov_layout' ):
        ProxLayout.__init__(self, prox.prox_markov, kgraph=kgraph, dimensions=dimensions, name=name)
        self.add_option("l", Numeric(default=3, help="Random walk length"))

class ProxMonteCarloLayout(ProxMarkovLayout):
    def __init__(self, kgraph=None, name='prox_monte_carlo_layout'):
        ProxLayout.__init__(self, prox.prox_markov_mtcl,  kgraph=kgraph, name=name )
        self.add_option("nb_throw", Numeric(default=10, 
                        help="The number of throws in montecarlo process") )

class ProxMarkovLayoutPCA(ProxMarkovLayout):
    """ Layout prox + PCA 3D

    Compute a layout by using prox (ProxMarkov) and then by reducing
    the "prox matrix" dimention using a PCA.
    """
    def __init__(self, kgraph=None, dimensions=3, name="ProxMarkovLayoutPCA"):
        ProxMarkovLayout.__init__(self, kgraph=kgraph, dimensions=dimensions, name=name)


    def _layout(self, subgraph, l=3, **kwargs):
        """Compute a n-dimention layout for the given subgraph according to the
        result of random walks in the given graph.
        """
        # prox geometry computation (layout in n>3 dimension), and color
        coords = ProxMarkovLayout._layout(self, subgraph, l=l)
        # reduction de dimension
        coords = pca(coords, self.dimensions)
        return coords

def ProxMarkovLayoutPCA2D():
    return ProxMarkovLayoutPCA(kgraph=None, dimensions=2, name="ProxMarkovLayoutPCA2D")


class ProxConfLayoutPCA(ProxMarkovLayoutPCA):
    """ Layout prox + PCA 3D

    Compute a layout by using prox (ProxMarkov) and then by reducing
    the "prox matrix" dimention using a PCA.
    """
    def __init__(self, kgraph=None, dimensions=3, name="ProxConflLayoutPCA"):
        ProxLayout.__init__(self, prox.confluence, kgraph=kgraph, dimensions=dimensions, name=name)
        self.add_option("l", Numeric(default=3, help="Random walk length") )



class ProxBigraphLayoutPCA(ProxLayout):
    def __init__(self, prox_func, kgraph=None, dimensions=3, name='prox_markov_bigraph_ayout'):
        ProxLayout.__init__(self, prox_func, kgraph=None, name=name)
        self.dimensions = dimensions

    def __call__(self, graph, l=2,  **kwargs ):
        """Compute a n-dimention layout for the given bipartite subgraph according
        to the result of random walks in the given graph (also bipartite).

        """
        assert "type" in graph.vertex_attributes()

        neighbors_fct = ig.Graph.neighbors
        dimensions = self.dimensions
        
        pzlist = range(graph.vcount())

        coords = []
        for vid in pzlist:
            length = l - (l%2) if graph.vs[vid]["type"] else l - (l%2) + 1
            pline = prox.prox_markov(graph, [vid], l=length,  neighbors_fct=neighbors_fct)
            coords.append([pline.get(vid, .0) for vid in pzlist])

        # reduction de dimension
        coords = pca(coords, dimensions)
        layout = to_layout(coords, dimensions)
        coords = [ (x-0.5,y-0.5) if graph.vs[i]['type'] else (x+0.5,y) for i, (x,y  ) in enumerate(layout.coords)  ]
        layout = to_layout(coords, dimensions, shaking=True)
        print layout.coords
        layout.colors = [ "#AAA000" if v['type'] else "#FF0000" for v in graph.vs ]
        return layout

class ProxMarkovLayoutRandomProj(ProxMarkovLayout):
    """ Layout prox * random 3D

    Compute a layout by using prox (ProxMarkov) and then by reducing
    the "prox matrix" dimention using a random matrix.
    """
    def __init__(self, kgraph=None, dimensions=3, name="ProxMarkovLayoutRandomProj"):
        ProxMarkovLayout.__init__(self, kgraph=kgraph, dimensions=dimensions, name=name)


    def _layout(self, subgraph, l=3, **kwargs):
        """Compute a n-dimention layout for the given subgraph according to the
        result of random walks in the given graph.
        """
        # prox geometry computation (layout in n>3 dimension), and color
        coords = ProxMarkovLayout._layout(self, subgraph, l=l)
        # reduction de dimension
        coords = random_proj(coords, self.dimensions)
        return coords



class KamadaKawai3DLayout(AbstractLayout):
    def __init__(self, name="kamada_kawai_3D"):
        AbstractLayout.__init__(self, name)

    def __call__(self, graph):
        layout = graph.layout_kamada_kawai_3d()
        return normalise(layout)


class KamadaKawaiLayout(AbstractLayout):
    """ 2D layout """
    def __init__(self, name="kamada_kawai_2D"):
        AbstractLayout.__init__(self, name)
        self.dimensions = 2

    def __call__(self, graph):
        layout = graph.layout_kamada_kawai(dim=2)
        return to_layout(layout.coords, dimensions=self.dimensions)


class FruchtermanReingoldLayout(AbstractLayout):
    """ 2D layout """
    def __init__(self, name="fruchterman_reingold_2D"):
        AbstractLayout.__init__(self, name)

    def __call__(self, graph):
        layout = graph.layout_fruchterman_reingold(dim=2)
        return to_layout(layout.coords)


class Random3DLayout(AbstractLayout):
    def __init__(self, name="random_3D"):
        AbstractLayout.__init__(self, name)

    def __call__(self, graph):
        layout = graph.layout_random_3d()
        return normalise(layout)


class Grid3DLayout(AbstractLayout):
    def __init__(self, name="grid_3D"):
        AbstractLayout.__init__(self, name)
        self.add_option("width", Numeric(default=0, 
            help="""the number of vertices in a single row of the layout. 
            Zero means that the height should be determined automatically."""))
        self.add_option("height", Numeric(default=0,
            help="""the number of vertices in a single column of the layout. 
            Zero means that the height should be determined automatically."""))

    def __call__(self, graph, width=0, height=0):
        layout = graph.layout_grid(width=width, height=height, dim=3)
        return normalise(layout)


