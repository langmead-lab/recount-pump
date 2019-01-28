#!/bin/sh

# Assuming this is equally valid to run on either normal (KNL) or
# normal-skx (skylake) queues, or their development versions.

d=$(dirname $0)

python ${d}/../../src/cluster.py prepare \
    --ini-base creds \
    --cluster-ini ~/.recount/cluster-skx.ini \
    1
