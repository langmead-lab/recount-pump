#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""job_loop

Usage:
  job_loop prepare [options] <project-id>
  job_loop run [options] <project-id>

Options:
  --cluster-ini <ini>          Cluster ini file [default: ~/.recount/cluster.ini].
  --cluster-section <section>  ini file section for cluster [default: cluster].
  --db-ini <ini>               Database ini file [default: ~/.recount/db.ini].
  --db-section <section>       ini file section for database [default: client].
  --profile=<profile>          AWS credentials profile section.
  --endpoint-url=<url>         Endpoint URL for S3 API.  If not set, uses AWS default.
  --queue-ini <ini>            Queue ini file [default: ~/.recount/queue.ini].
  --queue-section <section>    ini file section for database [default: queue].
  --log-ini <ini>              ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>          set level for log aggregation; could be CRITICAL,
                               ERROR, WARNING, INFO, DEBUG [default: INFO].
  --max-fail <int>             Maximum # poll failures before quitting [default: 10].
  --poll-seconds <int>         Seconds to wait before re-polling after failed poll [default: 5].
  -a, --aggregate              enable log aggregation.
  -h, --help                   Show this screen.
  --version                    Show version.
"""

"""
Runs on the cluster.  Repeatedly checks the queue for another job.  If it gets
one, fires off a nextflow job to run it.

Philosophically, seems like we'd like to avoid these being overly
reliant on the DB being up throughout the computation.

Cluster ini file might look like this:

# === ~/.recount/log.ini ===
# [cluster]
# name = marcc
# analysis_dir = /scratch/groups/blangme2/recount_analysis
# scratch_dir = /scratch/groups/blangme2/recount_scratch
#  
"""

import time
import os
import log
import sys
import tempfile
import shutil
import pytest
from docopt import docopt
from queueing.service import queueing_service_from_config
from toolbox import session_maker_from_config
from analysis import Analysis
from pump import Project, add_project_ex
from mover import Mover
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser
    sys.exc_clear()


def parse_job(body):
    try:
        body = body.encode()
    except AttributeError:
        pass
    toks = body.split(b' ')
    if 4 != len(toks):
        raise ValueError('Could not parse job string: "%s"' % body)
    job_id, job_name, input_string, analysis_string = toks
    return int(job_id), job_name, input_string, analysis_string


def do_job(body):
    job_id, job_name, input_string, analysis_string = parse_job(body)
    log.info(__name__, 'Handling job: {id=%d, name="%s", input="%s", analysis="%s"}' %
             (int(job_id), job_name, input_string, analysis_string), 'job_loop.py')
    return True


def ready_for_analysis(analysis, analysis_dir):
    url = analysis.image_url
    image_bn = url.split('/')[-1]
    log.info(__name__, 'Check image file "%s" exists in analysis '
             'dir "%s"' % (image_bn, analysis_dir), 'job_loop.py')
    image_fn = os.path.join(analysis_dir, image_bn)
    return os.path.exists(image_fn)


def download_image(url, cluster_name, analysis_dir, aws_profile=None, s3_endpoint_url=None):
    image_bn = url.split('/')[-1]
    log.info(__name__, 'Check image "%s" exists in cluster "%s" analysis '
             'dir "%s"' % (image_bn, cluster_name, analysis_dir),
             'job_loop.py')
    image_fn = os.path.join(analysis_dir, image_bn)
    mover = Mover(profile=aws_profile, endpoint_url=s3_endpoint_url,
                  enable_web=True, enable_s3=aws_profile is not None)
    mover.get(url, image_fn)


def prepare(project_id, cluster_name, analysis_dir, session,
            aws_profile=None, s3_endpoint_url=None, get_image=False):
    proj = session.query(Project).get(project_id)
    analysis = session.query(Analysis).get(proj.analysis_id)
    if get_image and not ready_for_analysis(analysis, analysis_dir):
        download_image(analysis.image_url, cluster_name, analysis_dir, aws_profile, s3_endpoint_url)
    return ready_for_analysis(analysis, analysis_dir)


def job_loop(project_id, q_ini, q_section, cluster_name, analysis_dir,
             session, max_fails=10, sleep_seconds=10):
    prepare(project_id, cluster_name, analysis_dir, session)
    attempt, success, fail = 0, 0, 0
    qserv = queueing_service_from_config(q_ini, q_section)
    q_name = 'stage_%d' % project_id
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


def read_cluster_config(cluster_fn, section):
    cfg = RawConfigParser()
    cfg.read(cluster_fn)
    if section not in cfg.sections():
        raise RuntimeError('No [%s] section in log ini file "%s"' % (section, cluster_fn))
    return cfg.get(section, 'name'), cfg.get(section, 'analysis_dir')


def test_cluster_config():
    tmpdir = tempfile.mkdtemp()
    config = """[cluster]
name = stampede2
analysis_dir = /path/i/made/up
"""
    test_fn = os.path.join(tmpdir, '.tmp.init')
    with open(test_fn, 'w') as fh:
        fh.write(config)
    name, analysis_dir = read_cluster_config(test_fn, 'cluster')
    assert 'stampede2' == name
    assert '/path/i/made/up' == analysis_dir
    shutil.rmtree(tmpdir)


def test_download_image():
    srcdir, dstdir = tempfile.mkdtemp(), tempfile.mkdtemp()
    base_fn = 'test_download_image.simg'
    test_fn = os.path.join(srcdir, base_fn)
    with open(test_fn, 'w') as fh:
        fh.write('dummy image')
    download_image(test_fn, 'marcc', dstdir)
    assert os.path.exists(os.path.join(dstdir, base_fn))
    shutil.rmtree(srcdir)
    shutil.rmtree(dstdir)


def test_integration(db_integration):
    if not db_integration:
        pytest.skip('db integration testing disabled')


def test_with_db(session):
    srcdir, dstdir = tempfile.mkdtemp(), tempfile.mkdtemp()
    project_name = 'test-project'
    analysis_name = 'test-analysis'
    base_fn = 'test_image.simg'
    image_url = os.path.join(srcdir, base_fn)
    with open(image_url, 'w') as fh:
        fh.write('dummy image')
    input_set_name = 'test-input-set'
    input_set_csv = '\n'.join(['NA,NA,ftp://genomi.cs/1_1.fastq.gz,ftp://genomi.cs/1_2.fastq.gz,NA,NA,NA,NA,wget',
                               'NA,NA,ftp://genomi.cs/2_1.fastq.gz,ftp://genomi.cs/2_2.fastq.gz,NA,NA,NA,NA,wget'])
    csv_fn = os.path.join(srcdir, 'project.csv')
    with open(csv_fn, 'w') as ofh:
        ofh.write(input_set_csv)
    project_id, _, _, _ = add_project_ex(
        project_name, analysis_name, image_url,
        input_set_name, csv_fn, session)
    prepare(project_id, 'test', dstdir, session, get_image=True)
    assert os.path.exists(os.path.join(dstdir, base_fn))


def test_parse_job():
    a, b, c, d = parse_job('123 job_name input_string analysis_string')
    assert 123 == a
    assert b'job_name' == b
    assert b'input_string' == c
    assert b'analysis_string' == d
    a, b, c, d = parse_job(b'123 job_name input_string analysis_string')
    assert 123 == a
    assert b'job_name' == b
    assert b'input_string' == c
    assert b'analysis_string' == d


if __name__ == '__main__':
    args = docopt(__doc__)
    agg_ini = os.path.expanduser(args['--log-ini']) if args['--aggregate'] else None
    log.init_logger(__name__, log_ini=agg_ini, agg_level=args['--log-level'])
    log.init_logger('sqlalchemy', log_ini=agg_ini, agg_level=args['--log-level'],
                    sender='sqlalchemy')
    try:
        db_ini = os.path.expanduser(args['--db-ini'])
        cluster_ini = os.path.expanduser(args['--cluster-ini'])
        cluster_name, analysis_dir = \
            read_cluster_config(cluster_ini, args['--cluster-section'])
        q_ini = os.path.expanduser(args['--queue-ini'])
        if args['prepare']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(prepare(int(args['<project-id>']),
                          cluster_name,
                          analysis_dir,
                          Session(),
                          aws_profile=args['--profile'],
                          s3_endpoint_url=args['--endpoint-url'],
                          get_image=True))
        if args['run']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(job_loop(int(args['<project-id>']), q_ini,
                           args['--queue-section'],
                           cluster_name, analysis_dir,
                           Session(),
                           max_fails=int(args['--max-fail']),
                           sleep_seconds=int(args['--poll-seconds'])))
    except Exception:
        log.error(__name__, 'Uncaught exception:', 'job_loop.py')
        raise
