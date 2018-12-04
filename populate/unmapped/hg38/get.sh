#!/bin/sh

for i in `tail -n +2 manifest.csv | cut -d',' -f5` ; do
    echo $i
    ii=$(basename $i)
    ii=$(echo $ii | sed 's/\.gz$//')
    curl $i | gzip -dc > $ii
done
