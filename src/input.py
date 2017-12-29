#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, DateTime, Table
from base import Base
from sqlalchemy.orm import relationship


class Input(Base):
    """
    An input sample.  Initial location of raw data is specified with urls.
    This needs to specify enough info so that the analysis can download all the
    needed input data and the right tools can be run, in the right modes.
    """
    __tablename__ = 'input'

    id = Column(Integer, Sequence('input_id_seq'), primary_key=True)
    url_1 = Column(String(1024))  # URL where obtained
    url_2 = Column(String(1024))
    url_3 = Column(String(1024))
    checksum_1 = Column(String(256))
    checksum_2 = Column(String(256))
    checksum_3 = Column(String(256))
    retrieval_method = Column(String(64))


# Creates many-to-many association between Annotations and AnnotationSets
input_association_table = Table('input_set_association', Base.metadata,
    Column('input_id', Integer, ForeignKey('input.id')),
    Column('input_set_id', Integer, ForeignKey('input_set.id'))
)


class InputSet(Base):
    """
    For gathering many sources under a single key.
    """
    __tablename__ = 'input_set'

    id = Column(Integer, Sequence('input_set_id_seq'), primary_key=True)
    inputs = relationship("Input", secondary=input_association_table)


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
        lambda_reads_1_md5 = '8f4a7d568d2e930922e25c9d6e1b482f'
        lambda_reads_2 = 'http://www.cs.jhu.edu/~langmea/resources/reads_2.fq'
        lambda_reads_2_md5 = '899e197478a235b2fd29d8501aea4104'
        longreads = 'longreads.fq'
        longreads_md5 = '076b0e9f81aa599043b9e4be204a8014'

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
                d1 = Input(retrieval_method='url', url_1=lambda_reads_1, url_2=lambda_reads_2)
                self.assertEqual(0, len(list(self.session.query(Input))))
                self.session.add(d1)
                self.session.commit()
                inputs = list(self.session.query(Input))
                self.assertEqual(1, len(inputs))
                self.assertEqual(lambda_reads_1, inputs[0].url_1)
                self.assertEqual(lambda_reads_2, inputs[0].url_2)
                self.session.delete(d1)
                self.session.commit()
                self.assertEqual(0, len(list(self.session.query(Input))))

            def test_simple_inputset_insert(self):
                inp1 = Input(retrieval_method="url",
                             url_1=lambda_reads_1, checksum_1=lambda_reads_1_md5,
                             url_2=lambda_reads_2, checksum_2=lambda_reads_2_md5)
                inp2 = Input(retrieval_method="url", url_1=longreads, checksum_1=longreads_md5)
                inp3 = Input(retrieval_method="url", url_1=lambda_reads_2, checksum_1=lambda_reads_2_md5)

                # add inputs
                self.assertEqual(0, len(list(self.session.query(Input))))
                self.assertEqual(0, len(list(self.session.query(InputSet))))
                self.session.add(inp1)
                self.session.add(inp2)
                self.session.add(inp3)
                self.session.commit()
                self.assertEqual(3, len(list(self.session.query(Input))))
                srcs = list(self.session.query(Input))

                # add input sets with associations
                self.session.add(InputSet(inputs=[inp1, inp2]))
                self.session.add(InputSet(inputs=[inp1, inp2, inp3]))
                self.session.commit()
                self.assertEqual(2, len(list(self.session.query(InputSet))))
                sss = list(self.session.query(InputSet))
                self.assertEqual(2, len(sss[0].inputs))
                self.assertEqual(3, len(sss[1].inputs))
                self.assertEqual(5, len(list(self.session.query(input_association_table))))

                for obj in srcs + sss:
                    self.session.delete(obj)
                self.assertEqual(0, len(list(self.session.query(Input))))
                self.assertEqual(0, len(list(self.session.query(InputSet))))
                self.assertEqual(0, len(list(self.session.query(input_association_table))))

        sys.argv.remove('--test')
        unittest.main()

