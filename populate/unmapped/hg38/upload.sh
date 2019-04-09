#!/bin/sh

aws --profile jhu-langmead s3 cp \
    --acl public-read \
    unmapped_hisat2_idx.tar.gz \
    s3://recount-ref/hg38/
