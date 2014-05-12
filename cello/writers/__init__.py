#-*- coding:utf-8 -*-
import re
from cello.pipeline import Optionable

class AbstractWriter(Optionable):
    """ Abstract writer
    """
    def __init__(self):
        Optionable.__init__(self, self.__class__.__name__)
    
    def add_document(self, kdoc):
        """ Add a document to the database
        
        @param kdoc: the document to add
        @type kdoc: L{KodexDoc}
        """
        raise NotImplementedError

    def close(self):
        """ Close the writer (and the underlying databases or files).
        
        @note: It should be call when everything you want has been written.
        It's flush the cache if needed.
        """
        pass

    def __call__(self, kdocs):
        """ Processing method, may be override if needed.
        """
        add_document = self.add_document
        for kdoc in kdocs:
            add_document(kdoc)
            yield kdoc


class ScreenWriter(AbstractWriter):
    """ Write a repr. of documents on the standart output
    """
    
    def __init__(self, fields=None, outformat=None, encoding='utf8'):
        """
        @param fields: print only the indicated fields (all if None)
        @param outformat : pythonic dict format "docnum:%(docnum)s  title:%(title)s " % {'docnum':'any', 'title': 'boo'}
                > docnum:any title:boo
        """
        AbstractWriter.__init__(self)
        self._fields = fields 
        self.fields_format = None
        self.format = outformat
        self.encoding = encoding
        # parsing format 
        if outformat is not None:        
            pattern = re.compile("%\(([a-z]+)\)")
            _fields = pattern.findall(outformat)
            self.fields_format = lambda kdoc : outformat % { field: kdoc[field] for field in _fields } 
        

    def add_document(self, kdoc):
        """ Prints fields of L{KodexDoc} on standart output
        """
        def _format(field):
            if type(field) == list:
                return "[%s]" % ",".join(field)
            return field

        _outformat = self.fields_format

        if self._fields is None  and self.format is None:
            doc_repr = repr(kdoc)
        elif self.format is None :
            doc_repr = ("<Doc(\"%s\")>\n" % kdoc.docnum) + "\n".join([ '%s:%s'% (field, _format(kdoc[field])) \
                          for field in self._fields if field in kdoc ])  
        else : 
            doc_repr = _outformat(kdoc)  
            
        print( ("%s" % doc_repr).encode(self.encoding) )


class IndexWriter(AbstractWriter):

    def __init__(self, idx):
        """ 
        Helper component to add document in a solr index
        :param idx: Cello.Index
        """
        AbstractWriter.__init__(self)
        self._logger = logging.getLogger(self.__class__.__name__)
        self.idx = idx

    def __call__(self, docs):
        try:
            self.idx.add_documents(docs)
        except Exception as error :
            self._logger.error("IndexError")
            raise

    def close(self):
        pass
