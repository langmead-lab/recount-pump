#!/bin/sh

set -ex

../../aws/logs/delete.sh recount-allen
../../aws/db/reset_db.sh recount
../../aws/sqs/delete.sh stage_1
