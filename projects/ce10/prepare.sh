#!/bin/bash

set -ex

export RECOUNT_INTEGRATION_TEST=1
if [[ -d creds ]] ; then
    rm -rf creds.old
    mv creds creds.old
fi
./setup.sh && ../common/make_creds.py
docker image ls -q quay.io/benlangmead/recount-rs5:latest
