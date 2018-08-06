#!/usr/bin/env bash

d=`dirname $0`

mkdir -p $d/images

BASENAME=quay.io_benlangmead_recount-rna-seq-lite-nf-2018-07-23-353aacc3b34f.img

if [ ! -f "$d/images/${BASENAME}" ] ; then
    wget -O $d/images/${BASENAME}.gz https://s3.amazonaws.com/recount-pump/image/${BASENAME}.gz
    gunzip $d/images/${BASENAME}.gz
    [ ! -f "$d/images/${BASENAME}" ] && echo "Did not create file" && exit 1
fi
