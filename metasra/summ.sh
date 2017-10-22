#!/bin/sh

for i in *.sqlite ; do
    echo "File: $i"
    echo "# distinct samples: "
    sqlite3 ${i} 'select count(DISTINCT sample_accession) from sample_type;'
done
