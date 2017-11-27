#!/bin/sh

# Upload directory with reference files to Synapse as single tarball. 

set -e

dr=$1
[ -z "${dr}" ] && echo "Must specify directory as argument" && exit 1

scr_dir=`dirname $0`
ref_id=`cat ${scr_dir}/synapse_references_id.txt`

[ -z "${ref_id}" ] && echo "Could not get ref_id" && exit 1

# Create new subdirectory for this species
species_id=`synapse create -parentid ${ref_id} -name ${dr} | awk '{print $3}'`
[ -z "${species_id}" ] && echo "Could not get species_id" && exit 1

# For populating the description field
host=`hostname -f`
dt=`date`

cd ${dr}
for d in * ; do
    tar -cvf - ${d} | gzip -c > ${d}.tar.gz
    md5=`md5sum ${d}.tar.gz | awk '{print $1}'`
    synapse add -parentid ${species_id} --description "Uploaded from ${host}, ${dt}, md5=${md5}" ${d}.tar.gz
    rm -f ${d}.tar.gz
done
cd ..
