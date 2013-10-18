Manage Cello's documents
========================

Documents objects (:class:`doc`) are central in cello framework. Until now 

Create a document ::

    >>> from cello.models import Doc
    >>> doc = Doc()

and then declare somme value fields ::

    >>> from cello.models import ValueField
    >>> doc.url = ValueField(desc="URL of the document")
    >>> doc.title = ValueField(desc="title")


