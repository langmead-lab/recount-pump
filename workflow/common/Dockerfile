FROM continuumio/miniconda:4.5.12

RUN apt-get update -y && apt-get install -y gcc g++ libz-dev make

# bwtool is not in bioconda, unfortunately
RUN git clone https://github.com/CRG-Barcelona/libbeato.git && cd libbeato && git checkout 0c30432af9c7e1e09ba065ad3b2bc042baa54dc2 && \
    ./configure && make && make install && cd .. && \
    git clone https://github.com/CRG-Barcelona/bwtool.git && cd bwtool && git checkout 139e3adf6db87ae7442024c7e4352dc9844a9256 && \
    ./configure && make && make install && cd .. && \
    rm -rf libbeato bwtool

# install conda environment
COPY env.yml /env-base.yml
RUN chmod a+r /env-base.yml

# don't need these anymore
RUN apt-get remove --purge -y gcc g++ make

# for stampede2
RUN mkdir -p /scratch /work /home1
RUN chmod a+rwx /scratch /work /home1

# For pgrep, needed by aspera installation
RUN apt-get update -y && apt-get install -y procps
RUN useradd -ms /bin/bash recount && chpasswd recount:recount

# Add base conda packages then delete some extraneous files
RUN conda env create -q -f /env-base.yml && \
    conda clean -y -p -t && \
    rm -f /opt/conda/pkgs/mkl-*/lib/libmkl*avx512*.so* && \
    rm -f /opt/conda/envs/recount/lib/libmkl*avx512*.so* && \
    rm -f /opt/conda/envs/recount/lib/libQt* && \
    rm -f /opt/conda/envs/recount/bin/ldc2 && \
    rm -f /opt/conda/envs/recount/bin/qmake && \
    rm -rf /opt/conda/envs/recount/man/* \
           /opt/conda/envs/recount/include/* \
           /opt/conda/envs/recount/annotation/* \
           /opt/conda/envs/recount/translations/*

# Download but do not install (since root cannot)
RUN curl -LO https://download.asperasoft.com/download/sw/connect/3.7.4/aspera-connect-3.7.4.147727-linux-64.tar.gz && \
    tar zxf aspera-connect-3.7.4.147727-linux-64.tar.gz && \
    rm -f aspera-connect-3.7.4.147727-linux-64.tar.gz && \
    mv /aspera-connect-3.7.4.147727-linux-64.sh /install-aspera.sh

RUN echo '#!/bin/bash\n\
if [[ ! -x ~/.aspera/connect/bin/ascp ]] ; then\n\
    /install-aspera.sh\n\
fi\n' > /startup.sh

RUN chmod a+x /startup.sh
RUN chmod a+x /install-aspera.sh

USER recount
WORKDIR /home/recount
