#!/bin/sh

# Author: Ben Langmead
#   Date: 11/26/17

# sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Homo_sapiens/UCSC/hg38/Homo_sapiens_UCSC_hg38.tar.gz hg38 Homo_sapiens UCSC
# sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Mus_musculus/UCSC/mm10/Mus_musculus_UCSC_mm10.tar.gz mm10 Mus_musculus UCSC
# sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Drosophila_melanogaster/UCSC/dm6/Drosophila_melanogaster_UCSC_dm6.tar.gz dm6 Drosophila_melanogaster UCSC
# sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Danio_rerio/UCSC/danRer10/Danio_rerio_UCSC_danRer10.tar.gz danRer10 Danio_rerio UCSC
# sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Rattus_norvegicus/UCSC/rn6/Rattus_norvegicus_UCSC_rn6.tar.gz rn6 Rattus_norvegicus UCSC

set -e

URL=$1
NM=$2
SPECIES=$3
SOURCE=$4

[ ! -d igenomes ] && echo "Expected igenomes subdir" && exit 1

[ -z "${URL}"     ] && echo "Must specify URL as first argument" && exit 1
[ -z "${NM}"      ] && echo "Must specify shortname as 2nd argument" && exit 1
[ -z "${SPECIES}" ] && echo "Must specify species (e.g. Homo_sapiens) as 3rd argument" && exit 1
[ -z "${SOURCE}"  ] && echo "Must specify source (e.g. UCSC) as 4th argument" && exit 1

FN=`basename ${URL}`

if [ ! -d ${NM} ] ; then
    
    if [ ! -d igenomes/${SPECIES}/${SOURCE} ] ; then
        if [ ! -f igenomes/${FN} ] ; then
            echo "Downloading iGenomes package"
            
            # Download & explode
            wget -O igenomes/${FN} ${URL}
        fi
        cd igenomes && tar zvfx ${FN} && cd ..
        
        # Don't need per-chromosome FASTAs
        rm -rf igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/Chromosomes
    else
        echo "iGenomes package already present"
    fi
    
    # Double-check that it looks good
    GENOME_FA="igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/WholeGenomeFasta/genome.fa"
    if [ ! -f "${GENOME_FA}" ] ; then
        echo "No genome FASTA!  Check if igenomes download and explode worked."
        echo "${GENOME_FA}"
        exit 1
    fi
if [[ ! -d ${NM}/fasta ]]; then  

    #adding ERCC & SIRV control transcripts
    pushd ercc
    /bin/bash -x ./01_get_ercc.sh
    popd
    test -f ercc/ercc_all.fasta
    cat ercc/ercc_all.fasta >> igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/WholeGenomeFasta/genome.fa

    pushd sirv
    /bin/bash -x ./get_all.sh
    /bin/bash -x cp.sh
    popd
    test -f sirv/SIRV_isoforms_multi-fasta_170612a.fasta 
    cat sirv/SIRV_isoforms_multi-fasta_170612a.fasta >> igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/WholeGenomeFasta/genome.fa

    #index is now out of date with the addition of the ERCC/SIRVs
    rm -f igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/WholeGenomeFasta/genome.fa.fai
    rm -f igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/WholeGenomeFasta/genome.dict

    echo "Populating ${NM}/fasta"
    mkdir -p ${NM}/fasta
    cp igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/WholeGenomeFasta/genome.fa ${NM}/fasta/
fi 

    echo "Populating ${NM}/gtf"
    mkdir -p ${NM}/gtf
    #pick up Gencodev26 (GTEx uses) for featureCounts counting
    curl ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_26/gencode.v26.chr_patch_hapl_scaff.annotation.gtf.gz | gzip -cd > ${NM}/gtf/gencode.v26.chr_patch_hapl_scaff.annotation.gtf

    echo "Building ${NM}/salmon_index"
    #GTF annotation contains refs not in the FASTA
    #passing a ref mapping file (identity) will force any lines with unknown refs in the GTF to be ignored
    fgrep ">" ${NM}/fasta/genome.fa | perl -ne 'chomp; $f=$_; $f=~s/^>//; print "$f $f\n"; print STDERR "^$f\t\n";' > ${NM}/fasta/genome.fa.mapping 2> ${NM}/fasta/genome.fa.refs
    egrep -f ${NM}/fasta/genome.fa.refs ${NM}/gtf/gencode.v26.chr_patch_hapl_scaff.annotation.gtf > ${NM}/gtf/gencode.v26.chr_patch_hapl_scaff.annotation.subset.gtf
    rm ${NM}/gtf/gencode.v26.chr_patch_hapl_scaff.annotation.gtf
    ln -fs gencode.v26.chr_patch_hapl_scaff.annotation.subset.gtf ${NM}/gtf/genes.gtf
    mkdir -p ${NM}/transcriptome
    gffread -w ${NM}/transcriptome/transcripts.fa \
            -g ${NM}/fasta/genome.fa \
            -m ${NM}/fasta/genome.fa.mapping \
            ${NM}/gtf/genes.gtf
   
    #cat the additional transcripts from the ERCC/SIRVs post gffread so
    #that we get the whole transcript's sequence, not just the exons 
    cat ercc/ercc_all.gtf >> ${NM}/gtf/genes.gtf
    cat ercc/ercc_all.fasta >> ${NM}/transcriptome/transcripts.fa
    cat sirv/SIRV_isoforms_multi-fasta-annotation_C_170612a.gtf >> ${NM}/gtf/genes.gtf
    cat sirv/SIRV_isoforms_multi-fasta_170612a.fasta >> ${NM}/transcriptome/transcripts.fa
    
    mkdir -p ${NM}/salmon_index
    salmon index -i ${NM}/salmon_index -t ${NM}/transcriptome/transcripts.fa
    
    echo "To populate ${NM}/hisat2_idx and ${NM}/star_idx, run the below commands"
    echo "==========="

    # hisat2: 2.1.0 py27pl5.22.0_0 bioconda
    mkdir -p ${NM}/hisat2_idx    
    cat >.hisat2_${NM}.sh << EOF
#!/bin/bash -l
#SBATCH
#SBATCH --job-name=hisat2_build
#SBATCH --partition=parallel
#SBATCH --output=.hisat2_${NM}.sh.o
#SBATCH --error=.hisat2_${NM}.sh.e
#SBATCH --nodes=1
#SBATCH --mem=100G
#SBATCH --time=2:00:00
#SBATCH --ntasks-per-node=24

set -e

NM=${NM}
SOURCE=${SOURCE}
SPECIES=${SPECIES}
IN=igenomes/\${SPECIES}/\${SOURCE}/\${NM}/Sequence/WholeGenomeFasta/genome.fa
OUT=\${NM}/hisat2_idx

hisat2-build --threads 24 \${IN} \${OUT}/genome
EOF
    echo "sbatch .hisat2_${NM}.sh"

    # star: 2.5.3a-0 bioconda
    mkdir -p ${NM}/star_idx
    cat >.star_${NM}.sh << EOF
#!/bin/bash -l
#SBATCH
#SBATCH --job-name=star_build
#SBATCH --partition=parallel
#SBATCH --output=.star_${NM}.sh.o
#SBATCH --error=.star_${NM}.sh.e
#SBATCH --nodes=1
#SBATCH --mem=100G
#SBATCH --time=2:00:00
#SBATCH --ntasks-per-node=24

set -e

NM=${NM}
SOURCE=${SOURCE}
SPECIES=${SPECIES}
IN=igenomes/\${SPECIES}/\${SOURCE}/\${NM}/Sequence/WholeGenomeFasta/genome.fa
OUT=\${NM}/star_idx
TMP=\${NM}/star_tmp

rm -rf \${TMP}

STAR \
    --runThreadN 24 \
    --runMode genomeGenerate \
    --genomeDir \${OUT} \
    --outTmpDir \${TMP} \
    --genomeFastaFiles \${IN}

rm -rf \${TMP}
EOF
    echo "sbatch .star_${NM}.sh"

fi
