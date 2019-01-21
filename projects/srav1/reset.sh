#!/bin/sh

set -ex

PROJ=srav1

../../aws/logs/delete.sh recount_${PROJ}
../../aws/db/reset_db.sh recount_${PROJ}
../../aws/sqs/delete.sh ${PROJ}_proj1_q
../../aws/sqs/delete.sh ${PROJ}_proj1_q_dlq
