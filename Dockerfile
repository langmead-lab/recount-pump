FROM python:3.4-jessie
WORKDIR /code

RUN apt-get update && apt-get install -y libarchive-dev squashfs-tools graphviz

RUN wget -q https://github.com/singularityware/singularity/releases/download/2.5.2/singularity-2.5.2.tar.gz && \
    tar xf singularity-2.5.2.tar.gz && \
    cd singularity-2.5.2 && \
    ./configure --prefix=/usr/local >/dev/null && \
    make >/dev/null && \
    make install >/dev/null && \
    cd .. && \
    rm -rf singularity-2.5.2 singularity-2.5.2.tar.gz

RUN pip install --upgrade pip

ADD requirements.txt /code
RUN pip install --quiet -r requirements.txt

RUN mkdir -p /root/.recount /root/.aws

ADD wait-for-it.sh /code
ADD unit_test.sh /code
ADD e2e_test.sh /code
ADD test_entry.sh /code
ADD test /code/test
ADD src /code/src
