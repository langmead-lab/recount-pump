#!/bin/sh

set -ex

bash ../populate/synapse_download.sh ce10
mkdir ref
mv ce10 ref

mkdir -p input
cp accessions.txt input

mkdir -p output

export RECOUNT_REF=`pwd`/ref
export RECOUNT_TEMP=/tmp
