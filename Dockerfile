FROM python:3.4-jessie
WORKDIR /code

RUN apt-get update
RUN apt-get install -y emacs-nox
RUN pip install -r requirements.txt

ADD src /code/src
ADD wait-for-it.sh /code
ADD requirements.txt /code
