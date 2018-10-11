#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""pump

Usage:
  pump add-project [options] <name> <analysis-id> <input-set-id> <reference-id>
  pump summarize-project [options] <project-id>
  pump stage [options] <project-id>

Options:
  --db-ini <ini>              Database ini file [default: ~/.recount/db.ini].
  --db-section <section>      ini file section for database [default: client].
  --queue-ini <ini>           Queue ini file [default: ~/.recount/queue.ini].
  --queue-section <section>   ini file section for database [default: queue].
  --chunk <strategy>          Set chunking strategy; not implemented; 1 SRR at a time
  --log-ini <ini>             ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>         set level for log aggregation; could be CRITICAL,
                              ERROR, WARNING, INFO, DEBUG [default: INFO].
  -h, --help                  Show this screen.
  --version                   Show version.
"""

import os
import log
import pytest
import json
import boto3
from docopt import docopt
from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, DateTime
from base import Base
from input import Input, InputSet
from analysis import Analysis
from reference import Reference, Source, SourceSet, Annotation, AnnotationSet
from toolbox import session_maker_from_config, parse_queue_config


class Project(Base):
    """
    Defines a collection of jobs to be run, which in turn supply the data for a
    recount/Snaptron compilation.  This is defined by associating a collection
    of inputs (InputSet) with a set of Analyses (AnalysisSet) to be run on all
    of them. 
    """
    __tablename__ = 'project'

    id = Column(Integer, Sequence('project_id_seq'), primary_key=True)
    name = Column(String(1024), nullable=False)
    input_set_id = Column(Integer, ForeignKey('input_set.id'), nullable=False)
    analysis_id = Column(Integer, ForeignKey('analysis.id'), nullable=False)
    reference_id = Column(Integer, ForeignKey('reference.id'), nullable=False)

    def deepdict(self, session):
        d = self.__dict__.copy()
        iset = session.query(InputSet).get(self.input_set_id)
        analysis = session.query(Analysis).get(self.analysis_id)
        del d['input_set_id']
        d['input_set'] = iset.deepdict(session)
        del d['analysis_id']
        d['analysis'] = analysis.deepdict(session)
        del d['_sa_instance_state']
        return d

    def to_job_string(self, input_str, analysis_str, reference_str):
        name = self.name
        if isinstance(name, bytes):
            name = name.decode()
        job_str = ' '.join([str(self.id), name, input_str, analysis_str, reference_str])
        if job_str.count(' ') != 4:
            raise RuntimeError('Bad job string; must have exactly 4 spaces: "%s"' % job_str)
        return job_str

    @classmethod
    def queue_name_cl(cls, ident):
        return 'stage_%d' % ident

    def queue_name(self):
        return Project.queue_name_cl(self.id)

    @classmethod
    def parse_job_string(cls, st):
        """
        Do some mild data validation and return parsed job-attempt parameters.
        """
        toks = st.split(' ')
        assert 5 == len(toks)
        my_id = int(toks[0])
        proj_name, input_str, analysis_str, reference_str = toks[1:5]
        return my_id, proj_name, input_str, analysis_str, reference_str

    def job_iterator(self, session, chunking_stragegy=None):
        """
        For each input in the project, return a string describing a job that
        can process that input on any cluster.
        TODO: Allow chunking; otherwise, only 1 SRR at a time is handled
        """
        iset = session.query(InputSet).get(self.input_set_id)
        analysis = session.query(Analysis).get(self.analysis_id)
        analysis_str = analysis.to_job_string()
        reference = session.query(Reference).get(self.reference_id)
        reference_str = reference.name
        for input in iset.inputs:
            yield self.to_job_string(input.to_job_string(), analysis_str, reference_str)


class TaskAttempt(Base):
    """
    Table for job attempts.  Each time a worker gets a task from the queue, it
    updates this.
    """
    __tablename__ = 'task_attempt'

    id = Column(Integer, Sequence('project_id'), primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    input_id = Column(Integer, ForeignKey('input.id'))
    time = Column(DateTime)
    node_name = Column(String(1024), nullable=False)
    worker_name = Column(String(1024), nullable=False)


class TaskSuccess(Base):
    """
    Table for job attempts.  Each time a worker gets a task from the queue, it
    updates this.
    """
    __tablename__ = 'task_success'

    id = Column(Integer, Sequence('project_event_id_seq'), primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    input_id = Column(Integer, ForeignKey('input.id'))
    time = Column(DateTime)
    node_name = Column(String(1024), nullable=False)
    worker_name = Column(String(1024), nullable=False)


class TaskFailure(Base):
    """
    Table for job attempts.  Each time a worker gets a task from the queue, it
    updates this.
    """
    __tablename__ = 'task_failure'

    id = Column(Integer, Sequence('project_event_id_seq'), primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    input_id = Column(Integer, ForeignKey('input.id'))
    time = Column(DateTime)
    node_name = Column(String(1024), nullable=False)
    worker_name = Column(String(1024), nullable=False)


class FailedTasks(Base):
    """
    When a task has failed so many times that it needs to be deleted from the
    queue unfulfilled, it goes here.
    """
    __tablename__ = 'failed_tasks'

    id = Column(Integer, Sequence('failed_tasks_id_seq'), primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    input_id = Column(Integer, ForeignKey('input.id'))
    time = Column(DateTime)
    node_name = Column(String(1024), nullable=False)
    worker_name = Column(String(1024), nullable=False)
    job_string = Column(String(1024), nullable=False)

    @classmethod
    def job_iterator(cls, project_id, session, chunking_stragegy=None):
        """
        For each input in the project, return a string describing a job that
        can process that input on any cluster.
        TODO: Allow chunking; otherwise, only 1 SRR at a time is handled
        """
        proj = session.query(Project).get(project_id)
        analysis = session.query(Analysis).get(proj.analysis_id)
        analysis_str = analysis.to_job_string()
        reference = session.query(Reference).get(proj.reference_id)
        reference_str = reference.name
        for input in session.query(FailedTasks).filter_by(project_id=project_id):
            yield proj.to_job_string(input.to_job_string(), analysis_str, reference_str)


def add_project(name, analysis_id, input_set_id, reference_id, session):
    """
    Given a project name and csv file, populate the database with the
    appropriate project rows
    """
    proj = Project(name=name, analysis_id=analysis_id, input_set_id=input_set_id,
                   reference_id=reference_id)
    session.add(proj)
    session.commit()
    return proj.id


def get_queue(sqs_client, queue_name):
    resp = sqs_client.create_queue(QueueName=queue_name)
    assert 'QueueUrl' in resp
    return resp['QueueUrl']


def stage_failed_tasks(project_id, sqs_client, session, chunking_strategy=None):
    """
    Stage everything in the FailedTasks table for the given project
    """
    proj = session.query(Project).get(project_id)
    q_url = get_queue(sqs_client, proj.queue_name())
    log.info('stage_failed using sqs queue url ' + q_url, 'pump.py')
    n = 0
    for job_str in FailedTasks.job_iterator(project_id, session, chunking_strategy):
        log.debug('stage failed job "%s" from "%s" to "%s"' % (job_str, proj.name, proj.queue_name()), 'pump.py')
        resp = sqs_client.send_message(QueueUrl=q_url, MessageBody=job_str)
        meta = resp['ResponseMetadata']
        status = meta['HTTPStatusCode']
        if status != 200:
            raise IOError('bad status code (%d) after attempt to send message to: %s' % (status, q_url))
        n += 1
    log.info('Staged %d failed jobs from "%s" to "%s"' % (n, proj.name, proj.queue_name()), 'pump.py')


def stage_project(project_id, sqs_client, session, chunking_strategy=None):
    """
    Stage all the jobs in the given project
    """
    proj = session.query(Project).get(project_id)
    q_url = get_queue(sqs_client, proj.queue_name())
    log.info('stage_project using sqs queue url ' + q_url, 'pump.py')
    n = 0
    for job_str in proj.job_iterator(session, chunking_strategy):
        log.debug('stage job "%s" from "%s" to "%s"' % (job_str, proj.name, proj.queue_name()), 'pump.py')
        resp = sqs_client.send_message(QueueUrl=q_url, MessageBody=job_str)
        meta = resp['ResponseMetadata']
        status = meta['HTTPStatusCode']
        if status != 200:
            raise IOError('bad status code (%d) after attempt to send message to: %s' % (status, q_url))
        n += 1
    log.info('Staged %d jobs from "%s" to "%s"' % (n, proj.name, proj.queue_name()), 'pump.py')


def test_integration(db_integration):
    if not db_integration:
        pytest.skip('db integration testing disabled')


def _simple_project(session):
    analysis = Analysis(name='recount-rna-seq-v1', image_url='fake')
    session.add(analysis)
    session.commit()
    assert 1 == len(list(session.query(Analysis)))

    inp1 = Input(retrieval_method="url",
                 acc_r='SRR123', acc_s='SRP123',
                 url_1='fake1', checksum_1='fake1',
                 url_2='fake2', checksum_2='fake2')
    inp2 = Input(retrieval_method="url",
                 acc_r='SRR1234', acc_s='SRP1234',
                 url_1='fake1', checksum_1='fake1')

    # add inputs
    assert 0 == len(list(session.query(Input)))
    assert 0 == len(list(session.query(InputSet)))
    session.add(inp1)
    session.add(inp2)
    session.commit()
    assert 2 == len(list(session.query(Input)))

    # add input sets with associations
    input_set = InputSet(inputs=[inp1, inp2])
    session.add(input_set)
    session.commit()
    assert 1 == len(list(session.query(InputSet)))

    src1 = Source(retrieval_method="s3",
                  url_1='s3://recount-pump/ref/ce10/ucsc_tracks.tar.gz', checksum_1='')
    src2 = Source(retrieval_method="s3",
                  url_1='s3://recount-pump/ref/ce10/fasta.tar.gz', checksum_1='')
    session.add(src1)
    session.add(src2)
    session.commit()
    ss = SourceSet(sources=[src1, src2])
    session.add(ss)
    session.commit()
    an1 = Annotation(retrieval_method='s3',
                     url='s3://recount-pump/ref/ce10/gtf.tar.gz', checksum='')
    session.add(an1)
    session.commit()
    anset = AnnotationSet(annotations=[an1])
    session.add(anset)
    ref1 = Reference(tax_id=6239, name='celegans', longname='caenorhabditis_elegans',
                     conventions='', comment='', source_set_id=ss.id, annotation_set_id=anset.id)
    session.add(ref1)
    session.commit()
    assert ref1.id is not None

    proj = Project(name='my_project', input_set_id=input_set.id,
                   analysis_id=analysis.id, reference_id=ref1.id)
    session.add(proj)
    session.commit()
    assert 1 == len(list(session.query(Project)))
    return proj


def test_job_string_1():
    proj = Project(id=1, name='proj')
    st = proj.to_job_string('input-str', 'analysis-str', 'reference-str')
    assert '1 proj input-str analysis-str reference-str' == st


def test_job_string_2():
    my_id, proj_name, input_str, analysis_str, reference_str = \
        Project.parse_job_string('1 proj input-str analysis-str reference-str')
    assert 1 == my_id
    assert 'proj' == proj_name
    assert 'input-str' == input_str
    assert 'analysis-str' == analysis_str
    assert 'reference-str' == reference_str


def test_stage(q_enabled, q_client_and_resource, session):
    if not q_enabled:
        pytest.skip('Skipping queue-enabled test')
    q_client, q_resource = q_client_and_resource
    proj = _simple_project(session)
    resp = q_client.create_queue(QueueName=proj.queue_name())
    assert 'QueueUrl' in resp
    q_url = resp['QueueUrl']
    stage_project(proj.id, q_client, session)
    queue = q_resource.get_queue_by_name(QueueName=proj.queue_name())
    assert q_url == queue.url
    msg1 = q_client.receive_message(QueueUrl=q_url)
    msg2 = q_client.receive_message(QueueUrl=q_url)
    messages = []
    messages.extend(msg1['Messages'])
    messages.extend(msg2['Messages'])
    assert 2 == len(messages)
    bodies = [
        '1 my_project 1,SRR123,SRP123,fake1,fake2,None,fake1,fake2,None,url fake celegans',
        '1 my_project 2,SRR1234,SRP1234,fake1,None,None,fake1,None,None,url fake celegans'
    ]
    bodies.remove(messages[0]['Body'])
    bodies.remove(messages[1]['Body'])
    assert 0 == len(bodies)


def go():
    args = docopt(__doc__)
    log_ini = os.path.expanduser(args['--log-ini'])
    log.init_logger(log.LOG_GROUP_NAME, log_ini=log_ini, agg_level=args['--log-level'])
    log.init_logger('sqlalchemy', log_ini=log_ini, agg_level=args['--log-level'],
                    sender='sqlalchemy')
    try:
        db_ini = os.path.expanduser(args['--db-ini'])
        q_ini = os.path.expanduser(args['--queue-ini'])
        if args['add-project']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_project(args['<name>'], args['<analysis-id>'],
                              args['<input-set-id>'], args['<reference-id>'],
                              Session()))
        if args['summarize-project']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            session = Session()
            proj = session.query(Project).get(int(args['<project-id>']))
            print(json.dumps(proj.deepdict(session), indent=4, separators=(',', ': ')))
        elif args['stage']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            boto3_session = boto3.session.Session()
            region, endpoint = parse_queue_config(q_ini)
            sqs_client = boto3_session.client('sqs',
                                              endpoint_url=endpoint,
                                              region_name=region)
            print(stage_project(int(args['<project-id>']), sqs_client, Session(),
                                chunking_strategy=args['--chunk']))
    except Exception:
        log.error('Uncaught exception:', 'pump.py')
        raise


if __name__ == '__main__':
    go()
