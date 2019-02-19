#!/usr/bin/env bash

set -ex

PROJ_INI=$1
if [[ -z "${PROJ_INI}" ]] ; then
    PROJ_INI=project.ini
fi

STUDY=$(grep '^study' ${PROJ_INI} | cut -d"=" -f2 | tr -d '[:space:]')

../../aws/logs/delete.sh ${STUDY}
../../aws/db/reset_db.sh ${STUDY}
../../aws/sqs/delete.sh ${STUDY}_proj1_q
../../aws/sqs/delete.sh ${STUDY}_proj1_q_dlq
