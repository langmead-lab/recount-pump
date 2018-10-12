FROM continuumio/miniconda:4.5.4

# install conda environment
COPY env.yml /tmp/env-base.yml
RUN conda env create -q -f /tmp/env-base.yml && \
    conda clean -y -p -t && \
    rm -f /opt/conda/pkgs/qt-*/lib/libQt*WebEngineCore*.so.* && \
    rm -f /opt/./conda/envs/recount/lib/libQt*WebEngineCore.so.* && \
    rm -f /opt/conda/pkgs/mkl-*/lib/libmkl*avx512*.so* && \
    rm -f /opt/conda/envs/recount/lib/libmkl*avx512*.so*

# install generic workflow wrapper script
COPY workflow.bash /workflow.bash

# for stampede2
RUN mkdir -p /scratch /work /home1
