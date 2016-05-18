#-*- coding:utf-8 -*-
""" :mod:`cello.clustering.labelling.model`
===========================================

Labelling data models
---------------------
"""
import six
from builtins import range

import igraph as ig

class Label(object):
    """ Basic cluster label object
    
    >>> label = Label(u"black cat", score=1.2, role="animals")
    >>> label
    Label(u'black cat', 1.2, role='animals')
    >>> str(label)
    'black cat'

    Note that role is optional:

    >>> label = Label("black bird", score=1.5)
    >>> label
    Label('black bird', 1.5)
    """
    # should we restrict the Label object to following attr ?
    #__slot__ = ['label', 'score', 'role']
    labelid = 0

    def __init__(self, label, score=1., role=None):
        """
        :param label: the label it self
        :type label: unicode
        :param score: score of the label
        :type score: float
        :param role: optional category of the label
        :type role: str in utf8
        
        .. warning:: If the given label is not in unicode it will be decode from
            utf8 by default
        """
        if six.PY2 and not isinstance(label, unicode):
            label = label.decode("utf8")
        self.label = label
        self.score = score
        self.role = role
        self._id = Label.labelid
        Label.labelid += 1

    @property
    def id(self):
        return self._id

    def __str__(self):
        if six.PY2:
            return self.label.encode("utf8")
        else:
            return self.label

    def __repr__(self):
        lrepr = []
        lrepr.append("u'%s'" % str(self))
        lrepr.append('%s' % self.score)
        if self.role is not None:
            lrepr.append("role='%s'" % self.role)
        return "Label(%s)" % (", ".join(lrepr))

    def as_dict(self, full=False):
        """ returns a serialisable copy of the label (ie a dict)
        
        :param full: if True also return the uniq id of the label

        :hide:
            >>> from pprint import pprint
        
        >>> label = Label("black bird", score=1.5)
        >>> pprint(label.as_dict())
        {'label': 'black bird', 'role': None, 'score': 1.5}

        Note that attributs that are violently added during the object life are
        also exported :
        
        >>> label.tf = 25
        >>> pprint(label.as_dict())
        {'label': 'black bird', 'role': None, 'score': 1.5, 'tf': 25}

        But not if that attributes starts by `_`

        >>> label._id = 42
        >>> pprint(label.as_dict())
        {'label': 'black bird', 'role': None, 'score': 1.5, 'tf': 25}

        """
        lcopy = {}
        lcopy.update({attr: value for attr, value in six.iteritems(self.__dict__)\
                        if not attr.startswith('_')})
        if full:
            lcopy["id"] = self._id
        return lcopy


class LabelledVertexCover(ig.VertexCover):
    """ Sub class of :class:`igraph.VertexCover` with labels on clusters.

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
    [Label(u'cluster one', 1, role='demo'), Label(u'other label', 0.5, role='demo')]
    """
    def __init__(self, graph, clusters=None, labels=None, misc_cluster=None):
        super(LabelledVertexCover, self).__init__(graph, clusters=clusters)
        self.misc_cluster = misc_cluster
        self._labels = [[] for _ in range(len(clusters))]
        self._label_set = {}
        #note: on peut ajouter/enlevé des labels sur chaque clusters, mais si
        #on veux modifier le clustering il faut faire une nouvel VertexCover

    @staticmethod
    def FromVertexCover(cover):
        """ Create a  :class:`LabelledVertexCover` from a  :class:`igraph.VertexCover`
        
        >>> g = ig.Graph.Formula("a--A:B:C, b--A:B, c--C:D")
        >>> vcover = ig.VertexCover(g, [[0,1,2,3,4], [5,3,6]])
        >>> print(vcover)
        Cover with 2 clusters
        [0] a, A, B, C, b
        [1] c, C, D
        >>> lvcover = LabelledVertexCover.FromVertexCover(vcover)
        >>> print(lvcover)
        Cover with 2 clusters
        [0] a, A, B, C, b (labels: )
        [1] c, C, D (labels: )

        """
        misc_cluster = -1
        if hasattr(cover, "misc_cluster"):
            misc_cluster = cover.misc_cluster
        return LabelledVertexCover(cover.graph, cover, misc_cluster=misc_cluster)

    @property
    def labels(self):
        """ List of list of labels (on list of labels for each cluster)
        """
        lall = self._label_set
        return [[lall[lid] for lid in labellist] for labellist in self._labels]

    def all_labels(self):
        """ Retunrs all the labels (present at least in one cluster)
        """
        return self._label_set.values()

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
        if label.id not in self._label_set:
            self._label_set[label.id] = label
        self._labels[cid].append(label.id)

    def _formatted_cluster_iterator(self):
        """Iterates over the clusters and formats them into a string to be
        presented in the summary.
        """
        if self._graph.is_named():
            names = self._graph.vs["name"]
        else:
            names = range(self._graph.vcount())
        for cid, cluster in enumerate(self):
            misc = "{Misc}" if cid == self.misc_cluster else ""
            vertices = ", ".join(str(names[member]) for member in cluster)
            labels_str = ", ".join(str(label) for label in self.labels[cid])
            labels = "(labels: %s)" % (labels_str)
            yield "%s%s %s" % (misc, vertices, labels)

