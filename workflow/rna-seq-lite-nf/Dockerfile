FROM continuumio/miniconda:4.5.4

# install conda environment
COPY env.yml /tmp/env.yml
RUN conda env create -q -f /tmp/env.yml

WORKDIR /data

# install nextflow script
RUN mkdir /recount-bin
COPY workflow.nf /recount-bin/workflow.nf
COPY workflow.bash /recount-bin/workflow.bash

CMD ["bash", "-c", "source activate recount && bash /recount-bin/workflow.bash"]
