[z]cat <GTF> | cut -f 1,4,5 | perl -ne '($chrm,$start,$end)=split(/\t/,$_); $start--; print "$chrm\t$start\t$end";'

zcat gencode.v28.basic.annotation.gtf.gz | cut -f 1,3,4,5,7,9 | perl -ne '($chrm,$type,$start,$end,$strand,$info)=split(/\t/,$_); $start--; $idtag="$type"."_id";  $info=~/$idtag "([^"]+)"/; $id=$1; next if(!$id); print "$chrm\t$start\t$end\t$id\t0\t$strand\n";'
