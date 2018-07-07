#!/usr/bin/env python

from __future__ import print_function
import boto3
import os

print('Opening session')
profile = 'minio'
session = boto3.Session(profile_name=profile)
s3 = session.resource('s3', endpoint_url='http://127.0.0.1:9000')

print('Listing buckets')
names = [b.name for b in s3.buckets.all()]
print(names)

if 'python-test' not in names:
    bucket = s3.create_bucket(Bucket='python-test')
    bucket.wait_until_exists()
else:
    bucket = s3.Bucket('python-test')

print('Writing file')
with open('.test.txt', 'wb') as fh:
    print(b'Hello, world!', file=fh)
with open('.test.txt', 'rb') as fh:
    bucket.put_object(Key='python-test.txt', Body=fh)

print('Getting file')
if os.path.exists('python-test.txt'):
    os.remove('python-test.txt')
bucket.download_file('python-test.txt', 'python-test.txt')

if not os.path.exists('python-test.txt'):
    raise RuntimeError('failed to get file')

with open('python-test.txt', 'rb') as fh:
    for ln in fh:
        print('FILE: ' + ln, end='')

print('PASSED')
