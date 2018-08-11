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
  -a, --aggregate             enable log aggregation.
  -h, --help                  Show this screen.
  --version                   Show version.
"""

import os
import log
import pytest
import json
from docopt import docopt
from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, DateTime
from sqlalchemy.orm import relationship
from base import Base
from input import Input, InputSet
from analysis import Analysis
from reference import Reference, Source, SourceSet, Annotation, AnnotationSet
from toolbox import session_maker_from_config
from queueing.service import queueing_service_from_config


class Project(Base):
    """
    Defines a collection of jobs to be run, which in turn supply the data for a
    recount/Snaptron compilation.  This is defined by associating a collection
    of inputs (InputSet) with a set of Analyses (AnalysisSet) to be run on all
    of them. 
    """
    __tablename__ = 'project'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(1024))
    input_set_id = Column(Integer, ForeignKey('input_set.id'))
    analysis_id = Column(Integer, ForeignKey('analysis.id'))
    reference_id = Column(Integer, ForeignKey('reference.id'))

    event = relationship("ProjectEvent")  # events associated with this project

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
        assert isinstance(input_str, bytes)
        assert isinstance(analysis_str, bytes)
        assert isinstance(reference_str, bytes)
        job_str = b' '.join([str(self.id).encode(), self.name.encode(), input_str, analysis_str, reference_str])
        if job_str.count(b' ') != 4:
            raise RuntimeError('Bad job string; must have exactly 4 spaces: "%s"' % job_str)
        return job_str

    @classmethod
    def parse_job_string(cls, st):
        """
        Do some mild data validation and return parsed job-attempt parameters.
        """
        assert isinstance(st, bytes)
        toks = st.split(b' ')
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
        reference_str = reference.name.encode()
        for input in iset.inputs:
            yield self.to_job_string(input.to_job_string(), analysis_str, reference_str)


class ProjectEvent(Base):
    """
    Event types:
    1. Staging a job
    2. Launching a staged job to the queue
    3. Committing results from a completed job to the staging area
    """
    __tablename__ = 'project_event'

    id = Column(Integer, Sequence('project_event_id_seq'), primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    time = Column(DateTime)
    event = Column(String(1024))


class Job(Base):
    """
    Job: an association between an analysis and an input
    """
    __tablename__ = 'job'

    id = Column(Integer, Sequence('job_id_seq'), primary_key=True)
    analysis_id = Column(Integer, ForeignKey('analysis.id'))
    input_id = Column(Integer, ForeignKey('input.id'))


class Attempt(Base):
    """
    A job assigned to run on a particular cluster at a particular time.
    """
    __tablename__ = 'attempt'

    id = Column(Integer, Sequence('attempt_id_seq'), primary_key=True)
    job_id = Column(Integer, ForeignKey('job.id'))
    description = Column(String(1024))
    time = Column(DateTime)
    # 1, 2, 3, ... depending on which attempt this is.  0 if it's unknown.
    attempt = Column(Integer)


class AttemptResult(Base):
    """
    Result of an attempt: whether it succeeded, where results 
    """
    __tablename__ = 'attempt_result'

    id = Column(Integer, Sequence('attempt_result_id_seq'), primary_key=True)
    job_attempt_id = Column(Integer, ForeignKey('attempt.id'))
    description = Column(String(1024))


class ProjectStage(Base):
    """
    Holds jobs that are currently running or that are to be run in the future.
    """
    __tablename__ = 'project_stage'

    id = Column(Integer, Sequence('project_stage_id_seq'), primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    job_id = Column(Integer, ForeignKey('project.id'))


class ProjectActive(Base):
    """
    Holds jobs that are currently running or that are to be run in the future.
    """
    __tablename__ = 'project_active'

    id = Column(Integer, Sequence('project_stage_id_seq'), primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    job_id = Column(Integer, ForeignKey('project.id'))


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


def stage_project(project_id, queue_service, session, chunking_strategy=None):
    proj = session.query(Project).get(project_id)
    queue_name = 'stage_%d' % project_id
    if not queue_service.queue_exists(queue_name):
        queue_service.queue_create(queue_name)
    n = 0
    for job_str in proj.job_iterator(session, chunking_strategy):
        log.debug(__name__, 'Staged job "%s" from "%s" to "%s"' % (job_str, proj.name, queue_name), 'pump.py')
        queue_service.publish(queue_name, job_str)
        n += 1
    log.info(__name__, 'Staged %d jobs from "%s" to "%s"' % (n, proj.name, queue_name), 'pump.py')


def test_integration(db_integration):
    if not db_integration:
        pytest.skip('db integration testing disabled')


def test_add_project(session):
    analysis = Analysis(name='recount-rna-seq-v1', image_url='fake')
    session.add(analysis)
    session.commit()
    assert 1 == len(list(session.query(Analysis)))

    inp1 = Input(retrieval_method="url",
                 url_1='fake1', checksum_1='fake1',
                 url_2='fake2', checksum_2='fake2')
    inp2 = Input(retrieval_method="url", url_1='fake1', checksum_1='fake1')

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
    session.commit()
    ref1 = Reference(tax_id=6239, name='celegans', longname='caenorhabditis_elegans',
                     conventions='', comment='', source_set_id=ss.id, annotation_set_id=anset.id)

    proj = Project(name='my_project', input_set_id=input_set.id, analysis_id=analysis.id, reference_id=ref1.id)
    session.add(proj)
    session.commit()
    assert 1 == len(list(session.query(Project)))

    session.delete(proj)
    session.delete(input_set)
    session.commit()
    session.delete(inp1)
    session.delete(inp2)
    session.delete(analysis)
    session.commit()
    assert 0 == len(list(session.query(Analysis)))
    assert 0 == len(list(session.query(Input)))
    assert 0 == len(list(session.query(InputSet)))
    assert 0 == len(list(session.query(Project)))


def test_job_string_1():
    proj = Project(id=1, name='proj')
    st = proj.to_job_string(b'input-str', b'analysis-str', b'reference-str')
    assert b'1 proj input-str analysis-str reference-str' == st


def test_job_string_2():
    my_id, proj_name, input_str, analysis_str, reference_str = \
        Project.parse_job_string(b'1 proj input-str analysis-str reference-str')
    assert 1 == my_id
    assert b'proj' == proj_name
    assert b'input-str' == input_str
    assert b'analysis-str' == analysis_str
    assert b'reference-str' == reference_str


if __name__ == '__main__':
    args = docopt(__doc__)
    agg_ini = os.path.expanduser(args['--log-ini']) if args['--aggregate'] else None
    log.init_logger(__name__, log_ini=agg_ini, agg_level=args['--log-level'])
    log.init_logger('sqlalchemy', log_ini=agg_ini, agg_level=args['--log-level'],
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
            qserv = queueing_service_from_config(q_ini, args['--queue-section'])
            print(stage_project(int(args['<project-id>']), qserv, Session(),
                                chunking_strategy=args['--chunk']))
    except Exception:
        log.error(__name__, 'Uncaught exception:', 'pump.py')
        raise
