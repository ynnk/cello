#-*- coding:utf-8 -*-
"""  :mod:`cello.engine`
========================

Cello processing system
^^^^^^^^^^^^^^^^^^^^^^^

code sample
~~~~~~~~~~~

from cello.engine import Cellist

cellist = Cellist()
cellist.requires('foo', 'bar', 'boo')

# one can make imaginary components
one, two, three = One(), Two(), Three()| plusOne()

foo_comps = [ one, two, three ]
foo_options = {'default': two.name }
cellist.set('foo', *foo_comps, **foo_options )

# or
cellist['bar'].append(One())
cellist['bar'].append(Two(), default=True)
cellist['bar'].append(Three(), default=True)

# or 
# XXX ca c est pas sur du tout que ca marche 

cellist["boo"].set(one, two, three)
cellist["boo"].set_options(multiple = True)
cellist["boo"].defaults = [lab.name for lab in (one, two, three )]

cellist.configure( request_options )

# test before running 
cellist.validate()

res = cellist.solo('boo', boo_args)

# plays all
results = cellist.play()
"""

import time 
import logging
from cello import CelloError
from cello.pipeline import Pipeline, Optionable, Composable


class Block(object):
    """ A block is a processing step realised by one component.
    
    A component is a callable object that has a *name* attribute,
    often it is also a :class:`.Optionable` object or a pipeline beeing a `.Composable` .
    
    Block object provides methods to discover and parse components options (if any).
    """
    #TODO: ajout du nom des input/output (needed si automatisation du run)
    #TODO: ajout validation de type sur input/output

    def __init__(self, name, *components, **options ):
        """
        :param name: name of the Block
        :type name: str
        """
        self._name = name
        self._logger = logging.getLogger(__name__)

        self.reset()        
        self.set(*components)
        self.set_options(**options)        

    def reset(self):
        """ Removes all the components of the block
        """        
        self.clear_selections()
        self._components = []
        self._components_dict =  {}

    def clear_selections(self):
        """ cancel the current selections
        """
        # component names list to keep order 
        self._selected = [] 
        self._selected_opts = {}

    def set_options(self, required=False, hidden=False, multiple=False,  defaults=[] ):
        """
        :param required: whether the block will be required or not
        :type required: bool
        :param hidden: whether the block will be hidden to the user or not
        :type hidden: bool
        :param multiple:
        :type multiple: bool
        :param default:
        :type default: bool
        """        
        self.required = required
        self.hidden = hidden
        self.multiple = multiple

        if not len(defaults) and len(self._components):
            self.select(self._components[0].name, {})
        else:
            for name in defaults:
                self.select(name, {})
        self.defaults = defaults

        # TODO depends         
        # self.depends = depends # *dependence_block_names  

    def set(self, *components):
        """ Set the possible components of the block
        :param components: components to append Optionables or Composables
        """
        self.reset()
        if len(components) == 1:
            self.append(Pipeline(components[0]))
        else:
            for comp in components:
                self._logger.info("SET %s %s %s", self._name, comp, type(comp) )
                if isinstance(comp,  (Optionable,Composable)):
                    self.append(comp)
                else: raise ValueError("component %s is not type of Optionable or Composable" % comp)

    def append(self, component, default=False):
        """ Add one component to the block
        
        :param default: if true this component will be use by default
        :type default: bool
        """
        #TODO check component is a component...
        if not component.name in self._components :
            self._components_dict[component.name] = component
            self._components.append(component)
            if default: 
                self.select(component.name, {} )
        else :
            raise ValueError("We already have a component with the name %s" % component.name)

    def select(self, comp_name, options):
        """ set an component as runnable with given options
        - Options will be then passed to optionable.parse_options
        - Use iter_runnables to get all selected optionables
        and associated options
        
        :param name: name of the component to select
        :type comp_name: str
        :param options: options to set to thhe components
        :type options: dict
        """
        component = self._components_dict.get(comp_name, None)
        if component == None:
            raise ValueError(" '%s' has no candidate '%s' (%s)"\
                  %(self._name, comp_name, self.component_names()) )
        # add component as selected, aware of multiple
        if not comp_name in self._selected:
            if len(self._selected)  and not self.multiple:
                self.clear_selections()
            self._selected.append(comp_name)
        else :
            # TODO the component has already been selected
            # and is not set as multiple.            
            pass
        # component might be a function or any callable 
        # only Optoinable will get options        
        if isinstance(component, Optionable):
            self._selected_opts[comp_name] = component.parse_options(options)
        # XXX NOT implemented
        # TODO implements options parsing
    

    def iter_runnables(self):
        """ generator of pairs optionable, options
        yields optionable and options marked as selected
        use KebComponent.select to mark optionables
        """
        for k in self._selected:
            yield ( self._components_dict[k], self._selected_opts.get(k, {}))

    def component_names(self):
        """ returns the list of component names
        """
        return self._components_dict.keys()

    def __len__(self):
        """ returns the count of components of the given name
        """
        return len(self._components)
    

    def __getitem__(self, name):
        """ returns the component of the given name
        """
        return self._components_dict[name]

    def as_dict(self):
        """ returns a dictionary representation of the block and of all
        component options
        """
        return

class Cellist(object):
    """
    """
    
    def __init__(self, ):
        self._blocks = {} # 
        self._names = []
        self.time = 0
        self._logger = logging.getLogger(__name__)

    def requires(self, *names):
        """ declare what will be used in this engine 
            before adding or setting any component
            Order will be preserved for runnning task
        """ 
        if len(names) == 0:
            raise ValueError
    
        if self._blocks is not None and len(self._blocks) > 0 :
            raise CelloError("Method 'declare_types' should be called only once before adding any composant")   
        if len(names) != len(set(names)):
            raise ValueError("Duplicate block name %s" % names)
        self._names = names if type(names) in (tuple,list) else [names] 

    
    def set(self, name, *optionables, **options):
        """ Set available components
           @param opt_type : L{str} component type in ('searching', 'expanding', 'graph_building', 'clustering', 'labelling')
           @param optionables: a list of initialised instance of component
           @param options : see Block attributes
       """
        assert name in self._names, \
            "%s is not one of (%s)" % (name, ",".join(self._names))
        comp = Block(name, *optionables, **options)
        self._blocks[name] = comp

    def __contains__(self, name):
        """ returns wether a block of the given name exists
        """
        return name in self._blocks

    def __getitem__(self, name):
        """ returns the block of the given name
        """
        return self._blocks[name]
    
    def __len__(self):
        """ returns block count
        """
        return len(self._blocks)

    
    def names(self):
        """ returns the sequence of block names
        """
        return self._names

    def configure(self, config):
        """ configure all the blocks from an (horible) configuration dictionary
        this data are coming from a json client request and has to be parsed 
        
        :param request: dictionary that give the component to use for each step
               and the associated options 

        .warning Values in these dictionnary are strings 

        format
        ======
            { block_name: [{
                    'name' : "name_of_the_comp_to_use"
                    'options' : {
                            name : value,
                            name : va...
                        },
                    },{...}
                ],
              comp_type : [{....
           }
          take the default value if missing.
        """
        self._logger.info("Parsing json, retrieve the components to use")

        for block_name in self._names:
            block = self[block_name]
            request_comps = config.get(block_name, []) # request
            # comp not given, check if hidden or not required
            if len(request_comps) == 0:
                if block.hidden:
                    # TODO set defaut options
                    pass
                elif block.required: 
                    raise ValueError("Component '%s' is required but None given" % block_name)
            # comp is given
            elif type(request_comps) == list and len(request_comps):
                # remove defaults
                block.clear_selection()
                for req_comp in request_comps:
                    req_comp_name = req_comp.get("name", None)
                    if req_comp_name is not None:
                        block.select(req_comp_name, req_comp.get("options", {}) )
                    else : 
                        raise ValueError("Config error in '%s' " % block_name)
    
    def validate(self):
        """ Check that the component configuration is ok """
        # TODO implements requires
        for name in self._names:
            if not(name in self) or len(self[name].iter_runnables() ) == 0:
                raise ValueError("'%s' component is declared but none is set")
    
    def play(self, name, *args):
        """ Run Block  with args
        It runs all component with sam arguments *args,
        and the given or defaults options for this optionable

        @param comp_type: <str> type of component to run
        @param args: all arguments that should be pass to optionables
        """
        self._logger.info("playing %s with %s args: "% (name, len(args)) )
        start = time.time()
        results = None
        run_comps = {}

        for comp, options in self[name].iter_runnables():
            # TODO store args and kwargs ?
            run_comps[comp.name] = {
                "obj" : repr(comp),
                #@"%s_args"% name , args, # args too fat
                "kwargs" : options,
            }
            self._logger.info("%s: %s component: %s, args=%s, kwargs=%s" % (name, comp.name, comp, len(args), options))

            # !!! Defaut multiple behavior is used as pipeline !!!
            # given that the args in input are also the returning value
            # This behavior allows to modify the data given in input.
            # actually same arg if given several times 
            # but may be transformed during the process
            # then finally returned
            results = comp( *args, **options)

            # TODO implements different mode for multiple 
            # another way of doing would be declare a list var outside the loop,
            # then append the result of each call to the components __call__
            # and finally returns all computed results
            # >>> results.append( comp(*args, **options) )
            # >>> return *results

        self.time += time.time()-start

        return results
    
    def as_dict(self):
        """ dict repr of the components """
        return { 'names' : self._names, 
                 'components': { name: self[name].as_dict() for name in self._names }
               }

