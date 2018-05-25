#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""pump

Usage:
  pump add-project <db-config> <name> <analysis-id> <input-set-id>
  pump add-project-ex <db-config> <name> <analysis-name> <analysis-image-url>
                      <input-set-name> <input-set-table>
                      (<cluster-name> <wrapper-url>)...
  pump test

Options:
  -h, --help    Show this screen.
  --version     Show version.
"""

import os
import sys
import unittest
from docopt import docopt
from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, DateTime, create_engine
from base import Base
from sqlalchemy.orm import relationship, sessionmaker
from input import import_input_set, Input, InputSet
from analysis import add_analysis_ex, parse_cluster_analyses, Analysis, Cluster, ClusterAnalysis
from toolbox import session_maker_from_config


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

    event = relationship("ProjectEvent")  # events associated with this project


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
    cluster_id = Column(Integer, ForeignKey('cluster.id'))
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
    cluster_id = Column(Integer, ForeignKey('cluster.id'))


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


def add_project(name, analysis_id, input_set_id, session):
    """
    Given a project name and csv file, populate the database with the
    appropriate project rows
    """
    proj = Project(name=name, analysis_id=analysis_id, input_set_id=input_set_id)
    session.add(proj)
    session.commit()
    return proj.id


def add_project_ex(name, analysis_name, analysis_image_url, cluster_analyses,
                   input_set_name, input_set_csv_fn, session):
    """
    Given some high-level details about a project, analysis, input set, and
    cluster/analysis combinations, populate the database accordingly.  This is
    a helpful all-in-one call to start from if you are starting a new project.
    """
    analysis_id, n_added_cluster, n_added_cluster_analysis = \
        add_analysis_ex(analysis_name, analysis_image_url, cluster_analyses, session)
    input_set_id, n_added_input = import_input_set(input_set_name, input_set_csv_fn, session)
    project = session.query(Project).filter_by(name=name).first()
    if project is not None:
        raise ValueError('Project with name "%s" already exists' % name)
    project_id = add_project(name, analysis_id, input_set_id, session)
    return project_id, analysis_id, input_set_id, \
           n_added_input, n_added_cluster, n_added_cluster_analysis


def _setup():
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


class TestPump(unittest.TestCase):
    def setUp(self):
        self.session = _setup()

    def tearDown(self):
        self.session.close()

    def test_add_project(self):
        analysis = Analysis(name='recount-rna-seq-v1', image_url='fake')
        self.session.add(analysis)
        self.session.commit()
        self.assertEqual(1, len(list(self.session.query(Analysis))))

        inp1 = Input(retrieval_method="url",
                     url_1='fake1', checksum_1='fake1',
                     url_2='fake2', checksum_2='fake2')
        inp2 = Input(retrieval_method="url", url_1='fake1', checksum_1='fake1')

        # add inputs
        self.assertEqual(0, len(list(self.session.query(Input))))
        self.assertEqual(0, len(list(self.session.query(InputSet))))
        self.session.add(inp1)
        self.session.add(inp2)
        self.session.commit()
        self.assertEqual(2, len(list(self.session.query(Input))))

        # add input sets with associations
        input_set = InputSet(inputs=[inp1, inp2])
        self.session.add(input_set)
        self.session.commit()
        self.assertEqual(1, len(list(self.session.query(InputSet))))

        proj = Project(name='my_project', input_set_id=input_set.id, analysis_id=analysis.id)
        self.session.add(proj)
        self.session.commit()
        self.assertEqual(1, len(list(self.session.query(Project))))

        self.session.delete(proj)
        self.session.delete(input_set)
        self.session.delete(inp1)
        self.session.delete(inp2)
        self.session.delete(analysis)
        self.session.commit()
        self.assertEqual(0, len(list(self.session.query(Analysis))))
        self.assertEqual(0, len(list(self.session.query(Input))))
        self.assertEqual(0, len(list(self.session.query(InputSet))))
        self.assertEqual(0, len(list(self.session.query(Project))))

    def test_add_project_ex(self):
        project_name = 'recount-rna-seq-human'
        analysis_name = 'recount-rna-seq-v1'
        image_url = 's3://recount-pump/analysis/recount-rna-seq-v1.img'
        cluster_analyses1 = [
            ('stampede2', 's3://recount-pump/analysis/recount-rna-seq-v1/stampede2.sh'),
            ('marcc', 's3://recount-pump/analysis/recount-rna-seq-v1/marcc.sh')
        ]
        input_set_name = 'all_human'
        input_set_csv = '\n'.join(['NA,NA,ftp://genomi.cs/1_1.fastq.gz,ftp://genomi.cs/1_2.fastq.gz,NA,NA,NA,NA,wget',
                                   'NA,NA,ftp://genomi.cs/2_1.fastq.gz,ftp://genomi.cs/2_2.fastq.gz,NA,NA,NA,NA,wget'])
        csv_fn = '.test_add_project_ex.csv'
        with open(csv_fn, 'w') as ofh:
            ofh.write(input_set_csv)
        project_id, analysis_id, input_set_id, n_added_input, \
        n_added_cluster, n_added_cluster_analysis = \
            add_project_ex(project_name, analysis_name, image_url,
                           cluster_analyses1, input_set_name, csv_fn, self.session)
        self.assertEqual(2, n_added_input)
        self.assertEqual(2, n_added_cluster)
        self.assertEqual(2, n_added_cluster_analysis)
        self.assertEqual(1, len(list(self.session.query(Project))))
        self.assertEqual(1, len(list(self.session.query(InputSet))))
        self.assertEqual(2, len(list(self.session.query(Input))))
        self.assertEqual(1, len(list(self.session.query(Analysis))))
        self.assertEqual(2, len(list(self.session.query(Cluster))))
        self.assertEqual(2, len(list(self.session.query(ClusterAnalysis))))
        for tab in [Analysis, Input, InputSet, Project, Cluster, ClusterAnalysis]:
            self.session.query(tab).delete()
            self.assertEqual(0, len(list(self.session.query(tab))))
        os.remove(csv_fn)


if __name__ == '__main__':
    args = docopt(__doc__)
    if args['add-project']:
        with open(args['<db-config>']) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        print(add_project(args['<name>'], args['<analysis-id>'],
                          args['<input-set-id>'], Session()))
    elif args['add-project-ex']:
        with open(args['<db-config>']) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        print(add_project_ex(args['<name>'], args['<analysis-name>'],
                             args['<analysis-image-url>'],
                             args['<input-set-name>'], args['<input-set-csv>'],
                             args['<cluster-analyses>'], Session()))
    elif args['test']:
        sys.argv.remove('test')
        unittest.main()
