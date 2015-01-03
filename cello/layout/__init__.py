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

def hsv_colors(n_colors, saturation=0.4, value=0.8):
    """ Helper, computes a set of colors for n clusters using hsv colors """ 
    colors = []
    for i in xrange(n_colors):
        colors.append( hsvToRgb((1.*i / n_colors * 360), saturation, value) )
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

