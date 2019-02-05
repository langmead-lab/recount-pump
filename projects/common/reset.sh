#!/bin/sh

set -ex

STUDY=$(grep '^study' project.ini | cut -d"=" -f2 | tr -d '[:space:]')

../../aws/logs/delete.sh ${STUDY}
../../aws/db/reset_db.sh ${STUDY}
../../aws/sqs/delete.sh ${STUDY}_proj1_q
../../aws/sqs/delete.sh ${STUDY}_proj1_q_dlq
