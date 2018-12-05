#!/bin/sh

aws --profile jhu-langmead s3 cp --acl public-read \
    srav1.txt s3://recount-meta/srav1/srav1.txt
