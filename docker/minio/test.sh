#!/bin/sh

echo "=== Showing 'minio' configuration ==="

aws configure list --profile minio

echo "=== Listing buckets ==="

aws --endpoint-url http://127.0.0.1:9000 --profile minio s3 ls
