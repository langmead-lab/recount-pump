#!/bin/sh

set -ex

mkdir -p git
cd git
rm -rf recount-pump
git clone git@github.com:langmead-lab/recount-pump.git -- recount-pump
cd recount-pump/nextflow
docker build container
