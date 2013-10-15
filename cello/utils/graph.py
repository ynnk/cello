#-*- coding:utf-8 -*-


def random_vertex(graph, attr=None, from_edges=False):
    """ return a random vertex of the given graph

    @param attr: if not None return the attribute 'attr' of the random vertex, instead of the id (of the random vertex).
    @param from_edges: if True get an edges by random and then pick one of the ends of the edge by random
    """
    if from_edges:
        # random edge
        es = random.choice(graph.es)
        vid = random.choice([es.source, es.target])
    else:
        # random node
        vid = random.choice(xrange(self.graph.vcount()))
    # return attr or vid
    if attr is not None:
        return self.graph.vs[vid][attr]
    else:
        return vid
