
from cello.pipeline import DocPipelineElmt, OptDocPipelineElmt, DocListPipelineElmt


#{ AbstractExpander
class AbstractExpand(OptDocPipelineElmt):
    """ Expand a list of L{KodexDoc}.
    This is an abstract class, the method
    """
    def __init__(self, name):
        OptDocPipelineElmt.__init__(self, name)

    def _expand(self, doc, **kargs):
        """ Expand a given document

        @param doc: the document to expand
        @type doc: L{KodexDoc}

        @return: an expanded L{KodexDoc}
        @precondition: returned document should have a not empty "terms" field
        """
        raise NotImplementedError

    def __call__(self, kdocs, **kargs):
        """ Expand each document.
        Apply the method L{_expand} to each document (this __call__ method may also be override).

        @param kdocs: a L{KodexDoc} generator
        """
        for kdoc in kdocs:
            yield self._expand(kdoc, **kargs)

    def close(self):
        """ Close the underlying storage structure
        """
        pass


class AbstractDocListExpand(DocListPipelineElmt):
    """ Expand a list of L{KodexDoc}.
    This is an abstract class, the method 
    """
    def __init__(self, name):
        DocListPipelineElmt.__init__(self, name)

    def __call__(self, kdocs, **kargs):
        """ Expand each document.

        @param docs: an iterable object over L{KodexDoc}
        
        @return: a list of L{KodexDoc}
        @rtype: [L{KodexDoc}, ...]
        """
        raise NotImplementedError
        return [kdoc for kdoc in kdocs]

    def close(self):
        """ Close the underlying storage structure
        """
        pass
#}


class Consumer(AbstractExpand):
    """ No operation expander
        Consume iterator before returning a list 
    """
    def __init__(self):
        AbstractExpand.__init__(self, "Consumer_expander")
    
    def __call__(self, kdocs, **kargs):
        return [kdoc for kdoc in kdocs]

class NoopExpand(AbstractExpand):
    """ No operation expander
        Simply returns the same doc
    """
    def __init__(self):
        AbstractExpand.__init__(self, "noop_expander")
    
    def _expand(self, doc, *args, **kargs):
        """ returns the same doc """
        return doc
