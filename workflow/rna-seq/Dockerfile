FROM continuumio/miniconda:4.5.4

# install conda environment
COPY env.yml /tmp/env.yml
RUN conda env create -q -f /tmp/env.yml

# install globus-cli using pipe
RUN bash -c "source activate rnaseq && pip install --quiet globus-cli"

WORKDIR /data

# install nextflow script
RUN mkdir /recount-bin
COPY rna_seq.nf /recount-bin/rna_seq.nf
COPY rna_seq.bash /recount-bin/rna_seq.bash

CMD ["bash", "-c", "source activate rnaseq && bash /recount-bin/rna_seq.bash"]
