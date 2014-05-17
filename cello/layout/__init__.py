#-*- coding:utf-8 -*-
""" :mod:`cello.layout`
======================


SubModules
----------

.. toctree::

    cello.layout.simple
    cello.layout.proxlayout
    cello.layout.transform

Helpers
-------
"""


def export_layout(layout):
    """ Build a dictionary view of a layout

    >>> import igraph as ig
    >>> graph = ig.Graph.Formula("a--b--c--d, a--a")
    
    >>> from cello.layout.simple import GridLayout
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

