FROM continuumio/miniconda:4.5.4

# install conda environment
COPY env.yml /tmp/env.yml
RUN conda env create -q -f /tmp/env.yml
RUN chmod -R a+rwx /opt/conda/envs/*/share/nextflow

# install nextflow script
COPY workflow.nf /workflow.nf
COPY workflow.bash /workflow.bash

CMD ["bash", "-c", "source activate recount && bash /workflow.bash"]
