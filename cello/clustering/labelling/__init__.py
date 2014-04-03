#-*- coding:utf-8 -*-
""" :mod:`cello.clustering.labelling`
=====================================

SubModules
----------

.. toctree::

    cello.clustering.labelling.basic


Labelling data models
---------------------
"""

import igraph as ig

class Label(object):
    """ Basic cluster label object
    
    >>> label = Label("black cat", score=1.2, role="animals")
    >>> label
    Label('black cat', 1.2, role='animals')
    >>> str(label)
    'black cat'

    Note that role is optional:

    >>> label = Label("black bird", score=1.5)
    >>> label
    Label('black bird', 1.5)
    """
    #TODO gestion utf8 / unicpde
    
    # should we restrict the Label object to following attr ?
    #__slot__ = ['label', 'score', 'role']

    def __init__(self, label, score=1., role=None):
        """
        :param label: the label it self
        :type label: str in utf8
        :param score: score of the label
        :type score: float
        :param role: optional category of the label
        :type role: str in utf8
        """
        self.label = label
        self.score = score
        self.role = role

    def __str__(self):
        return self.label

    def __repr__(self):
        lrepr = ["'%s'" % self.label, '%s' % self.score]
        if self.role is not None:
            lrepr.append("role='%s'" % self.role)
        return "Label(%s)" % (", ".join(lrepr))


class LabelledVertexCover(ig.VertexCover):
    """ :class:`igraph.VertexCover` with labels on clusters.

    >>> g = ig.Graph.Formula("a--A:B:C, b--A:B, c--C:D")
    >>> vcover = LabelledVertexCover(g, [[0,1,2,3,4], [5,3,6]])
    >>> vcover.add_label(0, Label("cluster one", score=1, role='demo'))
    >>> vcover.add_label(0, Label("other label", score=0.5, role='demo'))
    >>> vcover.add_label(1, Label("cluster two", score=2, role='demo'))
    >>> print(vcover)
    Cover with 2 clusters
    [0] a, A, B, C, b (labels: cluster one, other label)
    [1] c, C, D (labels: cluster two)
    >>> vcover.labels[0]
    [Label('cluster one', 1, role='demo'), Label('other label', 0.5, role='demo')]

    """
    def __init__(self, graph, clusters=None, labels=None):
        super(LabelledVertexCover, self).__init__(graph, clusters=clusters)
        self._labels = [[] for _ in xrange(len(clusters))]
        #note: on peut ajouter/enlevé des labels sur chaque clusters, mais si
        #on veux modifier le clustering il faut faire une nouvel VertexCover

    @property
    def labels(self):
        """ List of list of labels (on list of labels for each cluster)
        """
        return self._labels

    def add_labels(self, cid, labels):
        """ Add a list of labels to one cluster

        :param cid: cluster id
        :type cid: int
        :param labels: the labels to add
        :type labels: list of :class:`.Label`
        """
        for label in labels:
            self.add_label(cid, label)

    def add_label(self, cid, label):
        """ Add one label to one cluster
        
        >>> g = ig.Graph.Formula("a--A:B:C, b--A:B, c--C:D")
        >>> vcover = LabelledVertexCover(g, [[0,1,2,3,4], [5,3,6]])
        >>> vcover.add_label(0, Label("cluster one", score=1, role='demo'))
        >>> vcover.labels[0]
        [Label('cluster one', 1, role='demo')]

        Warning the `label` should be a :class:`.Label`:

        >>> vcover.add_label(0, "cluster one")
        Traceback (most recent call last):
        ...
        TypeError: label should be a Label object


        :param cid: cluster id
        :type cid: int
        :param label: a label to append
        :type label: :class:`.Label`
        """
        if not isinstance(label, Label):
            raise TypeError("label should be a Label object")
        self._labels[cid].append(label)

    def _formatted_cluster_iterator(self):
        """Iterates over the clusters and formats them into a string to be
        presented in the summary.
        """
        if self._graph.is_named():
            names = self._graph.vs["name"]
            for cid, cluster in enumerate(self):
                vertices = ", ".join(str(names[member]) for member in cluster)
                labels = "(labels: %s)" % (", ".join(map(str, self.labels[cid])))
                yield "%s %s" % (vertices, labels)
        else:
            for cid, cluster in enumerate(self):
                vertices = ", ".join(str(member) for member in cluster)
                labels = "(labels: %s)" % (", ".join(map(str, self.labels[cid])))
                yield "%s %s" % (vertices, labels)
