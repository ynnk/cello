#!/usr/bin/env python
#-*- coding:utf-8 -*-
""" Carrot² "Document Clustering Server" interface
"""
import logging
import urllib

import igraph as ig

from cello.utils import urllib2_json_urlopen
from cello.clustering import ClusteringMethod

class Carrot2Clustering(ClusteringMethod):
    """ Carrot² "Document Clustering Server" wrapper
    """
    def __init__(self,
                name="carrot2",
                doc_title_attr="title",
                doc_url_attr=None,
                doc_terms_field='terms_filtered',
                server_url="http://localhost:8080"
            ):
        ClusteringMethod.__init__(self, name)
        self._logger = logging.getLogger("cello.clustering.Carrot2")
        self._server_url = server_url
        # doc transformation
        self._doc_title_attr = doc_title_attr
        self._doc_url_attr = doc_url_attr
        self._doc_terms_field = doc_terms_field
        # options
        self.add_enum_option(
            "algo",
            ["lingo", "stc", "kmeans"],
            "lingo",
            "Carrot2 algorithm to use",
            str
        )

    def _clustering(self, graph, algo="lingo"):
        url = self._server_url + "/dcs/rest"
        request_data = {}
        request_data["dcs.algorithm"] = algo
        request_data["dcs.output.format"] = "JSON"
        request_data["dcs.clusters.only"] = "true"
        #request_data["MultilingualClustering.defaultLanguage"] 

        docnum_to_vid = {}
        # prepare the xml
        doc_xml = []
        doc_xml.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
        doc_xml.append("<searchresult>")
        doc_xml.append("<query></query>")
        for vdoc in graph.vs.select(type=True):
            kdoc = vdoc["_doc"]
            carrot_docnum = int(kdoc.docnum)
            docnum_to_vid[carrot_docnum] = vdoc.index
            doc = []
            doc.append("<document id=\"%s\">" % carrot_docnum)
            # title and url
            if self._doc_title_attr is not None:
                doc.append("\t<title>%s</title>" % kdoc[self._doc_title_attr])
            if self._doc_url_attr is not None:
                doc.append("\t<url>%s</url>" % kdoc[self._doc_url_attr])
            else:
                doc.append("\t<url></url>")
            # snippet
            doc_snippet = []
            for term in kdoc.iter_field(self._doc_terms_field):
                doc_snippet.append(term.encode("utf8"))
            doc.append("\t<snippet>%s</snippet>" % " ".join(doc_snippet) )
            doc.append("</document>")
            doc_xml.append("\n".join(doc))
        doc_xml.append("</searchresult>")
        request_data["XmlDocumentSource.xml"] = "\n".join(doc_xml)
        request_data["dcs.c2stream"] = "\n".join(doc_xml)
        # run the query
        request_data = urllib.urlencode(request_data)
        results = urllib2_json_urlopen(url, request_data)
        # parse results
        clusters = []
        for carrot_cluster in results["clusters"]:
            clusters.append([docnum_to_vid[docnum] for docnum in carrot_cluster["documents"]])
        return ig.VertexCover(graph, clusters)


