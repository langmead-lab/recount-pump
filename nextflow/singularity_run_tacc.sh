#!/bin/sh

# Author: Ben Langmead
#  Email: langmea@cs.jhu.edu
#   Date: 1/5/2018

# Runs a singularity container containing the next flow script and its
# in-container driver.  Assumes we're running on TACC, where no user-
# defined directory binding is allowed.  Instead we have to use the
# TACC-standard bind points: $SCRATCH to /scratch, $WORK to /work, and
# $HOME to /home1.

# To accomplish this, we create a new subdirectory of
# $SCRATCH/recount-pump, inside which we create subdirectories input,
# output, and temp.

# $WORK/recount-pump/ref contains ref files.

set -ex

job_name=$1
image_file=$2

test -n "${job_name}"
test -n "${image_file}"
test -f "${image_file}"

mkdir -p "${SCRATCH}/recount-pump"
test ! -d "${SCRATCH}/recount-pump/${job_name}"

INPUT_DIR="${SCRATCH}/recount-pump/${job_name}/input"
OUTPUT_DIR="${SCRATCH}/recount-pump/${job_name}/output"
TEMP_DIR="${SCRATCH}/recount-pump/${job_name}/temp"

mkdir -p "${INPUT_DIR}" "${OUTPUT_DIR}" "${TEMP_DIR}"

RECOUNT_REF="${WORK}/recount-pump/ref"

test -n "${RECOUNT_REF}"
test -d "${RECOUNT_REF}"

RECOUNT_JOB="${job_name}" && singularity exec \
    ${image_file} \
    /bin/bash -c \
    "source activate rnaseq_v0 && bash /home/biodocker/bin/rna_seq.bash"
