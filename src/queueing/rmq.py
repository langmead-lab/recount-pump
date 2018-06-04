#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""
Some discussion about how RabbitMQ/AMQP notions like 'exchanges' translate
into SQS:

https://stackoverflow.com/questions/46880229/migrate-from-amqp-to-amazon-sns-sqs-need-to-understand-concepts
"""

import pika
import pika.exceptions
import unittest
import generic


class RmqService(generic.Service):

    def __init__(self, host='localhost'):
        self.params = pika.ConnectionParameters(host)
        self.connection = pika.BlockingConnection()
        self.channel = self.connection.channel()
        self.get_outstanding = False
        self.get_queue, self.get_delivery_tag = None, None

    def get(self, queue):
        # If you want to be notified of Basic.GetEmpty, use the
        # Channel.add_callback method adding your Basic.GetEmpty callback which should expect only one parameter, frame
        if self.get_outstanding:
            raise RuntimeError('Already have a get outstanding')
        method_frame, header_frame, body = self.channel.basic_get(queue=queue)
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


class TestRmqService(unittest.TestCase):

    def setUp(self):
        service = RmqService()
        if service.queue_exists('TestRmq'):
            service.queue_delete('TestRmq')

    def test_create_delete(self):
        service = RmqService()
        self.assertFalse(service.queue_exists('TestRmq'))
        service.queue_create('TestRmq')
        self.assertTrue(service.queue_exists('TestRmq'))
        service.queue_delete('TestRmq', if_empty=True)
        self.assertFalse(service.queue_exists('TestRmq'))

    def test_publish(self):
        service = RmqService()
        self.assertFalse(service.queue_exists('TestRmq'))
        service.queue_create('TestRmq')
        self.assertTrue(service.queue_exists('TestRmq'))
        service.publish('TestRmq', 'test_publish_1')
        service.publish('TestRmq', 'test_publish_2')
        service.publish('TestRmq', 'test_publish_3')
        service.queue_delete('TestRmq')
        self.assertFalse(service.queue_exists('TestRmq'))

    def test_publish_get_1(self):
        service = RmqService()
        self.assertFalse(service.queue_exists('TestRmq'))
        service.queue_create('TestRmq')
        service.publish('TestRmq', 'test_publish_get_1 1')
        service.publish('TestRmq', 'test_publish_get_1 2')
        service.publish('TestRmq', 'test_publish_get_1 3')
        msg1 = service.get('TestRmq')
        self.assertEqual('test_publish_get_1 1', msg1)
        service.ack()
        msg2 = service.get('TestRmq')
        self.assertEqual('test_publish_get_1 2', msg2)
        service.ack()
        msg3 = service.get('TestRmq')
        self.assertEqual('test_publish_get_1 3', msg3)
        service.ack()
        # messages might be requeued since they're unacknowledged
        service.queue_delete('TestRmq')
        self.assertFalse(service.queue_exists('TestRmq'))


if __name__ == '__main__':
    unittest.main()