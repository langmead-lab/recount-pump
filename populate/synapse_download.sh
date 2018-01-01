#!/bin/sh

# Upload directory with reference files to Synapse as single tarball. 

set -e

species=$1
[ -z "${species}" ] && echo "specify species shortname (e.g. dm6) as argument"
refid=`cat synapse_references_id.txt`
synid=`synapse list ${refid} | grep ${species} | awk '{print $1}'`

test -n $synid

mkdir -p $synid
pushd $synid && synapse get -r $synid && popd
