#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, DateTime, Table
from base import Base
from sqlalchemy.orm import relationship


class Analysis(Base):
    """
    An analysis is embodied simply as a singularity image.  A customized
    companion wrapper script is needed for each cluster where this analysis
    might run.  See ClusterAnalysis for comments on why.
    """
    __tablename__ = 'analysis'

    id = Column(Integer, Sequence('analysis_id_seq'), primary_key=True)
    name = Column(String(1024))
    image_url = Column(String(4096))
    cluster_analysis = relationship("ClusterAnalysis")


class Cluster(Base):
    """
    A cluster has a name which should be the contents of $HOME/cluster.txt on
    all cluster nodes.
    """
    __tablename__ = 'cluster'

    id = Column(Integer, Sequence('cluster_id_seq'), primary_key=True)
    name = Column(String(1024))  # "marcc" or "stampede2" for now
    cluster_analysis = relationship("ClusterAnalysis")


class ClusterAnalysis(Base):
    """
    An analysis is a singularity image, which is self-contained for the
    most part.  However, not every cluster has the same policy for whether/how
    directories outside the contained can be bound to directories inside the
    image.  For that reason, this table associates a wrapper script with
    every cluster/image combination.  The wrapper takes two arguments: a
    job name and an input directory.  Whatever copies and directory bindings
    are necessary to make these work with the image, the wrapper script
    handles it.
    """
    __tablename__ = 'cluster_analysis'

    id = Column(Integer, Sequence('cluster_analysis_id_seq'), primary_key=True)
    analysis_id = Column(Integer, ForeignKey('analysis.id'))
    cluster_id = Column(Integer, ForeignKey('cluster.id'))
    wrapper_url = Column(String(4096))  # image wrapper


def add_cluster(name, session):
    """
    Add new cluster with given name
    """
    c = Cluster(name=name)
    session.add(c)
    session.commit()
    return c.id


def add_analysis(name, image_url, session):
    """
    Add new cluster with given name
    """
    a = Analysis(name=name, image_url=image_url)
    session.add(a)
    session.commit()
    return a.id


def add_cluster_analysis(cluster_id, analysis_id, wrapper_url, session):
    """
    Add new wrapper script for given cluster and analysis 
    """
    ca = ClusterAnalysis(analysis_id=analysis_id, cluster_id=cluster_id,
                         wrapper_url=wrapper_url)
    session.add(ca)
    session.commit()
    return ca.id


if __name__ == '__main__':
    import sys
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    usage_msg = '''
Usage: analysis.py <cmd> [options]*

Commands:

    add-cluster <engine_url> <name>
    add-analysis <engine_url> <name> <image_url>
    add-cluster-analysis <engine_url> <cluster_id> <analysis_id> <wrapper_url>
    help
    test'''

    def print_usage():
        print('\n' + usage_msg.strip() + '\n')

    if len(sys.argv) <= 1 or sys.argv[1] == 'help':
        print_usage()
        sys.exit(0)

    if sys.argv[1] == 'test':
        import unittest

        def _setup():
            engine = create_engine('sqlite:///:memory:', echo=True)
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            return Session()

        class TestAnalysis(unittest.TestCase):

            def setUp(self):
                self.session = _setup()

            def tearDown(self):
                self.session.close()

            def test_analysis1(self):
                a1 = Analysis(name='recount-rna-seq-v1',
                              image_url='s3://recount-pump/analysis/recount-rna-seq-v1.img')
                self.assertEqual(0, len(list(self.session.query(Analysis))))
                self.session.add(a1)
                self.session.commit()
                self.assertEqual(1, len(list(self.session.query(Analysis))))
                cluster_name = 'stampede2'
                c1 = Cluster(name=cluster_name)
                self.assertEqual(0, len(list(self.session.query(Cluster))))
                self.session.add(c1)
                self.session.commit()
                self.assertEqual(1, len(list(self.session.query(Cluster))))
                ca1 = ClusterAnalysis(analysis_id=a1.id, cluster_id=c1.id,
                                      wrapper_url='s3://recount-pump/analysis/recount-rna-seq-v1/cluster/' + cluster_name + '.sh')
                self.assertEqual(0, len(list(self.session.query(ClusterAnalysis))))
                self.session.add(ca1)
                self.session.commit()
                self.assertEqual(1, len(list(self.session.query(ClusterAnalysis))))

                self.session.delete(ca1)
                self.session.delete(a1)
                self.session.delete(c1)
                self.session.commit()
                self.assertEqual(0, len(list(self.session.query(Analysis))))
                self.assertEqual(0, len(list(self.session.query(Cluster))))
                self.assertEqual(0, len(list(self.session.query(ClusterAnalysis))))


        sys.argv.remove('test')
        unittest.main()

    elif len(sys.argv) >= 3 and sys.argv[2] == 'add-cluster':
        engine_url = sys.argv[1]
        engine = create_engine(engine_url, echo=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        if len(sys.argv) < 4:
            raise ValueError('add-cluster requires 1 argument')

        name = sys.argv[3]
        print(add_cluster(name, Session()))

    elif len(sys.argv) >= 3 and sys.argv[2] == 'add-analysis':
        engine_url = sys.argv[1]
        engine = create_engine(engine_url, echo=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        if len(sys.argv) < 5:
            raise ValueError('add-analysis requires 2 arguments')

        name, image_url = sys.argv[3], sys.argv[4]
        print(add_analysis(name, image_url, Session()))

    elif len(sys.argv) >= 3 and sys.argv[2] == 'add-cluster-analysis':
        engine_url = sys.argv[1]
        engine = create_engine(engine_url, echo=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        if len(sys.argv) < 6:
            raise ValueError('add-cluster-analysis requires 3 arguments')

        cluster_id, analysis_id, wrapper_url = sys.argv[3], sys.argv[4], sys.argv[5]
        print(add_cluster_analysis(cluster_id, analysis_id, wrapper_url, Session()))

    else:
        print_usage()
        sys.exit(1)
