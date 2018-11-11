#!/bin/bash

python \
    ../../src/run.py go \
    run_docker_test \
    $(cat image.txt) \
    "" \
    "{}" \
    ../common/accessions.txt
