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

# Ensure directories
test -d /recount-input
test -d /recount-output
test -d /recount-ref
test -d /recount-temp

# Ensure tools are installed
which hisat2
which fastq-dump
which sambamba
which stringtie
which bamCoverage
which regtools
which wiggletools
which featureCounts
which nextflow

RESULTS_DIR=/recount-output/results

# Gather inputs
ls /recount-input
INPUT=`ls /recount-input/*`
test -n "${INPUT}"

# Set cache directory for fastq-dump
mkdir -p $HOME/.ncbi
mkdir -p /recount-temp/ncbi

cat >$HOME/.ncbi/user-settings.mkfg <<EOF
/repository/user/main/public/root = "/recount-temp/ncbi"
EOF

# Run nextflow workflow
$d/rna_seq.nf \
    --in ${INPUT} \
    --out ${RESULTS_DIR} \
    --ref /recount-ref \
    --temp /recount-temp $*

md5sum ${INPUT} | cut -d' ' -f 1 > .input.md5
RESULTS_DIR_FINAL=$RESULTS_DIR-`cat .input.md5`
mv $RESULTS_DIR $RESULTS_DIR_FINAL

if false ; then
    # This is some dummy code to see if we can run the Globus CLI in a
    # slick way from inside the container.  If so, we'd like to xfer
    # the output files directly to the server that can act as a
    # gathering place for outputs, aggregating them by study (for
    # recount) and by compilation (for Snaptron) and then storing them
    # and/or pushing them to the ultimate host.
    
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
fi

echo SUCCESS
