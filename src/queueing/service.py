#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""
For more on how to install a local RabbitMQ service using Docker, see
/software/rabbitmq in this repo.
"""

import sys
import queueing.rmq
import queueing.sqs
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser
    sys.exc_clear()


def get_queueing_service(type, port, host):
    if type == 'rmq':
        return queueing.rmq.RmqService()
    elif type == 'sqs':
        return queueing.sqs.SqsService()
    else:
        raise RuntimeError('Bad queueing service type "%s"' % type)


def queueing_service_from_config(ini_fn, section):
    typ, port, host = read_queue_config(ini_fn, section)
    if typ == 'rmq':
        return queueing.rmq.RmqService(host=host, port=port)
    else:
        assert typ == 'sqs'
        return queueing.sqs.SqsService()  # TODO


def read_queue_config(ini_fn, section='queue'):
    cfg = RawConfigParser()
    cfg.read(ini_fn)
    if section not in cfg.sections():
        raise RuntimeError('No [%s] section in log ini file "%s"' % (section, ini_fn))
    typ, port, host = cfg.get(section, 'type'), cfg.getint(section, 'port'), cfg.get(section, 'host')
    if typ.lower() not in ['rmq', 'sqs']:
        raise ValueError('Bad queueing service type: "%s"' % typ)
    return typ, port, host
