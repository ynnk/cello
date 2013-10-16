#-*- coding:utf-8 -*-
""" :mod:`cello.utils.log`
=========================

:copyright: (c) 2013 - 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}

Helper function to setup a basic logger for a cello app
"""

import logging
    
#{ logging

# NullHandler is not defined in python < 2.6
try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

def get_basic_logger(level=logging.WARN):
    """ return a basic logger that print on stdout msg from cello lib
    """
    logger = logging.getLogger('cello')
    logger.setLevel(level)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(level)
    # create formatter and add it to the handlers
    formatter = ColorFormatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(ch)
    return logger


class ColorFormatter(logging.Formatter):
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
    COLORS = {
        'WARNING'  : YELLOW,
        'INFO'     : WHITE,
        'DEBUG'    : BLUE,
        'CRITICAL' : YELLOW,
        'ERROR'    : RED,
        
        'RED'      : RED,
        'GREEN'    : GREEN,
        'YELLOW'   : YELLOW,
        'BLUE'     : BLUE,
        'MAGENTA'  : MAGENTA,
        'CYAN'     : CYAN,
        'WHITE'    : WHITE,
    }
    RESET_SEQ = "\033[0m"
    COLOR_SEQ = "\033[1;%dm"
    BOLD_SEQ  = "\033[1m"
    # Add a color formater for logging messagess

    def __init__(self, *args, **kwargs):
        # can't do super(...) here because Formatter is an old school class
        logging.Formatter.__init__(self, *args, **kwargs)

    def format(self, record):
        levelname = record.levelname
        color     = ColorFormatter.COLOR_SEQ % (30 + ColorFormatter.COLORS[levelname])
        message   = logging.Formatter.format(self, record)
        message   = message.replace("$RESET", ColorFormatter.RESET_SEQ)\
                           .replace("$BOLD",  ColorFormatter.BOLD_SEQ)\
                           .replace("$COLOR", color)
        for k,v in ColorFormatter.COLORS.items():
            message = message.replace("$" + k,    ColorFormatter.COLOR_SEQ % (v+30))\
                             .replace("$BG" + k,  ColorFormatter.COLOR_SEQ % (v+40))\
                             .replace("$BG-" + k, ColorFormatter.COLOR_SEQ % (v+40))
        return message + ColorFormatter.RESET_SEQ




def get_app_logger_color(appname, app_log_level=logging.INFO, log_level=logging.WARN):
    """ Configure the logging for an app using cello
    """
    # create lib handler
    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(log_level)
    # create formatter and add it to the handlers
    name = "cello" + "_"*(max(0, len(appname)-5))
    formatter = ColorFormatter('$BG-BLUE$WHITE%s$RESET:%%(asctime)s:$COLOR%%(levelname)s$RESET:$BOLD%%(name)s$RESET: %%(message)s' % name)
    stderr_handler.setFormatter(formatter)
    # get the logers it self
    logger = logging.getLogger("cello")
    logger.setLevel(logging.DEBUG)
    # add the handlers to the loggers
    logger.addHandler(stderr_handler)
    
    # create app handler
    app_stderr_handler = logging.StreamHandler()
    app_stderr_handler.setLevel(app_log_level)
    # create formatter and add it to the handlers
    app_formatter = ColorFormatter("$BG-CYAN$WHITE%s$RESET:%%(asctime)s:$COLOR%%(levelname)s$RESET:$BOLD%%(name)s$RESET: %%(message)s" % appname.upper())
    app_stderr_handler.setFormatter(app_formatter)
    # get the logers it self
    app_logger = logging.getLogger(appname)
    app_logger.setLevel(logging.DEBUG)
    # add the handlers to the loggers
    app_logger.addHandler(app_stderr_handler)
    return app_logger

#}
