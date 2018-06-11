FROM python:3.4-jessie
ADD src /code/src
ADD requirements.txt /code
WORKDIR /code
RUN pip install -r requirements.txt
CMD nosetests src/*.py src/*/*.py
