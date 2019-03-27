#!/bin/bash

set -e

which mc
mc stat s3/recount-meta/ce10_test/ce10_test.txt.gz
mc stat s3/recount-ref/ce10/star_idx.tar.gz
mc mb --ignore-existing s3/recount-output

