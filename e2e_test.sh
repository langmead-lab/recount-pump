#!/bin/bash

set -ex

export RECOUNT_INTEGRATION_TEST=1
pushd projects/ce10
rm -rf creds
./setup.sh && ../common/make_creds.py
test -d creds
docker image ls -q quay.io/benlangmead/recount-rs5:latest
./check_buckets.sh && ../common/init_model.sh && ./run.sh
