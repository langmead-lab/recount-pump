FROM quay.io/benlangmead/recount-base:latest

USER root

# install remaining conda packages
COPY more_conda.txt /tmp/more_conda.txt
RUN for i in `cat /tmp/more_conda.txt` ; do conda install -q -y -c conda-forge -c bioconda -c defaults -n recount $i ; done && \ 
    conda clean -y -p -t && \
    rm -rf /opt/conda/envs/recount/man/* \
           /opt/conda/envs/recount/include/* \
           /opt/conda/envs/recount/annotation/* \
           /opt/conda/envs/recount/translations/*

# install python dependencies for mover.py
#

# install samtools
RUN apt-get install -y autoconf gcc make
ENV SM_VER=1.9
RUN curl -OL https://github.com/samtools/samtools/releases/download/${SM_VER}/samtools-${SM_VER}.tar.bz2 && \
    bzip2 -dc samtools-${SM_VER}.tar.bz2 | tar xvf - && \
    rm -f samtools-${SM_VER}.tar.bz2 && \
    cd samtools-${SM_VER} && \
    autoheader && \
    autoconf && \
    ./configure --disable-bz2 --disable-lzma --disable-libcurl --without-libdeflate --without-curses && \
    make && \
    make install

# install bamcount static binary
ENV BC_VER=0.4.0
RUN mkdir -p /bamcount && \
    cd /bamcount && \
    wget -q https://github.com/ChristopherWilks/bamcount/releases/download/${BC_VER}/bamcount_static -O bamcount && \
    chmod a+x bamcount

# install Snakefile
COPY Snakefile /Snakefile
RUN chmod a+r /Snakefile

# install generic workflow wrapper script
COPY workflow.bash /workflow.bash
RUN chmod a+rx /workflow.bash

# install download.sh
COPY download.sh /download.sh
RUN chmod a+r /download.sh

USER recount
WORKDIR /home/recount/

# See src/run.py where this command is repeated
CMD ["bash", "-c", "source activate recount && /startup.sh && /workflow.bash"]
