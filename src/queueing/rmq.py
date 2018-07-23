#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""
Some discussion about how RabbitMQ/AMQP notions like 'exchanges' translate
into SQS:

https://stackoverflow.com/questions/46880229/migrate-from-amqp-to-amazon-sns-sqs-need-to-understand-concepts
"""

import pytest
import pika
import pika.exceptions


class RmqService():

    def __init__(self, host='localhost', port=5672):
        self.params = pika.ConnectionParameters(host=host, port=port)
        self.connection = pika.BlockingConnection(parameters=self.params)
        self.channel = self.connection.channel()
        self.get_outstanding = False
        self.get_queue, self.get_delivery_tag = None, None

    def close(self):
        self.connection.close()

    def get(self, queue):
        # If you want to be notified of Basic.GetEmpty, use the
        # Channel.add_callback method adding your Basic.GetEmpty callback which should expect only one parameter, frame
        if self.get_outstanding:
            raise RuntimeError('Already have a get outstanding')
        method_frame, header_frame, body = self.channel.basic_get(queue=queue)
        if method_frame is None:
            return None
        if method_frame.NAME != 'Basic.GetOk':
            raise RuntimeError('Reponse from basic_get was "%s" (not Basic.GetOk)', method_frame.NAME)
        self.get_outstanding = True
        self.get_queue = queue
        self.get_delivery_tag = method_frame.delivery_tag
        return body

    def queue_create(self, name):
        if self.queue_exists(name):
            raise RuntimeError('Queue with name "%s" already exists', name)
        self.channel.queue_declare(queue=name)

    def queue_exists(self, name):
        try:
            self.channel.queue_declare(queue=name, passive=True)
        except pika.exceptions.ChannelClosed:
            self.channel = self.connection.channel()
            return False
        return True

    def queue_delete(self, name, if_empty=False):
        self.channel.queue_delete(queue=name, if_empty=if_empty)

    def ack(self):
        if not self.get_outstanding:
            raise RuntimeError('No get outstanding')
        assert self.get_queue is not None
        self.channel.basic_ack(delivery_tag=self.get_delivery_tag)
        self.get_outstanding = False
        self.get_queue = None
        self.get_delivery_tag = None

    def publish(self, queue, message):
        self.channel.basic_publish(exchange='',  # default exchange
                                   routing_key=queue,
                                   body=message)


def test_create_delete(q_enabled, q_service):
    if not q_enabled: pytest.skip('Skipping RMQ tests')
    assert not q_service.queue_exists('TestRmq')
    q_service.queue_create('TestRmq')
    assert q_service.queue_exists('TestRmq')
    q_service.queue_delete('TestRmq', if_empty=True)
    assert not q_service.queue_exists('TestRmq')


def test_publish(q_enabled, q_service):
    if not q_enabled: pytest.skip('Skipping RMQ tests')
    assert not q_service.queue_exists('TestRmq')
    q_service.queue_create('TestRmq')
    assert q_service.queue_exists('TestRmq')
    q_service.publish('TestRmq', 'test_publish_1')
    q_service.publish('TestRmq', 'test_publish_2')
    q_service.publish('TestRmq', 'test_publish_3')
    q_service.queue_delete('TestRmq')
    assert not q_service.queue_exists('TestRmq')


def test_publish_get_1(q_enabled, q_service):
    if not q_enabled: pytest.skip('Skipping RMQ tests')
    assert not q_service.queue_exists('TestRmq')
    q_service.queue_create('TestRmq')
    q_service.publish('TestRmq', 'test_publish_get_1 1')
    q_service.publish('TestRmq', 'test_publish_get_1 2')
    q_service.publish('TestRmq', 'test_publish_get_1 3')
    msg1 = q_service.get('TestRmq')
    assert b'test_publish_get_1 1' == msg1
    q_service.ack()
    msg2 = q_service.get('TestRmq')
    assert b'test_publish_get_1 2' == msg2
    q_service.ack()
    msg3 = q_service.get('TestRmq')
    assert b'test_publish_get_1 3' == msg3
    q_service.ack()
    # messages might be requeued since they're unacknowledged
    q_service.queue_delete('TestRmq')
    assert not q_service.queue_exists('TestRmq')


def test_get_empty(q_enabled, q_service):
    if not q_enabled: pytest.skip('Skipping RMQ tests')
    assert not q_service.queue_exists('TestRmq')
    q_service.queue_create('TestRmq')
    q_service.publish('TestRmq', 'test_get_empty_1 1')
    msg1 = q_service.get('TestRmq')
    assert b'test_get_empty_1 1' == msg1
    q_service.ack()
    msg2 = q_service.get('TestRmq')
    q_service.queue_delete('TestRmq')
    assert not q_service.queue_exists('TestRmq')
