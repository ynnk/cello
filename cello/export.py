#-*- coding:utf-8 -*-
""" :mod:`cello.export`
========================
"""
from cello.schema import Doc, Numeric

def export_docs(kdocs, exclude=[]):
    """ Transform the list of kdoc

    remove all the attributes of KodexDoc that are not fields (of elements) or elements attributes
    """
    return [doc.as_dict(exclude=exclude) for doc in kdocs]


def export_graph(graph):
    """ Transform a graph (igraph graph) to a dictionary
    to send it to template (or json)


    :param graph: the graph to transform
    :type graph: :class:`igraph.Graph`
    """
    import igraph
    # create the graph dict
    graph_dict = {}
    graph_dict['vs'] = []
    graph_dict['es'] = []
    graph_dict['attributes'] = {}
    # check argument
    if not isinstance(graph, igraph.Graph):
        return graph_dict
    # default graph attrs
    graph_dict['attributes']['directed'] = graph.is_directed()
    graph_dict['attributes']['bipartite'] = 'type' in graph.vs and graph.is_bipartite() 
    # vertices
    for vtx in graph.vs:
        vertex = vtx.attributes()
        # colors still needs some conversion to r;g;b 255
        vertex["color"] = vertex.get("color", (99,99,99)) # ";".join([ "%s" % int(255*c) for c in vertex.get("color", (0.2,0.2,0.2)) ])
        # transformation des Kodex_Doc en docnum
        if "_doc" in vertex and isinstance(vertex["_doc"], Doc):
            docnum = vertex["_doc"].docnum
            vertex["docnum"] = docnum
            del vertex["_doc"]
        else:
            vertex["docnum"] = None
        
        # transformation des Kodex_LU en 'form"
        #~ if "kodex_LU" in vertex and isinstance(vertex["kodex_LU"], KodexLU):
            #~ form = vertex["kodex_LU"].form
            #~ vertex["klu_form"] = form
            #~ del vertex["kodex_LU"]
        #~ else:
            #~ vertex["klu_form"] = None
        graph_dict['vs'].append(vertex)
    # edges
    for edg in graph.es:
        #TODO pourquoi pas partir de edg.attributes()
        edge = {}
        edge["s"] = edg.source
        edge["t"] = edg.target
        edge["w"] = edg["weight"]
        # recopier tous les attributs
        edge.update({
            attr_name: edg[attr_name] for attr_name in graph.es.attribute_names()
        })
        #TODO check il n'y a pas de 's' 't' ou 'w' dans attr
        graph_dict['es'].append(edge)
    return graph_dict


def export_clustering(vertex_cover):
    """ Build a dictionary view of a vertex cover (a clustering)
    
    .. Note:: for each cluster 'docnums' are extracted from vertices that have a
    (not None) '_doc' attribute
    
    .. code-block:: js

        [
            {
                'gids': [1, 3, 5, 8],
                'docnums': [u'docnum_1', ...]
                'misc': False,
            },
            ...
        ]
    
    :param vertex_cover: the vertex cover to convert
    :type vertex_cover: :class:`igraph.VertexCover`
    
    >>> import igraph as ig
    >>> g = ig.Graph.Formula("a--b, a--c, a--d")
    >>> from cello.schema import Doc
    >>> g.vs['_doc'] = None
    >>> g.vs[0]['_doc'] = Doc(docnum=45526)
    >>> g.vs[2]['_doc'] = Doc(docnum=8886)

    >>> from cello.clustering import MaximalCliques
    >>> clustering = MaximalCliques()
    >>> cover = clustering(g)
    >>> export_clustering(cover)
    [{'docs': [45526], 'misc': False, 'gids': [0, 3]}, {'docs': [45526, 8886], 'misc': False, 'gids': [0, 2]}, {'docs': [45526], 'misc': False, 'gids': [0, 1]}]
    """
    clusters = []
    if hasattr(vertex_cover, "misc_cluster") : # "misc" cluster id
        misc_cluster = vertex_cover.misc_cluster
    else: # pas de "misc"
        misc_cluster = -1

    gid_to_doc = None
    if hasattr(vertex_cover, 'graph') and '_doc' in vertex_cover.graph.vs.attributes():
        gid_to_doc = {gid: doc.docnum \
            for gid, doc in enumerate(vertex_cover.graph.vs['_doc']) \
            if doc is not None
        }

    for cnum, gids in enumerate(vertex_cover):
        cluster = {}
        # is misc ?
        cluster['misc'] = cnum == misc_cluster
        cluster['gids'] = gids
        # doc ?
        cluster['docs'] = []
        if gid_to_doc:
            cluster['docs'] = [gid_to_doc[gid] for gid in gids if gid in gid_to_doc]
        # add the cluster
        clusters.append(cluster)

    return clusters

def prepare_clustering(vertex_cover, docs, graph):
    """ Run the clustering method on the graph
    
    .. note:: arguments should be setted according to the clustering object options.
    .. seealso:: L{cello.clustering}
    """
    # clusters = {cluster_id:{"docs":[KodexDoc, ...], "terms":[KodexLU, ...]}, ...}
    clusters = {}
    if hasattr(vertex_cover, "misc_cluster") : # "misc" cluster id
        misc_cluster = vertex_cover.misc_cluster
    else: # pas de "misc"
        misc_cluster = -1
    # save the cluster membership of each document
    if docs:
        for doc in docs:
            if not "clusters" in doc.schema : doc["clusters"] = Numeric(multi=True)
            
    ### construction du dictionaire 'self.clusters'
    for k, vids in enumerate(vertex_cover):
        if k == misc_cluster: k = 9998
        clusters[k] = {}
        # Liste des sommets (docs and terms) du clusters
        nodes = graph.vs[set(vids)]
        # documents
        clusters[k]['docs'] = nodes.select(type=True)["_doc"]
        # terms
        terms = nodes.select(type=False)
        if len(terms) and "kodex_LU" in graph.vs.attribute_names():
            clusters[k]['terms'] = terms["kodex_LU"]
        else:
            clusters[k]['terms'] = []
        # labels
        clusters[k]['labels'] = {}
        # ajoute l'info sur le cluster dans le documents
        if docs :
            for doc in clusters[k]['docs']:
                doc.clusters.append(k)

    clustering = {}
    cluster_list = []
    cluster_misc = {}
    for cluster_id, cluster in clusters.iteritems():
        new_cluster = {}
        new_cluster["docnums"] = [kdoc.docnum for kdoc in cluster["docs"]]
        labels = {}
        for name, data  in cluster["labels"].iteritems():
            labels[name] = {}
            labels[name]['models'] = [(klu.form, score) for klu, score in data['models'] ]
        new_cluster["labels"] = labels
        if cluster_id == 9998: #XXX: ce 9998 ici ca ne va pas !
            cluster_misc = new_cluster
        else:
            cluster_list.append((cluster_id, new_cluster))
    cluster_list.sort()
    clustering["clusters"] = [cluster for _, cluster in cluster_list]
    clustering["misc"] = cluster_misc

    return clustering
