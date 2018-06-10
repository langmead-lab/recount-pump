#!/bin/sh

echo "=== Showing 'minio' configuration ==="

aws configure list --profile minio

echo "=== Adding 'test' bucket ==="

aws --endpoint-url http://127.0.0.1:9000 --profile minio s3 mb s3://test

echo "=== Listing buckets ==="

aws --endpoint-url http://127.0.0.1:9000 --profile minio s3 ls
