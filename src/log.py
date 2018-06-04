#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""log

Usage:
  log test [options]
  log message [options]

Options:
  --log-ini <ini>          ini file for log aggregator [default: ~/.recount/log.ini].
  --log-section <section>  ini file section for log aggregator [default: log].
  --log-level <level>      set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  -a, --aggregate          enable log aggregation.
  -h, --help               Show this screen.
  --version                Show version.
"""

import os
import sys
import socket
import unittest
import logging
import watchtower
from docopt import docopt
from logging.handlers import SysLogHandler
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser

_default_log_ini_dir = os.path.expanduser('~/.recount')
_default_log_ini_fn = os.path.join(_default_log_ini_dir, 'log.ini')
_default_log_ini_fn_section = 'log'
_default_format = '%(asctime)s %(message)s'
_default_format_with_hostname = '%(asctime)s %(hostname)s %(message)s'
_default_datefmt = '%b %d %H:%M:%S'


def msg(name, module, text, level):
    if level == logging.DEBUG:
        logging.getLogger(name).debug(module + ': ' + text)
    elif level == logging.INFO:
        logging.getLogger(name).info(module + ': ' + text)
    if level == logging.WARNING:
        logging.getLogger(name).warning(module + ': ' + text)
    if level == logging.ERROR:
        logging.getLogger(name).error(module + ': ' + text)
    if level == logging.CRITICAL:
        logging.getLogger(name).critical(module + ': ' + text)


def debug(name, module, text):
    msg(name, module, text, logging.DEBUG)


def info(name, module, text):
    msg(name, module, text, logging.INFO)


def warning(name, module, text):
    msg(name, module, text, logging.WARNING)


def error(name, module, text):
    msg(name, module, text, logging.ERROR)


def critical(name, module, text):
    msg(name, module, text, logging.CRITICAL)


def new_default_formatter():
    return logging.Formatter(fmt=_default_format, datefmt=_default_datefmt)


def init_loggers(names, aggregation_ini=None, aggregation_section='log',
                 level=logging.DEBUG, agg_level=logging.INFO):
    for name in names:
        lg = logging.getLogger(name)
        lg.setLevel(level)

        # First set up default handler, to console with simple message
        default_handler = logging.StreamHandler()
        default_formatter = logging.Formatter(fmt=_default_format, datefmt=_default_datefmt)
        default_handler.setFormatter(default_formatter)
        lg.addHandler(default_handler)

        if aggregation_ini is not None:
            # see comment for syslog_handler_from_ini
            agg_handler = syslog_handler_from_ini(
                aggregation_ini, aggregation_section, agg_level)
            lg.addHandler(agg_handler)

        return lg


def read_log_config(config_fn, section):
    cfg = RawConfigParser()
    cfg.read(config_fn)
    if section not in cfg.sections():
        raise RuntimeError('No [%s] section in log ini file "%s"' % (section, config_fn))
    return cfg.get(section, 'host'), int(cfg.get(section, 'port')), \
           cfg.get(section, 'format'), cfg.get(section, 'datefmt')


def add_hostname_filter(add_to):
    """
    add_to could be a handler or a logger.  For our purposes it's probably a
    handler for a log aggregator.
    """

    class ContextFilter(logging.Filter):
        """
        "Filter" seems just to annotate log messages with hostname
        """
        hostname = socket.gethostname()

        def filter(self, record):
            record.hostname = ContextFilter.hostname
            return True

    add_to.addFilter(ContextFilter())


def syslog_handler_from_ini(ini_fn=_default_log_ini_fn,
                            ini_section=_default_log_ini_fn_section,
                            agg_level=logging.INFO):
    """
    For when using a log aggregator is as simple as specifying a few settings
    like this:

    [log]
    host = keep-my-logs.service.com
    port = 777
    format = %(asctime)s %(hostname)s recount-pump: %(message)s
    datefmt = %b %d %H:%M:%S
    """
    host, port, fmt, datefmt = read_log_config(config_fn=ini_fn, section=ini_section)
    agg_handler = SysLogHandler(address=(host, port))
    add_hostname_filter(agg_handler)
    agg_formatter = logging.Formatter(fmt=_default_format_with_hostname, datefmt=_default_datefmt)
    agg_handler.setFormatter(agg_formatter)
    agg_handler.setLevel(agg_level)
    return agg_handler


class TestReference(unittest.TestCase):

    def test_simple_source_insert(self):
        config = """[mylog]
host = blah.log_agg.com
port = 999
format = %(asctime)s %(hostname)s recount-pump: %(message)s
datefmt = %b %d %H:%M:%S
"""
        test_fn = '.tmp.init'
        with open(test_fn, 'w') as fh:
            fh.write(config)
        host, port, format, datefmt = read_log_config(config_fn=test_fn, section='mylog')
        self.assertEqual('blah.log_agg.com', host)
        self.assertEqual(999, port)
        self.assertEqual('%(asctime)s %(hostname)s recount-pump: %(message)s', format)
        self.assertEqual('%b %d %H:%M:%S', datefmt)
        os.remove(test_fn)


if __name__ == '__main__':
    args = docopt(__doc__)

    if args['test']:
        del sys.argv[1:]
        unittest.main()
    elif args['message']:
        agg_ini = os.path.expanduser(args['--log-ini']) if args['--aggregate'] else None
        init_loggers([__name__], aggregation_ini=agg_ini,
                     aggregation_section=args['--log-section'],
                     agg_level=args['--log-level'])
        info(__name__, 'log.py', "This is an info message")
        debug(__name__, 'log.py', "This is a debug message")
