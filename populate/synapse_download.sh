#!/bin/sh

# Download reference files from synapse and expand 

d=`dirname $0`

set -e

species=$1
[ -z "${species}" ] && echo "specify species shortname (e.g. dm6) as argument"
refid=`cat $d/synapse_references_id.txt`
synid=`synapse list ${refid} | grep ${species} | awk '{print $1}'`

test -n $synid

mkdir -p $species
pushd $species
synapse get -r $synid
#for i in *.tar.gz ; do
#    tar zxvf $i
#done
popd
