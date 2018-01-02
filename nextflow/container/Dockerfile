################## BASE IMAGE ######################

FROM biocontainers/biocontainers:latest

################## METADATA ######################
LABEL base.image="biocontainers:latest"
LABEL version="1"
LABEL software="recount-pump"
LABEL software.version="0.0.1"
LABEL tags="Genomics"

################## MAINTAINER ######################
MAINTAINER Ben Langmead <ben.langmead@gmail.com>

################## INSTALLATION ######################

ADD rna_seq.yml /tmp/
ADD rna_seq.nf /home/biodocker/bin/
RUN conda env create -f /tmp/rna_seq.yml
RUN git clone https://github.com/griffithlab/regtools.git -- regtools && \
    cd regtools && \
    git checkout tags/0.3.0 && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    mv regtools /home/biodocker/bin/ && \
    cd ../.. && \
    rm -rf regtools

WORKDIR /data

CMD ["source activate rnaseq_v0 && rna-seq.nf"]
