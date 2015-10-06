#-*- coding:utf-8 -*-
""" :mod:`cello.layout.transform`
================================

Set of component to transform a layout (reduce dimention, normalize, shake, ...)
"""
import warnings

import numpy as np
import scipy as sc
from matplotlib.mlab import PCA

import igraph as ig

from reliure import Composable, Optionable


class ReducePCA(Composable):
    """ Reduce a layout dimention by a PCA

    .. note:: the input layout should have the same number of dim than vertices

    >>> import igraph as ig
    >>> layout = ig.Layout([[1, 0, 0, 0, 0], [1, 1, 0, 0, 0], [1, 0, 1, 0, 0], [1, 0, 0, 1, 0], [1, 0, 0, 0, 1]])
    >>> layout
    <Layout with 5 vertices and 5 dimensions>
    >>> # we can then reduce it with a PCA:
    >>> pca = ReducePCA(2)
    >>> pca(layout)
    <Layout with 5 vertices and 2 dimensions>

    Some limit cases:

    >>> # if the input layout is empty nothing is done:
    >>> pca(ig.Layout())
    <Layout with no vertices and 2 dimensions>
    >>> pca = ReducePCA(3)
    >>> pca(ig.Layout([[1, 1], [0, 1]])).coords
    [[1.0, 1.0, 0.0], [0.0, 1.0, 0.0]]

    """
    def __init__(self, dim=3):
        super(ReducePCA, self).__init__()
        self.out_dim = dim

    def robust_pca(self, mat, nb_fail=0):
        if nb_fail > 5:
            raise ValueError("Fail (x%d) to compute PCA" % nb_fail)
        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            nb_dim = mat.shape[1]
            try:
                mat_saved = mat.copy()  #Note save the matrix because it may me modified in PCA
                # normalisation
                mat = mat / np.sqrt((mat**2).sum(1))[:, np.newaxis]
                # centrage
                mat = mat - mat.mean(0)
                # pca
                mypca = PCA(mat)
                result = mypca.Y[:, :self.out_dim]
            except np.linalg.LinAlgError as err: # uniform matrix
                self._logger.warn("pca() np.linalg.LinAlgError : %s" % (err))
                # retry
                result = self.robust_pca(mat_saved + np.identity(nb_dim), nb_fail=nb_fail+1)
            except Warning as warn: # catch warnings as error
                self._logger.warn('pca() %s' % warn)
                if nb_dim <= 3:
                    result = np.identity(nb_dim)
                else:
                    result = self.robust_pca(np.identity(nb_dim), nb_fail=nb_fail+1)
        return result

    def __call__(self, layout):
        """ Process a PCA
        """
        if len(layout) > 0 and len(layout) != layout.dim:
            raise ValueError('The layout should have same number of vertices and dimensions')
        mat = np.array(layout.coords)
        if len(layout) == 0:
            result = []
        else:
            if layout.dim <= self.out_dim:
                result = np.hstack((mat, np.zeros((len(layout), self.out_dim - layout.dim)))).tolist()
            else:
                result = self.robust_pca(mat).tolist()

        return ig.Layout(result, dim=self.out_dim)


class ReduceRandProj(Composable):
    """ Reduce a layout dimention by a a random projection

    >>> import igraph as ig
    >>> layout = ig.Layout([[1, 0, 0, 0], [1, 1, 0, 0], [1, 0, 1, 0], [1, 0, 0, 1], [1, 0, 0, 0]])
    >>> layout
    <Layout with 5 vertices and 4 dimensions>

    >>> rproj = ReduceRandProj(dim=3)
    >>> rproj(layout)
    <Layout with 5 vertices and 3 dimensions>
    >>> rproj(ig.Layout([]))
    <Layout with no vertices and 2 dimensions>
    """
    #TODO use http://scikit-learn.org/stable/modules/random_projection.html
    def __init__(self, dim=3):
        super(ReduceRandProj, self).__init__()
        self.out_dim = dim

    def __call__(self, layout):
        """ Process the random projection
        """
        if len(layout) == 0:
            return layout
        mat = np.array(layout.coords)
        mat_r = sc.rand(layout.dim, self.out_dim)
        result = mat.dot(mat_r)
        return ig.Layout(result.tolist())


def normalise(layout):
    """ Normalize a :class:`igraph.Layout` between -0.5 and 0.5

    >>> import igraph as ig
    >>> import numpy as np
    >>> layout = ig.Layout([[10,  0,  0], [0,  10,  0], [0,   0,  0], [0,   0, 10], [0,  -10,  0]])
    >>> np.array(normalise(layout).coords).max()
    0.5
    >>> np.array(normalise(layout).coords).min()
    -0.5
    >>> normalise(ig.Layout([]))
    <Layout with no vertices and 2 dimensions>
    """
    if len(layout) == 0:
        return layout
    layout.fit_into([1.] * layout.dim)
    layout.center()
    return layout


class Shaker(Composable):
    """ 'Shake' a layout to ensure that no vertices have the same position

    >>> import igraph as ig
    >>> layout = ig.Layout([[1, 0], [1, 1], [1, 0]])
    >>> layout
    <Layout with 3 vertices and 2 dimensions>

    >>> shaker = Shaker(0.2)
    >>> layout = shaker(layout)
    >>> layout.coords
    [[-0.6666666666666666, -0.33333333333333337], [0.33333333333333337, 0.6666666666666666], [0.33333333333333337, -0.33333333333333337]]

    If the layout is empty:
    >>> shaker(ig.Layout())
    <Layout with no vertices and 2 dimensions>
    """
    def __init__(self, kelastic=0.3):
        """
        :param kelastic: coeficient d'elasticité: `force = kelastic * dlen`
        """
        super(Shaker, self).__init__(name='shake')
        self.kelastic = kelastic

    def shake(self, layout):
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
        dists_min = (sizes[:, None] + sizes[None, :]) / 2
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
                        force = self.kelastic * (dists_min[source, dest] - dists[source, dest])
                        deplacements[source, :] += - force * vect_depl
                        deplacements[dest, :] -= - force * vect_depl
            # mise a jour des positions
            layout_mat += deplacements

        layout = ig.Layout(layout_mat.tolist())
        layout = normalise(layout)
        return layout

    def __call__(self, layout):
        """ Process the shaking !
        """
        if len(layout) == 0:
            return layout
        return self.shake(layout)



class ByConnectedComponent(Optionable):
    """ Compute a given layout on each connected component, and then merge it.
    """
    def __init__(self, layout):
        self._layout_mth = layout
        # expose layout option
        if isinstance(self._layout_mth, Optionable):
            pass
            # TODO

    def __call__(self, graph, **kwargs):
        # split the graph in N connected components
        connected_components = graph.clusters()
        subgraphs = connected_components.subgraphs()
        # compute a list of vertex position (cc id, and id in subgraph)
        vertex_cc = []
        next_by_cc = [0] * len(connected_components)
        for cc_num in connected_components.membership:
            v_num = next_by_cc[cc_num]
            next_by_cc[cc_num] += 1
            vertex_cc.append((cc_num, v_num))
        # compute layout for each cc
        layout_mth = self._layout_mth
        layouts = [layout_mth(cc, **kwargs) for cc in subgraphs]
        # move each layout
        #TODO
        cc_graph = ig.Graph.Full()
        
        # merge layouts
        layout = [layouts[cc_num][v_num] for cc_num, v_num in vertex_cc]
        return ig.Layout(layout)


