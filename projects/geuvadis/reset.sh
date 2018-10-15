#!/bin/sh

set -ex

../../aws/logs/delete.sh recount-geuvadis
../../aws/db/reset_db.sh recount
../../aws/sqs/delete.sh geuv_proj1_q
