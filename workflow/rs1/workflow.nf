#!/usr/bin/env nextflow

/*
 * Example rs1 HISAT2-based RNA-seq pipeline
 * Author: Ben Langmead
 *   Date: 9/21/2018
 *
 * Published outputs:
 * - Alignment log (<accession>_align_log.txt)
 * - BigWigs
 *   + Unique (<accession>.unique.bw)
 *   + All (<accession>.all.bw)
 * - Junction counts (<accession>.jx_bed)
 * - Gene & exon counts (<accession>.all.gene_count, <accession>.unique.gene_count)
 */

params.in   = 'accessions.txt'
params.out  = 'results'
params.ref  = '${RECOUNT_REF}'
params.temp = '${RECOUNT_TEMP}'
params.cpus = 1 

srrs = Channel
       .fromPath(params.in)
       .splitCsv(header: ['srr', 'srp', 'species'])
       .ifEmpty { error "Cannot find any accessions in: ${params.in}" }


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
    test -f ${params.ref}/${species}/fasta/genome.fa
    """
}

process sra_fastq {
    tag { srr }

    cpus ${params.cpus}
    executor 'local'

    input:
    set srr, srp, species from srrs2
    
    output:
    set srr, srp, species, '*.fastq' into fastq
    
    """
    parallel-fastq-dump --tmpdir ${params.temp} -s ${srr} -t ${task.cpus} --split-files -I --skip-technical
    ls *_2.fastq 2>/dev/null || \
        for i in *_1.fastq ; do
            mv \$i `echo \$i | sed 's/_1.fastq/_0.fastq/'`
        done
    """
}

process hisat2_align {
    tag { srr }
    
    cpus ${params.cpus}
    executor 'local'

    input:
    set srr, srp, species, file('?.fastq') from fastq

    output:
    set srr, srp, species, 'o.bam' into bam
    set srr, srp, 'o.log' into align_log

    """
    IDX=${params.ref}/${species}/hisat2_idx/genome
    READ_FILES="-U 1.fastq"
    if [[ -f 2.fastq ]] ; then
        READ_FILES="-1 1.fastq -2 2.fastq"
    fi
    HISAT2_ARGS="-t --mm -x \${IDX} --threads ${task.cpus}"
    hisat2 \
        \${READ_FILES} \
        \${HISAT2_ARGS} \
        --novel-splicesite-outfile tmp_splicing.tab \
        2>o.log && \
    hisat2 \
        \${READ_FILES} \
        \${HISAT2_ARGS} \
        --known-splicesite-infile tmp_splicing.tab \
        2>>o.log | \
    sambamba view -S -f bam -F "not unmapped" -o o.bam /dev/stdin
    """
}

process publish_align_log {
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

process bam_sort {
    tag { srr }

    cpus ${params.cpus}
    executor 'local'

    input:
    set srr, srp, species, file(bam) from bam
    
    // Channels can't be reused, so I have to make several.
    // Is there a less silly way to funnel output to N other process?
    output:
    set srr, srp, species, 'o.sorted.bam', 'o.sorted.bam.bai' into sorted_bam1, sorted_bam2, sorted_bam3,
                                                                   sorted_bam4, sorted_bam5, sorted_bam6
    
    """
    sambamba sort --tmpdir=${params.temp} -p -m 10G --nthreads=${task.cpus} -o o.sorted.bam ${bam}
    sambamba index --nthreads=${task.cpus} o.sorted.bam
    """
}

process bam_to_bw_all {
    tag { srr }
    
    input:
    set srr, srp, species, file(sbam), file(sbam_idx) from sorted_bam2

    output:
    set srr, srp, file('o.all.bw') into bw_all_publish
    set srr, srp, file('o.all.bw') into bw_all
    
    """
    mv ${sbam} i.bam
    mv ${sbam_idx} i.bam.bai
    bamCoverage -b i.bam -o o.all.bw
    """
}

process bam_to_bw_unique {
    tag { srr }
    
    input:
    set srr, srp, species, file(sbam), file(sbam_idx) from sorted_bam3

    output:
    set srr, srp, file('o.unique.bw') into bw_unique_publish
    set srr, srp, file('o.unique.bw') into bw_unique
    
    """
    mv ${sbam} i.bam
    mv ${sbam_idx} i.bam.bai
    bamCoverage --minMappingQuality 10 -b i.bam -o o.unique.bw
    """
}

process publish_bw_all {
    tag { srr }
    publishDir params.out, mode: 'copy'
    
    input:
    set srr, srp, file(bw) from bw_all_publish
    
    output:
    file('*.all.bw') into bw_all_final
    
    """
    mv ${bw} ${srr}.all.bw
    """
}

process publish_bw_unique {
    tag { srr }
    publishDir params.out, mode: 'copy'
    
    input:
    set srr, srp, file(bw) from bw_unique_publish
    
    output:
    file('*.unique.bw') into bw_unique_final
    
    """
    mv ${bw} ${srr}.unique.bw
    """
}

process gene_count_all {
    tag { srr }
    publishDir params.out, mode: 'copy'
    
    input:
    set srr, srp, species, file(bam), file(bai) from sorted_bam5
    
    output:
    file('*.all.gene_count') into gene_count_all_final
    
    """
    GTF=${params.ref}/${species}/gtf/genes.gtf
    featureCounts -f -p -a \${GTF} -F GTF -t exon -g gene_id -o tmp ${bam}
    awk -v OFS='\\t' '\$1 !~ /^#/ && \$1 !~ /^Geneid/ && \$NF != 0 {print "${srr}",\$0}' tmp > ${srr}.all.gene_count
    """
}

process gene_count_unique {
    tag { srr }
    publishDir params.out, mode: 'copy'
    
    input:
    set srr, srp, species, file(bam), file(bai) from sorted_bam6
    
    output:
    file('*.unique.gene_count') into gene_count_unique_final
    
    """
    GTF=${params.ref}/${species}/gtf/genes.gtf
    featureCounts -Q 10 -f -p -a \${GTF} -F GTF -t exon -g gene_id -o tmp ${bam}
    awk -v OFS='\\t' '\$1 !~ /^#/ && \$1 !~ /^Geneid/ && \$NF != 0 {print "${srr}",\$0}' tmp > ${srr}.unique.gene_count
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
    # TODO: copy jx_tmp file via globus
    """
}
