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
 * - wiggletools
 *
 * Published outputs:
 * - Alignment log (<accession>_align_log.txt)
 * - BigWigs
 *   + Unique (<accession>.unique.bw)
 *   + All (<accession>.all.bw)
 * - AUCs for BigWigs (<accession>.unique.auc, <accession>.all.auc)
 * - Junction counts (<accession>.jx_count)
 *   + similar to bed_to_juncs output, but includes count and accession
 * - Assembly (<accession>.gtf)
 *
 * TODO:
 * - Let input csv specify URL and/or retrieval method
 *   + As of now retrieval is always with fastq-dump
 * - Add more recount/Snaptron postprocessing
 *   + Junction annotation
 *   + Annotation quantification (gene & exon)
 */

params.in         = 'accessions.txt'
params.temp       = '/tmp'
params.refdir     = '${HOME}/recount-refs'
params.outdir     = 'results'
params.cpus       = 8
params.stop_after_alignment = false

srr = Channel
      .fromPath(params.in)
      .splitCsv(header: ['srr', 'species'])
      .ifEmpty { error "Cannot find any accessions in: ${params.in}" }


// Doing this first means checks are skipped when pipeline is resumed?
process preliminary {
    tag { srr }
    
    input:
    set srr, species from srr
    
    output:
    set srr, species into srr2
    
    """
    # Ensure all the expected support files are around
    test -d ${params.refdir}/${species}
    for i in 1 2 3 4 5 6 7 8 ; do
        test -f ${params.refdir}/${species}/hisat2_idx/genome.\${i}.ht2
    done
    test -f ${params.refdir}/${species}/fasta/genome.fa
    test -f ${params.refdir}/${species}/gtf/genes.gtf
    """
}

process sra_fastq {
    tag { srr }

    input:
    set srr, species from srr2
    
    output:
    set srr, species, '*.fastq' into fastq
    
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
    set srr, species, file('?.fastq') from fastq

    output:
    set srr, species, 'o.sam' into sam
    set srr, 'o.log' into align_log

    """
    IDX=${params.refdir}/${species}/hisat2_idx/genome
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
    set srr, species, file(samf) from sam
    
    output:
    set srr, species, 'o.bam' into bam
    
    """
    sambamba view -S -f bam -t ${task.cpus} ${samf} > o.bam
    """
}

process bam_sort {
    tag { srr }
    cpus params.cpus

    input:
    set srr, species, file(bam) from bam
    
    // Channels can't be reused, so I have to make several.
    // Is there a less silly way to funnel output to N other process?
    output:
    set srr, species, 'o.sorted.bam', 'o.sorted.bam.bai' into sorted_bam1
    set srr, species, 'o.sorted.bam', 'o.sorted.bam.bai' into sorted_bam2
    set srr, species, 'o.sorted.bam', 'o.sorted.bam.bai' into sorted_bam3
    set srr, species, 'o.sorted.bam', 'o.sorted.bam.bai' into sorted_bam4
    
    """
    sambamba sort --tmpdir=${params.temp} -p -m 10G -t ${task.cpus} -o o.sorted.bam ${bam}
    sambamba index -t ${task.cpus} o.sorted.bam
    """
}

process assemble {
    tag { srr }
    
    input:
    set srr, species, file(sbam), file(sbam_idx) from sorted_bam1

    output:
    set srr, file('o.gtf') into gtf_publish

    """
    stringtie -l ${srr} ${sbam} > o.gtf
    """
}

process publish_gtf {
    tag { srr }
    publishDir params.outdir, mode: 'copy'
    
    input:
    set srr, file(gtf) from gtf_publish
    
    output:
    file('*.gtf') into gtf_final
    
    """
    mv ${gtf} ${srr}.gtf
    """
}

process bam_to_bw_all {
    tag { srr }
    
    input:
    set srr, species, file(sbam), file(sbam_idx) from sorted_bam2

    output:
    set srr, file('o.all.bw') into bw_all_publish
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
    set srr, species, file(sbam), file(sbam_idx) from sorted_bam3

    output:
    set srr, file('o.unique.bw') into bw_unique_publish
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
    set srr, file(bw) from bw_all_publish
    
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
    set srr, file(bw) from bw_unique_publish
    
    output:
    file('*.unique.bw') into bw_unique_final
    
    """
    mv ${bw} ${srr}.unique.bw
    """
}

process extract_junctions {
    tag { srr }

    input:
    set srr, species, file(sbam), file(sbam_idx) from sorted_bam4

    output:
    set srr, 'o.jx_bed' into jx_bed
    
    """
    # Options:
    # -a INT   Minimum anchor length; jxs w/ min length on both sides are reported
    # -i INT   Minimum intron length. [70]
    # -I INT   Maximum intron length. [500000]

    FA=${params.refdir}/${species}/fasta/genome.fa
    GTF=${params.refdir}/${species}/gtf/genes.gtf
    regtools junctions extract -i 20 -a 1 -o o.jx_bed ${sbam}
    #regtools junctions extract -i 20 -a 1 -o otmp.jx_bed ${sbam}
    #regtools junctions annotate -E -o o.jx_bed otmp.jx_bed \${FA} \${GTF}
    """
}

process count_junctions {
    tag { srr }
    publishDir params.outdir, mode: 'copy'
    
    input:
    set srr, file(jxb) from jx_bed
    
    output:
    file('*.jx_count') into jx_count_final
    
    """
#!/usr/bin/env python
with open('$jxb', 'r') as ifh:
    with open('$srr' + '.jx_count', 'w') as ofh:
        for i, ln in enumerate(ifh):
            toks = ln.rstrip().split('\\t')
            assert len(toks) == 12, (i, ln)
            chrom, strand = toks[0], toks[5]
            starts = list(map(int, toks[11].split(",")))
            size = int(toks[10].split(",")[0])
            left_pos = int(toks[1]) + starts[0] + size + 1
            right_pos = int(toks[1]) + starts[1]
            ofh.write('\\t'.join(map(str, ['$srr', chrom, left_pos, right_pos, strand, toks[4]])) + '\\n')
    """
}

process calc_all_auc {
    tag { srr }
    publishDir params.outdir, mode: 'copy'

    input:
    set srr, file(bw) from bw_all
    
    output:
    file('*.auc') into auc_all_final
    
    """
    # wiggletools expects .bw suffix for bigWig input
    mv $bw i.bw
    wiggletools print ${srr}.all.auc AUC i.bw
    """
}

process calc_unique_auc {
    tag { srr }
    publishDir params.outdir, mode: 'copy'

    input:
    set srr, file(bw) from bw_unique
    
    output:
    file('*.auc') into auc_unique_final
    
    """
    # wiggletools expects .bw suffix for bigWig input
    mv $bw i.bw
    wiggletools print ${srr}.unique.auc AUC i.bw
    """
}
