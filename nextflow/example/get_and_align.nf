#!/usr/bin/env nextflow

/*
 * For testing different ways of getting files and aligning them.
 */

params.refdir = '/Users/langmead/indexes/hisat2/ce10'
params.outdir = 'results'

srr = Channel
      .fromPath(params.in)
      .splitText()
      .map{ it.trim() }

process sra_fastq {
    tag { srr }

    input:
    val(srr)
    
    output:
    set srr, '*.fastq' into fastq
    
    """
    fastq-dump ${srr} --split-files -I --skip-technical
    ls *_2.fastq 2>/dev/null || \
        for i in *_1.fastq ; do
            mv \$i `echo \$i | sed 's/_1.fastq/_0.fastq/'`
        done
    """
}

process align {
    tag { srr }
    publishDir params.outdir, mode: 'copy'

    input:
    set (srr, file('?.fastq')) from fastq

    output:
    set srr, file('*.sam') into sam_pe

    """
    if [[ -f 2.fastq ]] ; then
        hisat2 -x ${params.refdir}/genome -1 1.fastq -2 2.fastq -S o.sam -t
    elif [[ -f 1.fastq ]] ; then
        hisat2 -x ${params.refdir}/genome -U 1.fastq -S o.sam -t
    else
        ls -l
        exit 1
    fi
    mv o.sam ${srr}.sam
    """
}
