#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""
For more on how to install a local RabbitMQ service using Docker, see
/software/rabbitmq in this repo.
"""

import rmq
import sqs


def get_queueing_service(type='rmq'):
    if type == 'rmq':
        return rmq.RmqService()
    elif type == 'sqs':
        return sqs.SqsService()
    else:
        raise RuntimeError('Bad queueing service type "%s"' % type)
