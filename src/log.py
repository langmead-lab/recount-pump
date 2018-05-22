#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

import os
import logging
import unittest
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser

_log_ini_dir = os.path.expanduser('~/.recount')
_log_ini_fn = os.path.join(_log_ini_dir, 'log.ini')
_default_format = '%(asctime)s %(message)s'
_default_datefmt = '%b %d %H:%M:%S'


def new_default_formatter():
    return logging.Formatter(fmt=_default_format, datefmt=_default_datefmt)


def new_logger(with_aggregation=True, level=logging.INFO):
    logger = logging.getLogger()
    if with_aggregation:
        add_hostname_filter(logger)
        add_syslog_handler(logger)
    formatter = new_default_formatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.debug('Created logger')
    return logger


def read_log_config(config_fn=_log_ini_fn, section='log'):
    cfg = RawConfigParser()
    cfg.read(config_fn)
    if section not in cfg.sections():
        raise RuntimeError('No [%s] section in log ini file "%s"' % (section, config_fn))
    host = cfg.get(section, 'host')
    port = cfg.get(section, 'port')
    port = int(port)
    format = cfg.get(section, 'format')
    datefmt = cfg.get(section, 'datefmt')
    return host, port, format, datefmt 


def add_hostname_filter(logger):

    class ContextFilter(logging.Filter):
        """
        "Filter" seems just to annotate log messages with hostname
        """
        hostname = socket.gethostname()

        def filter(self, record):
            record.hostname = ContextFilter.hostname
            return True

    f = ContextFilter()
    logger.addFilter(f)


def add_syslog_handler(logger):
    host, port, format, datefmt = read_log_config()

    syslog = SysLogHandler(address=(host, port))
    formatter = logging.Formatter(format, datefmt=datefmt)

    syslog.setFormatter(formatter)
    logger.addHandler(syslog)


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
    import socket
    from logging.handlers import SysLogHandler

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    add_hostname_filter(logger)
    add_syslog_handler(logger)

    logger.info("This is a message")
