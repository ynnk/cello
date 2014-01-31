#-*- coding:utf-8 -*-
"""  :mod:`cello.engine`
========================

Cello processing system
^^^^^^^^^^^^^^^^^^^^^^^

code sample
~~~~~~~~~~~

Here is a simple exemple of Cellist usage. First you need to setup your Cellist::

    from cello.engine import Cellist

    cellist = Cellist()
    cellist.requires('foo', 'bar', 'boo')

    # one can make imaginary components
    one, two, three = One(), Two(), Three()| plusOne()

    # one can configure a block with this three components:
    foo_comps = [ one, two, three ]
    foo_options = {'default': two.name }
    cellist.set('foo', *foo_comps, **foo_options )

    # or
    cellist['bar'].append(One(), default=True)
    cellist['bar'].append(Two(), default=True)
    cellist['bar'].append(Three(), default=True)
    cellist["boo"].set_options(multiple = True)

    # or
    cellist["boo"].set(one, two, three)
    cellist["boo"].set_options(multiple = True)
    cellist["boo"].defaults = [lab.name for lab in (one, two, three )]


And then you can configure and run it::

    cellist.configure(request_options)

    # test before running 
    cellist.validate()

    res = cellist.solo('boo', boo_args)
    

    # plays all blocks
    results = cellist.play()
"""

import time
import logging
from collections import OrderedDict

from cello import CelloError
from cello.pipeline import Pipeline, Optionable, Composable


class Block(object):
    """ A block is a processing step realised by one component.
    
    A component is a callable object that has a *name* attribute,
    often it is also a :class:`.Optionable` object or a pipeline beeing a :class:`.Composable` .
    
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

        self.has_run = False
        self.time = 0
        self.warnings = []
        self.errors = []

    def reset(self):
        """ Removes all the components of the block
        """
        self.clear_selections()
        self._components = OrderedDict()

    def clear_selections(self):
        """ cancel the current selections
        """
        self._selected = []
        self._selected_opts = {}

    def set_options(self, required=True, hidden=False, multiple=False, defaults=[]):
        """ Set the options of the block
        
        :param required: whether the block will be required or not
        :type required: bool
        :param hidden: whether the block will be hidden to the user or not
        :type hidden: bool
        :param multiple: if True more than one component may be selected (and run)
        :type multiple: bool
        :param default: names of the selected components
        :type default: list of str, or str
        """
        self.required = required
        self.hidden = hidden
        self.multiple = multiple

        if self.required and not len(defaults) and len(self._components):
            # select the first component by default
            self.select(self._components.values()[0].name, {})
        else:
            if isinstance(defaults, basestring):
                # in case only one component is selected by defautl
                self.select(defaults, {})
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
            self.append(Pipeline(components[0])) #XXX: pourquoi l'encapsulation dans Pipeline ?
            #TODO: si encapsulation dans Pipeline needed il faut le faire dans append
        else:
            for comp in components:
                self._logger.info("SET %s %s %s", self._name, comp, type(comp) )
                #TODO: le check sur Composable ne suffit pas ?
                if isinstance(comp, (Optionable,Composable)):
                    self.append(comp)
                else:
                    raise ValueError("component '%s' is not type of Optionable or Composable" % comp)

    def append(self, component, default=False):
        """ Add one component to the block
        
        :param default: if true this component will be use by default
        :type default: bool
        """
        #TODO check component is a component.
        if not component.name in self._components:
            self._components[component.name] = component
            if default:
                self.select(component.name, {})
        else:
            raise ValueError("We already have a component with the name '%s'" % component.name)

    def select(self, comp_name, options):
        """ set an component as runnable with given options.
        
        `options` will be passed to :func:`.Optionable.parse_options` is the
        component is :class:`Optionable`.
        
        You can use :func:`iter_runnables` to get all selected components
        and associated options, or :func:`play` to run it.
        
        :param name: name of the component to select
        :type comp_name: str
        :param options: options to set to the components
        :type options: dict
        """
        try:
            component = self._components[comp_name]
        except KeyError:
            raise ValueError("'%s' has no candidate '%s' (%s)"\
                  %(self._name, comp_name, self.component_names()) )
        # add component as selected, aware of multiple
        if not comp_name in self._selected:
            if len(self._selected) and not self.multiple:
                self.clear_selections()
            self._selected.append(comp_name)
        else :
            # TODO the component has already been selected
            # and is not set as multiple.
            pass
        # component might be a function or any callable
        # only Optionable will get options
        if isinstance(component, Optionable):
            self._selected_opts[comp_name] = component.parse_options(options)

    def play(self, *args):
        """ Run the selected component of the block
        """
        #TODO encapsulate result in a 'RunResult' or 'BlockResult' (?)
        _break_on_error = True
        start = time.time()
        # dict containing block running informations
        run_comps = {}
        # components marked selected
        runnables = ((self._components[k], self._selected_opts.get(k, {}))\
                        for k in self._selected )
        # run
        for comp, options in runnables:
            # TODO store args and kwargs ?
            run_comps[comp.name] = {
                "name": comp.name,
                "obj" : repr(comp),
                #@"%s_args"% name , args, # args too fat
                "kwargs" : options,
            }
            self._logger.info("%s: %s component: %s, args=%s, kwargs=%s" % (self._name, comp.name, comp, args, options))

            # !!! Defaut multiple behavior is used as pipeline !!!
            # given that the args in input are also the returning value
            # This behavior allows to modify the data given in input.
            # actually same arg if given several times 
            # but may be transformed during the process
            # then finally returned
            try :            
                # mulit = False or pipeline
                results = comp(*args, **options)

                # TODO implements different mode for multiple 
                # another way would be declaring a list var outside the loop,
                # then append the result of each call to the components __call__
                # and finally returns all computed results
                # >>> results.append( comp(*args, **options) )
                # >>> return *results

            # TODO catch warnings TODO
            # warning may be raised for many reasons like:
            # * options has been modified 
            # * deprecation
            # * pipeline inconsistency 
            # * graph with no edge ... 
            
            except Exception as e:
                # component error handling
                self.errors.append(e.message) 
                self.errors.append( "error in component %s %s /n %s"%( comp, comp.name, e.message ) )
                if _break_on_error:
                    break
            
            # component time
            now = time.time()
            tick = now - start
            start = now
            self.time += tick
            run_comps[comp.name]['time'] = tick

            # TODO create a Result object 
            # will all necessary data ie:
            # multi mode option(False, pipeline, map)
            # args
            # warnings : boolean
            # errors : boolean
            # components { name, kwargs,warning, errors, time,  }
            # time (running/computation time)
            # results: [] or 
             
        return results

    def component_names(self):
        """ returns the list of component names.
        
        Component names will have the same order than components
        """
        return self._components.keys()

    def __len__(self):
        """ returns the count of components of the given name
        """
        return len(self._components)

    def __getitem__(self, name):
        """ returns the component of the given name
        """
        return self._components[name]

    def as_dict(self):
        """ returns a dictionary representation of the block and of all
        component options
        """
        #TODO
        return


class Cellist(object):
    """ The Cello engine.
    
    """
    def __init__(self):
        self._blocks = {}
        self._names = []
        self.time = 0
        self._logger = logging.getLogger(__name__)

    def requires(self, *names):
        """ Declare what block will be used in this engine.
        
        It should be call before adding or setting any component.
        Blocks order will be preserved for runnning task.
        """ 
        if len(names) == 0:
            raise ValueError
    
        if self._blocks is not None and len(self._blocks) > 0 :
            raise CelloError("Method 'declare_types' should be called only once before adding any composant")   
        if len(names) != len(set(names)):
            raise ValueError("Duplicate block name %s" % names)
        self._names = names if type(names) in (tuple,list) else [names] 

    def set(self, name, *optionables, **options):
        """ Set available components and the options of one block.

       :param name: block name
       :param optionables: a list of components
       :param options: options of the block
       """
        assert name in self._names, \
            "%s is not one of (%s)" % (name, ",".join(self._names))
        comp = Block(name, *optionables, **options)
        self._blocks[name] = comp

    def __contains__(self, name):
        """ returns whether a block of the given name exists
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
        self._logger.info("playing %s with %s args: "% (name, len(args)))
        return self[name].play(*args)

    def as_dict(self):
        """ dict repr of the components """
        drepr = {
            'names' : self._names,
            'components': {name: self[name].as_dict() for name in self._names}
        }
        return drepr

