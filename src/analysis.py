#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""analysis

Usage:
  analysis add-analysis [options] <name> <image-url>

Options:
  --db-ini <ini>           Database ini file [default: ~/.recount/db.ini].
  --db-section <section>   ini file section for database [default: client].
  --log-ini <ini>          ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>      set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  -h, --help               Show this screen.
  --version                Show version.
"""


from __future__ import print_function
import os
import log
import pytest
from docopt import docopt
from sqlalchemy import Column, Integer, String, Sequence
from base import Base
from toolbox import session_maker_from_config


class Analysis(Base):
    """
    An analysis is embodied simply as a singularity image.
    """
    __tablename__ = 'analysis'

    id = Column(Integer, Sequence('analysis_id_seq'), primary_key=True)
    name = Column(String(1024))
    image_url = Column(String(4096))

    def deepdict(self, session):
        d = self.__dict__.copy()
        del d['_sa_instance_state']
        return d

    def to_job_string(self):
        """
        Return the string that should represent this analysis in a queued job.
        """
        return self.image_url


def add_analysis(name, image_url, session):
    """
    Add new analysis with given name
    """
    a = Analysis(name=name, image_url=image_url)
    session.add(a)
    session.commit()
    return a.id


def test_integration(db_integration):
    if not db_integration:
        pytest.skip('db integration testing disabled')


def test_analysis1(session):
    analysis_name = 'recount-rna-seq-v1'
    image_url = 's3://recount-pump/analysis/recount-rna-seq-v1.img'

    a1 = Analysis(name=analysis_name, image_url=image_url)
    assert 0 == len(list(session.query(Analysis)))
    session.add(a1)
    session.commit()
    assert 1 == len(list(session.query(Analysis)))

    session.delete(a1)
    session.commit()
    assert 0 == len(list(session.query(Analysis)))


if __name__ == '__main__':
    args = docopt(__doc__)
    log_ini = os.path.expanduser(args['--log-ini'])
    log.init_logger(log.LOG_GROUP_NAME, log_ini=log_ini, agg_level=args['--log-level'])
    log.init_logger('sqlalchemy', log_ini=log_ini, agg_level=args['--log-level'],
                    sender='sqlalchemy')
    try:
        db_ini = os.path.expanduser(args['--db-ini'])
        if args['add-analysis']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_analysis(args['<name>'], args['<image-url>'], Session()))
    except Exception:
        log.error('Uncaught exception:', 'analysis.py')
        raise
