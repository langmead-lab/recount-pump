#!/bin/sh

set -ex

docker-compose up -d
sleep 15

export AWS_ACCESS_KEY_ID=minio
export AWS_SECRET_ACCESS_KEY=minio123
export RECOUNT_TEST_DB="postgres://recount:recount-postgres@localhost:25432/recount-test"
export RECOUNT_TEST_Q="http://localhost:29324"
export RECOUNT_TEST_S3="http://localhost:29000"

# Needs to match cluster.ini
export RECOUNT_IMAGES="${HOME}/recount-images"
export SINGULARITY_CACHEDIR="${RECOUNT_IMAGES}"

./unit_test.sh

export RECOUNT_CREDS="$HOME/.creds_integration_test/.recount"

rm -rf ~/.creds_integration_test
cp -r creds ~/.creds_integration_test
for i in $(ls ~/.creds_integration_test/*.override) ; do
    echo "*** Renaming ${i} ***"
    mv ${i} $(echo ${i} | sed 's/\.override$//')
done

./e2e_test.sh
