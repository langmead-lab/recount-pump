FROM bioconductor/release_core2

RUN apt-get update -y && apt-get install -y wget

RUN pip install synapseclient awscli

# copied from https://hub.docker.com/r/continuumio/miniconda/~/dockerfile/
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda2-4.5.11-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

# install conda environment
COPY env.yml /env-base.yml
RUN . /opt/conda/etc/profile.d/conda.sh && conda env create -q -f /env-base.yml && \
    conda clean -y -p -t
