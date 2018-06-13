#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""job_loop

Usage:
  job_loop add-input [options] <>
  job_loop test [options]

Options:
  --max-fail <int>         maximum # poll failures before quitting [default: 5].
  --poll-seconds <int>     seconds to wait before polling again when poll fails [default: 5].
  --log-ini <ini>          ini file for log aggregator [default: ~/.recount/log.ini].
  --log-section <section>  ini file section for log aggregator [default: log].
  --log-level <level>      set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  -a, --aggregate          enable log aggregation.
  -h, --help               Show this screen.
  --version                Show version.
"""

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


def job_loop(max_fails=10, sleep_seconds=10):
    attempt, success, fail = 0, 0, 0
    while True:
        attempt += 1
        if poll_queue():
            success += 1
            log.info(__name__, 'Job start', 'job_loop.py')
            do_job()
            log.info(__name__, 'Job end', 'job_loop.py')
        else:
            fail += 1
            if fail >= max_fails:
                log.info('Job loop end after %d poll failures' % fail)
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
            print(job_loop(max_fails=args['--max-fail'],
                           sleep_seconds=args['--poll-seconds']))
        elif args['test']:
            del sys.argv[1:]
            log.info(__name__, 'running tests', 'job_loop.py')
            unittest.main(exit=False)
    except Exception:
        log.error(__name__, 'Uncaught exception:', 'job_loop.py')
        raise
