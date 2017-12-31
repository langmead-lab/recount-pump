#!/usr/bin/env nextflow

/*
 * Example RNA-seq pipeilne
 * Author: Ben Langmead
 *   Date: 12/31/2017s
 *
 * Requires:
 * - hisat2
 * - fastq-dump (sra-tools)
 * - sambamba
 * - stringtie
 * - bamCoverage (deepTools)
 * - regtools (not in conda as of now; must install via GitHub)
 *
 * Published outputs:
 * - Alignment log (<accession>_align_log.txt)
 * - BigWigs
 *   + Unique (<accession>.unique.bw)
 *   + All (<accession>.all.bw)
 * - Junction bed (<accession>.jx_bed)
 * - Assembly (<accession>.gtf)
 *
 * TODO:
 * - Let input format be csv with each line specifying:
 *   + Accession
 *   + Species abbreviation (used to find FASTA, index, annotations)
 *   + URL and/or retrieval method
 *   ... as of now, just accession is specified; user specifies
 *   --refdir and retrieval is always with fastq-dump
 * - Add more recount/Snaptron postprocessing
 *   + Junction annotation
 *   + Annotation quantification (gene & exon)
 *   + Mean bigWigs
 *   + Coverage-standardization of bigWigs
 */

params.in     = 'accessions.txt'
params.temp   = '/tmp'
params.refdir = '/Users/langmead/indexes/hisat2/ce10'
params.outdir = 'results'
params.cpus   = 8
params.stop_after_alignment = false

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

    input:
    set (srr, file('?.fastq')) from fastq

    output:
    set srr, 'o.sam' into sam
    set srr, 'o.log' into align_log

    """
    if [[ -f 2.fastq ]] ; then
        hisat2 -x ${params.refdir}/genome --min-intronlen 20 -1 1.fastq -2 2.fastq -S o.sam -t 2>o.log
    elif [[ -f 1.fastq ]] ; then
        hisat2 -x ${params.refdir}/genome --min-intronlen 20 -U 1.fastq -S o.sam -t 2>o.log
    else
        ls -l
        exit 1
    fi
    """
}

process publish_align_logs {
    tag { srr }
    publishDir params.outdir, mode: 'copy'

    input:
    set srr, file(logf) from align_log

    output:
    file('*_align_log.txt') into align_log_final
    
    """
    mv ${logf} ${srr}_align_log.txt
    """
}

process sam_to_bam {
    tag { srr }
    cpus params.cpus

    input:
    set srr, file(samf) from sam
    
    output:
    set srr, 'o.bam' into bam
    
    """
    sambamba view -S -f bam -t ${task.cpus} ${samf} > o.bam
    """
}

process bam_sort {
    tag { srr }
    cpus params.cpus

    input:
    set srr, file(bam) from bam
    
    // Channels can't be reused, so I have to make several.
    // Is there a less silly way to funnel output to N other process?
    output:
    set srr, 'o.sorted.bam', 'o.sorted.bam.bai' into sorted_bam1
    set srr, 'o.sorted.bam', 'o.sorted.bam.bai' into sorted_bam2
    set srr, 'o.sorted.bam', 'o.sorted.bam.bai' into sorted_bam3
    set srr, 'o.sorted.bam', 'o.sorted.bam.bai' into sorted_bam4
    
    """
    sambamba sort --tmpdir=${params.temp} -p -m 10G -t ${task.cpus} -o o.sorted.bam ${bam}
    sambamba index -t ${task.cpus} o.sorted.bam
    """
}

/*
// Disabled, but useful if you want to stop after alignment

process publish_bam_sort {
    tag { srr }
    publishDir params.outdir, mode: 'copy'
    
    input:
    set srr, file(sbam) from sorted_bam
    
    output:
    file('*.sorted.bam') into sorted_bam_final
    
    """
    mv ${sbam} ${srr}.sorted.bam
    """
}
*/

process assemble {
    tag { srr }
    
    input:
    set srr, file(sbam), file(sbam_idx) from sorted_bam1

    output:
    set srr, file('o.gtf') into gtf

    """
    stringtie -l ${srr} ${sbam} > o.gtf
    """
}

process publish_gtf {
    tag { srr }
    publishDir params.outdir, mode: 'copy'
    
    input:
    set srr, file(gtf) from gtf
    
    output:
    file('*.gtf') into gtf_final
    
    """
    mv ${gtf} ${srr}.gtf
    """
}

process bam_to_bw_all {
    tag { srr }
    
    input:
    set srr, file(sbam), file(sbam_idx) from sorted_bam2

    output:
    set srr, file('o.all.bw') into bw_all
    
    """
    mv ${sbam} i.bam
    mv ${sbam_idx} i.bam.bai
    bamCoverage -b i.bam -o o.all.bw
    """
}

process bam_to_bw_unique {
    tag { srr }
    
    input:
    set srr, file(sbam), file(sbam_idx) from sorted_bam3

    output:
    set srr, file('o.unique.bw') into bw_unique
    
    """
    mv ${sbam} i.bam
    mv ${sbam_idx} i.bam.bai
    bamCoverage --minMappingQuality 10 -b i.bam -o o.unique.bw
    """
}

process publish_bw_all {
    tag { srr }
    publishDir params.outdir, mode: 'copy'
    
    input:
    set srr, file(bw) from bw_all
    
    output:
    file('*.all.bw') into bw_all_final
    
    """
    mv ${bw} ${srr}.all.bw
    """
}

process publish_bw_unique {
    tag { srr }
    publishDir params.outdir, mode: 'copy'
    
    input:
    set srr, file(bw) from bw_unique
    
    output:
    file('*.unique.bw') into bw_unique_final
    
    """
    mv ${bw} ${srr}.unique.bw
    """
}

process extract_junctions {
    tag { srr }

    input:
    set srr, file(sbam), file(sbam_idx) from sorted_bam4

    output:
    set srr, 'o.jx_bed' into jx_bed
    
    """
    # Options:
    # -a INT   Minimum anchor length; jxs w/ min length on both sides are reported
    # -i INT   Minimum intron length. [70]
    # -I INT   Maximum intron length. [500000]

    regtools junctions extract -i 20 -a 1 -o o.jx_bed ${sbam}
    """
}

process publish_jx_bed {
    tag { srr }
    publishDir params.outdir, mode: 'copy'
    
    input:
    set srr, file(jx_bed) from jx_bed
    
    output:
    file('*.jx_bed') into jx_bed_final
    
    """
    mv ${jx_bed} ${srr}.jx_bed
    """
}
