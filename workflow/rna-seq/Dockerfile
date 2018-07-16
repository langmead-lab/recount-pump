FROM continuumio/miniconda:4.5.4

# install conda environment
COPY env.yml /tmp/env.yml
RUN conda env create -f /tmp/env.yml

# install globus-cli using pipe
RUN bash -c "source activate rnaseq && pip install globus-cli"

WORKDIR /data

# install nextflow script
COPY rna_seq.nf /tmp/rna_seq.nf
COPY rna_seq.bash /tmp/rna_seq.bash

CMD ["bash", "-c", "source activate rnaseq && bash /tmp/rna_seq.bash"]
