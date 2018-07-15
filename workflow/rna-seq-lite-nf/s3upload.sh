#!/bin/sh

for i in *.img.zstd ; do
    aws s3 cp $i s3://recount-pump/image/$i
done
