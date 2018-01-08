#!/bin/sh

set -ex

bash ../populate/synapse_download.sh ce10
mkdir ref
mv ce10 ref
cd ref/ce10
for i in *.tar.gz ; do tar zxvf $i ; done
cd ../..

mkdir -p input
cp accessions.txt input

mkdir -p output

export RECOUNT_REF=`pwd`/ref
export RECOUNT_TEMP=/tmp
