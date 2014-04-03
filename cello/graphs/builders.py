#!/usr/bin/env python
#-*- coding:utf-8 -*-
""" Graph creation objects.

G{classtree AbstractGraphBuilder}
"""

import logging

from bisect import bisect
import igraph as ig

import cello.graphs.prox 
from cello.graphs import GraphBuilder, AbstractGraphBuilder, EDGE_WEIGHT_ATTR 

logger = logging.getLogger("cello.builders")


#{ Graph builders

class Scoring():
    @staticmethod    
    def one(termset, term, doc):
        return 1
            
class AbstractSetGraph(AbstractGraphBuilder):
    EDGE_WEIGHT_ATTR = "weight"
    
    def __init__(self, copy_tops=[], copy_bottoms=[], weight_attr=None, name="TermSetGraph"):
        AbstractGraphBuilder.__init__(self, self.__class__.__name__, directed=False)
        self._logger = logging.getLogger(self.__class__.__name__)
        self.copy_tops = copy_tops or []
        self.copy_bottoms = copy_bottoms or []
        self.weight_attr = weight_attr or self.EDGE_WEIGHT_ATTR
        
        self.declare_vattr("type")
        self.declare_vattr("label")
        self.declare_vattr("color")
        self.declare_vattr("_doc")
        
        for k in copy_tops: 
            self.declare_vattr(k)
        for k in copy_bottoms: 
            self.declare_vattr(k)
        self.declare_eattr(EDGE_WEIGHT_ATTR)
        
    

class FieldSetGraph(AbstractSetGraph):
    """
    Build a graph from a field 
    """
    # TODO handle scoring
    
    def __init__(self, *field_names, **kwargs):
        AbstractSetGraph.__init__(self,  **kwargs)
        self.field_names = field_names
        
    def _parse(self, docs ):
        copy_tops = self.copy_tops
        copy_bottoms = self.copy_bottoms
        fnames = self.field_names
        weight_attr = self.weight_attr
        edge_score = Scoring.one
        
        for doc in docs:
            doc_gid = self.add_get_vertex( (True, doc.docnum) )
            self.set_vattr(doc_gid, "_doc", doc)
            self.set_vattr(doc_gid, "type", True)            
            self.set_vattr(doc_gid, "color", (255,0,0) )
            self.set_vattr(doc_gid, "label", doc.title)
            for k in copy_tops:
                self.set_vattr(doc_gid, k, doc[k])
                
        for doc in docs:
            doc_gid = self.add_get_vertex((True, doc.docnum))
            for fname in fnames:
                termset = doc[fname]
                for term in termset:
                    term_gid = self.add_get_vertex((False, term))
                    self.set_vattr(term_gid, "type", False)
                    self.set_vattr(term_gid, "color", (0,0,255))
                    self.set_vattr(term_gid, "label", term)
                    for k in copy_bottoms:
                        self.set_vattr(term_gid, k, term[k])
                    # add edge with score
                    eid = self.add_get_edge(doc_gid, term_gid)
                    self.set_eattr(eid, weight_attr, edge_score(termset, term, doc) )
            

class TermSetGraph(AbstractSetGraph):
    """
    Build a graph from a termset.
    Termset contains 
    By convention and for reusability we suppose that 
     * Documents are type True vertices (should it be int ? to handle tripartite ?)
     * Terms are type false vertices. 
    """
    def __init__(self, **kwargs):
        AbstractSetGraph.__init__(self,  **kwargs)

    def _parse(self, termset, weighted=True, **kwargs):
        """ Private methode called by self.build_graph().
        """
        copy_tops = self.copy_tops
        copy_bottoms = self.copy_bottoms
        weight_attr = self.weight_attr
        
        edge_score = Scoring.one

        # add top vertices aka docs
        for term in termset:
            for doc in termset[term].postings:
                doc_gid = self.add_get_vertex((True, doc.docnum))
                self.set_vattr(doc_gid, "_doc", doc)
                self.set_vattr(doc_gid, "type", True)            
                self.set_vattr(doc_gid, "color", "#00F")
                self.set_vattr(doc_gid, "label", doc.title[:10])
                for k in copy_tops:
                    self.set_vattr(doc_gid, k, doc[k])
        # add bottoms (terms) and edges
        for term in termset:
            term_gid = self.add_get_vertex((False, term))
            self.set_vattr(term_gid, "type", False)
            self.set_vattr(term_gid, "color", "#F00")
            self.set_vattr(term_gid, "label", term)
            for k in copy_bottoms:
                self.set_vattr(term_gid, k, term[k])
                
            for doc in termset[term].postings:
                doc_gid = self.add_get_vertex((True, doc.docnum))
                # ad edge
                eid = self.add_get_edge(doc_gid, term_gid)
                self.set_eattr(eid, weight_attr, edge_score(termset, term, doc))
        
        
        

class DocsTermsGraphBuilder(AbstractGraphBuilder):
    """ Build the bigraph doc<->term
    """

    def __init__(self, term_field="",		
                       termset_field="terms",
                       scores_attr=None,
                       doc_attr_copy=[],
                       term_attr_copy=[],
                       name="bgbuilder"):
        """
        from 'terms_field' and 'terms_scores_field' if a list is provided then
        the choice of the field became an option.
        
        @param terms_field: the name of the term field used to build the graph
        @param terms_lus_field: name of the score field (data field) where KodexLu of terms may be found
        @param terms_scores_field: name of the score field used to weight the graph. No weight if None.
        @param TODO
        """
        AbstractGraphBuilder.__init__(self, name, directed=False)
        self._logger = logging.getLogger(self.__class__.__name__)
        # Optionable init 
        self.add_option("doc_min",
                        "1", 
                        "Removes terms connected to less than *doc_min* documents",
                        int)
        self.add_option("doc_max_ratio",
                        "0.9",
                        "Removes terms connected to more than *doc_max_ratio* precents of the results documents",
                        float)
        # attr to copy
        self._doc_attr_copy = DocsTermsGraphBuilder.check_attr_copy_arg(kdoc_attr_copy, "doc_attr_copy")
        self._term_attr_copy = DocsTermsGraphBuilder.check_attr_copy_arg(klu_attr_copy, "term_attr_copy")

        # terms field
        self._terms_field = terms_field
        self._term_field_choice = False
        if isinstance(terms_field, (list, tuple)):
            if len(terms_field) == 0:
                ValueError("terms_field should be either a *non-emtpy* list or a string")
            self._term_field_choice = True
            self.add_enum_option("terms",
                                 terms_field,
                                 terms_field[0],
                                 "Terms field used for building the graph",
                                 str)
        elif not isinstance(terms_field, basestring):
            ValueError("terms_field should be either a list or a string")
        # klus field
        self._terms_lus_field = terms_lus_field
        # weight field
        self._weight = False
        self._weight_choice = False
        if isinstance(terms_scores_field, basestring):
            self._weight = True
            self._terms_scores_field = terms_scores_field
            self.add_bool_option("weighted",
                                    "True",
                                    "Whether to weight the graph or not")
        elif isinstance(terms_scores_field, (list, tuple)):
            if len(terms_scores_field) == 0:
                ValueError("terms_scores_field should be either a *non-emtpy* list or a string")
            self._weight = True
            self._weight_choice = True
            self._terms_scores_field = terms_scores_field
            self.add_enum_option(EDGE_WEIGHT_ATTR,
                                 terms_scores_field + ["no"],
                                 terms_scores_field[0],
                                 "How to weight the graph",
                                 str)
        # Graph builder init 
        self.declare_vattr("type")
        self.declare_vattr("doc")
        self.declare_vattr("term")
        new_attrs = set(vattr for _, vattr, _ in self._doc_attr_copy)
        new_attrs.update(vattr for _, vattr, _ in self._term_attr_copy)
        for vattr in new_attrs:
            self.declare_vattr(vattr)
        #edges attrs
        self.declare_eattr(EDGE_WEIGHT_ATTR)

    @staticmethod
    def check_attr_copy_arg(kdoc_attr_arg, field_name):
        if not isinstance(kdoc_attr_arg, (list, tuple, set)):
            raise ValueError("'%s' should be a list (or a tuple)" % field_name)
        error_msg = "elements of '%s' should be either ('attr_name') or ('kdoc_attr_name', 'vtx_attr_name') or ('doc_attr_name', 'vtx_attr_name', convert_fct)" % field_name
        attr_copy = []
        for attrs in kdoc_attr_arg:
            if len(attrs) == 1:
                if not isinstance(attrs, basestring):
                    raise ValueError(error_msg)
                kattr, vattr = attrs
                filter_fct = lambda x: x
            elif len(attrs) == 2:
                kattr, vattr = attrs
                filter_fct = lambda x: x
                if not isinstance(kattr, basestring) or not isinstance(vattr, basestring):
                    raise ValueError(error_msg)
            else:
                if len(attrs) != 3:
                    raise ValueError(error_msg)
                kattr, vattr, filter_fct = attrs
                if not isinstance(kattr, basestring) \
                        or not isinstance(vattr, basestring) \
                        or not callable(filter_fct) :
                    raise ValueError(error_msg)
            attr_copy.append((kattr, vattr, filter_fct))
        return attr_copy
        
    def _parse(self, kdocs, weighted=True, weight=None, terms=None):
        """ Private methode called by self.build_graph().
        """
        for rank, kdoc in enumerate(kdocs):
            # ajout doc
            doc_gid = self.add_get_vertex((True, kdoc.docnum))
            self.set_vattr(doc_gid, "type", True)
            self.set_vattr(doc_gid, "doc", kdoc)
            #copy les kdoc attrs
            for kattr, vattr, convert in self._kdoc_attr_copy:
                self.set_vattr(doc_gid, vattr, convert(kdoc[kattr]))

        # two for loops in order to have the doc in first
        # (useful for more simple bipartite projection in clustering)
        for kdoc in kdocs:
            doc_gid = self.add_get_vertex((True, kdoc.docnum))
            if not self._term_field_choice:
                term_field = self._terms_field
            else:
                term_field = terms
            # ajout terms et liens
            for term in kdoc.iter_field(term_field):
                # ajout term, if needed
                term_gid = self.add_get_vertex((False, term))
                if self.get_vattr(term_gid, "term") is None:
                    # si nouveau sommet, on ajoute les attributs
                    self.set_vattr(term_gid, "type", False)
                    klu = kdoc.get_element_attr(self._terms_lus_field, term)
                    self.set_vattr(term_gid, "term", klu)
                    #copy les klu attrs
                    for kattr, vattr, convert in self._klu_attr_copy:
                        self.set_vattr(term_gid, vattr, convert(klu[kattr]))
                # get the edge weight
                if not self._weight or not weighted or weight == "no":
                    weight_value = 1.
                elif not self._weight_choice:
                    weight_value = kdoc.get_element_attr(self._terms_scores_field, term)
                else:
                    assert weight in self._terms_scores_field, "Incorect weight value !"
                    weight_value = kdoc.get_element_attr(weight, term)
                # ajout edge
                if weight_value > 1e-8:
                    eid = self.add_get_edge(doc_gid, term_gid)
                    self.set_eattr(eid, EDGE_WEIGHT_ATTR, weight_value)
                    #self._logger.debug("Ajout edge: %s <-> %s (%s)" % (doc_gid, term_gid, term))

    def __call__(self, docs, weighted=True, weight=None, terms=None, doc_min=1, doc_max_ratio=0.9):
        """ Build and return the graph

        @param docs: the L{KodexEngine} docs attribut (list of L{KodexDoc})
        @type docs: [L{KodexDoc}, ...]

        @param weighted: wheter to wheigt the graph or not
        @type weighted: bool
        
        @param doc_min: terms connected to less than *doc_min* documents are removed
        @type doc_min: int

        @param doc_max_ratio: terms connected to more than *doc_max_ratio* precents of the results documents are removed
        @type doc_max_ratio: float

        @note: There is a C{"type"} attribut on graph vertices:
         - Document have attribute type=True
         - Terms have attribute type=False
         
        """
        graph = self.build_graph(docs, weighted, weight, terms)
        
        # some verifications
        assert graph.is_bipartite(), "The Document<->Term graph is not bipartite !"
        return graph


class SimpleGraphBuilder(AbstractGraphBuilder):
    """ Build a simple graph between the KodexDoc
    """

    def __init__(self, neighbors_field="_all_terms",
                       neighbors_scores_field=None,
                       name="sgbuilder",
                       copy=[]):
        """
        from 'neighbors_field' and 'neighbors_scores_field' if a list is provided then
        the choice of the field became an option.
        
        @param neighbor_field: the name of the neighbor/term field used to build the graph
        @param neighbor_scores_field: name of the score field used to weight the graph. No weight if None.
        @param copy: kdoc attr that will be copied into vertices
        """
        AbstractGraphBuilder.__init__(self, name, directed=False)
        self._logger = logging.getLogger(self.__class__.__name__)
        # neighbors/terms field
        self._neighbors_field = neighbors_field
        self._neighbor_field_choice = False
        self._attrs_to_copy = copy
        if isinstance(neighbors_field, (list, tuple)):
            if len(neighbors_field) == 0:
                ValueError("neighbors_field should be either a *non-emtpy* list or a string")
            self._term_field_choice = True
            self.add_enum_option("neighbors",
                                 neighbors_field,
                                 neighbors_field[0],
                                 "Neighbors/terms field used for building the graph",
                                 str)
        elif not isinstance(neighbors_field, basestring):
            ValueError("neighbors_field should be either a list or a string")
        # weight field
        self._weight = False
        self._weight_choice = False
        if isinstance(neighbors_scores_field, basestring):
            self._weight = True
            self._neighbors_scores_field = neighbors_scores_field
            self.add_bool_option("weighted",
                                    "True",
                                    "Whether to weight the graph or not")
        elif isinstance(neighbors_scores_field, (list, tuple)):
            if len(neighbors_scores_field) == 0:
                ValueError("neighbors_scores_field should be either a *non-emtpy* list or a string")
            self._weight = True
            self._weight_choice = True
            self._neighbors_scores_field = neighbors_scores_field
            self.add_enum_option(EDGE_WEIGHT_ATTR,
                                 neighbors_scores_field + ["no"],
                                 neighbors_scores_field[0],
                                 "How to weight the graph",
                                 str)
        # Graph builder init
        self.declare_vattr("type")
        self.declare_vattr("_doc")
        for attr in copy:
            self.declare_vattr(attr)
        self.declare_eattr(EDGE_WEIGHT_ATTR)

    def _parse(self, kdocs, weighted=True, weight=None, neighbors=None):
        """ Private methode called by self.build_graph().
        """
        kdocs_idx = {} # garde un dico docnum->gid, pour etre sur que l'on ajoute pas des sommets hors result set
        for rank, _doc in enumerate(kdocs):
            # ajout doc
            kdoc = _doc.as_dict()
            doc_gid = self.add_get_vertex((True, kdoc['docnum']))
            self.set_vattr(doc_gid, "_doc", _doc)
            self.set_vattr(doc_gid, "type", True)
            for attr in self._attrs_to_copy:
                self.set_vattr(doc_gid, attr, kdoc[attr])
            kdocs_idx[kdoc['docnum']] = doc_gid

        #
        for kdoc in kdocs:
            doc_gid = self.add_get_vertex((True, kdoc['docnum']))
            if not self._neighbor_field_choice:
                neighbor_field = self._neighbors_field
            else:
                neighbor_field = neighbors
            # ajout neighbors (liens)
            for neighbor in kdoc[neighbor_field]:
                # ajout neighbor, if needed
                if neighbor not in kdocs_idx:
                    #self._logger.warning("'%s' is not a KodexDoc of the result set" % neighbor)
                    continue #TODO: ajout avec type = False ?
                    #self.add_get_vertex((False, neighbor))
                neighbor_gid = kdocs_idx[neighbor]
                # get the edge weight
                if not self._weight or not weighted or weight == "no":
                    weight_value = 1.
                elif not self._weight_choice:
                    weight_value = kdoc.get_element_attr(self._neighbors_scores_field, neighbor)
                else:
                    assert weight in self._neighbors_scores_field, "Incorect weight value !"
                    weight_value = kdoc.get_element_attr(weight, neighbor)
                # ajout edge
                if weight_value > 1e-8:
                    eid = self.add_get_edge(doc_gid, neighbor_gid)
                    self.set_eattr(eid, EDGE_WEIGHT_ATTR, weight_value)
                    #self._logger.debug("Ajout edge: %s <-> %s (%s)" % (doc_gid, neighbor_gid, neighbor))

    def __call__(self, docs, weighted=True, weight=None, neighbors=None):
        """ Build and return the graph

        @param docs: the L{KodexEngine} docs attribut (list of L{KodexDoc})
        @type docs: [L{KodexDoc}, ...]

        @param weighted: wheter to wheigt the graph or not
        @type weighted: bool

        @note: There is a C{"type"} attribut on graph vertices:
         - Document present in the result set have attribute type=True
         - Other have attribute type=False
        """
        graph = self.build_graph(docs, weighted, weight, neighbors)
        self._logger.info("Graph: |V_docs|=%d, |E|=%d" % (graph.vcount(), graph.ecount()))
        return graph

class EdgeConfluence():
    
    def __init__(self):
        pass
        
    def __call__(self, graph):
        print "EdgeConfluence", graph.summary(), graph.is_directed()
        prx = {k: prox.confluence(graph, [k], neighbors_fct = ig.Graph.neighbors, l=5 , method=prox.prox_markov ) for k in graph.vs.indices  }
        conf = [ prx[e.source][e.target] for e in graph.es]
        graph.es['conf']= conf
        
        prx = {k: prox.prox_markov(graph, [k], neighbors_fct = ig.Graph.neighbors, l=3  ) for k in graph.vs.indices  }
        conf = [ prx[e.source][e.target] for e in  graph.es]
        graph.es['prox']= conf
        return graph

class SubGraphExtractor(AbstractGraphBuilder):
    """ Build a simple graph between the KodexDoc by extracting a subgraph from a kgaph
    """

    def __init__(self, kgraph,
                       kdocs_kgraph_attr="kgraph_id",
                       kdocs_vindex_attr=None,
                       name="subgraph_extractor"):
        """
        @param kgraph: the KodexGraph
        @param kdocs_kgraph_attr: the name of KodexDoc attribute that store the kgraph_id of the doc, if None kdocs_vindex_attr is used instead
        @param kdocs_vindex_attr: the name of KodexDoc attribute that may be used to retrieve vertex using kgraph.vindex
        """
        AbstractGraphBuilder.__init__(self, name)
        self._logger = logging.getLogger("kodex.gbuilder.SubGraphExtractor")
        
        if kdocs_vindex_attr is None and kdocs_kgraph_attr is None:
            raise ValueError("kdocs_vindex_attr and kdocs_kgraph_attr should not both be None")
        
        self._kgraph = kgraph
        self._kdocs_kgraph_attr = kdocs_kgraph_attr
        self._kdocs_vindex_attr = kdocs_vindex_attr

    def _parse(self, kdocs):
        pass

    def __call__(self, kdocs):
        kdocs_kgraph_attr = self._kdocs_kgraph_attr
        kdocs_vindex_attr = self._kdocs_vindex_attr
        # construction de la liste des kgraphids
        # check tout les id ok
        new_kdocs = []
        kgraph_ids = []
        for kdoc in kdocs:
            if kdocs_kgraph_attr is not None:
                graph_id = kdoc[kdocs_kgraph_attr]
            else:
                vtx_index = kdoc[kdocs_vindex_attr]
                if vtx_index not in self._kgraph.vindex:
                    raise ValueError, "Vertex %s not found in the graph" % vtx_index
                    continue #TODO: affiché un warning mais continué quand même
                graph_id = self._kgraph.vindex[vtx_index]
            
            if graph_id < 0 or graph_id > self._kgraph.graph.vcount():
                raise ValueError, "Vertex %s doesn't exist in the graph" % graph_id
                continue #TODO: affiché un warning mais continué quand même
            pos = bisect(kgraph_ids, graph_id)
            kgraph_ids.insert(pos, graph_id)
            new_kdocs.insert(pos, kdoc)

        # exctraction du graph
        graph = self._kgraph.graph.subgraph(kgraph_ids)
        # ajout des kdoc et des types
        graph.vs["type"] = True
        graph.vs["kodex_doc"] = new_kdocs
        graph.vs["kgraph_id"] = kgraph_ids
        
        if EDGE_WEIGHT_ATTR not in graph.es.attribute_names():
            graph.es[EDGE_WEIGHT_ATTR] = 1
        
        self._logger.info("Graph: |V_docs|=%d, |E|=%d" % (graph.vcount(), graph.ecount()))
        return graph
#}


