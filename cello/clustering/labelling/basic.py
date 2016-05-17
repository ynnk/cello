#-*- coding:utf-8 -*-
""" :mod:`cello.clustering.labelling.basic`
==========================================

Classes
-------
"""
# python 2 and 3 compatibility
#from __future__ import unicode_literals
import six

from itertools import chain
import igraph as ig

from reliure import Optionable, Composable
from reliure.types import Text

from cello.clustering.labelling import Label, LabelledVertexCover

class VertexAsLabel(Optionable):
    """ Create labels by transforming cluster vertices

    One can create a :class:`VertexAsLabel` this way:

    >>> vtx_to_label = lambda graph, cluster, vtx: None if vtx["name"].islower() else Label(vtx["name"], 1.2)
    >>> labeller = VertexAsLabel(vtx_to_label)

    and then use it:

    >>> g = ig.Graph.Formula("a--A:B:C, b--A:B, c--C:D")
    >>> vcover = ig.VertexCover(g, [[0,1,2,3,4], [5,3,6]])
    >>> vcover = labeller(vcover)
    >>> print(vcover)
    Cover with 2 clusters
    [0] a, A, B, C, b (labels: A, B, C)
    [1] c, C, D (labels: C, D)
    >>> vcover.labels[1]
    [Label('C', 1.2), Label('D', 1.2)]
    
    Here is an other example:

    >>> g = ig.Graph.Full(4)
    >>> vtx_to_label = lambda _, __, vtx: Label("--%s--" % vtx.index) if vtx.index % 2 == 0 else None
    >>> labeller = VertexAsLabel(vtx_to_label)
    >>> vcover = ig.VertexCover(g, [[0,1,2,3]])
    >>> vcover = labeller(vcover)
    >>> print(vcover)
    Cover with 1 clusters
    [0] 0, 1, 2, 3 (labels: --0--, --2--)

    It is also possible to generate more than one label per vertex :

    >>> vtx_to_label = lambda graph, cluster, vtx: (Label(cat, 1.) for cat in vtx["cat"])
    >>> labeller = VertexAsLabel(vtx_to_label)
    >>> g = ig.Graph.Formula("a, b, A, B, C, a--A:C, b--B")
    >>> g.vs["cat"] = [[], [], ["one", "two"], ["b", "Bé"], ["one", "three"]]
    >>> vcover = ig.VertexCover(g, [[0,2,4], [1,3]])
    >>> vcover = labeller(vcover)
    >>> print(vcover)
    Cover with 2 clusters
    [0] a, A, C (labels: one, two, one, three)
    [1] b, B (labels: b, Bé)

    .. note:: this class may also be use by inheritance, see
        :class:`TypeFalseLabel` for an example.

    But if `vtx_to_label` is given, it should be callable:

    >>> labeller = VertexAsLabel(vtx_to_label=True)
    Traceback (most recent call last):
    ...
    TypeError: argument 'vtx_to_label' should be None or sould be callable

    """
    def __init__(self, vtx_to_label=None, name=None):
        """ Build the labelling component.
        
        .. warning:: If `vtx_to_label` is not provided the method
            :func:`vtx_to_label` should be overriden.

        :param vtx_to_label: a function that should return either None or a
            :class:`.Label` object. This function take 3 argument : the graph 
            (:class:`igraph.Graph`), the cluster vertices indexes (a list of
            int) and a vertex object (:class:`igraph.Vertex`).
        :type vtx_to_label: `graph, cluster, vtx --> Label`
        """
        super(VertexAsLabel, self).__init__(name=name)
        if vtx_to_label is not None and not callable(vtx_to_label):
            raise TypeError("argument 'vtx_to_label' should be None or sould be callable")
        self._vtx_to_label = vtx_to_label

    def vtx_to_label(self, graph, cluster, vtx, **kwargs):
        """ Function used to transform a vertex to a label.
        
        This is called on each vertex of each cluster. If the vertex should not
        be transformed into a label, then it sould return `None`.
        
        :param graph: the graph 
        :type graph: :class:`igraph.Graph`
        :param cluster: the curent cluster (list of vectex indexes)
        :type cluster: list of int
        :param vtx: The vertex to transform into label (or not)
        :type vtx: :class:`igraph.Vertex`
        
        :returns: a :class:`.Label` object that correspond to `vtx` (or `None`)
        :rtyoe: None or :class:`.Label`
        
        Note that by default this method is not implemented:

        >>> labeller = VertexAsLabel()
        >>> g = ig.Graph.Formula("a--A:B:C, b--A:B, c--C:D")
        >>> labeller.vtx_to_label(g, [0,1,2], g.vs[0])
        Traceback (most recent call last):
        ...
        NotImplementedError
        """
        if self._vtx_to_label is not None:
            return self._vtx_to_label(graph, cluster, vtx, **kwargs)
        else:
            raise NotImplementedError

    @Optionable.check
    def __call__(self, vertex_cover, **kwargs):
        # if not labelled vertex cover transform it
        if not isinstance(vertex_cover, LabelledVertexCover):
            vertex_cover = LabelledVertexCover.FromVertexCover(vertex_cover)
        # compute labels for each cluster
        # keep ref for optimisation
        graph = vertex_cover.graph
        vs = graph.vs
        # use tuple either of list : more efficient
        astuple = lambda x: (x, ) if type(x) == Label else x
        for cid, cluster in enumerate(vertex_cover):
            alllabels = (astuple(self.vtx_to_label(graph, cluster, vs[vtx], **kwargs)) for vtx in cluster)
            labels = [label for labels in alllabels if labels is not None for label in labels if label is not None]
            vertex_cover.add_labels(cid, labels)
        return vertex_cover


class TypeFalseLabel(VertexAsLabel):
    """ Transform all `type=False` vertices of the cluster to label.

    :hide:
        >>> from pprint import pprint

    For exemple on the following bipartite graph:

    >>> g = ig.Graph.Formula("a--A:B:C, b--A:B, c--C:D")
    >>> g.vs["type"] = [vtx["name"].islower() for vtx in g.vs]

    one can build a labeller this way:

    >>> labeller = TypeFalseLabel(vtx_attr='name', role='terms')

    and use it this way:

    >>> vcover = ig.VertexCover(g, [[0,1,2,3,4], [5,3,6]])
    >>> vcover = labeller(vcover)
    >>> print(vcover)
    Cover with 2 clusters
    [0] a, A, B, C, b (labels: A, B, C)
    [1] c, C, D (labels: C, D)
    >>> vcover.labels[0]
    [Label('A', 1.0, role='terms'), Label('B', 1.0, role='terms'), Label('C', 0.5, role='terms')]
    >>> vcover.labels[1]
    [Label('C', 1.0, role='terms'), Label('D', 1.0, role='terms')]

    also note that the index of the original vertex is stored in each label:

    >>> vcover.labels[1][0].vtx
    3
    >>> pprint(g.vs[vcover.labels[1][0].vtx].attributes())
    {'name': 'C', 'type': False}

    One can chouse the scoring method with an option:

    >>> labeller.print_options()
    score (Text, default=recall, in: {recall, precision}): Label scoring method

    the scoring are this:

    * **precision**:  :math:`\\frac{|\Gamma(v)\,\cup\,C|}{|\Gamma(v)|}` where
      :math:`\Gamma(v)` is neighborooh of v, and :math:`C` is the set of cluster vertices.

    * **recall**: :math:`\\frac{|\Gamma(v)\,\cup\,C|}{|C_\\top|}` where
      :math:`\Gamma(v)` is neighborooh of v, :math:`C` is the set of cluster
      vertices, and :math:`C_\\top` the set of top-vertices (or True-vertices)
      of the cluster.

    Here is an exemple with precision score:

    >>> vcover = ig.VertexCover(g, [[0,1,2,3,4], [5,3,6]])
    >>> vcover = labeller(vcover, score=u"precision")
    >>> vcover.labels[1]
    [Label('C', 0.5, role='terms'), Label('D', 1.0, role='terms')]

    """
    def __init__(self, vtx_attr, role=None, name=None):
        """ Build the labelling component
        
        :attr vtx_attr: the vertex attribute to use as label string
        :type vtx_attr: str
        :attr role: the role of the created vertices
        :type role: str
        :attr name: the name of the component
        :type name: str
        """
        super(TypeFalseLabel, self).__init__(name=name)
        self.vtx_attr = vtx_attr
        self.role = role
        self.add_option("score", Text(
            default=u"recall", choices=[u"recall", u"precision"],
            help="Label scoring method"
        ))

    @staticmethod
    def scoring_prop_inclust(graph, cluster, vtx):
        """ precision: prop of neighbours that are in cluster
        """
        vois = set(nei.index for nei in vtx.neighbors())
        commun = vois.intersection(cluster)
        return len(commun) / (1.*len(vois))

    @staticmethod
    def scoring_prop_ofclust(graph, cluster, vtx):
        """ recall: prop of cluster doc that are in neighbours
        """
        cluster_doc = [1 for c in cluster if graph.vs[c]["type"]]
        if len(cluster_doc) == 0:
            return 0.
        vois = set(nei.index for nei in vtx.neighbors())
        commun = vois.intersection(cluster)
        return len(commun) / (1.*len(cluster_doc))

    def vtx_to_label(self, graph, cluster, vtx, score=None):
        label = None
        if not 'type' in graph.vs.attributes():
            raise ValueError("The graph should be bipartite, and have a 'type' attribute on each vertex")
        if not vtx['type']:
            if score == u"precision":
                wgt = TypeFalseLabel.scoring_prop_inclust(graph, cluster, vtx)
            else:
                wgt = TypeFalseLabel.scoring_prop_ofclust(graph, cluster, vtx)
            label = Label(vtx[self.vtx_attr], wgt, self.role)
            label.vtx = vtx.index
        return label


@Composable
def normalize_score_max(vertex_cover, **kwargs):
    for cid, vertices in enumerate(vertex_cover):
        labels = vertex_cover.labels[cid]
        _max = max([ l.score for l in labels ])
        for label in labels:
            label.score = label.score / _max
    return vertex_cover
