#-*- coding:utf-8 -*-
""" :mod:`cello.index`
======================

"""
#TODO: add doc
import warnings
import logging

from cello.exceptions import CelloError
from cello.schema import Doc    #FIXME: unused import


class CelloIndexError(CelloError):
    """Raised when index cannot be open """
    pass


class Index:
    """ Abstract class, provide methods to access an index of a collection.
    """
    def __init__(self):
        self._logger = logging.getLogger("cello.%s" % self.__class__.__name__)

    def __len__(self):
        """ Number of documents in the index
        
        :return: number of document in the index
        :rtype: `int`
        """
        raise NotImplementedError

    def close(self):
        """ Close the index.
        """
        pass
    
    def delete(self):
        """ Delete the index, also close it
        """
        raise NotImplementedError

    def create(self):
        """ Create the index
        """
        raise NotImplementedError

    def exist(self):
        """ Whether the index exist
        """
        raise False

    def has_document(self, *args, **kwargs):
        """ Whether a document is in the index
        
        :param docnum: the document uniq identifier (in the collection).
        :type docnum: `str` or `unicode`
        
        :return: True if the document is present in the index
        :rtype: boolean
        """
        raise NotImplementedError

    def get_document(self, docnum):
        """ Retrun a document
        
        @note: it is preferable to use :func:`get_documents` when you have multiple
        documents tio fetch, implementations are often more efficent.
        
        :param docnum: the document uniq identifier (in the collection).
        :type docnum: str or unicode
        :return: a :class:`Doc` object with at least a setted docnum.
        :rtype: :class:`Doc`
        """
        raise NotImplementedError

    def get_documents(self, docnums):
        """ Seek some documents from the index
        
        @note: it is preferable to use this method raither the 
        :func:`get_documents` when you have multiple documents io fetch, many
        implementations are more efficent.
        
        :param docnums: the list (or at least iterable) of document's uniq
        identifier (in the collection).
        :type docnums: list of str or unicode
        :return: a generator (or a list) of :class:`Doc` object with at least
        a setted docnum.
        :rtype: (:class:`Doc`, ...)
        """
        warnings.warn("Unefficient implementation: it calls self.get_document for each doc", RuntimeWarning)
        return (self.get_document(docnum) for docnum in docnums)

    def iter_docnums(self):
        """ Return an iterator over all I{docnums} of the collection
        """
        raise NotImplementedError

    def add_document(self, kdoc):
        """ Add a document in the index
        :param kdoc: the document to add
        """
        raise NotImplementedError

    def add_documents(self, kdocs):
        """ Add a set of documents in the index
        :param kdocs: a list of  document to add
        """
        warnings.warn("Unefficient implementation: it calls self.add_document for each term", RuntimeWarning)
        add_document = self.add_document
        fails_on = []
        for kdoc in kdocs:
            if not add_document(kdoc):
                fails_on.append(kdoc.docnum)
        return fails_on

    def update_document(self, docnum, doc):
        """ Partial update a document.
        
        Note: this is a partial update, ie. only the given fields will be updated.
        Fields that are present in the index but not given will stay has they are.
        
        :param docnum: the document identifier
        :param doc: the new document
        """
        raise NotImplementedError

    def update_documents(self, docs):
        """ Partial update a set of documents.

        :param docs: a dictionary `{docnum:doc}`
        """
        warnings.warn("Unefficient implementation: it calls self.update_document for each doc", RuntimeWarning)
        return (self.update_document(docnum, doc) for docnum, doc in docs.iteritems())

