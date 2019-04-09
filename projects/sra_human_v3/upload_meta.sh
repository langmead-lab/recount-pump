#!/bin/bash

set -e

superstudy=sra_human_v3
taxon_id=9606

for i in *_${taxon_id}.json.zst ; do
    aws --profile jhu-langmead s3 cp \
        $i s3://recount-pump-experiments/${superstudy}/${i}
done
