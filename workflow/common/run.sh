#!/bin/bash

set -ex

d=$(dirname $0)
IMAGE=$(cat image.txt)

INI_FILE=${HOME}/.recount/cluster.ini
test -f ${INI_FILE}

name=run_docker_test
ref_base=$(grep '^ref_base' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
temp_base=$(grep '^temp_base' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
input_base=$(grep '^input_base' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
output_base=$(grep '^output_base' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
ref_mount=$(grep '^ref_mount' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
temp_mount=$(grep '^temp_mount' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
input_mount=$(grep '^input_mount' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
output_mount=$(grep '^output_mount' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')

test -n "${name}"
test -n "${ref_base}"
test -n "${temp_base}"
test -n "${input_base}"
test -n "${output_base}"
test -n "${ref_mount}"
test -n "${temp_mount}"
test -n "${input_mount}"
test -n "${output_mount}"

docker run -it \
    -e RECOUNT_JOB_ID=${name} \
    -e RECOUNT_INPUT=${input_mount} \
    -e RECOUNT_OUTPUT=${output_mount} \
    -e RECOUNT_TEMP=${temp_mount} \
    -e RECOUNT_CPUS=${cpus} \
    -e RECOUNT_REF=${ref_mount} \
    -v $(cd $d/.. ; pwd):/work \
    -v ${ref_base}:${ref_mount} \
    -v ${temp_base}:${temp_mount} \
    -v ${input_base}:${input_mount} \
    -v ${output_base}:${output_mount} \
    $* \
    --rm \
    ${IMAGE} \
    /bin/bash
