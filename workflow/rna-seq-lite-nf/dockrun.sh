#!/bin/sh

# Author: Ben Langmead
#  Email: langmea@cs.jhu.edu
#   Date: 1/5/2018

# Runs a docker container containing the next flow script and its
# in-container driver, setting up these directory mappings ahead of
# time:
#  first arg -> /recount-input
#  second arg -> /recount-output
#  ${RECOUNT_REF} -> /recount-ref
#  ${RECOUNT_TEMP} -> /recount-temp

set -ex

IMAGE=$(cat image.txt)
NAME=rna_seq_lite

INPUT_DIR=`realpath $1`
OUTPUT_DIR=`realpath $2`
shift 2

test -n "${INPUT_DIR}"
test -d "${INPUT_DIR}"

test -n "${OUTPUT_DIR}"
test -d "${OUTPUT_DIR}"

test -n "${RECOUNT_REF}"
test -d "${RECOUNT_REF}"

test -n "${RECOUNT_TEMP}"
test -d "${RECOUNT_TEMP}"

docker run \
    -v `pwd`:/app \
    -e "INPUT=/recount-input" \
    -e "OUTPUT=/recount-output" \
    -e "RECOUNT_REF=/recount-ref" \
    -e "RECOUNT_TEMP=/recount-temp" \
    -v ${INPUT_DIR}:/recount-input \
    -v ${OUTPUT_DIR}:/recount-output \
    -v ${RECOUNT_REF}:/recount-ref \
    -v ${RECOUNT_TEMP}:/recount-temp \
    ${IMAGE} \
    /bin/bash -c \
    "source activate rnaseq_lite && bash /tmp/rna_seq_lite.bash"
