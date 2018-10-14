#!/bin/sh

species=$1
[ -z "${species}" ] && echo 'specify species as first arg'

for i in ${species}/* ; do
    aws s3 cp $i s3://recount-ref/${species}/`basename $i`
    # TODO: make public
done
