FROM continuumio/miniconda:4.5.4

# install conda environment
COPY env.yml /tmp/env.yml
RUN conda env create -f /tmp/env.yml

WORKDIR /data

# install nextflow script
COPY rna_seq_lite.nf /home/biodocker/bin/
COPY rna_seq_lite.bash /home/biodocker/bin/

CMD ["bash", "-c", "source activate rnaseq_lite && bash /home/biodocker/bin/rna_seq_lite.bash"]
