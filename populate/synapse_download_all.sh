#!/bin/sh

set -ex

genomes=`cut -d' ' -f 4 from_igenomes_all.sh | tail -n 10 | grep -v TAIR`

for g in $genomes ; do
    echo "================="
    echo "Downloading $g"
    echo "================="
    bash synapse_download.sh $g
done
 