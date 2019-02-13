#!/bin/bash

d=$(dirname $0)

study=$(grep '^study' project.ini | cut -d"=" -f2 | tr -d '[:space:]')

for i in *.json.zst ; do
    aws --profile jhu-langmead s3 cp \
        $i s3://recount-pump-experiments/${study}/${i}
done
