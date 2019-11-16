#!/usr/bin/env bash

set -ex

PROJ_INI=$1
if [[ -z "${PROJ_INI}" ]] ; then
    PROJ_INI=project.ini
fi

STUDY=$(grep '^study' ${PROJ_INI} | cut -d"=" -f2 | tr -d '[:space:]')

log_enable=$(grep '^enable' creds/log.ini | cut -d"=" -f2 | tr -d '[:space:]')

../../aws/db/reset_db.sh ${STUDY}
if [[ -z ${log_enable} || ${log_enable} == "true" ]] ; then
    echo "=== Deleting logs ==="
    ../../aws/logs/delete.sh ${STUDY}
else
    echo "=== Skipping logs (disabled) ==="
fi

../../aws/sqs/delete.sh ${STUDY}_proj1_q
../../aws/sqs/delete.sh ${STUDY}_proj1_q_dlq
