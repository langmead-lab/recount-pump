#!/bin/sh

# Author: Ben Langmead
#  Email: langmea@cs.jhu.edu
#   Date: 1/5/2018

# Runs a singularity container containing the next flow script and its
# in-container driver, setting up these directory mappings ahead of
# time.

# Note that TACC has restrictions on directory binding.  They are
# described here:

#  first arg -> /recount-input
#  second arg -> /recount-output
#  ${RECOUNT_REF} -> /recount-ref
#  ${RECOUNT_TEMP} -> /recount-temp

set -ex

input_dir=`realpath $1`
output_dir=`realpath $2`
image=$3
shift 3

if [ -n "${image}" ] ; then
    if ! echo ${image} | grep -q '^shub' ; then
        # not a URL, so must be extant file
        test -f "${image}"
    fi 
else
    # default singularity-hub version
    image="shub://langmead-lab/recount-pump:recount-pump"
fi

test -n "${input_dir}"
test -d "${input_dir}"

test -n "${output_dir}"
test -d "${output_dir}"

test -n "${RECOUNT_REF}"
test -d "${RECOUNT_REF}"

test -n "${RECOUNT_TEMP}"
test -d "${RECOUNT_TEMP}"

export INPUT="/recount-input" && \
export OUTPUT="/recount-output" && \
export RECOUNT_REF="/recount-ref" && \
export RECOUNT_TEMP="/recount-temp" && \
singularity exec \
    --bind ${input_dir}:/recount-input \
    --bind ${output_dir}:/recount-output \
    --bind ${RECOUNT_REF}:/recount-ref \
    --bind ${RECOUNT_TEMP}:/recount-temp \
    ${image} \
    /bin/bash -c \
    "source activate rnaseq_v0 && bash /home/biodocker/bin/rna_seq.bash"
