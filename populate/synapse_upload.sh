#!/bin/sh

# Upload directory with reference files to Synapse as single tarball. 

set -e

dr=$1
[ -z "${dr}" ] && echo "Must specify directory as argument" && exit 1

scr_dir=`dirname $0`
ref_id=`cat ${scr_dir}/synapse_references_id.txt`

[ -z "${ref_id}" ] && echo "Could not get ref_id" && exit 1

cd ${dr}
tar -cvf * | gzip -c > ${dr}.tar.gz
host=`hostname -f`
dt=`date`
md5=`md5sum ${dr}.tar.gz | awk '{print $1}'`
synapse add -parentid ${ref_id} --description "Uploaded from ${host}, ${dt}, md5=${md5}" ${dr}.tar.gz
rm -f ${dr}.tar.gz
cd ..
