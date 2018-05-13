#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

import os
import logging
from ConfigParser import RawConfigParser

log_ini_dir = os.path.expanduser('~/.recount')
log_ini_fn = os.path.join(log_ini_dir, 'log.ini')


def read_log_config(config_fn=log_ini_fn, section='log'):
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


if __name__ == '__main__':
    import socket
    from logging.handlers import SysLogHandler

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    add_hostname_filter(logger)
    add_syslog_handler(logger)

    logger.info("This is a message")
