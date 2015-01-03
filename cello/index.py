#-*- coding:utf-8 -*-
""" :mod:`cello.index`
======================

"""
#TODO: add doc
import warnings
import logging

from cello.schema import Doc    #FIXME: unused import


class CelloIndexError(RuntimeError):
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

    def __contains__(self, key):
        """
        True if index has document with `key`
        """
        return self.has_document(key)
    

    def get(self, key, default=None):
        item = self.__getitem__(key)
        return item if item is not None else default

    def __getitem__(self, key):
        return self.get_document(key)

    def __setitem__(self,  key, document):
        uniqkey = self.get_uniq_key()
        
        if document is  None: 
            raise ValueError("document cant be 'None'")
        if uniqkey is None:
            raise ValueError("Can t use setitem if index has no uniq key")
        if key != document[uniqkey]:
            raise ValueError( "key should match uniqkey value in document %s != %s" % ( key, document[uniqkey] ))   

        self.add_document(document)

    def iteritems(self):
        return iter(self)

    def iterkeys(self):
        for k, v in iter(self):
            yield k
            
    def itervalues(self):
        for k, v in iter(self):
            yield v
            
    def iter_docnums(self, incr=1000):
        return self.iterkeys()

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

    def exists(self):
        """ Whether the index exists
        """
        raise False

    def has_document(self, *args, **kwargs):
        """ Whether a document is in the index
        
        :param docnum: the document uniq identifier (in the collection).
        :type docnum: `str` or `unicode`
        
        :return: True if the document is present in the index
        :rtype: boolean
        """
        return self.get_document(docnum) is not None

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

    def update_document(self, doc, add_if_new=False):
        """ Partial update a document.
        
        Note: this is a partial update, ie. only the given fields will be updated.
        Fields that are present in the index but not given will stay has they are.
        
        :param doc: the new document
        :param add_if_new: add document has new ones if they do not exist yet
        
        The docnum should be provided !
        """
        raise NotImplementedError

    def update_documents(self, docs, add_if_new=False):
        """ Partial update a set of documents.

        :param docs: a list of document
        :param add_if_new: add document has new ones if they do not exist yet
        """
        warnings.warn("Unefficient implementation: it calls self.update_document for each doc", RuntimeWarning)
        return (self.update_document(doc, add_if_new=add_if_new) for doc in docs)

