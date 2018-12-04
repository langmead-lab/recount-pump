#!/bin/sh

d=$(dirname $0)

python ${d}/../../src/cluster.py run \
    --ini-base ${d}/creds \
    --cluster-ini ~/.recount/cluster-skx.ini \
    1
