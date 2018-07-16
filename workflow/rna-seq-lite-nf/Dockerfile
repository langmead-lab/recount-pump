FROM continuumio/miniconda:4.5.4

# install conda environment
COPY env.yml /tmp/env.yml
RUN conda env create -q -f /tmp/env.yml

WORKDIR /data

# install nextflow script
RUN mkdir /recount-bin
COPY rna_seq_lite.nf /recount-bin/rna_seq_lite.nf
COPY rna_seq_lite.bash /recount-bin/rna_seq_lite.bash

CMD ["bash", "-c", "source activate rnaseq_lite && bash /recount-bin/rna_seq_lite.bash"]
