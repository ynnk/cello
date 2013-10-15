#-*- coding:utf-8 -*-
"""
:mod:`cello.pipeline`
=====================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

Abstract objects used to setup processing pipelines.


inheritance diagrams
--------------------

.. inheritance-diagram:: cello.pipeline

Class
-----
"""

class Optionable:
    """ Abstract class for an optionable component
    """

    def __init__(self, name):
        """ 
        :param name: name of the Optionable component
        :type name: str
        """
        self._options_info = {}
        self._force_options = {}
        self._options_order = []
        self.name = name

    @staticmethod
    def _parse_bool(value):
        if value is None:
            return False
        if value is True or value is False:
            return value
        boolean = str(value).strip().lower()
        return boolean in ['true','yes', 'on', '1']

    @property
    def name(self):
        """Name of the optionables component"""
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def force_option_value(self, opt_name, value):
        """ force the value of an option.
        The option is then no more listed by :func:`get_options()`.
        
        :param opt_name: option name
        :type opt_items: str
        
        :param value: option value
        """
        if not opt_name in self._options_info:
            raise KodexValueError, "Unknow option name (%s)" % opt_name
        self._force_options[opt_name] = value

    def change_option_default(self, opt_name, default_val):
        """ Change the default value of an option
        
        :param opt_name: option name
        :type opt_items: str
        
        :param value: new default option value
        """
        print "change_option_default %s %s" % (opt_name, default_val) 
        if opt_name in self._options_info:
            self._options_info[opt_name]["default"] = default_val
            self._options_info[opt_name]["value"] = default_val   #XXX: est-ce que c'est utile ? ou donc ?
        else:
            raise KodexValueError, "Unknow option name (%s)" % opt_name

    def add_bool_option(self, opt_name, default, description):
        """ Add a boolean option
        
        :param opt_name: option's name
        :type opt_name: str
        
        :param default: default value of the option
        :type default: str
    
        :param description: short description of the option
        :type description: str
        """
        self._add_option(
            opt_name,
            {
                'type':'bool',
                'default':default,
                'description':description,
                'cast':Optionable._parse_bool
            }
        )

    def add_enum_option(self, opt_name, enum, default, description, cast):
        """ Add an option to the object same as add option except enum can be provided  
        
        :param opt_name: option name
        :type opt_items: str
        
        :param enum: list of possible values
        
        :param default_val: default value
        
        :param description: short description of the option
        :type description: str
        
        :param cast: function to transform the option value from string to
             appropriate format
        :type cast: function
        """
        #TODO check default est bien dans enum
        if enum is not None and type(enum) == list and len(set(enum)) == len(enum):
            self._add_option(opt_name, {'type':'enum', 'enum':enum, 'default':default, 'description':description, 'cast':cast})

    def add_option(self, opt_name, default, description, cast, **kwargs):
        """ Add an option to the object
        
        :param opt_name: option name
        :type opt_name: str
        
        :param default: default value
        :type default: str
        
        :param description: short description of the option
        :type description: str
        
        :param cast: function to transform the option value from string to
            appropriate format
        :type cast: function
        """
        self._add_option(opt_name, {'type':'text','default':default, 'description':description, 'cast':cast} )
        
    def _add_option(self, opt_name, opt):
        """ private methode used to add an option.
        
        an option 'opt' is a dict with ::
            {
             'type':'text', # 'text' or 'enum' or 'bool'
             'enum': [],    # if enum
             'default':default,
             'description':description,
             'cast':cast
            }
        """
        assert opt_name not in self._options_info, "Option '%s' already setted" %opt_name
        opt['value'] = opt['default']
        self._options_info[opt_name] = opt
        self._options_order.append(opt_name)

    def parse_options(self, options):
        parse = {}
        for name, opt in self._options_info.iteritems():
            try:            
                parse[name] = opt['cast'](options.get(name, opt['default']))
            except ValueError as error: 
                raise KodexValueError( "Wrong argument '%s' in option '%s' from component '%s':\n%s"\
                    %  ( options.get(name, opt['default']), name, self.name,  error.message) )
                
        for name, value in self._force_options.iteritems():
            parse[name] = value
        return parse

    def get_default_value(self, opt_name):
        """ Return the default value of a given option
        
        :param opt_name: option name
        :type opt_name: str
        """
        if opt_name in self._force_options:
            return self._force_options[opt_name]
        return self._options_info[opt_name]["default"]

    def get_options(self):
        """
        :returns: dictionary of all options (with option's information)
        :rtype: dict
        """
        #TODO: replace the dict by a list to get ordered options
        return dict(self.get_ordered_options())

    def get_ordered_options(self):
        """
        :returns: **ordered** list of all options (with option's information)
        :rtype: list ::
            [(<opt_name>, )]
        """
        return [(opt_name, self._options_info[opt_name]) \
                    for opt_name in self._options_order \
                    if not opt_name in self._force_options]

class Composable:
    """ Basic composable element, ie. an object that may be a basic element of a pipeline
    
    >>> e1 = Composable()
    >>> e2 = Composable()
    >>> chain = e1 | e2
    >>> iterable = xrange(10)
    >>> for e in chain(iterable):
    >>>     print("result: %s" % e)
    
    Is the same than :
    
    >>> e1 = Composable()
    >>> e2 = Composable()
    >>> for e in e2(e1(iterable)):
    >>>     print("result: %s" % e)
    """

    def __init__(self):
        pass

    def __or__(self, other):
        if not callable(other):
            raise Exception("%r is not composable with %r" % (self, other))
        return ComposableChain(self, other)

    def __call__(self, filename):
        raise NotImplementedError


class ComposableChain(Composable, Optionable):
    def __init__(self, *composables):
        # Composable init
        Composable.__init__(self)
        self.items = []
        for comp in composables:
            if isinstance(comp, ComposableChain):
                self.items.extend(comp.items)
            else:
                self.items.append(comp)
        # Optionable init
        opt_items = [item for item in self.items if isinstance(item, Optionable)]
        # Check than a given options is not in two items
        all_opt_names = {}
        for item in opt_items:
            opt_names = item.get_options().keys()
            for opt_name in opt_names:
                assert not opt_name in all_opt_names, "Option '%s' present both in %s and in %s" % (opt_name, item, all_opt_names[opt_name])
                all_opt_names[opt_name] = item
        # create the "meta" name of the optionable pipeline, and init optionable
        name = "|".join(item.name for item in opt_items)
        Optionable.__init__(self, name)
        

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           ", ".join(repr(item) for item in self.items))

    def __call__(self, element_iter, **kwargs):
        items = self.items
        for item in items:
            item_kwargs = {}
            if isinstance(item, Optionable):
                # if Optionable, build kargs
                item_kwargs = item.parse_options(kwargs)
            element_iter = item(element_iter, **item_kwargs)
        return element_iter

    def __getitem__(self, item):
        return self.items.__getitem__(item)

    def __len__(self):
        return len(self.items)

    def __eq__(self, other):
        return (other
                and self.__class__ is other.__class__
                and self.items == other.items)

    def parse_options(self, options):
        opt = {}
        for item in self.items:
            if isinstance(item, Optionable):
                opt.update(item.parse_options(options))
        return opt

    def get_options(self):
        opt = {}
        for item in self.items:
            if isinstance(item, Optionable):
                opt.update(item.get_options())
        return opt

    def get_ordered_options(self):
        opts = []
        for item in self.items:
            if isinstance(item, Optionable):
                opts += item.get_ordered_options()
        return opts

    def force_option_value(self, opt_name, value):
        flg = False
        for item in self.items:
            if isinstance(item, Optionable):
                if opt_name in item.get_options():
                    item.force_option_value(opt_name, value)
                    flg  = True
        if not flg :
            raise KodexValueError, "Unknow option name (%s)" % opt_name

    def change_option_default(self, opt_name, default_val):
        flg = False
        for item in self.items:
            if isinstance(item, Optionable):
                if opt_name in item.get_options():
                    item.change_option_default(opt_name, default_val)
                    flg  = True
        if not flg :
            raise KodexValueError, "Unknow option name (%s)" % opt_name

    def get_default_value(self, opt_name):
        val = None
        for item in self.items:
            if isinstance(item, Optionable):
                if opt_name in item.get_options():
                    val = item.get_default_value(opt_name)
        if val is None:
            raise ValueError("'%s' is not an existing option" % opt_name)
        return val

    def close(self):
        """ Close all the element of the pipeline
        """
        for item in self.items:
            if hasattr(item, "close"):
                item.close()


#{ Document Pipeline

class DocPipelineElmt(Composable):
    """ Basic document pipeline element
    """
    def __init__(self):
        Composable.__init__(self)
    
    def __call__(self, kdocs):
        """
        :param kdocs: input generator of :class:`KodexDoc`
        :type kdocs: 
        
        :returns: generator of L{Doc}
        :rtype: (L{Doc}, ...)
        """
        raise NotImplementedError

class OptDocPipelineElmt(DocPipelineElmt, Optionable):
    """ :class:`Optionable` document pipeline element.
    """
    def __init__(self, name):
        DocPipelineElmt.__init__(self)
        Optionable.__init__(self, name)
    
    def __call__(self, kdocs, **kwargs):
        raise NotImplementedError

class DocListPipelineElmt(OptDocPipelineElmt):
    """ Excactly as :class:`OptDocPipelineElmt` except than the :func:`__call__`
    method returns a list and not a generator.
    """
    def __call__(self, kdocs):
        raise NotImplementedError

