#!/usr/bin/env bash

set -ex

proj=$1
shift

url=https://recount-meta.s3.amazonaws.com/${proj}/${proj}.json.gz

curl -qI ${url} 2>/dev/null | grep '200 OK'

curl ${url} 2>/dev/null \
    | gzip -dc \
    | jq -c '.[] | {srr: ._id, srp: ._source.study.accession}' \
    | sed 's/[^A-Z0-9:]//g' \
    | awk -v FS=':' '{print $3,$2}' \
    | sort -k1,1 -k2,2
