#!/bin/bash

ver=$1
[ -z "${ver}" ] && echo "give version as argument" && exit 1

set -x

for i in $(find . -name ver.txt) ; do
    echo "${ver}" > $i
done
