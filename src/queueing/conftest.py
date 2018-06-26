#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""
conftest.py

pytest fixtures for the project
"""

import os
import pytest
import queueing.rmq


def pytest_generate_tests(metafunc):
    q_var = 'RECOUNT_TEST_Q'
    q_enabled = q_var in os.environ
    if 'q_enabled' in metafunc.fixturenames:
        metafunc.parametrize('q_enabled', [q_enabled], indirect=True)


@pytest.fixture(scope='session')
def q_enabled(request):
    return request.param


@pytest.yield_fixture(scope='session')
def q_service(q_enabled):
    if q_enabled:
        qurl = os.environ['RECOUNT_TEST_Q']
        host, port = 'localhost', 5672
        if ':' in qurl:
            assert qurl.count(':') == 1
            host, port = qurl.split(':')
            port = int(port)
        else:
            host = qurl
        service = queueing.rmq.RmqService(host=host, port=port)
        if service.queue_exists('TestRmq'):
            service.queue_delete('TestRmq')

        yield service

        if service.queue_exists('TestRmq'):
            service.queue_delete('TestRmq')
        service.close()
    else:
        yield None
