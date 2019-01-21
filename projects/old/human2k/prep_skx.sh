#!/bin/sh

d=$(dirname $0)

python ${d}/../../src/cluster.py prepare \
    --ini-base ${d}/creds \
    --cluster-ini ~/.recount/cluster-skx.ini \
    1
