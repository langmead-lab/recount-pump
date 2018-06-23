#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

import unittest

import sys
import pytest
from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, create_engine
from base import Base
from sqlalchemy.orm import relationship, Session
from toolbox import session_maker_from_config


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
    A cluster has a name which should be the contents of
    $HOME/.recount/cluster.txt on all cluster nodes.
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


def add_analysis_ex(name, image_url, cluster_analyses, session):
    """
    Add an Analysis along with a list of ClusterAnalysis's.  Add new Cluster
    objects as needed.
    """
    analysis_id = add_analysis(name, image_url, session)
    n_added_cluster = 0
    n_added_cluster_analysis = 0
    for cluster_name, wrapper in cluster_analyses:
        cluster = session.query(Cluster).filter_by(name=cluster_name).first()
        if cluster is None:
            cluster_id = add_cluster(cluster_name, session)
            n_added_cluster += 1
        else:
            cluster_id = cluster.id
        add_cluster_analysis(cluster_id, analysis_id, wrapper, session)
        n_added_cluster_analysis += 1
    return analysis_id, n_added_cluster, n_added_cluster_analysis


def parse_cluster_analyses(pairs):
    """
    Parse cluster analyses formatted like <cluster_name1>:<wrapper_url1>
    <cluster_name2>:<wrapper_url2>, ...
    """
    ret = []
    for pair in pairs:
        toks = pair.split(':', 1)
        if len(toks) < 2:
            raise ValueError('Expected <cluster_name>:<wrapper_url> pair, got "%s"' % pair)
        ret.append((toks[0], toks[1]))
    return ret


@pytest.fixture(scope='session')
def engine():
    return create_engine('sqlite:///:memory:')


@pytest.yield_fixture(scope='session')
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.yield_fixture
def session(engine, tables):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""
    connection = engine.connect()
    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction
    my_session = Session(bind=connection)

    yield my_session

    my_session.close()
    # roll back the broader transaction
    transaction.rollback()
    # put back the connection to the connection pool
    connection.close()


def test_analysis1(session):
    analysis_name = 'recount-rna-seq-v1'
    image_url = 's3://recount-pump/analysis/recount-rna-seq-v1.img'
    wrapper_url = 's3://recount-pump/analysis/recount-rna-seq-v1/cluster/'
    cluster_name = 'stampede2'

    a1 = Analysis(name=analysis_name, image_url=image_url)
    assert 0 == len(list(session.query(Analysis)))
    session.add(a1)
    session.commit()
    assert 1 == len(list(session.query(Analysis)))
    c1 = Cluster(name=cluster_name)
    assert 0 == len(list(session.query(Cluster)))
    session.add(c1)
    session.commit()
    assert 1 == len(list(session.query(Cluster)))
    ca1 = ClusterAnalysis(analysis_id=a1.id, cluster_id=c1.id,
                          wrapper_url=wrapper_url + cluster_name + '.sh')
    assert 0 == len(list(session.query(ClusterAnalysis)))
    session.add(ca1)
    session.commit()
    assert 1 == len(list(session.query(ClusterAnalysis)))

    session.delete(ca1)
    session.delete(a1)
    session.delete(c1)
    session.commit()
    assert 0 == len(list(session.query(Analysis)))
    assert 0 == len(list(session.query(Cluster)))
    assert 0 == len(list(session.query(ClusterAnalysis)))


def test_add_analysis_ex(session):
    analysis_name = 'recount-rna-seq-v1'
    image_url = 's3://recount-pump/analysis/recount-rna-seq-v1.img'
    cluster_analyses1 = [
        ('stampede2', 's3://recount-pump/analysis/recount-rna-seq-v1/stampede2.sh'),
        ('marcc', 's3://recount-pump/analysis/recount-rna-seq-v1/marcc.sh')
    ]
    analysis_id, n_added_cluster, n_added_cluster_analysis = \
        add_analysis_ex(analysis_name, image_url,
                        cluster_analyses1, session)
    assert 2 == n_added_cluster
    assert 2 == n_added_cluster_analysis
    assert 1 == len(list(session.query(Analysis)))
    assert 2 == len(list(session.query(Cluster)))
    assert 2 == len(list(session.query(ClusterAnalysis)))
    analysis_name2 = 'recount-rna-seq-v2'
    image_url2 = 's3://recount-pump/analysis/recount-rna-seq-v2.img'
    cluster_analyses2 = [
        ('stampede2', 's3://recount-pump/analysis/recount-rna-seq-v1/stampede3.sh'),
        ('hhpc', 's3://recount-pump/analysis/recount-rna-seq-v1/hhpc.sh')
    ]
    analysis_id2, n_added_cluster2, n_added_cluster_analysis2 = \
        add_analysis_ex(analysis_name2, image_url2,
                        cluster_analyses2, session)
    assert 1 == n_added_cluster2
    assert 2 == n_added_cluster_analysis2
    assert 2 == len(list(session.query(Analysis)))
    assert 3 == len(list(session.query(Cluster)))
    assert 4 == len(list(session.query(ClusterAnalysis)))
    session.query(ClusterAnalysis).delete()
    session.query(Cluster).delete()
    session.query(Analysis).delete()
    assert 0 == len(list(session.query(Analysis)))
    assert 0 == len(list(session.query(Cluster)))
    assert 0 == len(list(session.query(ClusterAnalysis)))


if __name__ == '__main__':
    usage_msg = '''
Usage: analysis.py <cmd> [options]*

Commands:

    add-cluster <db_config> <name>
    add-analysis <db_config> <name> <image_url>
    add-cluster-analysis <db_config> <cluster_id> <analysis_id> <wrapper_url>
    add-analysis-ex <db_config> <name> <image_url> <cluster_name1>:<wrapper_url1> <cluster_name2>:<wrapper_url2>, ...
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
        sys.argv.remove('test')
        unittest.main()

    elif len(sys.argv) >= 3 and sys.argv[1] == 'add-cluster':
        if len(sys.argv) < 4:
            raise ValueError('add-cluster requires 1 argument')
        with open(sys.argv[2]) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        name = sys.argv[3]
        print(add_cluster(name, Session()))

    elif len(sys.argv) >= 3 and sys.argv[1] == 'add-analysis':
        if len(sys.argv) < 5:
            raise ValueError('add-analysis requires 2 arguments')
        with open(sys.argv[2]) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        name, image_url = sys.argv[3], sys.argv[4]
        print(add_analysis(name, image_url, Session()))

    elif len(sys.argv) >= 3 and sys.argv[1] == 'add-cluster-analysis':
        if len(sys.argv) < 6:
            raise ValueError('add-cluster-analysis requires 3 arguments')
        with open(sys.argv[2]) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        cluster_id, analysis_id, wrapper_url = sys.argv[3], sys.argv[4], sys.argv[5]
        print(add_cluster_analysis(cluster_id, analysis_id, wrapper_url, Session()))

    elif len(sys.argv) >= 3 and sys.argv[1] == 'add-analysis-ex':
        if len(sys.argv) < 6:
            raise ValueError('add-cluster-analysis requires 4 arguments')
        with open(sys.argv[2]) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        name, image_url = sys.argv[3], sys.argv[4]
        cluster_analyses = parse_cluster_analyses(sys.argv[5:])
        print(add_analysis_ex(name, image_url, cluster_analyses, Session()))

    else:
        print_usage()
        sys.exit(1)

