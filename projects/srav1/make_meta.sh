#!/usr/bin/env bash

curl https://raw.githubusercontent.com/nellore/runs/master/sra/hg19.stats_by_sample.tsv | \
    awk '{print $2,$5}' | \
    sed 's/^index/#index/' |
    sort -k1,1 > \
    srav1.txt
