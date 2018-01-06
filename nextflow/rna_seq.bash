#!/usr/bin/env bash

# Author: Ben Langmead
#  Email: langmea@cs.jhu.edu
#   Date: 1/5/2018

# Designed to run the nextflow script from inside a container where the
# supporting directories have already been set up, i.e.:
#  /recount-input
#  /recount-output
#  /recount-ref
#  /recount-temp

set -ex

d=`dirname $0`

test -d /recount-input
test -d /recount-output
test -d /recount-ref
test -d /recount-temp

RESULTS_DIR=/recount-output/results

ls /recount-input

INPUT=`ls /recount-input/*`

$d/rna_seq.nf \
    --in ${INPUT} \
    --out ${RESULTS_DIR} \
    --ref /recount-ref \
    --temp /recount-temp $*

md5sum ${INPUT} | cut -d' ' -f 1 > .input.md5
RESULTS_DIR_FINAL=$RESULTS_DIR-`cat .input.md5`
mv $RESULTS_DIR $RESULTS_DIR_FINAL

globus login --no-local-server
globus endpoint search marcc | grep 'marcc#dtn' | cut -d' ' -f1 > .marcc.id
globus endpoint search XSEDE | grep 'XSEDE TACC stampede2' | cut -d' ' -f1 > .stampede2.id

MARCC=`cat .marcc.id`
XSEDE=`cat .stampede2.id`

globus transfer \
    --label "test-xfer" \
    $XSEDE:/work/04265/benbo81/stampede2/ERR204938_1.fastq.gz \
    $MARCC:/net/langmead-bigmem.ib.cluster/storage/recount-pump/ERR204938_1.fastq.gz > .xfer.log

grep 'Task ID' .xfer.log | cut -d' ' -f 3 > .xfer.id

globus task wait `cat .xfer.id`

echo SUCCESS
