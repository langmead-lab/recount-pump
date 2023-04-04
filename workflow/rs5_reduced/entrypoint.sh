#!/usr/bin/env bash
set -exo pipefail

#source activate recount
if [[ -n $SLEEP ]]; then
    sleep 1d
fi
mkdir -p $RECOUNT_INPUT $RECOUNT_OUTPUT $RECOUNT_TEMP $RECOUNT_TEMP_BIG
/bin/bash -x /workflow.bash > $RECOUNT_OUTPUT/full.run 2>&1
