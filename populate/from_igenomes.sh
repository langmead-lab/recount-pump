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
    
    echo "Populating ${NM}/fasta"
    mkdir -p ${NM}/fasta
    cp igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/WholeGenomeFasta/genome.* ${NM}/fasta/
    
    echo "Populating ${NM}/gtf"
    mkdir -p ${NM}/gtf
    GENES_DIR="igenomes/${SPECIES}/${SOURCE}/${NM}/Annotation/Genes"
    cp "$GENES_DIR/genes.gtf" ${NM}/gtf/
    [ -d "${GENES_DIR}.gencode" ] && cp "${GENES_DIR}.gencode/genes.gtf" ${NM}/gtf/genes_gencode.gtf
    
    echo "Building ${NM}/kallisto_index"
    mkdir -p ${NM}/transcriptome
    gffread -w ${NM}/transcriptome/transcripts.fa \
            -g ${NM}/fasta/genome.fa \
            ${NM}/gtf/genes.gtf

    mkdir -p ${NM}/kallisto_index
    kallisto index -i kallisto_index/transcriptome_index transcriptome/transcripts.fa

    echo "Building ${NM}/salmon_index"
    mkdir -p ${NM}/salmon_index
    salmon index -i salmon_index -t transcriptome/transcripts.fa
    
    echo "Populating ${NM}/ucsc_tracks"
    mkdir -p ${NM}/ucsc_tracks
    # TODO
    
    echo "Populating ${NM}/bowtie_idx"
    mkdir -p ${NM}/bowtie_idx
    cp igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/BowtieIndex/*.ebwt ${NM}/bowtie_idx
    
    echo "Populating ${NM}/bowtie2_idx"
    mkdir -p ${NM}/bowtie2_idx
    cp igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/Bowtie2Index/*.bt2 ${NM}/bowtie2_idx

    echo "Populating ${NM}/bwa_idx"
    mkdir -p ${NM}/bwa_idx
    cp igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/BWAIndex/genome.fa* ${NM}/bwa_idx

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
