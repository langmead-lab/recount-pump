FROM python:3.4-jessie
ADD src /code/src
ADD requirements.txt /code
WORKDIR /code
RUN apt-get update
RUN apt-get install -y emacs-nox
RUN pip install -r requirements.txt
