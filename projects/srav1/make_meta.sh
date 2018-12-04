#!/usr/bin/env bash

curl https://raw.githubusercontent.com/nellore/runs/master/sra/hg19.stats_by_sample.tsv | \
    sed 's/^sample/#sample/' | \
    awk '{print $2,$5}' > \
    srav1.txt

