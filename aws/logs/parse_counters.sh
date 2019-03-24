#!/usr/bin/env bash

# Scrape all the counter names from all the relevant scripts.

d=$(dirname $0)

metrics=$(grep 'log.*COUNT_' $d/../../src/*.py | sed 's/.*COUNT/COUNT/' | sed 's/ .*//' | grep -v '%')
metrics="${metrics} $(grep 'echo \"COUNT_' $d/../../workflow/*/Snakefile | sed 's/.*COUNT/COUNT/' | sed 's/ .*//' | grep -v '%')"
metrics="${metrics} $(python $d/../../src/stats.py snakefile $d/../../workflow/*/Snakefile)"
metrics=$(echo ${metrics} | sort -u)

echo ${metrics}
