#!/bin/bash

d=$(dirname $0)

python \
    ../../src/run.py go \
    --ini-base ${d}/../../creds/.recount \
    run_docker_test \
    $(cat image.txt) \
    "" \
    "{}" \
    ../common/accessions.txt \
    --fail-on-error
