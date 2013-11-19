#-*- coding:utf-8 -*-
""" :mod:`cello.utils`
======================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

.. toctree::

    cello.utils.graph
    cello.utils.prox
    cello.utils.log

"""

#{ urllib2

import re
import urllib2
import logging
import simplejson as json

JSON_CLEAN_LAST_COMMA = re.compile(",([\s]*\})")
def _json_text_clean(json_text):
    return JSON_CLEAN_LAST_COMMA.sub(r"\1", json_text).strip()


def urllib2_json_urlopen(request_url, request_data=None, logger=None):
    """ Make a request with urllib2 and retrive a JSON
    """
    request_url = request_url.encode('utf8')
    
    if logger is not None:
        logger.debug("urllib2: open url = %s" % request_url)
        logger.debug("urllib2: with params = %s" % request_data)
        
    response = urllib2.urlopen(request_url, request_data)
    json_text = response.read()
    json_text = _json_text_clean(json_text)
    # data are provided in json
    try:
        results = json.loads(json_text)
    except ValueError:
        logger.error("Fail to parse the json: %s" % json_text)
        raise
    response.close()
    return results

def urllib2_setup_proxy(proxy=None):
    """ Setup a proxy for urllib2
    """
    # urllib2 tries to use the proxy to find the localhost
    # Proxy support may not work at irit if no empty is set for the request
    if proxy:
        proxy_support = urllib2.ProxyHandler({'http' : proxy})
        opener = urllib2.build_opener(proxy_support)
        urllib2.install_opener(opener)

#}


def deprecated(new_fct_name, logger=None):
    if logger is None:
        logger = logging.getLogger("kodex")
    nfct_name = new_fct_name
    def aux_deprecated(func):
        """This is a decorator which can be used to mark functions
        as deprecated. It will result in a warning being emmitted
        when the function is used."""
        def newFunc(*args, **kwargs):
            msg = "DeprecationWarning: use '%s' instead of '%s'." % (new_fct_name, func.__name__)
            logger.warning(msg)
            warnings.warn(msg, category=DeprecationWarning)
            return func(*args, **kwargs)
        newFunc.__name__ = func.__name__
        newFunc.__doc__ = func.__doc__
        newFunc.__dict__.update(func.__dict__)
        return newFunc
    return aux_deprecated
