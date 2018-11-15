FROM quay.io/benlangmead/recount-base:latest

# install conda environment
COPY more_conda.txt /tmp/more_conda.txt
RUN for i in `cat /tmp/more_conda.txt` ; do conda install -q -y -c bioconda -c conda-forge -c defaults -n recount $i ; done && \ 
    conda clean -y -p -t && \
    rm -rf /opt/conda/envs/recount/man/* \
           /opt/conda/envs/recount/include/* \
           /opt/conda/envs/recount/annotation/* \
           /opt/conda/envs/recount/translations/*

# install Snakefile
COPY Snakefile /Snakefile

# install generic workflow wrapper script
COPY workflow.bash /workflow.bash

RUN wget -O /depth2bedgraph.awk \
        https://gist.githubusercontent.com/nathanhaigh/c8322002a42e40c479d3d766aab32547/raw/899df12b5c76f1f9171768fe5dc1feaa5423fe0a/depth2bedgraph.awk && \
    chmod a+r /depth2bedgraph.awk

CMD ["bash", "-c", "source activate recount && bash /workflow.bash"]
