#!/bin/sh

set -ex

which mc
docker-compose up -d
sleep 25

export AWS_ACCESS_KEY_ID=minio
export AWS_SECRET_ACCESS_KEY=minio123
export RECOUNT_TEST_DB="postgres://recount:recount-postgres@localhost:25432/recount-test"
export RECOUNT_TEST_Q="http://localhost:29324"
export RECOUNT_TEST_S3="http://localhost:29000"

# Needs to match cluster.ini
export RECOUNT_IMAGES="${HOME}/recount-images"
export SINGULARITY_CACHEDIR="${RECOUNT_IMAGES}"

# Remove python and pytest caches
./clean.sh
./unit_test.sh
./e2e_test.sh
