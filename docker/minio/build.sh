#!/bin/sh

d=`dirname $0`

rm -rf src
cp -r $d/../../src .
cp $d/../../requirements.txt .
docker build --tag benlangmead/recount-minio $* . 
