FROM continuumio/miniconda:4.5.4

# install conda environment
COPY env.yml /tmp/env-base.yml
RUN conda env create -q -f /tmp/env-base.yml && conda clean -y -p -t

# install generic workflow wrapper script
COPY workflow.bash /workflow.bash

# for stampede2
RUN mkdir -p /scratch /work /home1
