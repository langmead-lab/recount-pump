#!/bin/bash

set -ex

which wget
STAGING=/tmp/staging

setup_refs() {
    manifest=$1
    test -f $manifest
    while IFS=, read -r src dst
    do
        fulldst=${STAGING}/${dst}
        mkdir -p $(dirname $fulldst)
        wget -O $fulldst $src
    done < $manifest
}

setup_refs /tmp/manifest.csv

echo "Final contents of ${STAGING}"
tree ${STAGING}
