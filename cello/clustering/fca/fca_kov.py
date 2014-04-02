#!/usr/bin/env python
#-*- coding:utf-8 -*-
""" Formal Concept Analysis (FCA) using algorithm proposed in :

P. Krajca, J. Outrata, and V. Vychodil, “Computing Formal Concepts by Attribute Sorting,” Fundamenta Informaticae, vol. 115, no. 4, p. 395–417, 2012.
"""

import sys
import igraph as ig

class RContext:
    """ R-Context object
    """
    def __init__(self, context, objs, attrs):
        self._context = context
        self.objs = objs
        self.attrs = attrs
        self._attr_scores = None

    def compute_scores(self):
        scores = [(Y, len([1 for obj in self.objs if self._context.connected(obj, Y)]) )
                   for _, Y in self.attrs]
        scores.sort(key=lambda x: x[1])

        self._attr_scores = dict((Y, s) for s, (Y, _) in enumerate(scores))

    def score(self, attr):
        if self._attr_scores is None:
            self.compute_scores()
        return self._attr_scores[attr]

    def clarification(self):
        new_attrs = {}
        for attr in self.attrs:
            sign = ".".join(str(obj) for obj in self.objs if self._context.connected(obj, attr[1]))
            new_attrs[sign] = new_attrs.get(sign, [])
            new_attrs[sign].append(attr)
        
        new_attrs = [(sum(n for n, _ in elems), frozenset(attr for _, attrs in elems for attr in attrs))
                        for elems in new_attrs.itervalues()]

        self.attrs = new_attrs

    def remove_connected_to_all(self):
        new_attrs = []
        removed_attrs = []
        for attr in self.attrs:
            nb_vois = len([1 for obj in self.objs if self._context.connected(obj, attr[1])])
            if nb_vois == len(self.objs):
                removed_attrs.append(attr)
            else:
                new_attrs.append(attr)
        self.attrs = new_attrs
        return removed_attrs


################################################################################
class AbstractKOV:
    def __init__(self):
        self._level = 0
        self.result = []

    def debug(self, msg):
        #print("  " * self._level + " " + msg)
        pass

    def connected(self, obj, attrs):
        """ True if *obj* verify all *attrs*
        """
        raise NotImplementedError

    def score(self, attrs, rcontext=None):
        """ Number of objs (in the sub relation) verifing all *attrs*
        """
        raise NotImplementedError

    def get_initial_rcontext(self, no_sort=False):
        raise NotImplementedError

    def get_obj_names(self, objs):
        raise NotImplementedError

    def get_attr_names(self, attrs):
        raise NotImplementedError

    def all_attr(self):
        raise NotImplementedError

    ###
    def score(self, attrs, rcontext):
        return rcontext.score(attrs)


    def krajca_compute(self, rcontext):
        self._level += 1
        self.debug("<<< enter Compute")
        union_attrs = frozenset(elem for _, attr in rcontext.attrs for elem in attr)
        
        c_objs = tuple(rcontext.objs)
        c_attrs = tuple(attr for attr in self.all_attr() if attr not in union_attrs)
        self.result.append((c_objs, c_attrs))
        self.debug("Store: <{%s}, {%s}> #" % (
                        ", ".join(self.get_obj_names(c_objs)),
                        ", ".join(self.get_attr_names(c_attrs))
                    ))

        for n, attr in rcontext.attrs:
            if n == 0:
                self.debug("Select (%d, %s) " % (n, attr))
                C, D = self.krajca_closure(rcontext, (n, attr))
                self.debug("set <C, D> = <{%s}, %s>" % (", ".join(self.get_obj_names(C)), D))
                if sum(n for (n, _) in D) == 0:
                    new_rcontext = self.krajca_reduce(rcontext, C, D)
                    self.krajca_compute(new_rcontext)
                else:
                    self.debug("failure")
        self.debug("exit Compute >>>")
        self._level -= 1

    def krajca_closure(self, rcontext, Ynew):
        C = [obj for obj in rcontext.objs if self.connected(obj, Ynew[1])]
        
        D = [attr for attr in rcontext.attrs if self.score(Ynew[1], rcontext) <= self.score(attr[1], rcontext)]
        for obj in C:
            D = [attr for attr in D if self.connected(obj, attr[1])]
        return C, D


    def krajca_reduce(self, rcontext, C, D):
        objs = C
        Dmin = min(self.score(attrs, rcontext) for (n, attrs) in D)
        self.debug("Dmin: %s" % Dmin)
        def new_val(attr):
            n, B = attr
            #self.debug("(%d, %s) f = %d" % (n, B, self.score(B, rcontext[0])))
            if n == 0 and self.score(B, rcontext) < Dmin:
                return (len(B), B)
            else:
                return (n, B)
        attrs = [new_val(attr) for attr in rcontext.attrs if attr not in D]
        new_rcontext = RContext(self, objs, attrs)
        new_rcontext.clarification()
        #self.debug("new rcontext: (%s, %s)" % new_rcontext)
        return new_rcontext


    def krajca(self):
        self._level = 0
        self.result = []
        # setp 1
        rcontext = self.get_initial_rcontext()
        # step 2 merge identical attrs
        rcontext.clarification()
        #step 3: compute concepts
        removed = rcontext.remove_connected_to_all()
        self.krajca_compute(rcontext)
        #TODO: step 4 cas ou l'un des meta_attr couvre tt le monde
        return set(self.result)


################################################################################
class DenseContextKOV(AbstractKOV):
    def __init__(self, relation, obj_names, attr_names):
        AbstractKOV.__init__(self)

        self._nb_obj = len(relation)
        self._nb_attr = len(relation[0])
        
        assert self._nb_obj == len(obj_names)
        assert self._nb_attr == len(attr_names)
        
        self._relation = relation
        self._obj_names = obj_names
        self._attr_names = attr_names

    def to_igraph(self):
        vertex_attrs = {}
        vertex_attrs["type"] = [True] * self._nb_obj + [False] * self._nb_attr
        vertex_attrs["name"] = self._obj_names + self._attr_names
        edges = [(obj, self._nb_obj + attr) for obj, robj in enumerate(self._relation) for attr, val in enumerate(robj) if val]

        graph = ig.Graph(n=self._nb_obj + self._nb_attr,
                         edges = edges,
                         directed=False,
                         vertex_attrs=vertex_attrs,
                        )
        return graph

    def connected(self, obj, attrs):
        """ True if *obj* verify all *attrs*
        """
        robj = self._relation[obj]
        return all(robj[attr] for attr in attrs)

    def get_initial_rcontext(self):
        objs = range(self._nb_obj)
        attrs = [(0, frozenset([attr])) for attr in range(self._nb_attr)]
        sort_fct = lambda val: len([1 for obj in xrange(self._nb_obj) if self.connected(obj, val[1])])
        attrs.sort(key=sort_fct)
        return RContext(self, objs, attrs)

    def get_obj_names(self, objs):
        return (self._obj_names[obj] for obj in objs)
        
    def get_attr_names(self, attrs):
        return (self._attr_names[attr] for attr in attrs)

    def all_attr(self):
        return range(self._nb_attr)

################################################################################

class IGraphKOV(AbstractKOV):
    def __init__(self, graph, name_vattr="name"):
        AbstractKOV.__init__(self)

        assert graph.is_bipartite
        assert "type" in graph.vs.attributes()

        self._graph = graph
        self._name_vattr = name_vattr
        
        self._objs =  [vtx.index for vtx in graph.vs.select(type=True)]
        self._attrs = [vtx.index for vtx in graph.vs.select(type=False)]

        self._nb_obj = len(self._attrs)
        self._nb_attr = len(self._objs)


    def connected(self, obj, attrs):
        """ True if *obj* verify all *attrs*
        """
        return all(self._graph.are_connected(obj, attr) for attr in attrs)


    def get_initial_rcontext(self, no_sort=False):
        attrs = [(0, frozenset([attr])) for attr in self._attrs]
        if not no_sort:
            sort_fct = lambda val: self._graph.degree(list(val[1])[0]) #XXX
            attrs.sort(key=sort_fct)
        return RContext(self, self._objs, attrs)

    def get_obj_names(self, objs):
        if self._name_vattr in self._graph.vs.attributes():
            return (self._graph.vs[obj][self._name_vattr] for obj in objs)
        else:
            return (str(obj) for obj in objs)
        
    def get_attr_names(self, attrs):
        return self.get_obj_names(attrs)

    def all_attr(self):
        return self._attrs

def compute_concepts_kov(bigraph):
    """ Compute the concepts of the given bigraph using the KOV algorithm
    """
    R = IGraphKOV(bigraph)
    res = R.krajca()
    return res


################################################################################
from cello.graphs.builder import GraphBuilder

class ConceptsBigraph(GraphBuilder):
    def __init__(self):
        GraphBuilder.__init__(self, False)
        self.declare_vattr("type") # True: object, False: concepts
        self.declare_vattr("concept")
        # edges attributes
        self.declare_eattr("nbp")
        self.declare_eattr("nbo")
        self.declare_eattr("dot")

    def _parse(self, bigraph):
        concepts = compute_concepts_kov(bigraph)
        # add the objects
        for vtx in bigraph.vs.select(type=True):
            gid_obj = self.add_get_vertex(vtx.index)
            assert gid_obj == vtx.index, "Object id (%d) different from old id (%d)" % (gid_obj, vtx.index)
            self.set_vattr(gid_obj, "type", True)
        nb_concepts = 0
        for cid, concept in enumerate(concepts):
            objs, props = concept
            if len(objs) == 0 or len(props) == 0:
                continue
            gid_concept = self.add_get_vertex("c%d" % cid)
            self.set_vattr(gid_concept, "type", False)
            self.set_vattr(gid_concept, "concept", concept)
            for obj in objs:
                gid_obj = self.add_get_vertex(obj)
                eid = self.add_get_edge(gid_concept, gid_obj)
                self.set_eattr(eid, "nbo", len(objs))
                self.set_eattr(eid, "nbp", len(props))
                self.set_eattr(eid, "dot", len(props)*len(objs))
            nb_concepts += 1
        self.set_gattr("nb_concepts", nb_concepts)


def build_concept_bigraph(bigraph):
    gbuilder = ConceptsBigraph()
    return gbuilder.build_graph(bigraph)

################################################################################
################################################################################
def main():
    from pprint import pprint
    R = DenseContextKOV(
        [[0,1,1], #a
         [1,1,1], #b
        ],
         ["a","b"],         # obj
         ["0", "1", "2" ]  # attr
        )
    res = R.krajca()
    pprint(res)
    return 
    
    R = DenseContextKOV(
        [[0,1,1,1,0,0], #a
         [1,1,0,0,0,1], #b
         [0,1,0,1,1,0], #c
         [1,0,1,0,1,0], #d
        ],
         ["a","b","c","d"],         # obj
         ["0", "1", "2", "3", "4", "5"]  # attr
        )

    good_res = set([((), (0, 1, 2, 3, 4, 5)),
     ((0,), (1, 2, 3)),
     ((0, 1, 2), (1,)),
     ((0, 1, 2, 3), ()),
     ((0, 2), (1, 3)),
     ((0, 3), (2,)),
     ((1,), (0, 1, 5)),
     ((1, 3), (0,)),
     ((2,), (1, 3, 4)),
     ((2, 3), (4,)),
     ((3,), (0, 2, 4))])


    res = R.krajca()
    pprint(res)
    assert res == good_res

    graph = R.to_igraph()
    res = compute_concepts_kov(graph)
    pprint(res)
    assert res == good_res


if __name__ == '__main__':
    sys.exit(main())



