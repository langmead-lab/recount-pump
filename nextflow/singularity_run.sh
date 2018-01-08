#!/bin/sh

# Author: Ben Langmead
#  Email: langmea@cs.jhu.edu
#   Date: 1/5/2018

# Runs a singularity container containing the next flow script and its
# in-container driver, setting up these directory mappings ahead of
# time:
#  first arg -> /recount-input
#  second arg -> /recount-output
#  ${RECOUNT_REF} -> /recount-ref
#  ${RECOUNT_TEMP} -> /recount-temp

set -ex

IMAGE="shub://langmead-lab/recount-pump:recount-pump"

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

singularity exec \
    --bind ${INPUT_DIR}:/recount-input \
    --bind ${OUTPUT_DIR}:/recount-output \
    --bind ${RECOUNT_REF}:/recount-ref \
    --bind ${RECOUNT_TEMP}:/recount-temp \
    ${IMAGE} \
    /bin/bash -c \
    "source activate rnaseq_v0 && bash /home/biodocker/bin/rna_seq.bash"
