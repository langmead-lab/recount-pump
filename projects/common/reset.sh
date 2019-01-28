#!/bin/sh

set -ex

STUDY=$(grep '^study' $d/project.ini | cut -d"=" -f2 | tr -d '[:space:]')

../../aws/logs/delete.sh recount_${STUDY}
../../aws/db/reset_db.sh recount_${STUDY}
../../aws/sqs/delete.sh ${STUDY}_proj1_q
../../aws/sqs/delete.sh ${STUDY}_proj1_q_dlq
