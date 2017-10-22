#!/usr/bin/env python

"""
Modeled on: http://boto3.readthedocs.io/en/latest/guide/sqs.html
"""

"""
Notes from: http://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide
- Every AWS resource is owned by an AWS account
- The AWS account owns the resources that are created in the account, regardless of who created the resources
- Permissions to create or access a resource are governed by permissions policies
- In Amazon SQS, the only resource is the queue
- Queue ARNs have the form arn:aws:sqs:region:account_id:queue_name
- An ARN that uses * or ? as a wildcard for the queue name
"""

import boto3

# Get the service resource
sqs = boto3.resource('sqs')

# Create the queue. This returns an SQS.Queue instance
queue = sqs.create_queue(QueueName='test', Attributes={'DelaySeconds': '5'})

# You can now access identifiers and attributes
print(queue.url)
print(queue.attributes.get('DelaySeconds'))
