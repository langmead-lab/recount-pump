#!/bin/sh

set -ex

../../aws/logs/delete.sh recount_h2k
../../aws/db/reset_db.sh recount_h2k
../../aws/sqs/delete.sh h2k_proj1_q
