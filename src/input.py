#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, DateTime, Table
from base import Base


class Input(Base):
    """
    An input sample.  Initial location of raw data is specified with urls.
    This needs to specify enough info so that the analysis can download all the
    needed input data and the right tools can be run, in the right modes.
    """
    __tablename__ = 'input'

    id = Column(Integer, Sequence('input_id_seq'), primary_key=True)
    url_1 = Column(String(1024))
    url_2 = Column(String(1024))
    url_3 = Column(String(1024))
    retrieval_method = Column(String(64))


def retrieve(input_id, session, toolbox, retries=0, timeout=None):
    inp = list(session.query(Input).filter_by(id=input_id))
    if len(inp) == 0:
        raise KeyError('No input record with id %d' % input_id)
    if len(inp) > 1:
        raise RuntimeError('Multiple input records with id %d' % input_id)
    inp = inp[0]
    if inp.retrieval_method == 'url':
        toolbox.need_one_of('curl', 'wget')
    elif inp.retrieval_method == 'sra':
        toolbox.need_all_of('prefetch', 'fastq-dump')
    else:
        raise ValueError('Unknown retrieval method: "%s"' % inp.retrieval_method)


def install_retriever():
    pass


if __name__ == '__main__':
    import sys

    if '--test' in sys.argv:
        import unittest
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        lambda_reads_1 = 'http://www.cs.jhu.edu/~langmea/resources/reads_1.fq'
        lambda_reads_2 = 'http://www.cs.jhu.edu/~langmea/resources/reads_2.fq'

        def _setup():
            engine = create_engine('sqlite:///:memory:', echo=True)
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            return Session()


        class TestReference(unittest.TestCase):

            def setUp(self):
                self.session = _setup()

            def tearDown(self):
                self.session.close()

            def test_simple_source_insert(self):
                d1 = Input(retrieval_method='url', url1=lambda_reads_1, url2=lambda_reads_2)
                self.assertEqual(0, len(list(self.session.query(Input))))
                self.session.add(d1)
                self.session.commit()
                inputs = list(self.session.query(Input))
                self.assertEqual(1, len(inputs))
                self.assertEqual(lambda_reads_1, inputs[0].url_1)
                self.assertEqual(lambda_reads_1, inputs[0].url_2)
                self.session.delete(d1)
                self.session.commit()
                self.assertEqual(0, len(list(self.session.query(Input))))

        sys.argv.remove('--test')
        unittest.main()

