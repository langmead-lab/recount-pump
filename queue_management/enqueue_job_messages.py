import argparse
#import boto.sqs
import boto3
#from boto.sqs.message import Message
import json
import sys
import os

parser = argparse.ArgumentParser(description='Enqueues passed in list of messages onto an AWS SQS queue')

parser.add_argument(
    '-q', '--queue', dest='queue', type=str, required=True,
    help='The name of the AWS SQS queue to save.')

parser.add_argument(
    '-a', '--account', dest='account', type=str,
    help='The AWS account ID whose queue is being saved.')

parser.add_argument(
    '-f', '--file', dest='input', type=str, required=True,
    help='The file listing the message strings to enqueue')

parser.add_argument(
    '-r', '--region', dest='aws_region', type=str, required=True,
    help='The AWS region where the queue is located.')

parser.add_argument(
    '-k', '--key', dest='aws_key', type=str, required=False,
    help='Your AWS account key.')

parser.add_argument(
    '-s', '--secret', dest='aws_secret', type=str, required=False,
    help='Your AWS account secret.')

args = parser.parse_args()

boto3_session = boto3.session.Session(profile_name='jhu-langmead')
sqs_client = boto3_session.client('sqs', endpoint_url=None, region_name=args.aws_region)
q_url = sqs_client.get_queue_url(QueueName=args.queue)['QueueUrl']

#adapted from from src/pump.py:stage_project(...)
sys.stderr.write('stage_project using sqs queue url ' + args.queue + '\n')
n = 0
with open(args.input,"r") as fin:
    for job_str in fin:
        job_str=job_str.rstrip()
        sys.stderr.write('stage job %s to %s\n' % (job_str, args.queue))
        resp = sqs_client.send_message(QueueUrl=q_url, MessageBody=job_str)
        meta = resp['ResponseMetadata']
        status = meta['HTTPStatusCode']
        if status != 200:
            raise IOError('bad status code (%d) after attempt to send message to: %s' % (status, q_url))
        n += 1
    if n == 0:
        raise RuntimeError('No jobs staged')
