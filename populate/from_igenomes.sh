#!/bin/sh

# Author: Ben Langmead
#   Date: 11/26/17

# sh from_igenomes.sh \
#   ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Homo_sapiens/UCSC/hg38/Homo_sapiens_UCSC_hg38.tar.gz \
#   hg38
#   Homo_sapiens
#   UCSC

set -e

URL=$1
NM=$2
SPECIES=$3
SOURCE=$4

which singularity >/dev/null 2>/dev/null || (echo "No singularity in PATH" && exit 1) 

[ ! -d igenomes ] && echo "Expected igenomes subdir" && exit 1

[ -z "${SINGULARITY_CACHEDIR}" ] && echo "Set SINGULARITY_CACHEDIR first" && exit 1

[ ! -f "${SINGULARITY_CACHEDIR}/star.simg" ] && echo "Run get_simgs.sh first" && exit 1

[ -z "${URL}"     ] && echo "Must specify URL as first argument" && exit 1
[ -z "${NM}"      ] && echo "Must specify shortname as 2nd argument" && exit 1
[ -z "${SPECIES}" ] && echo "Must specify species (e.g. Homo_sapiens) as 3rd argument" && exit 1
[ -z "${SOURCE}"  ] && echo "Must specify source (e.g. UCSC) as 4th argument" && exit 1

FN=`basename ${URL}`

if [ ! -d ${NM} ] ; then
    
    if [ ! -f igenomes/${FN} ] ; then
        echo "Downloading iGenomes package"
        wget -O igenomes/${FN} ${URL}
        cd igenomes && tar zvfx ${FN} && cd ..
    else
        echo "iGenomes package already present"
    fi
    
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
    cp igenomes/${SPECIES}/${SOURCE}/${NM}/Annotation/Genes/genes.gtf ${NM}/gtf/
    cp igenomes/${SPECIES}/${SOURCE}/${NM}/Annotation/Genes.gencode/genes.gtf ${NM}/gtf/genes_gencode.gtf
    
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
sing hisat2 build \
    --threads 24 \
    igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/WholeGenomeFasta/genome.fa \
    ${NM}/hisat2_idx/genome
EOF
    echo "sbatch .hisat2_${NM}.sh"

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

sing star \
    --runThreadN 24 \
    --runMode genomeGenerate \
    --genomeDir ${NM}/star_idx \
    --genomeFastaFiles igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/WholeGenomeFasta/genome.fa
EOF
    echo "sbatch .star_${NM}.sh"

fi
