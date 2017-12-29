#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, DateTime, Table
from base import Base


class Analysis(Base):
    __tablename__ = 'analysis'

    id = Column(Integer, Sequence('analysis_id_seq'), primary_key=True)
    container_url = Column(String(4096))


def set_up_bioconda(envname='recount-pump', ):
    """
    This runs on a cluster node and installs all the requisite analysis tools
    in a virtualenv using bioconda.
    """
    pass


def check_bioconda(envname='recount-pump', ):
    """
    This checks whether the requisite tools are (still) installed in a
    virtualenv of the given name.
    """
    pass


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:
        print('''
Usage: analysis.py <cmd> [options]*

Commands:
    test           run unit tests

Options:'''.strip())
        sys.exit(0)

    if sys.argv[1] == 'test':
        import unittest
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        star_container = 'shub://langmead-lab/recount-pump:star'

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
                a1 = Analysis(container_url=star_container)
                self.assertEqual(0, len(list(self.session.query(Analysis))))
                self.session.add(a1)
                self.session.commit()
                self.assertEqual(1, len(list(self.session.query(Analysis))))
                self.session.delete(a1)
                self.session.commit()
                self.assertEqual(0, len(list(self.session.query(Analysis))))


        sys.argv.remove('test')
        unittest.main()

