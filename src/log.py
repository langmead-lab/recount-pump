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
from docopt import docopt
from logging.handlers import SysLogHandler
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser
    sys.exc_clear()

_default_log_ini_dir = os.path.expanduser('~/.recount')
_default_log_ini_fn = os.path.join(_default_log_ini_dir, 'log.ini')
_default_log_ini_fn_section = 'log'
_default_datefmt = '%b %d %H:%M:%S'


def msg(name, sender, text, level):
    if sender is not None and len(sender) > 0:
        sender += ' '
    exc_info = sys.exc_info()[0] is not None
    logger = logging.getLogger(name)
    if level == logging.DEBUG:
        logger.debug(sender + text, exc_info=exc_info)
    elif level == logging.INFO:
        logger.info(sender + text, exc_info=exc_info)
    if level == logging.WARNING:
        logger.warning(sender + text, exc_info=exc_info)
    if level == logging.ERROR:
        logger.error(sender + text, exc_info=exc_info)
    if level == logging.CRITICAL:
        logger.critical(sender + text, exc_info=exc_info)


def debug(name, text, sender=''):
    msg(name, sender, text, logging.DEBUG)


def info(name, text, sender=''):
    msg(name, sender, text, logging.INFO)


def warning(name, text, sender=''):
    msg(name, sender, text, logging.WARNING)


def error(name, text, sender=''):
    msg(name, sender, text, logging.ERROR)


def critical(name, text, sender=''):
    msg(name, sender, text, logging.CRITICAL)


def init_logger(name, aggregation_ini=None, aggregation_section='log',
                level='DEBUG', agg_level='INFO', sender=None):
    lg = logging.getLogger(name)
    lg.setLevel(level if isinstance(level, int) else logging.getLevelName(level))

    # First set up default handler, to console with simple message
    default_handler = logging.StreamHandler()
    default_format = '%(asctime)s %(message)s'
    if sender is not None:
        # If a sender was specified, include it in the log string
        default_format = '%(asctime)s %(sender)s %(message)s'
    default_formatter = logging.Formatter(fmt=default_format, datefmt=_default_datefmt)
    default_handler.setFormatter(default_formatter)
    if sender is not None:
        add_sender_filter(default_handler, sender)
    lg.addHandler(default_handler)

    if aggregation_ini is not None:
        # see comment for syslog_handler_from_ini

        host, port, fmt, datefmt = read_log_config(config_fn=aggregation_ini,
                                                   section=aggregation_section)
        agg_handler = SysLogHandler(address=(host, port))
        agg_format = '%(asctime)s %(hostname)s %(message)s'
        if sender is not None:
            agg_format = '%(asctime)s %(hostname)s %(sender)s %(message)s'
        agg_formatter = logging.Formatter(fmt=agg_format, datefmt=_default_datefmt)
        agg_handler.setFormatter(agg_formatter)
        agg_handler.setLevel(agg_level)
        add_hostname_filter(agg_handler)
        if sender is not None:
            add_sender_filter(agg_handler, sender)
        lg.addHandler(agg_handler)


def read_log_config(config_fn, section):
    cfg = RawConfigParser()
    cfg.read(config_fn)
    if section not in cfg.sections():
        raise RuntimeError('No [%s] section in log ini file "%s"' % (section, config_fn))
    return cfg.get(section, 'host'), int(cfg.get(section, 'port')), \
           cfg.get(section, 'format'), cfg.get(section, 'datefmt')


def add_sender_filter(add_to, sender):
    """
    add_to could be a handler or a logger.  For our purposes it's probably a
    handler for a log aggregator.
    """

    class SenderFilter(logging.Filter):
        """
        "Filter" seems just to annotate log messages with hostname
        """
        def __init__(self, sender):
            super(SenderFilter, self).__init__()
            self.sender = sender

        def filter(self, record):
            record.sender = self.sender
            return True

    add_to.addFilter(SenderFilter(sender))


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


class TestLog(unittest.TestCase):

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
        host, port, fmt, datefmt = read_log_config(config_fn=test_fn, section='mylog')
        self.assertEqual('blah.log_agg.com', host)
        self.assertEqual(999, port)
        self.assertEqual('%(asctime)s %(hostname)s recount-pump: %(message)s', fmt)
        self.assertEqual('%b %d %H:%M:%S', datefmt)
        os.remove(test_fn)


if __name__ == '__main__':
    args = docopt(__doc__)

    if args['test']:
        del sys.argv[1:]
        unittest.main()
    elif args['message']:
        agg_ini = os.path.expanduser(args['--log-ini']) if args['--aggregate'] else None
        init_logger(__name__, aggregation_ini=agg_ini,
                    aggregation_section=args['--log-section'],
                    agg_level=args['--log-level'], sender='log.py')
        info(__name__, 'This is an info message')
        debug(__name__, 'This is a debug message')
