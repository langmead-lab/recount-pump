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
 * - Manifest file (<accession>.manifest)
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
    mkdir -p ${params.temp}
    """
}

process sra_fastq {
    tag { srr }

    cpus "${params.cpus}"
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
    
    cpus "${params.cpus}"
    executor 'local'

    input:
    set srr, srp, species, file('?.fastq') from fastq

    output:
    set srr, srp, species, 'o.bam' into bam
    set srr, srp, 'o.log' into publish_align_log

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

process bam_sort {
    tag { srr }

    cpus "${params.cpus}"
    executor 'local'

    input:
    set srr, srp, species, file(bam) from bam
    
    // Channels can't be reused, so I have to make several.
    // Is there a less silly way to funnel output to N other process?
    output:
    set srr, srp, species, 'o.sorted.bam', 'o.sorted.bam.bai' into sorted_bam2, sorted_bam3,
                                                                   sorted_bam4, sorted_bam5,
                                                                   sorted_bam6
    
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
    set srr, srp, file('o.all.bw') into publish_bw_all
    
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
    set srr, srp, file('o.unique.bw') into publish_bw_unique
    
    """
    mv ${sbam} i.bam
    mv ${sbam_idx} i.bam.bai
    bamCoverage --minMappingQuality 10 -b i.bam -o o.unique.bw
    """
}

process gene_count_all {
    tag { srr }
    
    input:
    set srr, srp, species, file(bam), file(bai) from sorted_bam5
    
    output:
    set srr, srp, file('o.all.gene_count') into publish_gc_all
    
    """
    GTF=${params.ref}/${species}/gtf/genes.gtf
    featureCounts -f -p -a \${GTF} -F GTF -t exon -g gene_id -o tmp ${bam}
    awk -v OFS='\\t' '\$1 !~ /^#/ && \$1 !~ /^Geneid/ && \$NF != 0 {print "${srr}",\$0}' tmp > o.all.gene_count
    """
}

process gene_count_unique {
    tag { srr }
    
    input:
    set srr, srp, species, file(bam), file(bai) from sorted_bam6
    
    output:
    set srr, srp, file('o.unique.gene_count') into publish_gc_unique
    
    """
    GTF=${params.ref}/${species}/gtf/genes.gtf
    featureCounts -Q 10 -f -p -a \${GTF} -F GTF -t exon -g gene_id -o tmp ${bam}
    awk -v OFS='\\t' '\$1 !~ /^#/ && \$1 !~ /^Geneid/ && \$NF != 0 {print "${srr}",\$0}' tmp > o.unique.gene_count
    """
}

process extract_junctions {
    tag { srr }

    input:
    set srr, srp, species, file(sbam), file(sbam_idx) from sorted_bam4

    output:
    set srr, srp, file('o.jx_bed') into publish_jx
    
    """
    FA=${params.ref}/${species}/fasta/genome.fa
    GTF=${params.ref}/${species}/gtf/genes.gtf
    regtools junctions extract -i 20 -a 1 -o o.jx_tmp ${sbam}
    regtools junctions annotate -E -o o.jx_bed o.jx_tmp \${FA} \${GTF}
    """
}

process publish_all {
    tag { srr }
    publishDir params.out, mode: 'copy'

    input:
    set  srr,  srp, file(logf)              from publish_align_log
    set srr1, srp1, file(all_bw)            from publish_bw_all
    set srr2, srp2, file(unique_bw)         from publish_bw_unique
    set srr3, srp3, file(all_gene_count)    from publish_gc_all
    set srr4, srp4, file(unique_gene_count) from publish_gc_unique
    set srr5, srp5, file(jx_bed)            from publish_jx

    output:
    file('*_align_log.txt')     into publish_final0
    file('*.all.bw')            into publish_final1
    file('*.unique.bw')         into publish_final2
    file('*.unique.gene_count') into publish_final3
    file('*.all.gene_count')    into publish_final4
    file('*.jx_bed')            into publish_final5
    file('*.manifest')          into publish_final6
    
    """
    # Name output files properly
    mv ${logf}              ${srr}_align_log.txt
    mv ${all_bw}            ${srr}.all.bw
    mv ${unique_bw}         ${srr}.unique.bw
    mv ${all_gene_count}    ${srr}.unique.gene_count
    mv ${unique_gene_count} ${srr}.all.gene_count
    mv ${jx_bed}            ${srr}.jx_bed
    
    # Create manifest
    echo "${srr}_align_log.txt"      > ${srr}.manifest
    echo "${srr}.all.bw"            >> ${srr}.manifest
    echo "${srr}.unique.bw"         >> ${srr}.manifest
    echo "${srr}.unique.gene_count" >> ${srr}.manifest
    echo "${srr}.all.gene_count"    >> ${srr}.manifest
    echo "${srr}.jx_bed"            >> ${srr}.manifest
    """
}
