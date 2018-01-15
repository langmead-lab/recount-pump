#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, DateTime
from base import Base
from sqlalchemy.orm import relationship
from input import import_input_set, Input, InputSet
from analysis import add_analysis_ex, parse_cluster_analyses, Analysis
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
    analysis_id = add_analysis_ex(analysis_name, analysis_image_url, cluster_analyses, session)
    input_set_id = import_input_set(input_set_name, input_set_csv_fn, session)
    return add_project(name, analysis_id, input_set_id, session)


if __name__ == '__main__':
    import sys

    usage_msg = '''
Usage: pump.py <cmd> [options]*

Commands:

    add-project <db_config> <name> <analysis_id> <input_set_id>
    add-project-ex <db_config> <name> <analysis_name> <analysis_image_url>
                   <input_set_name> <input_set_csv>
                   <cluster_name1>:<wrapper_url1> <cluster_name2>:<wrapper_url2>, ...
    help
    test

On each cluster, the user running the jobs should create a file
`$HOME/.recount/cluster.txt` containing the name of the cluster, matching the
<name> used to add the corresponding record with `add-cluster`.
'''

    def print_usage():
        print('\n' + usage_msg.strip() + '\n')

    if len(sys.argv) <= 1 or sys.argv[1] == 'help':
        print_usage()
        sys.exit(0)

    if sys.argv[1] == 'test':
        import unittest
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

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
                srcs = list(self.session.query(Input))

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
                pass

        sys.argv.remove('test')
        unittest.main()

    elif len(sys.argv) >= 3 and sys.argv[1] == 'add-project':
        if len(sys.argv) < 6:
            raise ValueError('add-project requires 3 arguments')
        with open(sys.argv[2]) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        name, analysis_id, input_set_id = sys.argv[3], sys.argv[4], sys.argv[5]
        print(add_project(name, analysis_id, input_set_id, Session()))

    elif len(sys.argv) >= 3 and sys.argv[1] == 'add-project-ex':
        if len(sys.argv) < 9:
            raise ValueError('add-project-ex requires 9 or more arguments')
        with open(sys.argv[2]) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        name, analysis_name, analysis_image_url = sys.argv[3], sys.argv[4], sys.argv[5]
        input_set_name, input_set_csv = sys.argv[6], sys.argv[7]
        cluster_analyses = parse_cluster_analyses(sys.argv[8:])
        print(add_project_ex(name, analysis_name, analysis_image_url,
                             input_set_name, input_set_csv, cluster_analyses,
                             Session()))

    else:
        print_usage()
        sys.exit(1)

