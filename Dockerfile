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

RUN echo '[queue]\n\
endpoint=http://elasticmq:9324\n\
region=us-east-1\n' >> /root/.recount/queue.ini

RUN echo '[client]\n\
url=postgres://recount:recount-postgres@db:5432/recount-test\n\
password=recount-postgres\n\
host=db\n\
port=5432\n\
user=recount\n' >> /root/.recount/db.ini

RUN echo '[cluster]\n\
name = test-cluster\n\
system = singularity\n\
ref_base = /temporary/ref\n\
temp_base = /temporary/temp\n\
output_base = /output\n\
temp_base = /temporary/analysis\n\
ref_mount = /container-mounts/recount/ref\n\
temp_mount = /container-mounts/recount/temp\n\
input_mount = /container-mounts/recount/input\n\
output_mount = /output\n' >> /root/.recount/cluster.ini

RUN echo '[default]\n\
region = us-east-1\n\
output = text\n\
s3 =\n\
    signature_version = s3v4\n' >> /root/.aws/config

RUN echo '[default]\n\
aws_access_key_id = minio\n\
aws_secret_access_key = minio123\n' >> /root/.aws/credentials

ENV S3_ENDPOINT http://s3:9000

ADD wait-for-it.sh /code
ADD unit_test.sh /code
ADD e2e_test.sh /code
ADD test_entry.sh /code
ADD test /code/test
ADD src /code/src
