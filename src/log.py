#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""log

Usage:
  log error <string> [options]
  log warning <string> [options]
  log info <string> [options]
  log debug <string> [options]

Options:
  --log-ini <ini>          ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>      set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  --ini-base <path>        Modify default base path for ini files.
  -h, --help               Show this screen.
  --version                Show version.
"""

import os
import sys
import socket
import logging
import watchtower
from docopt import docopt
from logging.handlers import SysLogHandler
if sys.version[:1] == '2':
    from ConfigParser import RawConfigParser
else:
    from configparser import RawConfigParser

_default_datefmt = '%b %d %H:%M:%S'

LOG_GROUP_NAME = 'recount'


def msg(sender, text, level):
    if sender is not None and len(sender) > 0:
        sender += ' '
    exc_info = sys.exc_info()[0] is not None
    logger = logging.getLogger(LOG_GROUP_NAME)
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


def debug(text, sender=''):
    msg(sender, text, logging.DEBUG)


def info(text, sender=''):
    msg(sender, text, logging.INFO)


def warning(text, sender=''):
    msg(sender, text, logging.WARNING)


def error(text, sender=''):
    msg(sender, text, logging.ERROR)


def critical(text, sender=''):
    msg(sender, text, logging.CRITICAL)


def make_default_handler(sender=None):
    """
    Set up default handler, which prints simple messages to the console.
    """
    default_handler = logging.StreamHandler()
    default_format = '%(asctime)s %(message)s'
    if sender is not None:
        # If a sender was specified, include it in the log string
        default_format = '%(asctime)s %(sender)s %(message)s'
    default_formatter = logging.Formatter(fmt=default_format, datefmt=_default_datefmt)
    default_handler.setFormatter(default_formatter)
    if sender is not None:
        add_sender_filter(default_handler, sender)
    return default_handler


def make_syslog_handler(cfg):
    host, port, fmt, datefmt = \
        cfg.get('syslog', 'host'), int(cfg.get('syslog', 'port')), \
        cfg.get('syslog', 'format'), cfg.get('syslog', 'datefmt')
    return SysLogHandler(address=(host, port))


def make_watchtower_handler(cfg):
    log_group = cfg.get('watchtower', 'log_group')
    stream_name = cfg.get('watchtower', 'stream_name')
    aws_profile = None
    if cfg.has_option('watchtower', 'aws_profile'):
        aws_profile = cfg.get('watchtower', 'aws_profile')
    # TODO: alternately, might want to create boto3 "session" for greater flexibility
    return watchtower.CloudWatchLogHandler(log_group=log_group,
                                           stream_name=stream_name,
                                           boto3_profile_name=aws_profile)


def init_logger(name, log_ini=None, level='DEBUG', agg_level='INFO', sender=None):
    lg = logging.getLogger(name)
    lg.setLevel(level if isinstance(level, int) else logging.getLevelName(level))
    lg.addHandler(make_default_handler(sender=sender))

    if log_ini is not None:
        # see comment for syslog_handler_from_ini
        info('Parsing log ini "%s"' % log_ini, 'log.py')
        cfg = RawConfigParser()
        cfg.read(log_ini)
        agg_format = '%(asctime)s %(hostname)s %(message)s'
        if sender is not None:
            agg_format = '%(asctime)s %(hostname)s %(sender)s %(message)s'
        agg_formatter = logging.Formatter(fmt=agg_format, datefmt=_default_datefmt)

        def _config_handler(hnd):
            hnd.setFormatter(agg_formatter)
            hnd.setLevel(agg_level)
            add_hostname_filter(hnd)
            if sender is not None:
                add_sender_filter(hnd, sender)
            lg.addHandler(hnd)

        if 'syslog' in cfg.sections():
            info('Found syslog handler in "%s"' % log_ini, 'log.py')
            _config_handler(make_syslog_handler(cfg))
        if 'watchtower' in cfg.sections():
            info('Found watchtower handler in "%s"' % log_ini, 'log.py')
            _config_handler(make_watchtower_handler(cfg))


def read_log_config(config_fn, section):
    cfg = RawConfigParser()
    cfg.read(config_fn)
    if section not in cfg.sections():
        raise RuntimeError('No [%s] section in log ini file "%s"' % (section, config_fn))
    return cfg.get(section, 'host'), int(cfg.get(section, 'port')),\
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
        def __init__(self, sendr):
            super(SenderFilter, self).__init__()
            self.sender = sendr

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


def test_log():
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
    assert 'blah.log_agg.com' == host
    assert 999 == port
    assert '%(asctime)s %(hostname)s recount-pump: %(message)s' == fmt
    assert '%b %d %H:%M:%S' == datefmt
    os.remove(test_fn)


def go():
    args = docopt(__doc__)

    def ini_path(argname):
        path = args[argname]
        if path.startswith('~/.recount/') and args['--ini-base'] is not None:
            path = os.path.join(args['--ini-base'], path[len('~/.recount/'):])
        return os.path.expanduser(path)

    log_ini = ini_path('--log-ini')
    init_logger(LOG_GROUP_NAME, log_ini=log_ini, agg_level=args['--log-level'])
    if args['error']:
        error(args['<string>'], 'log.py')
    elif args['warning']:
        warning(args['<string>'], 'log.py')
    elif args['info']:
        info(args['<string>'], 'log.py')
    elif args['debug']:
        debug(args['<string>'], 'log.py')


if __name__ == '__main__':
    go()
