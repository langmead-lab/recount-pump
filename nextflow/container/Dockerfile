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

# install conda environment
ADD rna_seq.yml /tmp/
RUN conda env create -f /tmp/rna_seq.yml

# install globus-cli using pipe
RUN bash -c "source activate rnaseq_v0 && pip install globus-cli"
# triggers nextflow dependency downloads
RUN bash -c "source activate rnaseq_v0 && (nextflow clean -f || true)"

# install regtools from github
RUN git clone https://github.com/griffithlab/regtools.git -- regtools && \
    cd regtools && \
    git checkout tags/0.3.0 && \
    mkdir build && \
    cd build && \
    export CMAKE_BUILD_TYPE=Release && \
    cmake .. && \
    make && \
    mv regtools /home/biodocker/bin/ && \
    cd ../.. && \
    rm -rf regtools

WORKDIR /data

# install nextflow script
COPY rna_seq.nf /home/biodocker/bin/
COPY rna_seq.bash /home/biodocker/bin/

CMD ["bash", "-c", "source activate rnaseq_v0 && bash /home/biodocker/bin/rna_seq.bash"]
