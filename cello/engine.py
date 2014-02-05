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
    
de que j'ai ecri de copié coller dans le notebook !!
    # plays all blocks
    results = cellist.play()
"""

import time
import logging
import warnings
import itertools
from collections import OrderedDict

from cello import CelloError
from cello.pipeline import Pipeline, Optionable, Composable

def define_logger(init):
    def wrapinit(self, *args, **kwargs):
        self._logger = logging.getLogger("%s.%s"%(__name__, self.__class__.__name__))
        init(self, *args, **kwargs)
    return wrapinit 
    
class Result(object):
    def __init__(self, block):
        self.name = block.name        
        self.multiple = block.multiple
        self.hidden = block.hidden
        self.components = {}
        self.outputs = []
        
    def walltime(self):
        """ Block computation time """
        return sum(c['time'] for c in self.components)
    
    @property
    def errors(self):
        """ Views on components errors """
        errors = (c['errors'] for c in self.components)
        return list(itertools.chain.from_iterable( errors ))
    
    @property
    def warnings(self):
        """ Views on components warnings """
        warnings = (c['warnings'] for c in self.components)
        return list(itertools.chain.from_iterable( warnings ))
    
    @property
    def has_error(self):
        """ wether any error happened in component  """
        return len(self.errors)
    
    @property
    def has_warning(self):
        return len(self.warnings)
    
     
class Block(object):
    """ A block is a processing step realised by one component.
    
    A component is a callable object that has a *name* attribute,
    often it is also a :class:`.Optionable` object or a pipeline beeing a :class:`.Composable` .
    
    Block object provides methods to discover and parse components options (if any).
    """
    #TODO: ajout du nom des input/output (needed si automatisation du run)
    #TODO: ajout validation de type sur input/output
    @define_logger
    def __init__(self, name, *components, **options):
        """
        :param name: name of the Block
        :type name: str
        """
        # declare attributs
        self._name = None 
        self._selected = []
        self._selected_opts = {}
        self._components = None
        # name
        self.name = name
        # default value for component options
        self.required = True
        self.hidden = False
        self.multiple = False
        self.defaults = []
        #handle results meta
        self.meta = Result(self)

        self.reset()
        if len(components):
            self.set(*components)
        if len(options):
            self.set_options(**options)

        # Attrs used to build a result object
        self.has_run = False
        
        

    @property
    def name(self):
        """Name of the optionable component"""
        return self._name

    @name.setter
    def name(self, name):
        if ' ' in name:
            raise ValueError("Block name should not contain space")
        self._name = name

    def reset(self):
        """ Removes all the components of the block
        """
        self.clear_selections()
        self._components = OrderedDict()

    def clear_selections(self):
        """ reset the current selections
        """
        self._selected = [] 
        self._selected_opts = {}

    def set_options(self, required=None, hidden=None, multiple=None, defaults=None):
        """ Set the options of the block.
        Only the not None given options are set
        
        :param required: whether the block will be required or not
        :type required: bool
        :param hidden: whether the block will be hidden to the user or not
        :type hidden: bool
        :param multiple: if True more than one component may be selected/ run) 
        :type multiple: bool
        :param default: names of the selected components
        :type default: list of str, or str
        """
        if required is not None:
            self.required = required
        if hidden is not None:
            self.hidden = hidden
        if multiple is not None:
            self.multiple = multiple
        if defaults is not None:
            if isinstance(defaults, basestring):
                defaults = [defaults]
            self.defaults = defaults

        # TODO depends
        # self.depends = depends # *dependence_block_names  

        

    def set(self, *components):
        """ Set the possible components of the block
        :param components: components to append Optionables or Composables
        """
        self._logger.info(" Set '%s': \n\t%s", self.name, "\n\t".join(( "%s %s"%(e.name, e) for e in components)))
        self.reset()
        if len(components) == 1:
            self.append(components[0], default=True)
        else:
            for _i, comp in enumerate(components):
                # handle Optionable or Composable function
                if isinstance(comp, Composable):
                    self.append(comp , default=_i==0)
                else:
                    raise ValueError("component '%s' is not type of Optionable or Composable" % comp)

    def append(self, component, default=False):
        """ Add one component to the block
        
        :param default: if true this component will be use by default
        :type default: bool
        """
        #TODO check component is a component.
        if len(self._components) == 0:
            component = Pipeline(component)
        if not component.name in self._components:
            self._components[component.name] = component
            if default:
                self.select(component.name, {})
        else:
            raise ValueError("We already have a component with the name '%s'" % component.name)



    def select(self, comp_name, options=None):
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
        if options is None:
            options = {}
        try:
            component = self._components[comp_name]
        except KeyError:
            raise ValueError("'%s' has no component '%s' (components are: %s)"\
                  %(self._name, comp_name, ", ".join(self.component_names())) )
        # add component as selected, aware of multiple
        if self._selected is None:
            self._selected = []
        if comp_name not in self._selected:
            if not self.multiple and len(self._selected):
                assert len(self._selected) == 1
                self._selected[0] = comp_name
            else:
                self._selected.append(comp_name)
        else :
            # TODO the component has already been selected
            # and is not set as multiple.
            pass
        # component might be a function or any callable
        # only Optionable will get options
        if isinstance(component, Optionable):
            self._selected_opts[comp_name] = component.parse_options(options)

    def validate(self):
        """ check that the block can be run
        """
        if self.required and len(self.selected()) == 0:
            raise CelloError("No component selected for block '%s'" % self.name)

    def play(self, *args):
        """ Run the selected components of the block
        !!! Defaut multiple behavior is used as *pipeline* !!!
        """
        # TODO 
        # multi mode option(False, pipeline, map)
        
        # TODO what if validate fails
        self.validate()
        
        _break_on_error = True
        start = time.time()
        
        # components marked selected
        runnables = ( (self._components[k], self._selected_opts.get(k, {}))
                        for k in self._selected )
        results = []
        # run
        for comp, options in runnables:
            # TODO store args and kwargs ?
            comp_res = {
                "name": comp.name,
                "obj" : repr(comp),
                #@"%s_args"% name , args, # args too fat
                "kwargs" : options,
                "errors" : [],
                "warnings" : [],
                "time" : 0
            }
            self._logger.info(" playing '%s': %s \n\tcomponent: %s,\n\targs=%s[...], \n\tkwargs=%s" % (self._name, comp.name, comp, str(args)[:100].replace('\n',''), options))

            try :            
                # multi = False or pipeline
                # given that the args in input are also the returning value
                # This behavior allows to modify the data given in input.
                # actually same arg if given several times 
                # but may be transformed during the process
                # then finally returned
                results.append( comp(*args, **options) )

                # TODO implements different mode for multiple 
                # another way would be declaring a list var outside the loop,
                # then append result of each call to the components __call__
                # and finally returns all computed results
                #   map( lambda x : x(*arg), *components )
                # >>> results.append( comp(*args, **options) )
                # >>> return *results

            # TODO catch warnings TODO
            # warning may be raised for many reasons like:
            # * options has been modified 
            # * deprecation
            # * pipeline inconsistency 
            # * graph with no edge ... 

            except Exception as err:
                # component error handling
                comp_res['errors'].append("error in component %s %s /n %s" % ( comp, comp.name, err.message ))
                if _break_on_error:
                    break
            
            # component time
            now = time.time()
            comp_res['time'] = now - start
            start = now
            self.meta.components[comp.name] = comp_res

        # XXX may return more than one value with multi=map 
        return results[0]

    def component_names(self):
        """ returns the list of component names.
        
        Component names will have the same order than components
        """
        return self._components.keys()

    def selected(self):
        """ returns the list of selected component names.
        
        if no component selected return the one marked as default.
        If the block is required and no component where indicated as default,
        then the first component is selected.
        """
        selected = self._selected
        if self._selected is None: # nothing has been selected yet
            selected = self.defaults
            if not len(selected) and self.required and len(self._components):
                selected = [self._components.values()[0].name]
        return selected

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
        return {}
    
class Engine(object):
    """ The Cello engine.
    
    """
    @define_logger
    def __init__(self):
        self._blocks = OrderedDict()
        self.time = 0

    def requires(self, *names):
        """ Declare what block will be used in this engine.
        
        It should be call before adding or setting any component.
        Blocks order will be preserved for runnning task.
        """ 
        if len(names) == 0:
            raise ValueError("You should give at least one block name")
    
        if self._blocks is not None and len(self._blocks) > 0 :
            raise CelloError("Method 'requires' should be called only once before adding any composant")
        if len(names) != len(set(names)):
            raise ValueError("Duplicate block name %s" % names)
        for name in names:
            self._blocks[name] = Block(name)

    def set(self, name, *optionables, **options):
        """ Set available components and the options of one block.
        :param name: block name
        :param optionables: a list of components
        :param options: options of the block
        """
        self._logger.info(" ** SET ** '%s' "% name)

        assert name in self._blocks, \
            "%s is not one of (%s)" % (name, ",".join(self._blocks.iterkeys()))
        comp = Block(name, *optionables, **options)
        self._blocks[comp.name] = comp

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
        return self._blocks.keys()

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

        for block_name in self._blocks:
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
        """ Check that the blocks configuration is ok """
        if not len(self._blocks):
            #XXX: better error than CelloError ?
            raise CelloError("There is no block in this engine")
        for block in self._blocks.itervalues():
            block.validate()

    def play(self, name, *args):
        """ Run Block  with args
        It runs all component with sam arguments *args,
        and the given or defaults options for this optionable

        @param comp_type: <str> type of component to run
        @param args: all arguments that should be pass to optionables
        """
        self._logger.info("\n\n\t\t\t >>>>> PLAYING '%s' with %s args: <<<<<<"% (name, len(args)))
        return self[name].play(*args)

    def as_dict(self):
        """ dict repr of the components """
        drepr = {
            'names': self._blocks.keys(),
            'components': {block.name: block.as_dict() for block in self._blocks.itervalues()}
        }
        return drepr

