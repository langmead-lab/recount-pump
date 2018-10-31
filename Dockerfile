FROM python:3.4-stretch
WORKDIR /code

RUN printf "deb http://httpredir.debian.org/debian jessie-backports main non-free\ndeb-src http://httpredir.debian.org/debian jessie-backports main non-free" > /etc/apt/sources.list.d/backports.list

RUN apt-get update -y && \
    apt-get install -y libarchive-dev squashfs-tools graphviz singularity-container

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
