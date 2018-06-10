#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""
Runs on the cluster.  Repeatedly checks the queue for another job.  If it gets
one, fires off a nextflow job to run it.
"""

"""
while True:
    if poll succeeds:
        log that job began
        run the job
        log that job ended
    else:
        increment failed poll count
        if greater than failed poll allowance:
            quit
        sleep
"""

import time
import os
import sys
import log
import unittest
from docopt import docopt


def poll_queue():
    pass


def do_job():
    pass


def job_loop(logger, max_fails=10, sleep_seconds=10):
    attempt, success, fail = 0, 0, 0
    while True:
        attempt += 1
        if poll_queue():
            success += 1
            logger.info('Job began')
            do_job()
            logger.info('Job ended')
        else:
            fail += 1
            if fail > max_fails:
                logger.info('Job loop ending after %d polling failures' % max_fails)
                break
            time.sleep(sleep_seconds)


if __name__ == '__main__':
    args = docopt(__doc__)
    agg_ini = os.path.expanduser(args['--log-ini']) if args['--aggregate'] else None
    log.init_logger(__name__, aggregation_ini=agg_ini,
                     aggregation_section=args['--log-section'],
                     agg_level=args['--log-level'])
    try:
        if args['run']:
            print(job_loop())
        elif args['test']:
            del sys.argv[1:]
            log.info(__name__, 'running tests', 'job_loop.py')
            unittest.main(exit=False)
    except Exception:
        log.error(__name__, 'Uncaught exception:', 'job_loop.py')
        raise
