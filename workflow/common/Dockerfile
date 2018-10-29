FROM continuumio/miniconda:4.5.11

RUN apt-get update -y && apt-get install -y gcc g++ libz-dev make

# bwtool is not in bioconda, unfortunately
RUN git clone https://github.com/CRG-Barcelona/libbeato.git && cd libbeato && git checkout 0c30432af9c7e1e09ba065ad3b2bc042baa54dc2
RUN cd libbeato/ && ./configure && make && make install
RUN git clone https://github.com/CRG-Barcelona/bwtool.git && cd bwtool && git checkout 139e3adf6db87ae7442024c7e4352dc9844a9256
RUN cd bwtool/ && ./configure && make && make install

# install conda environment
COPY env.yml /tmp/env-base.yml
RUN conda env create -q -f /tmp/env-base.yml && \
    conda clean -y -p -t && \
    rm -f /opt/conda/pkgs/qt-*/lib/libQt*WebEngineCore*.so.* && \
    rm -f /opt/./conda/envs/recount/lib/libQt*WebEngineCore.so.* && \
    rm -f /opt/conda/pkgs/mkl-*/lib/libmkl*avx512*.so* && \
    rm -f /opt/conda/envs/recount/lib/libmkl*avx512*.so*

# don't need these anymore
RUN apt-get remove --purge -y gcc g++ make

# for stampede2
RUN mkdir -p /scratch /work /home1
