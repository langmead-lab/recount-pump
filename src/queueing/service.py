#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""
For more on how to install a local RabbitMQ service using Docker, see
/software/rabbitmq in this repo.
"""

import rmq
import sqs
import abc


class Service(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get(self, queue):
        pass

    @abc.abstractmethod
    def queue_create(self, name):
        pass

    @abc.abstractmethod
    def queue_exists(self, name):
        pass

    @abc.abstractmethod
    def queue_delete(self, name, if_empty=False):
        pass

    @abc.abstractmethod
    def ack(self):
        pass

    @abc.abstractmethod
    def publish(self, queue, message):
        pass


def get_queueing_service(type='rmq'):
    if type == 'rmq':
        return rmq.RmqService()
    elif type == 'sqs':
        return sqs.SqsService()
    else:
        raise RuntimeError('Bad queueing service type "%s"' % type)
