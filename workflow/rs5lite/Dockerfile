FROM quay.io/benlangmead/recount-base:latest

USER root

# install remaining conda packages
COPY more_conda.txt /tmp/more_conda.txt
RUN for i in `cat /tmp/more_conda.txt` ; do conda install -q -y -c bioconda -c conda-forge -c defaults -n recount $i ; done && \ 
    conda clean -y -p -t && \
    rm -rf /opt/conda/envs/recount/man/* \
           /opt/conda/envs/recount/include/* \
           /opt/conda/envs/recount/annotation/* \
           /opt/conda/envs/recount/translations/*

# install bamcount
RUN apt-get install -y unzip
ENV BC_VER=0.2.4
RUN mkdir -p /bamcount && \
    cd /bamcount && \
    wget -q https://github.com/BenLangmead/bamcount/releases/download/${BC_VER}/bamcount-${BC_VER}.zip && \
    unzip bamcount-${BC_VER}.zip && \
    rm -f bamcount-${BC_VER}.zip

# install Snakefile
COPY Snakefile /Snakefile
RUN chmod a+r /Snakefile

# install generic workflow wrapper script
COPY workflow.bash /workflow.bash
RUN chmod a+rx /workflow.bash

USER recount
WORKDIR /home/recount/

# See src/run.py where this command is repeated
CMD ["bash", "-c", "source activate recount && /startup.sh && /workflow.bash"]
