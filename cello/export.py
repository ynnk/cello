#-*- coding:utf-8 -*-
from cello.schema import Doc, Numeric

def export_docs(kdocs, exclude=[]):
    """ Transform the list of kdoc

    remove all the attributes of KodexDoc that are not fields (of elements) or elements attributes
    """
    return [doc.as_dict(exclude=exclude) for doc in kdocs]

def export_graph(graph):
    """ Transform a graph (igraph graph) to a dictionary
    to send it to template (or json)

    """
    graph_dict = {}
    graph_dict['vs'] = []
    graph_dict['es'] = []
    graph_dict['attributes'] = {}
    import igraph
    if isinstance(graph, igraph.Graph) == False :  return graph_dict

    graph_dict['attributes']['directed'] = graph.is_directed()
    graph_dict['attributes']['bipartite'] = 'type' in graph.vs and graph.is_bipartite() 
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
    for edg in graph.es:
        edge = {}
        edge["s"] = edg.source
        edge["t"] = edg.target
        edge["w"] = edg["weight"] #TODO: recopier tous les attributs
        edge.update({ k:edg[k] for k in graph.es.attribute_names() })
        graph_dict['es'].append(edge)
    return graph_dict


def export_layout(layout):
    return {'desc': str(layout),
            'coords':[ coord for coord in layout ]
        }


def prepare_clustering(vertex_cover, docs, graph):
    """ Run the clustering method on the graph
    @note: arguments should be setted according to the clustering object options.
    @see: L{cello.clustering}
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