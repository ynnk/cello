#-*- coding:utf-8 -*-
""" :mod:`cello.exceptions`
===========================
"""

class SchemaError(Exception):
    """ Error
    
    #TODO: précissé le docstr, c'est quoi quand on a cette erreur exactement ?
    """
    pass

class FieldValidationError(Exception):
    """ Error in a field validation """
    def __init__(self, field, value, errors):
        super(FieldValidationError, self).__init__(field)
        self.field = field
        self.value = value
        self.errors = errors

    def __repr__(self):
        return "<FieldValidationError '%s', '%s'>" % (self.field, self.value)
        
    def __str__(self):
        return "FieldValidationError '%s' : %s \n  %s " % (self.field, self.value, 
                            "\n".join([ "\t*%s" % err for err in self.errors]))

