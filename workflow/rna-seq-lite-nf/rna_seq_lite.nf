#!/usr/bin/env nextflow

/*
 * Example RNA-seq pipeilne (lite)
 * Author: Ben Langmead
 *   Date: 7/15/2018
 *
 * Requires:
 * - hisat2
 * - fastq-dump (sra-tools)
 * - sambamba
 * - regtools (not in conda as of now; must install via GitHub)
 *
 * Published outputs:
 * - Alignment log (<accession>_align_log.txt)
 * - Junction counts (<accession>.jx_bed)
 *   + similar to bed_to_juncs output, but includes count, accession, motif, annotation status
 */

params.in   = 'accessions.txt'
params.out  = 'results'
params.ref  = '${RECOUNT_REF}'
params.temp = '${RECOUNT_TEMP}'

srrs = Channel
       .fromPath(params.in)
       .splitCsv(header: ['srr', 'srp', 'species'])
       .ifEmpty { error "Cannot find any accessions in: ${params.in}" }


// Doing this first means checks are skipped when pipeline is resumed?
process preliminary {
    tag { srr }

    input:
    set srr, srp, species from srrs

    output:
    set srr, srp, species into srrs2

    """
    # Ensure expected reference files are around
    test -d ${params.ref}/${species}
    for i in 1 2 3 4 5 6 7 8 ; do
        test -f ${params.ref}/${species}/hisat2_idx/genome.\${i}.ht2
    done
    """
}

process sra_fastq {
    tag { srr }

    input:
    set srr, srp, species from srrs2

    output:
    set srr, srp, species, '*.fastq' into fastq

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

    input:
    set srr, srp, species, file('?.fastq') from fastq

    output:
    set srr, srp, species, 'o.sam' into sam
    set srr, srp, 'o.log' into align_log

    """
    IDX=${params.ref}/${species}/hisat2_idx/genome
    if [[ -f 2.fastq ]] ; then
        hisat2 -x \${IDX} --min-intronlen 20 -1 1.fastq -2 2.fastq -S o.sam -t 2>o.log
    elif [[ -f 1.fastq ]] ; then
        hisat2 -x \${IDX} --min-intronlen 20 -U 1.fastq -S o.sam -t 2>o.log
    else
        ls -l
        exit 1
    fi
    """
}

process publish_align_logs {
    tag { srr }
    publishDir params.out, mode: 'copy'

    input:
    set srr, srp, file(logf) from align_log

    output:
    file('*_align_log.txt') into align_log_final

    """
    mv ${logf} ${srr}_align_log.txt
    """
}

process sam_to_bam {
    tag { srr }

    input:
    set srr, srp, species, file(samf) from sam

    output:
    set srr, srp, species, 'o.bam' into bam

    """
    sambamba view -S -f bam ${samf} > o.bam
    """
}

process bam_sort {
    tag { srr }

    input:
    set srr, srp, species, file(bam) from bam

    // Channels can't be reused, so I have to make several.
    // Is there a less silly way to funnel output to N other process?
    output:
    set srr, srp, species, 'o.sorted.bam', 'o.sorted.bam.bai' into sorted_bam1, sorted_bam2, sorted_bam3,
                                                                   sorted_bam4, sorted_bam5, sorted_bam6

    """
    sambamba sort --tmpdir=${params.temp} -p -m 10G -o o.sorted.bam ${bam}
    sambamba index o.sorted.bam
    """
}

process extract_junctions {
    tag { srr }
    publishDir params.out, mode: 'copy'

    input:
    set srr, srp, species, file(sbam), file(sbam_idx) from sorted_bam4

    output:
    file('*.jx_bed') into jx_bed_final

    """
    # Options:
    # -a INT   Minimum anchor length; jxs w/ min length on both sides are reported
    # -i INT   Minimum intron length. [70]
    # -I INT   Maximum intron length. [500000]

    FA=${params.ref}/${species}/fasta/genome.fa
    GTF=${params.ref}/${species}/gtf/genes.gtf
    regtools junctions extract -i 20 -a 1 -o o.jx_tmp ${sbam}
    regtools junctions annotate -E -o ${srr}.jx_bed o.jx_tmp \${FA} \${GTF}
    """
}
