#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""
conftest.py

pytest fixtures for the project
"""

import os
import pytest
import boto3
import time
from sqlalchemy import create_engine
from base import Base
from mover import S3Mover
from sqlalchemy.orm import Session


def check_test_db(metafunc):
    varname = 'RECOUNT_TEST_DB'
    db_integration = varname in os.environ
    if 'db_integration' in metafunc.fixturenames:
        metafunc.parametrize('db_integration', [db_integration], indirect=True)
    if 'engine' in metafunc.fixturenames:
        dbs = ['sqlite:///:memory:']
        if db_integration:
            dbs += os.environ[varname].split(',')
        metafunc.parametrize("engine", dbs, indirect=True)


def check_test_s3(metafunc):
    s3_var = 'RECOUNT_TEST_S3'
    s3_enabled = s3_var in os.environ
    if 's3_enabled' in metafunc.fixturenames:
        metafunc.parametrize('s3_enabled', [s3_enabled], indirect=True)


def check_test_q(metafunc):
    q_var = 'RECOUNT_TEST_Q'
    q_enabled = q_var in os.environ
    if 'q_enabled' in metafunc.fixturenames:
        metafunc.parametrize('q_enabled', [q_enabled], indirect=True)


def pytest_generate_tests(metafunc):
    check_test_db(metafunc)
    check_test_s3(metafunc)
    check_test_q(metafunc)


@pytest.fixture(scope='session')
def engine(request):
    return create_engine(request.param)


@pytest.fixture(scope='session')
def db_integration(request):
    return request.param


@pytest.yield_fixture(scope='session')
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.yield_fixture
def session(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()
    my_session = Session(bind=connection)

    yield my_session

    my_session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope='session')
def s3_enabled(request):
    return request.param


@pytest.yield_fixture(scope='session')
def s3_service(s3_enabled):
    if s3_enabled:
        service = S3Mover(endpoint_url=os.environ['RECOUNT_TEST_S3'])
        yield service
        service.close()
    else:
        yield None


@pytest.fixture(scope='session')
def q_enabled(request):
    return request.param


@pytest.yield_fixture(scope='session')
def q_client_and_resource(q_enabled):
    if q_enabled:
        boto3_session = boto3.session.Session()
        client = boto3_session.client('sqs',
                                      endpoint_url=os.environ['RECOUNT_TEST_Q'],
                                      region_name='us-east-1')
        resource = boto3.resource('sqs',
                                  endpoint_url=os.environ['RECOUNT_TEST_Q'],
                                  region_name='us-east-1')
        yield client, resource
        for queue in client.list_queues()['QueueUrls']:
            client.delete_queue(QueueUrl=queue)
        time.sleep(1)
        assert 'QueueUrls' not in client.list_queues()
    else:
        yield None
