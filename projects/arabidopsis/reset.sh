#!/bin/sh

set -ex

../../aws/logs/delete.sh recount-tair
../../aws/db/reset_db.sh recount_tair
../../aws/sqs/delete.sh tair10araport11_proj1_q
