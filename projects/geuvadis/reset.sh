#!/bin/sh

set -ex

../../aws/db/reset_db.sh recount
../../aws/sqs/delete.sh stage_1
