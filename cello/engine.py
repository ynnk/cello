#-*- coding:utf-8 -*-
"""  :mod:`cello.engine`
========================

Cello processing system
"""

class Block(object):
    """ A block is a processing step realised by one component.
    
    A component is a callable object that has a *name* attribute,
    often it is also a :class:`.Optionable` object.
    
    Block object provides methods to discover and parse components options (if any).
    """
    #TODO: ajout du nom des input/output (needed si automatisation du run)
    #TODO: ajout validation de type sur input/output

    def __init__(self, name, required=True, hidden=False):
        """
        :param name: name of the Block
        :type name: str
        :param required: whether the block will be required or not
        :type required: bool
        :param hidden: whether the block will be hidden to the user or not
        :type hidden: bool
        """
        self._name = name
        self._required = required
        self._hidden = hidden

    def reset(self):
        """ Removes all the components of the block
        """
        pass

    def append(self, component, default=False):
        """ Add one component to the block
        
        :param default: if true this component will be use by default
        :type default: bool
        """
        #TODO check component is a component...
        #TODO check no other with same name
        pass

    def set(self, *components):
        """ Set the possible components of the block
        """
        self.reset()
        self.append(components)

    def component_names(self):
        """ returns the list of component names
        """
        return

    def __getitem__(self, name):
        """ returns the component of the given name
        """
        return

    def as_dict(self):
        """ returns a dictionary representation of the block and of all
        component options
        """
        return

    def select(self, comp_name, options):
        """ select a given component
        
        :param comp_name: name of the component to select
        :type comp_name: str
        :param options: options to 
        :type opitons: dict
        """
        pass

    def clear_selection(self):
        """ cancel the current selection
        """
        pass

    #TODO: pour le moment que 1 input et 1 output...
    # pb si on gère plus: est-ce que c'est l'ordre qui compte ?
    # ou est-ce qu'on les nomes ?
    # dans les composants c'est lordre
    def run(self, inputs):
        """ Run selected component (with given options)
        """
        result =  None
        return result



#TODO: le nom c'est pas top...
# est-ce que l'on garde la distinction Engine et EngineBuilder ?
class Engine(object):
    """
    """
    
    def __init__(self, *blocks):
        self._blocks = blocks
        pass

    def append(self, block):
        """ add a processing block
        
        ..warning: the sequence order of blocks is important
        """
        # check if no other with same name
        # check the block is not empty (no component)
        pass

    def __getitem__(self, name):
        """ returns the block of the given name
        """
        if name not in self._blocks:
            raise ValueError
        return self._blocks[name]

    def block_names(self):
        """ returns the sequence of block names
        """
        return self._blocks_seq

    def as_dict(self):
        """ return a dictionary representation of the engine.
        """
        return

    def configure(self, config):
        """ configure all the blocks from an (horible) configuration dictionary
        """
        pass

