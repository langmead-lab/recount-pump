#!/usr/bin/env bash

# Author: Chris Wilks

gtf=$1
shift

[ -z "${gtf}" ] && echo "Specify GTF as first arg" && exit 1

cat ${gtf} | \
    cut -f 1,3,4,5,9 | \
    perl -ne '($chrm,$type,$start,$end,$info)=split(/\t/,$_); $start--; $idtag="$type"."_id";  $info=~/$idtag "([^"]+)"/; $id=$1; next if(!$id); print "$chrm\t$start\t$end\t$id\n";'
