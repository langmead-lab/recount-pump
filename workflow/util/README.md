For bwtool, check out Leo's script, which I based my stuff on:
* https://github.com/leekgroup/recount-website/blob/master/sum.sh

it takes a BED file

Is there an automated way to get the BED from a gtf?

I usually do it via a Perl "one liner", which probably isn't the best approach here

The `-fill=0 -with-sum` are important, that will just fill missing values with 0 rather than the max integer (which it defaults to strangely), the sum will be the last column.  That references: https://github.com/CRG-Barcelona/bwtool/wiki/summary

`[z]cat <GTF> | cut -f 1,4,5 | perl -ne '($chrm,$start,$end)=split(/\t/,$_); $start--; print "$chrm\t$start\t$end";'` is the basic idea, that should work for `bwtool` but it won't keep the transcript/exon names/ids around, we'd have to do more parsing of GTF; I'm looking around for examples of that (I've done it before).

`awk` of course could also be used
but I remember Perl syntax better than awk's

ok, here's one which parses out the (gene/exon/transcript_id) from last field and prints the strand (and unused score, always 0):

```
gzip -dc gencode.v28.basic.annotation.gtf.gz | \
    cut -f 1,3,4,5,7,9 | \
    perl -ne '($chrm,$type,$start,$end,$strand,$info)=split(/\t/,$_); $start--; $idtag="$type"."_id";  $info=~/$idtag "([^"]+)"/; $id=$1; next if(!$id); print "$chrm\t$start\t$end\t$id\t0\t$strand\n";'
```

it'll only print out transcripts,exons, and genes

ok, just tested my BED version of the gencode V28 GTF with `bwtool` it works (for the first 1K rows tested) and I also found, if we want to keep the IDs, add `-keep-bed` to the bwtool command, and we'll probably want to cut the output to just get the coordinates, ID, and sum.

```
bwtool summary <BED> <BW> /dev/stdout -fill=0 -with-sum -keep-bed \
    | cut -f1-4,13
```

And in that case, we can drop the score and strand from the original conversion one liner as well

```
gzip -dc gencode.v29.annotation.gtf.gz | \
    cut -f 1,3,4,5,9 | \
    perl -ne '($chrm,$type,$start,$end,$info)=split(/\t/,$_); $start--; $idtag="$type"."_id";  $info=~/$idtag "([^"]+)"/; $id=$1; next if(!$id); print "$chrm\t$start\t$end\t$id\n";' \
    > gencode.v29.annotation.bed
```
oh, and one more thing, bwtool defaults to printing the sums as decimals, however, adding the `-decimals=0` should take care of that

so the (updated) bwtool command would be:

```
bwtool summary \
    gencode.v29.annotation.bed \
    SRR1910389.bw \
    /dev/stdout \
        -fill=0 \
        -with-sum \
        -keep-bed \
        -decimals=0 \
    | cut -f1-4,11 \
    > SRR1910389_gencodev29_summ.tsv
```

thats adjusts the final cut to be on a BED file formatted to be just `chromosome,start,end,ID`

running `bwtool summary` with the full gencodev28 on a random GTEx BW from Rail on one of the ex-hadoop nodes took ~15 minutes (900 seconds).  that was for 860K intervals.
