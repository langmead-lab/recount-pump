#!/bin/sh

set -ex

../../aws/logs/delete.sh recount_srav1
../../aws/db/reset_db.sh recount_srav1
../../aws/sqs/delete.sh srav1_proj1_q
../../aws/sqs/delete.sh srav1_proj1_q_dlq
