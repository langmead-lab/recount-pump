#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""cluster

Usage:
  cluster prepare [options] <project-id>
  cluster run [options] <project-id>

Options:
  --cluster-ini <ini>          Cluster ini file [default: ~/.recount/cluster.ini].
  --destination-ini <ini>      Destination ini file [default: ~/.recount/destination.ini].
  --db-ini <ini>               Database ini file [default: ~/.recount/db.ini].
  --db-section <section>       ini file section for database [default: client].
  --queue-ini <ini>            Queue ini file [default: ~/.recount/queue.ini].
  --queue-section <section>    ini file section for database [default: queue].
  --log-ini <ini>              ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>          set level for log aggregation; could be CRITICAL,
                               ERROR, WARNING, INFO, DEBUG [default: INFO].
  --max-fail <int>             Maximum # poll failures before quitting [default: 10].
  --poll-seconds <int>         Seconds to wait before re-polling after failed poll [default: 5].
  --sysmon-interval <int>      Seconds between sysmon updated; 0 disables [default: 5]
  --s3-ini=<path>              Path to S3 ini file [default: ~/.recount/s3.ini].
  --s3-section=<string>        Name pf section in S3 ini [default: s3].
  --globus-ini=<path>          Path to globus ini file [default: ~/.recount/globus.ini].
  --globus-section=<string>    Name pf section in globus ini file describing the
                               application [default: recount-app].
  --curl=<curl>                curl executable [default: curl].
  -h, --help                   Show this screen.
  --version                    Show version.
"""

import time
import re
import os
import log
import sys
import tempfile
import shutil
import pytest
import run
import subprocess
import boto3
import multiprocessing
import socket
import json
import threading
import signal
import traceback
from resmon import SysmonThread
from datetime import datetime
from docopt import docopt
from toolbox import engine_from_config, session_maker_from_config, parse_queue_config
from analysis import Analysis, add_analysis
from input import Input, import_input_set
from pump import Project, TaskAttempt, TaskFailure, TaskSuccess, add_project
from reference import Reference, SourceSet, AnnotationSet, add_reference, add_source_set, \
    add_annotation_set, add_sources_to_set, add_annotations_to_set, add_source, add_annotation
from sqlalchemy import func
from sqlalchemy.orm import Session
from mover import Mover, MoverConfig
if sys.version[:1] == '2':
    from ConfigParser import RawConfigParser
else:
    from configparser import RawConfigParser


class Task(object):

    def __init__(self, body):
        self.proj_id, self.job_name, self.input_string, \
            self.analysis_name, self.reference_name = Project.parse_job_string(body)
        self.input_id, self.srr, self.srp, self.url1, self.url2, self.url3, \
            self.checksum1, self.checksum2, self.checksum3, \
            self.retrieval = Input.parse_job_string(self.input_string)

    def __str__(self):
        return '{proj_id=%d, name="%s", input="%s", analysis="%s", reference="%s"}' %\
               (self.proj_id, self.job_name, self.input_string,
                self.analysis_name, self.reference_name)


log_queue = multiprocessing.Queue()


def log_info(msg):
    if log_queue is None:
        log.info(msg, 'cluster.py')
    else:
        log_queue.put((msg, 'cluster.py'))


def log_info_detailed(node_name, worker_name, msg):
    log_info(' '.join([node_name, worker_name, msg]))


def docker_image_exists(url):
    if url.startswith('docker://'):
        url = url[len('docker://'):]
    cmd = ['docker', 'images', '-q', url]
    return len(subprocess.check_output(cmd)) > 0


def parse_image_url(url, system, cachedir=None):
    """
    Parse an image URL and return information about what type of repo it's
    stored in as well as what form it should take once it has been "pulled"
    to the local machine.
    """
    if cachedir is None:
        # only relevant for singularity
        cachedir = os.environ['SINGULARITY_CACHEDIR']
    typ = 'local'
    image_fn = None
    if url.startswith('docker://'):
        typ = 'docker'
        if system == 'singularity':
            image_name = url.split('/')[-1] + '.simg'
            image_name = image_name.replace(':', '-')
            image_fn = os.path.join(cachedir, image_name)
    elif url.startswith('shub://'):
        if system != 'singularity':
            raise ValueError('Bad image URL for system=singularity: "%s"' % url)
        toks = re.split('[:/]', url[7:])
        image_name = '-'.join(toks) + '.simg'
        image_fn = os.path.join(cachedir, image_name)
        typ = 'shub'
    else:
        image_name = url.split('/')[-1]
        image_fn = os.path.join(cachedir, image_name)
    assert image_fn is not None or system == 'docker'
    return image_fn, typ


def image_exists_locally(url, system, cachedir=None):
    image_fn, typ = parse_image_url(url, system, cachedir=cachedir)
    if image_fn is not None:
        return os.path.exists(image_fn)
    else:
        if os.system('which docker >/dev/null') != 0:
            raise RuntimeError('Image is for docker, but "docker" binary not in PATH')
        return docker_image_exists(url)


def md5(fn):
    image_md5 = subprocess.check_output(['md5sum', fn])
    return image_md5.decode().split()[0]


def do_job(body, cluster_ini, my_attempt, node_name,
           worker_name, session, mover_config=None, destination=None,
           source_prefix=None):
    """
    Given a job-attempt description string, parse the string and execute the
    corresponding job attempt.  The description string itself is composed in
    pump.py.
    """
    name, system, analysis_dir, _, _, _ = read_cluster_config(cluster_ini)
    task = Task(body)
    log_info_detailed(node_name, worker_name, 'got job: ' + str(task))
    tmp_dir = tempfile.mkdtemp()
    tmp_fn = os.path.join(tmp_dir, 'accessions.txt')
    assert not os.path.exists(tmp_fn)
    with open(tmp_fn, 'wt') as fh:
        fh.write(','.join([task.srr, task.srp, task.reference_name]) + '\n')
    assert os.path.exists(tmp_fn)
    analyses = session.query(Analysis).filter(Analysis.name == task.analysis_name).all()
    if 0 == len(analyses):
        raise ValueError('No analysis named "%s"' % task.analysis_name)
    assert 1 == len(analyses)
    image_url, config = analyses[0].image_url, analyses[0].config
    log_info_detailed(node_name, worker_name, 'parsing image URL: "%s"' % image_url)
    image_fn, _ = parse_image_url(image_url, system, cachedir=analysis_dir)
    if not image_exists_locally(image_url, system, cachedir=analysis_dir):
        raise RuntimeError('Image "%s" does not exist locally' % image_fn)
    if image_fn is not None:
        # TODO: we could check the md5 for a docker image too, though this is
        # a little tricky because 'docker images --digests' sometimes reports
        # <none> if the image hasn't been pushed or pulled yet
        log_info_detailed(node_name, worker_name, 'calculating md5 over local image "%s"' % image_fn)
        image_md5 = md5(image_fn)
        log_info_detailed(node_name, worker_name, 'md5: ' + image_md5)
    json.loads(config)  # Check that config is well-formed
    attempt_name = 'proj%d_input%d_attempt%d' % (task.proj_id, task.input_id, my_attempt)
    mover = None
    if mover_config is not None:
        mover = mover_config.new_mover()
    log_info_detailed(node_name, worker_name, 'Starting attempt "%s"' % attempt_name)
    ret = run.run_job(attempt_name, [tmp_fn], image_url, image_fn,
                      config, cluster_ini,
                      log_queue=log_queue, node_name=node_name,
                      worker_name=worker_name,
                      mover=mover, destination=destination,
                      source_prefix=source_prefix)
    return ret


def download_image(url, cluster_name, analysis_dir, mover):
    image_bn = url.split('/')[-1]
    log.info('Check image "%s" exists in cluster "%s" analysis '
             'dir "%s"' % (image_bn, cluster_name, analysis_dir),
             'cluster.py')
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)
    else:
        if not os.path.isdir(analysis_dir):
            raise RuntimeError('"%s" exists but is not a directory' % analysis_dir)
    image_fn = os.path.join(analysis_dir, image_bn)
    mover.get(url, image_fn)


def _remove_ext(fn):
    while fn.rfind('.') >= 0 and fn.rfind('.') > fn.rfind('/'):
        fn = fn[:fn.rfind('.')]
    return fn


def _download_file(mover, url, typ, cluster_name, reference_dir):
    base = os.path.basename(url)
    genome = os.path.basename(os.path.dirname(url))
    local_genome_dir = os.path.join(reference_dir, genome)
    if not os.path.exists(local_genome_dir):
        os.makedirs(local_genome_dir)
    else:
        if not os.path.isdir(local_genome_dir):
            raise RuntimeError('"%s" exists but is not a directory' % local_genome_dir)
    local_fn = os.path.join(local_genome_dir, base)
    if os.path.exists(local_fn):
        raise RuntimeError('Local %s file "%s" already exists' % (typ, local_fn))
    log.info('Downloading "%s" to cluster "%s" directory "%s"' %
             (url, cluster_name, reference_dir))
    mover.get(url, local_fn)
    if base.endswith('.tar.gz') or base.endswith('.tgz'):
        cmd = 'tar -C %s -xzf %s' % (local_genome_dir, local_fn)
        ret = os.system(cmd)
        if ret != 0:
            raise RuntimeError('Error running "%s"' % cmd)


def download_reference(reference, cluster_name, reference_dir, session, mover):
    """
    Download all the reference files associated with a project, including both
    "sources", which might be FASTAs or genome indexes, and "annotations"
    """
    for url, _ in SourceSet.iterate_by_key(session, reference.source_set_id):
        _download_file(mover, url, 'source', cluster_name, reference_dir)
    for url, _ in AnnotationSet.iterate_by_key(session, reference.annotation_set_id):
        _download_file(mover, url, 'annotation', cluster_name, reference_dir)
    return ready_reference(reference, cluster_name, reference_dir, session)


def ready_reference(reference, cluster_name, reference_dir, session):
    urls = list(SourceSet.iterate_by_key(session, reference.source_set_id))
    urls += list(AnnotationSet.iterate_by_key(session, reference.annotation_set_id))
    missing = []
    for url, _ in SourceSet.iterate_by_key(session, reference.source_set_id):
        base = _remove_ext(os.path.basename(url))
        genome = os.path.basename(os.path.dirname(url))
        local_genome_dir = os.path.join(reference_dir, genome)
        if not os.path.exists(local_genome_dir) or not os.path.isdir(local_genome_dir):
            missing.append(local_genome_dir)
        local_fn = os.path.join(local_genome_dir, base)
        if not os.path.exists(local_fn) or not os.path.isdir(local_fn):
            missing.append(local_fn)
    if len(missing) == 0:
        log.info('Full reference set "%s" available on "%s"' %
                 (reference.longname, cluster_name), 'cluster.py')
        return True
    else:
        log.info('One or more files missing from reference set "%s" on "%s": %s' %
                 (reference.longname, cluster_name, str(missing)), 'cluster.py')
        return False


def prepare_analysis(cluster_ini, proj, mover, session):
    cluster_name, system, analysis_dir, _, _, _ = read_cluster_config(cluster_ini)
    analysis = session.query(Analysis).get(proj.analysis_id)
    assert system in ['singularity', 'docker']
    url = analysis.image_url
    image_fn, typ = parse_image_url(url, system, cachedir=analysis_dir)
    if typ == 'docker':
        if system == 'singularity':
            if not os.path.exists(image_fn):
                cmd = 'singularity pull ' + url
                log.info('pulling: "%s"' % cmd, 'cluster.py')
                ret = os.system(cmd)
                if ret != 0:
                    raise RuntimeError('Command "%s" exited with level %d' % (cmd, ret))
        else:
            assert system == 'docker'
            assert url.startswith('docker://')
            image_name = url[len('docker://'):]
            if docker_image_exists(url):
                log.info('Docker image "%s" exists locally; not pulling' % image_name)
            else:
                log.info('Pulling docker image "%s"' % image_name)
                ret = os.system('docker pull ' + image_name)
                if ret != 0:
                    raise RuntimeError('Unable to pull image %s (exitlevel=%d)' % (image_name, ret))
    elif typ == 'shub':
        if system != 'singularity':
            raise RuntimeError('Analysis URL is shub:// but container system is not singularity')
        if not os.path.exists(image_fn):
            cmd = 'singularity pull ' + url
            log.info('pulling: "%s"' % cmd, 'cluster.py')
            ret = os.system(cmd)
            if ret != 0:
                raise RuntimeError('Command "%s" exited with level %d' % (cmd, ret))
    else:
        if not image_exists_locally(url, system, cachedir=analysis_dir):
            download_image(url, cluster_name, analysis_dir, mover)

    if not image_exists_locally(url, system, cachedir=analysis_dir):
        raise RuntimeError('Image "%s" does not exist locally after prep' % url)

    return True


def prepare_reference(cluster_ini, proj, mover, session):
    cluster_name, _, _, ref_base, _, _ = read_cluster_config(cluster_ini)
    reference = session.query(Reference).get(proj.reference_id)
    reference_ready = ready_reference(reference, cluster_name, ref_base, session)
    if reference_ready:
        return True
    return download_reference(reference, cluster_name, ref_base, session, mover)


def prepare(project_id, cluster_ini, session, mover):
    proj = session.query(Project).get(project_id)
    analysis_ready = prepare_analysis(cluster_ini, proj, mover, session)
    reference_ready = prepare_reference(cluster_ini, proj, mover, session)
    return analysis_ready, reference_ready


def log_attempt(job, node_name, worker_name, session):
    """
    Add a new task attempt to the data model
    """
    ta = TaskAttempt(project_id=job.proj_id, input_id=job.input_id,
                     time=datetime.utcnow(), node_name=node_name,
                     worker_name=worker_name)
    session.add(ta)
    session.commit()


def get_num_attempts(job, session):
    """
    Ask model for past number of attempts for this task.
    """
    q = session.query(TaskAttempt).\
        filter(TaskAttempt.project_id == job.proj_id).\
        filter(TaskAttempt.input_id == job.input_id)
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    return q.session.execute(count_q).scalar()


def log_failure(job, node_name, worker_name, session):
    """
    Add a new failed task attempt to the data model
    """
    ta = TaskFailure(project_id=job.proj_id, input_id=job.input_id,
                     time=datetime.utcnow(), node_name=node_name,
                     worker_name=worker_name)
    session.add(ta)
    session.commit()


def get_num_failures(job, session):
    """
    Ask model for past number of failed attempts for this task.
    """
    q = session.query(TaskFailure).\
        filter(TaskFailure.project_id == job.proj_id).\
        filter(TaskFailure.input_id == job.input_id)
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    return q.session.execute(count_q).scalar()


def log_success(job, node_name, worker_name, session):
    """
    Add a new successful task attempt to the data model
    """
    ta = TaskSuccess(project_id=job.proj_id, input_id=job.input_id,
                     time=datetime.utcnow(), node_name=node_name,
                     worker_name=worker_name)
    session.add(ta)
    session.commit()


def get_num_successes(job, session):
    """
    Ask model for past number of successful attempts for this task.
    """
    q = session.query(TaskSuccess).\
        filter(TaskSuccess.project_id == job.proj_id).\
        filter(TaskSuccess.input_id == job.input_id)
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    return q.session.execute(count_q).scalar()


def job_loop(project_id, q_ini, cluster_ini, worker_name, session,
             max_fails=10, sleep_seconds=10,
             mover_config=None, destination=None, source_prefix=None):
    node_name = socket.gethostname().split('.', 1)[0]
    log_info_detailed(node_name, worker_name, 'Getting queue client')
    aws_profile, region, endpoint = parse_queue_config(q_ini)
    boto3_session = boto3.session.Session(profile_name=aws_profile)
    q_client = boto3_session.client('sqs',
                                    endpoint_url=endpoint,
                                    region_name=region)
    log_info_detailed(node_name, worker_name, 'Getting project')
    proj = session.query(Project).get(project_id)
    log_info_detailed(node_name, worker_name, 'Getting queue')
    q_name = proj.queue_name()
    resp = q_client.create_queue(QueueName=q_name)
    q_url = resp['QueueUrl']
    only_delete_on_success = True
    attempt, success, fail = 0, 0, 0
    log_info_detailed(node_name, worker_name, 'Entering job loop, queue "%s"' % q_name)
    while True:
        attempt += 1
        msg_set = q_client.receive_message(QueueUrl=q_url)
        if 'Messages' not in msg_set:
            fail += 1
            if fail >= max_fails:
                log_info_detailed(node_name, worker_name, 'exit job loop after %d poll failures' % fail)
                break
            time.sleep(sleep_seconds)
        else:
            for msg in msg_set.get('Messages', []):
                body = msg['Body']
                success += 1
                job = Task(body)
                assert job.proj_id == project_id
                nattempts = get_num_attempts(job, session)
                nfailures = get_num_failures(job, session)
                my_attempt = nattempts

                log_info_detailed(node_name, worker_name,
                                  'job start; was attempted %d times previously (%d failures)' %
                                  (nattempts, nfailures))
                log_attempt(job, node_name, worker_name, session)
                succeeded = False
                if do_job(body, cluster_ini, my_attempt, node_name,
                          worker_name, session,
                          mover_config=mover_config,
                          destination=destination,
                          source_prefix=source_prefix):
                    log_success(job, node_name, worker_name, session)
                    log_info_detailed(node_name, worker_name, 'job success')
                    succeeded = True
                else:
                    log_failure(job, node_name, worker_name, session)
                    log_info_detailed(node_name, worker_name, 'job failure')
                if succeeded or not only_delete_on_success:
                    handle = msg['ReceiptHandle']
                    log.info('Deleting ' + handle, 'cluster.py')
                    q_client.delete_message(QueueUrl=q_url, ReceiptHandle=handle)


def read_cluster_config(cluster_fn, section=None):
    cfg = RawConfigParser()
    cfg.read(cluster_fn)
    if len(cfg.sections()) == 0:
        raise RuntimeError('Cluster ini file "%s" has no sections' % cluster_fn)
    if section is not None:
        if section not in cfg.sections():
            raise RuntimeError('No [%s] section in log ini file "%s"' % (section, cluster_fn))
    else:
        section = cfg.sections()[0]

    def _cfg_get_or_none(nm):
        if not cfg.has_option(section, nm):
            return None
        val = cfg.get(section, nm)
        return None if len(val) == 0 else val

    name = cfg.get(section, 'name')
    analysis_dir = _cfg_get_or_none('analysis_dir')
    ref_base = cfg.get(section, 'ref_base')
    system = _cfg_get_or_none('system')
    ncpus = _cfg_get_or_none('cpus') or 1
    nworkers = int(_cfg_get_or_none('workers') or 1)
    return name, system, analysis_dir, ref_base, ncpus, nworkers


def test_cluster_config():
    tmpdir = tempfile.mkdtemp()
    config = """[cluster]
name = stampede2
analysis_dir = /path/i/made/up/analysis
ref_base = /path/i/made/up/reference
"""
    test_fn = os.path.join(tmpdir, '.tmp.init')
    with open(test_fn, 'w') as fh:
        fh.write(config)
    name, system, analysis_dir, reference_dir, ncpus, nworkers = read_cluster_config(test_fn)
    assert 'stampede2' == name
    assert '/path/i/made/up/analysis' == analysis_dir
    assert '/path/i/made/up/reference' == reference_dir
    assert 1 == ncpus
    assert 1 == nworkers
    assert system is None
    shutil.rmtree(tmpdir)


def test_download_image():
    srcdir, dstdir = tempfile.mkdtemp(), tempfile.mkdtemp()
    base_fn = 'test_download_image.simg'
    test_fn = os.path.join(srcdir, base_fn)
    with open(test_fn, 'w') as fh:
        fh.write('dummy image')
    mover = Mover()
    download_image(test_fn, 'marcc', dstdir, mover)
    assert os.path.exists(os.path.join(dstdir, base_fn))
    shutil.rmtree(srcdir)
    shutil.rmtree(dstdir)


def test_download_file():
    srcdir, dstdir = tempfile.mkdtemp(), tempfile.mkdtemp()
    genome_dir = os.path.join(srcdir, 'ce10')
    tarball_dir = os.path.join(genome_dir, 'files')
    os.makedirs(tarball_dir)
    base_fns = ['file1', 'file2', 'file3']
    for base_fn in base_fns:
        test_fn = os.path.join(tarball_dir, base_fn)
        with open(test_fn, 'w') as fh:
            fh.write('dummy file')
    tarball_fn = os.path.join(genome_dir, 'file.tar.gz')
    cmd = 'cd %s && tar -czf file.tar.gz files' % genome_dir
    ret = os.system(cmd)
    assert ret == 0
    assert os.path.exists(tarball_fn)
    mover = Mover()
    _download_file(mover, tarball_fn, 'source', 'test-cluster', dstdir)
    assert os.path.exists(os.path.join(dstdir, 'ce10', 'files', 'file1'))
    assert os.path.exists(os.path.join(dstdir, 'ce10', 'files', 'file2'))
    assert os.path.exists(os.path.join(dstdir, 'ce10', 'files', 'file3'))
    shutil.rmtree(srcdir)
    shutil.rmtree(dstdir)


def test_integration(db_integration):
    if not db_integration:
        pytest.skip('db integration testing disabled')


def test_download_file_s3(s3_enabled, s3_service):
    if not s3_enabled:
        pytest.skip('Skipping S3 tests')
    dstdir = tempfile.mkdtemp()
    bucket_name = 'recount-ref'
    src = ''.join(['s3://', bucket_name, '/ce10/gtf.tar.gz'])
    assert s3_service.exists(src), src
    _download_file(s3_service, src, 'source', 'test-cluster', dstdir)
    assert os.path.exists(os.path.join(dstdir, 'ce10/gtf/genes.gtf'))


def test_with_db(session):
    srcdir, dstdir = tempfile.mkdtemp(), tempfile.mkdtemp()
    analysis_dir = os.path.join(dstdir, 'analysis')
    reference_dir = os.path.join(dstdir, 'reference')
    cluster_ini = os.path.join(srcdir, 'cluster.ini')
    with open(cluster_ini, 'wb') as fh:
        fh.write(b'[cluster]\n')
        fh.write(b'name = test-cluster\n')
        fh.write(b'analysis_dir = ' + analysis_dir.encode() + b'\n')
        fh.write(b'ref_base = ' + reference_dir.encode() + b'\n')
        fh.write(b'system = docker\n')
        fh.write(b'sudo = false\n')
    os.makedirs(analysis_dir)
    os.makedirs(reference_dir)
    project_name = 'test-project'
    analysis_name = 'test-analysis'
    input_set_name = 'test-input-set'
    input_set_csv = '\n'.join(['NA,NA,ftp://genomi.cs/1_1.fastq.gz,ftp://genomi.cs/1_2.fastq.gz,NA,NA,NA,NA,wget',
                               'NA,NA,ftp://genomi.cs/2_1.fastq.gz,ftp://genomi.cs/2_2.fastq.gz,NA,NA,NA,NA,wget'])
    csv_fn = os.path.join(srcdir, 'project.csv')
    with open(csv_fn, 'w') as ofh:
        ofh.write(input_set_csv)
    analysis_basename = 'recount-rna-seq-lite-nf.simg'
    analysis_fn = os.path.join(analysis_dir, analysis_basename)
    with open(analysis_fn, 'wb') as fh:
        fh.write(b'blah\n')
    analysis_id = add_analysis(analysis_name, analysis_basename, '{}', session)
    input_set_id, nadded = import_input_set(input_set_name, csv_fn, session)
    assert 2 == nadded
    source_set_id = add_source_set(session)
    # make fake source
    genome_dir = os.path.join(srcdir, 'ce10')
    os.makedirs(genome_dir)
    source_fn = os.path.join(genome_dir, 'source1.txt')
    with open(source_fn, 'wb') as fh:
        fh.write(b'blah\n')
    src1 = add_source(source_fn, None, None, None, None, None, 'local', session)
    add_sources_to_set([source_set_id], [src1], session)
    # make fake annotation
    annot_fn = os.path.join(genome_dir, 'annotation1.txt')
    with open(annot_fn, 'wb') as fh:
        fh.write(b'blah\n')
    annotation_set_id = add_annotation_set(session)
    ann1 = add_annotation(6239, annot_fn, None, 'local', session)
    add_annotations_to_set([annotation_set_id], [ann1], session)
    reference_id = add_reference(6239, 'ce10', 'NA', 'NA', 'NA', source_set_id, annotation_set_id, session)
    project_id = add_project(project_name, analysis_id, input_set_id, reference_id, session)
    mover_config = MoverConfig()
    prepare(project_id, cluster_ini, session, mover_config.new_mover())
    assert os.path.exists(os.path.join(reference_dir, 'ce10', 'source1.txt'))
    assert os.path.exists(os.path.join(reference_dir, 'ce10', 'annotation1.txt'))


def test_parse_image_url_1():
    image_fn, typ = parse_image_url('shub://langmead-lab/recount-pump:workflow_base',
                                    'singularity', cachedir='/cache')
    assert '/cache/langmead-lab-recount-pump-workflow_base.simg' == image_fn
    assert 'shub' == typ


def test_parse_image_url_2():
    image_fn, typ = parse_image_url('docker://quay.io/benlangmead/recount-pump:latest',
                                    'singularity', cachedir='/cache')
    assert '/cache/recount-pump-latest.simg' == image_fn
    assert 'docker' == typ


def test_parse_image_url_3():
    image_fn, typ = parse_image_url('docker://quay.io/benlangmead/recount-pump:latest',
                                    'docker', cachedir='/cache')
    assert image_fn is None
    assert 'docker' == typ


def worker(project_id, worker_name, q_ini, cluster_ini, engine, max_fail,
           poll_seconds,
           mover_config=None, destination=None, source_prefix=None):
    engine.dispose()
    connection = engine.connect()
    session = Session(bind=connection)
    signal.signal(signal.SIGUSR1, lambda sig, stack: traceback.print_stack(stack))
    print(job_loop(project_id, q_ini, cluster_ini, worker_name, session,
                   max_fails=max_fail,
                   sleep_seconds=poll_seconds,
                   mover_config=mover_config,
                   destination=destination,
                   source_prefix=source_prefix))


def log_worker():
    log.info('Entering worker log-relay thread', 'cluster.py')
    for tup in iter(log_queue.get, None):
        message, module = tup
        log.info(message, module)
    log.info('Exiting worker log-relay thread', 'cluster.py')


def parse_destination_ini(ini_fn, section='destination'):
    """
    Parse and return the fields of a destination.ini file

    Example:

        [destination]
        enabled=true
        destination=globus://endpoint-name/this/is/a/path.txt
        aws_endpoint=
        aws_profile=
    """
    if not os.path.exists(ini_fn):
        raise RuntimeError('destination ini file "%s" does not exist' % ini_fn)
    cfg = RawConfigParser()
    cfg.read(ini_fn)
    if not cfg.has_section(section):
        raise RuntimeError('destination init file "%s" does not have section "%s"'
                           % (ini_fn, section))

    def _get_option(nm):
        if not cfg.has_option(section, nm):
            return None
        opt = cfg.get(section, nm)
        return None if (len(opt) == 0) else opt

    enabled = _get_option('enabled')
    enabled = (enabled is None) or (enabled == 'true')
    destination_url = _get_option('destination')
    source_prefix = _get_option('source_prefix')
    aws_endpoint = _get_option('aws_endpoint')
    aws_profile = _get_option('aws_profile')
    return enabled, destination_url, source_prefix, aws_endpoint, aws_profile


def go():
    args = docopt(__doc__)
    log_ini = os.path.expanduser(args['--log-ini'])
    log.init_logger(log.LOG_GROUP_NAME, log_ini=log_ini, agg_level=args['--log-level'])
    log.init_logger('sqlalchemy', log_ini=log_ini, agg_level=args['--log-level'],
                    sender='sqlalchemy')
    signal.signal(signal.SIGUSR1, lambda sig, stack: traceback.print_stack(stack))
    try:
        db_ini = os.path.expanduser(args['--db-ini'])
        cluster_ini = os.path.expanduser(args['--cluster-ini'])
        q_ini = os.path.expanduser(args['--queue-ini'])
        dest_ini = os.path.expanduser(args['--destination-ini'])
        globus_ini = os.path.expanduser(args['--globus-ini'])
        s3_ini = os.path.expanduser(args['--s3-ini'])
        mover_config = MoverConfig(
            s3_ini=s3_ini,
            s3_section=args['--s3-section'],
            globus_ini=globus_ini,
            globus_section=args['--globus-section'],
            enable_web=True,
            curl_exe=args['--curl'])
        project_id = int(args['<project-id>'])
        if args['prepare']:
            session_maker = session_maker_from_config(db_ini, args['--db-section'])
            print(prepare(project_id, cluster_ini, session_maker(),
                          mover_config.new_mover()))
        if args['run']:
            enabled, destination_url, source_prefix, aws_endpoint, aws_profile = \
                parse_destination_ini(dest_ini)
            engine = engine_from_config(db_ini, args['--db-section'])
            connection = engine.connect()
            session = Session(bind=connection)
            prepare(project_id, cluster_ini, session, mover_config.new_mover())
            max_fails = int(args['--max-fail'])
            sleep_seconds = int(args['--poll-seconds'])
            procs = []
            sysmon_ival = int(args['--sysmon-interval'])
            _, _, _, _, _, nworkers = read_cluster_config(cluster_ini)
            # set up system monitor thread
            sm = None
            if sysmon_ival > 0:
                log.info('Starting system monitor thread with interval %d' %
                         sysmon_ival, 'cluster.py')
                sm = SysmonThread(seconds=int(sysmon_ival))
                sm.start()
            log_thread = threading.Thread(target=log_worker)
            log_thread.start()
            for i in range(nworkers):
                worker_name = 'worker_%d_of_%d' % (i+1, nworkers)
                t = multiprocessing.Process(target=worker,
                                            args=(project_id, worker_name, q_ini, cluster_ini,
                                                  engine, max_fails, sleep_seconds,
                                                  mover_config, destination_url,
                                                  source_prefix))
                t.start()
                log.info('Spawned process %d (pid=%d)' % (i+1, t.pid), 'cluster.py')
                procs.append(t)
            for i, proc in enumerate(procs):
                pid = proc.pid
                proc.join()
                log.info('Joined process %d (pid=%d)' % (i + 1, pid), 'cluster.py')
            log.info('All processes joined', 'cluster.py')
            log_queue.put(None)
            log_thread.join()
            log.info('Logging thread joined', 'cluster.py')
            if sysmon_ival > 0:
                log.info('Closing monitor thread', 'cluster.py')
                sm.close()
                log.info('Joining monitor thread', 'cluster.py')
                sm.join()
    except Exception:
        log.error('Uncaught exception:', 'cluster.py')
        raise


if __name__ == '__main__':
    go()
