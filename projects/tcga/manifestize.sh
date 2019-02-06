#!/bin/sh

zstd -dc gdc_manifest.2017-12-28T20_09_55.867662.txt.zst \
    | awk '$1 != "id" {print "tcga",$1,"gdc"}' \
    > tcga.txt
