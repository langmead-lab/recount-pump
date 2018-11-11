FROM quay.io/benlangmead/recount-base:latest

# install conda environment
COPY more_conda.txt /tmp/more_conda.txt
RUN for i in `cat /tmp/more_conda.txt` ; do conda install -q -y -c bioconda -c conda-forge -c defaults -n recount $i ; done 
RUN conda clean -y -p -t

# install Snakefile
COPY Snakefile /Snakefile

# install generic workflow wrapper script
COPY workflow.bash /workflow.bash

CMD ["bash", "-c", "source activate recount && bash /workflow.bash"]
