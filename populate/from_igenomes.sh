#!/bin/bash

# Author: Ben Langmead
#   Date: 11/26/17
# Updated by Chris Wilks

# this script assumes the following are in PATH:
#1) STAR
#2) gffread
#3) hisat2_build
#4) salmon


# sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Homo_sapiens/UCSC/hg38/Homo_sapiens_UCSC_hg38.tar.gz hg38 Homo_sapiens UCSC ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_26/gencode.v26.chr_patch_hapl_scaff.annotation.gtf.gz

# sh from_igenomes.sh ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M23/GRCm38.primary_assembly.genome.fa.gz grcm38 Mus_musculus gencode ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M23/gencode.vM23.primary_assembly.annotation.gtf.gz

set -e

URL=$1
NM=$2
SPECIES=$3
SOURCE=$4
GTF_URL=$5

[ ! -d igenomes ] && echo "Expected igenomes subdir" && exit 1

[ -z "${URL}"     ] && echo "Must specify URL as first argument" && exit 1
[ -z "${NM}"      ] && echo "Must specify shortname as 2nd argument" && exit 1
[ -z "${SPECIES}" ] && echo "Must specify species (e.g. Homo_sapiens) as 3rd argument" && exit 1
[ -z "${SOURCE}"  ] && echo "Must specify source (e.g. UCSC) as 4th argument" && exit 1
[ -z "${GTF_URL}"  ] && echo "Must specify annotation GTF file path (e.g. gencode.v26.chr_patch_hapl_scaff.annotation.gtf) as 5th argument" && exit 1

FN=`basename ${URL}`
GTF_URL_FN=`basename ${GTF_URL}`
GENOME_FA="igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/WholeGenomeFasta/genome.fa"

if [[ ! -d ${NM} || ! -d ${NM}/fasta || ! -d $NM/gtf ]] ; then
    
    if [[ ! -e $GENOME_FA && ${NM} -ne 'grcm38' ]] ; then
        if [ ! -f igenomes/${FN} ] ; then
            echo "Downloading iGenomes package"
            
            # Download & explode
            wget -O igenomes/${FN} ${URL}
        fi
        cd igenomes && tar zvfx ${FN} && cd ..
        
        # Don't need per-chromosome FASTAs
        rm -rf igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/Chromosomes
    else 
        if [[ ! -e $GENOME_FA && ${NM} -eq 'grcm38' ]]; then
            mkdir -p igenomes/${SPECIES}/${SOURCE}/${NM}/Sequence/WholeGenomeFasta
            wget -O igenomes/${FN} ${URL}
            #need to get rid of extra post-space parts of the headers
            zcat igenomes/${FN} | perl -ne 'chomp; $f=$_; if($f=~/^>/) { $f=~s/\s.+$//; } print "$f\n";' > $GENOME_FA
        else
            echo "iGenomes package already present"
        fi
    fi
    
    # Double-check that it looks good
    if [ ! -f "${GENOME_FA}" ] ; then
        echo "No genome FASTA!  Check if igenomes download and explode worked."
        echo "${GENOME_FA}"
        exit 1
    fi
    if [[ ! -d ${NM}/fasta ]]; then  
        echo "Populating ${NM}/fasta"
        mkdir -p ${NM}/fasta
        cp $GENOME_FA ${NM}/fasta/
        #adding ERCC & SIRV control transcripts
        pushd ercc
        /bin/bash -x ./01_get_ercc.sh
        popd
        test -f ercc/ercc_all.fasta
        cat ercc/ercc_all.fasta >> ${NM}/fasta//genome.fa

        pushd sirv
        /bin/bash -x ./get_all.sh
        /bin/bash -x cp.sh
        popd
        test -f sirv/SIRV_isoforms_multi-fasta_170612a.fasta 
        cat sirv/SIRV_isoforms_multi-fasta_170612a.fasta >> ${NM}/fasta//genome.fa
    fi 

    if [[ ! -d ${NM}/gtf ]]; then  
        echo "Populating ${NM}/gtf"
        mkdir -p ${NM}/gtf
        wget -O ${NM}/gtf/${GTF_URL_FN} $GTF_URL
        zcat ${NM}/gtf/${GTF_URL_FN} > ${NM}/gtf/genes.gtf

        echo "Building ${NM}/salmon_index"
        #in case GTF annotation contains refs not in the FASTA
        #passing a ref mapping file (identity) will force any lines with unknown refs in the GTF to be ignored
        fgrep ">" ${NM}/fasta/genome.fa | perl -ne 'chomp; $f=$_; $f=~s/^>//; print "$f $f\n"; print STDERR "^$f\t\n";' > ${NM}/fasta/genome.fa.mapping 2> ${NM}/fasta/genome.fa.refs
        egrep -f ${NM}/fasta/genome.fa.refs ${NM}/gtf/genes.gtf > ${NM}/gtf/genes.subset.gtf
        rm ${NM}/gtf/genes.gtf
        ln -fs genes.subset.gtf ${NM}/gtf/genes.gtf
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
    fi

    echo "To populate ${NM}/star_idx, run the below commands"
    echo "==========="

    # star: 2.7.3a
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
IN=\${NM}/fasta/genome.fa
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
