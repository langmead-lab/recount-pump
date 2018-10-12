#!/bin/bash

aws --profile jhu-langmead s3 cp \
    geuv.json.gz \
    s3://recount-pump-experiments/geuv/geuv.json.gz
