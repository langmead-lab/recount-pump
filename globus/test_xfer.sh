#!/bin/sh

set -ex

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
