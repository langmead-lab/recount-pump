#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""
conftest.py

pytest fixtures for the project
"""

import os
import pytest
from sqlalchemy import create_engine
from base import Base
from sqlalchemy.orm import Session


def pytest_generate_tests(metafunc):
    varname = 'RECOUNT_TEST_DB'
    db_integration = varname in os.environ
    if 'db_integration' in metafunc.fixturenames:
        metafunc.parametrize('db_integration', [db_integration], indirect=True)
    if 'engine' in metafunc.fixturenames:
        dbs = ['sqlite:///:memory:']
        if db_integration:
            dbs += os.environ[varname].split(',')
        metafunc.parametrize("engine", dbs, indirect=True)


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
