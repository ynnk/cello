#-*- coding:utf-8 -*-
""" :mod:`cello.layout`
======================


SubModules
----------

.. toctree::

    cello.layout.simple
    cello.layout.prox
    cello.layout.transform

Helpers
-------
"""
import igraph as ig

from cello.layout.simple import KamadaKawaiLayout
from cello.layout.simple import GridLayout
from cello.layout.simple import RandomLayout
from cello.layout.simple import FruchtermanReingoldLayout

from cello.layout.prox import ProxLayoutPCA
from cello.layout.prox import ProxLayoutRandomProj
from cello.layout.prox import ProxBigraphLayoutPCA
from cello.layout.prox import ProxBigraphLayoutRandomProj


def export_layout(layout):
    """ Build a dictionary view of a layout

    >>> graph = ig.Graph.Formula("a--b--c--d, a--a")
    
    >>> from cello.layout import GridLayout
    >>> layout_builder = GridLayout(dim=2)
    >>> layout = layout_builder(graph)
    >>> export_layout(layout)
    {'coords': [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], 'desc': '<Layout with 4 vertices and 2 dimensions>'}
    
    :param layout: the layout to convert
    :type layout: list of coord or :class:`igraph.Layout`
    """
    return {
        'desc': str(layout),
        'coords': [coord for coord in layout]
    }

