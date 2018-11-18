#!/bin/sh

set -ex

../../aws/logs/delete.sh recount_geuvadis
../../aws/db/reset_db.sh recount_geuvadis
../../aws/sqs/delete.sh geuv_proj1_q
