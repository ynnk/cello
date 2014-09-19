#-*- coding:utf-8 -*-
""" :mod:`cello.index`
======================

"""
#TODO: add doc
import warnings

from cello.exceptions import CelloError
from cello.schema import Doc    #FIXME: unused import


class CelloIndexError(CelloError):
    """Raised when index cannot be open """
    pass


class Index:
    """ Abstract class, provide methods to access an index of a collection.
    """
    def __init__(self):
        pass

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
        @param kdoc: the document to add
        @type kdoc: :class:`Doc`
        @return: True if the document has been added correctly
        @rtype: boolean
        """
        raise NotImplementedError

    def add_documents(self, kdocs):
        """ Add a set of documents in the index
        @param kdocs: a list of  document to add
        @type kdocs: (:class:`Doc`, ...)
        @return: list of docnum that has not been added correctly
        @rtype: [int, ...]
        """
        warnings.warn("Unefficient implementation: it calls self.add_document for each term", RuntimeWarning)
        add_document = self.add_document
        fails_on = []
        for kdoc in kdocs:
            if not add_document(kdoc):
                fails_on.append(kdoc.docnum)
        return fails_on
