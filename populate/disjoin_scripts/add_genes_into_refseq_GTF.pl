#!/usr/bin/env perl
#takes a GTF file output by doing refseq GFF2GTF via gffread
#and summarizes the exon rows back to the gene level
#this assumes the GTF was produced via a command similar to this:
#~/bin/gffread -E GRCh38_latest_genomic.gff -T -G -O -o GRCh38_latest_genomic.gff.gffread.full.gtf 2> GRCh38_latest_genomic.gff.gffread.err
use strict;
use warnings;

my $BAD_VAL=';';

my %h;
my %h3;
my %info_hash;
#no assumptions on input order of GTF exon rows
while(my $f = <STDIN>)
{
    #first print out the line as normal (exon/headers)
    print $f;
    chomp($f);
    my ($c,$j1,$t,$s,$e,$bp,$o,$j3,$info)=split(/\t/,$f); 
    #remove transcript_ids since this is the gene level
    $info=~s/transcript_id\s+"[^"]+";//g;
    #get gene_id to use as key
    $info=~/gene_id\s+"([^"]+)"/;
    my $gid=$1;
    #we make no assumptions about a gene having only one chromosome and/or strand
    push(@{$h{$gid}->{$c}->{$o}},[$s,$e]);

    if($h3{$gid} && $h3{$gid} ne $info)
    {
        print STDERR "INFO_MISMATCH\t$gid\t$info\t".$h3{$gid}."\n";
    }
    $h3{$gid}=$info;

    #now handle info field, this is to remove
    #duplicate fields which have different 
    #transcript/exon level values
    my @ifields = split(/;/,$info);
    for my $if (split(/;/,$info))
    {
        $if=~s/^\s+//;
        $if=~s/\s+$//;
        my @f2=split(/\s+/,$if);
        next if(!$f2[0]);
        my $k = shift(@f2);
        my $v = join(" ",@f2);
        #we'll add gene_id back ourselves
        next if($k =~ /gene_id/);
        if($info_hash{$gid}->{$k} && $info_hash{$gid}->{$k} ne $v)
        {
            $info_hash{$gid}->{$k}=$BAD_VAL;
            next;
        }
        $info_hash{$gid}->{$k} = $v;
    }
}
for my $gid (sort { $a cmp $b } keys %h) 
{ 
    my $inf=$info_hash{$gid};
    my @info;
    for my $k (sort keys %$inf)
    {
        my $v=$inf->{$k}; 
        if($v ne $BAD_VAL) { push(@info,"$k $v"); }
    }
    my $info = join("; ", @info);
    #sort chromosomes
    for my $c (sort { $a cmp $b } keys %{$h{$gid}}) 
    { 
        #sort strands
        for my $o (sort { $a cmp $b } keys %{$h{$gid}->{$c}}) 
        { 
            #sort by start coordinates
            my @exons = sort { $a->[0] <=> $b->[0] || $a->[1] <=> $b->[1]; } @{$h{$gid}->{$c}->{$o}};
            #if($gid=~/gene70/) 
            #{
            #    map { my ($s1,$e1)=@$_; print "$gid\t$s1\t$e1\n"; } @exons;
            #}
            my ($s,$e) = ($exons[0]->[0], $exons[$#exons]->[1]);
            print "$c\tRefSeq\tgene\t$s\t$e\t.\t$o\t.\tgene_id \"$gid\"; $info;\n";
       }
   }
} 
