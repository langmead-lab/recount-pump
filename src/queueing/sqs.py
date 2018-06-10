#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

import unittest
import boto3


class SqsService(object):
    def __init__(self):
        pass


def new_session(q_url, fake_client=False):
    return boto3.client('sqs'), q_url


def new_queue_and_session(name):
    client = boto3.client('sqs')
    resp = client.create_queue(QueueName=name)
    status = resp['HTTPStatusCode']
    if status != 200:
        raise IOError('Non-OK HTTPStatusCode after attempt to create queue with name "%s"' % (name))
    q_url = resp['QueueUrl']
    return client, q_url


def list_queues(session):
    client, q_url = session
    res = client.list_queues()
    return res.get('QueueUrls', None)


def receive_message(session):
    client, q_url = session
    resp = client.receive_message(QueueUrl=q_url)
    status = resp['HTTPStatusCode']
    if status != 200:
        raise IOError('Non-OK HTTPStatusCode after attempt to receive message from "%s": %d' % (q_url, status))
    if 'Messages' in resp:
        msgs = resp['Messages']
        if len(msgs) != 1:
            raise ValueError('Expected exactly one message, response for receive_message, got: %s' % (str(msgs)))
        msg = msgs[0]
        return (msg[u'Body'],
                lambda: client.delete_message(QueueUrl=q_url,
                                              ReceiptHandle=msg[u'ReceiptHandle']))
    return None, None


def send_message(session, body):
    client, q_url = session
    resp = client.send_message(QueueUrl=q_url, MessageBody=body)
    status = resp['HTTPStatusCode']
    if status != 200:
        raise IOError('Non-OK HTTPStatusCode after attemp to send message to "%s": %d' % (q_url, status))


def get_queue_attributes(client, q_url):
    resp = client.get_queue_attributes(QueueUrl=q_url, AttributeNames=['All'])
    return resp[u'Attributes']


class TestSqs(unittest.TestCase):

    def test_simple_source_insert(self):
        pass


if __name__ == '__main__':
    pass
