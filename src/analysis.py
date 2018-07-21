#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""analysis

Usage:
  analysis add-cluster [options] <name>
  analysis add-analysis [options] <name> <image-url>
  analysis add-cluster-analysis [options] <cluster-id> <analysis-id> <wrapper-url>
  analysis add-analysis-ex [options] <name> <image-url> (<cluster-name> <wrapper-url>)...

Options:
  --db-ini <ini>           Database ini file [default: ~/.recount/db.ini].
  --db-section <section>   ini file section for database [default: client].
  --log-ini <ini>          ini file for log aggregator [default: ~/.recount/log.ini].
  --log-section <section>  ini file section for log aggregator [default: log].
  --log-level <level>      set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  -a, --aggregate          enable log aggregation.
  -h, --help               Show this screen.
  --version                Show version.
"""


from __future__ import print_function
import os
import log
import pytest
from docopt import docopt
from sqlalchemy import Column, ForeignKey, Integer, String, Sequence
from base import Base
from sqlalchemy.orm import relationship
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

    def deepdict(self, session):
        d = self.__dict__.copy()
        del d['_sa_instance_state']
        return d


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


def add_analysis_ex(name, image_url, cluster_names, wrapper_urls, session):
    """
    Add an Analysis along with a list of ClusterAnalysis's.  Add new Cluster
    objects as needed.
    """
    analysis_id = add_analysis(name, image_url, session)
    n_added_cluster = 0
    n_added_cluster_analysis = 0
    for cluster_name, wrapper in zip(cluster_names, wrapper_urls):
        cluster = session.query(Cluster).filter_by(name=cluster_name).first()
        if cluster is None:
            cluster_id = add_cluster(cluster_name, session)
            n_added_cluster += 1
        else:
            cluster_id = cluster.id
        add_cluster_analysis(cluster_id, analysis_id, wrapper, session)
        n_added_cluster_analysis += 1
    return analysis_id, n_added_cluster, n_added_cluster_analysis


def test_integration(db_integration):
    if not db_integration:
        pytest.skip('db integration testing disabled')


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
    cluster_names = ['stampede2', 'marcc']
    wrapper_urls = ['s3://recount-pump/analysis/recount-rna-seq-v1/stampede2.sh',
                    's3://recount-pump/analysis/recount-rna-seq-v1/marcc.sh']
    analysis_id, n_added_cluster, n_added_cluster_analysis = \
        add_analysis_ex(analysis_name, image_url,
                        cluster_names, wrapper_urls, session)
    assert 2 == n_added_cluster
    assert 2 == n_added_cluster_analysis
    assert 1 == len(list(session.query(Analysis)))
    assert 2 == len(list(session.query(Cluster)))
    assert 2 == len(list(session.query(ClusterAnalysis)))
    analysis_name2 = 'recount-rna-seq-v2'
    image_url2 = 's3://recount-pump/analysis/recount-rna-seq-v2.img'
    cluster_names2 = ['stampede2', 'hhpc']
    wrapper_urls2 = ['s3://recount-pump/analysis/recount-rna-seq-v1/stampede3.sh',
                     's3://recount-pump/analysis/recount-rna-seq-v1/hhpc.sh']
    analysis_id2, n_added_cluster2, n_added_cluster_analysis2 = \
        add_analysis_ex(analysis_name2, image_url2,
                        cluster_names2, wrapper_urls2, session)
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
    args = docopt(__doc__)
    agg_ini = os.path.expanduser(args['--log-ini']) if args['--aggregate'] else None
    log.init_logger(__name__, aggregation_ini=agg_ini,
                     aggregation_section=args['--log-section'],
                     agg_level=args['--log-level'])
    log.init_logger('sqlalchemy', aggregation_ini=agg_ini,
                     aggregation_section=args['--log-section'],
                     agg_level=args['--log-level'],
                     sender='sqlalchemy')
    try:
        db_ini = os.path.expanduser(args['--db-ini'])
        if args['add-cluster']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_cluster(args['<name>'], Session()))
        elif args['add-analysis']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_analysis(args['<name>'], args['<image-url>'], Session()))
        elif args['add-cluster-analysis']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_cluster_analysis(args['<cluster-id>'], args['<analysis-id>'],
                                       args['<wrapper-url>'], Session()))
        elif args['add-analysis-ex']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            analysis_id, n_added_cluster, n_added_cluster_analysis = \
                add_analysis_ex(args['<name>'], args['<image-url>'],
                                args['<cluster-name>'], args['<wrapper-url>'],
                                Session())
            print(analysis_id)
    except Exception:
        log.error(__name__, 'Uncaught exception:', 'analysis.py')
        raise
