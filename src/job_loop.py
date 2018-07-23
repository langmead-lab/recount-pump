#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""job_loop

Usage:
  job_loop prepare-image [options] <image> <image-wrapper>
                                   <remote-image> <remote-image-wrapper>
  job_loop run [options] <queue-name>

Options:
  --max-fail <int>            Maximum # poll failures before quitting [default: 10].
  --poll-seconds <int>        Seconds to wait before re-polling after failed poll [default: 5].
  --queue-ini <ini>           Queue ini file [default: ~/.recount/queue.ini].
  --queue-section <section>   ini file section for database [default: queue].
  --log-ini <ini>             ini file for log aggregator [default: ~/.recount/log.ini].
  --log-section <section>     ini file section for log aggregator [default: log].
  --log-level <level>         set level for log aggregation; could be CRITICAL,
                              ERROR, WARNING, INFO, DEBUG [default: INFO].
  -a, --aggregate             enable log aggregation.
  -h, --help                  Show this screen.
  --version                   Show version.
"""

"""
Runs on the cluster.  Repeatedly checks the queue for another job.  If it gets
one, fires off a nextflow job to run it.
"""

import time
import os
import log
from docopt import docopt
from queueing.service import queueing_service_from_config


def do_job(body):
    toks = body.split(' ')
    if 4 != len(toks):
        raise ValueError('Could not parse job string: "%s"' % body)
    job_id, job_name, input_string, analysis_string = body.split()
    log.info(__name__, 'Handling job: {id=%d, name="%s", input="%s", analysis="%s"}' %
             (int(job_id), job_name, input_string, analysis_string), 'job_loop.py')
    return True


def job_loop(q_ini, q_section, q_name, max_fails=10, sleep_seconds=10):
    attempt, success, fail = 0, 0, 0
    qserv = queueing_service_from_config(q_ini, q_section)
    if not qserv.queue_exists(q_name):
        raise ValueError('No such queue: "%s"' % q_name)
    log.info(__name__, 'Entering job loop, queue "%s"' % q_name, 'job_loop.py')
    while True:
        attempt += 1
        body = qserv.get(q_name)
        if body is not None:
            success += 1
            log.info(__name__, 'Job start', 'job_loop.py')
            if do_job(body):
                log.info(__name__, 'Job success, acknowledging', 'job_loop.py')
                qserv.ack()
                log.info(__name__, 'Acknowledged', 'job_loop.py')
            else:
                log.info(__name__, 'Job failure', 'job_loop.py')
        else:
            fail += 1
            if fail >= max_fails:
                log.info(__name__, 'Job loop end after %d poll failures' % fail, 'job_loop.py')
                break
            time.sleep(sleep_seconds)


def prepare_image(image, remote_image):
    if not os.path.exists(image):
        # retrieve image at remote place, and copy to local
        log.info(__name__, 'Installed image from "%s" to "%s"' % (remote_image, image), 'job_loop.py')
        pass


if __name__ == '__main__':
    args = docopt(__doc__)
    agg_ini = os.path.expanduser(args['--log-ini']) if args['--aggregate'] else None
    log.init_logger(__name__, aggregation_ini=agg_ini,
                     aggregation_section=args['--log-section'],
                     agg_level=args['--log-level'])
    try:
        q_ini = os.path.expanduser(args['--queue-ini'])
        if args['prepare-image']:
            print(prepare_image(args['<image>'], args['<remote-image>']))
        if args['run']:
            print(job_loop(q_ini,
                           args['--queue-section'],
                           args['<queue-name>'],
                           max_fails=int(args['--max-fail']),
                           sleep_seconds=int(args['--poll-seconds'])))
    except Exception:
        log.error(__name__, 'Uncaught exception:', 'job_loop.py')
        raise
