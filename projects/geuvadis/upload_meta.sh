#!/bin/bash

study=geuv

aws --profile jhu-langmead s3 cp \
    ${study}.json.gz \
    s3://recount-pump-experiments/${study}/${study}.json.gz
