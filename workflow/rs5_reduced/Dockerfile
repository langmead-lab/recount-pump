FROM recount-pump:1.1.2sreduced_base

USER root

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    chmod a+x ./aws/install && \
    ./aws/install

WORKDIR /

# install Snakefile
COPY Snakefile /Snakefile
RUN chmod a+r /Snakefile

# install generic workflow wrapper script
COPY workflow.bash /workflow.bash
RUN chmod a+rx /workflow.bash

# install download.sh
COPY download.sh /download.sh
RUN chmod a+r /download.sh

COPY entrypoint.sh /entrypoint.sh
RUN chmod a+rx /entrypoint.sh

USER recount
WORKDIR /home/recount/

ENTRYPOINT ["bash", "-c", "/entrypoint.sh"]
