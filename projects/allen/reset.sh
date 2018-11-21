#!/bin/sh

set -ex

../../aws/logs/delete.sh recount_allen
../../aws/db/reset_db.sh recount_allen
../../aws/sqs/delete.sh allen_proj1_q
