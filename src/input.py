#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

from __future__ import print_function
from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, DateTime, Table
from base import Base
from sqlalchemy.orm import relationship
from toolbox import session_maker_from_config


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
    name = Column(String(1024))
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


def add_input(url_1, url_2, url_3, checksum_1, checksum_2, checksum_3, retrieval_method, session):
    """
    Add new input with associated retrieval info.
    """
    i = Input(url_1=url_1, url_2=url_2, url_3=url_3,
              checksum_1=checksum_1, checksum_2=checksum_2, checksum_3=checksum_3,
              retrieval_method=retrieval_method)
    session.add(i)
    session.commit()
    return i.id


def add_input_set(name, session):
    """
    Add new input set with given name.  It's empty at first.  Needs to be
    populated with, e.g., add-input-to-set.
    """
    iset = InputSet(name=name)
    session.add(iset)
    session.commit()
    return iset.id


def add_input_to_set(set_id, input_id, session):
    """
    Add input to input set.
    """
    input = session.query(Input).get(input_id)
    input_set = session.query(InputSet).get(set_id)
    input_set.inputs.append(input)
    session.commit()


def import_input_set(name, csv_fn, session):
    """
    Import all the entries from the CSV file into a new InputSet of the given
    name.
    """
    input_set = InputSet(name=name)
    n_added_input = 0
    with open(csv_fn, 'r') as csv_fh:
        for ln in csv_fh:
            ln = ln.rstrip()
            if len(ln) == 0:
                continue
            toks = ln.split(',')
            if len(toks) != 7:
                raise ValueError('Line did not have 7 tokens: "%s"' % ln)
            toks = list(map(lambda x: None if x == 'NA' else x, toks))
            url_1, url_2, url_3, checksum_1, checksum_2, checksum_3, retrieval_method = toks
            input = Input(url_1=url_1, url_2=url_2, url_3=url_3,
                          checksum_1=checksum_1, checksum_2=checksum_2, checksum_3=checksum_3,
                          retrieval_method=retrieval_method)
            session.add(input)
            input_set.inputs.append(input)
            n_added_input += 1
    session.add(input_set)
    session.commit()
    return input_set.id, n_added_input


if __name__ == '__main__':
    import sys

    usage_msg = '''
Usage: input.py <cmd> [options]*

Commands:

    add-input <db_config> <url_1> <url_2> <url_3> <checksum_1> <checksum_2> <checksum_3> <retrieval_method>
    add-input-set <db_config> <name>
    add-input-to-set <db_config> <set_id> <input_id>
    import-input-set <db_config> <name> <csv>
    help
    test
'''

    def print_usage():
        print('\n' + usage_msg.strip() + '\n')

    if len(sys.argv) <= 1 or sys.argv[1] == 'help':
        print_usage()
        sys.exit(0)

    if sys.argv[1] == 'test':
        import unittest
        import os
        from sqlalchemy import create_engine, MetaData
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

            def test_import_inputset(self):
                csv_text = '''ftp://genomi.cs/1.fastq.gz,ftp://genomi.cs/2.fastq.gz,NA,NA,NA,NA,wget'''
                with open('.tmp.csv', 'w') as ofh:
                    ofh.write(csv_text)
                import_input_set('test_inputset', '.tmp.csv', self.session)
                inputs, input_sets, input_assocs = list(self.session.query(Input)),\
                                                   list(self.session.query(InputSet)),\
                                                   list(self.session.query(input_association_table))

                self.assertEqual(1, len(inputs))
                self.assertEqual(1, len(input_sets))
                self.assertEqual(1, len(input_assocs))
                #self.session.query(input_association_table).delete()
                self.session.query(Input).delete()
                self.session.query(InputSet).delete()
                self.assertEqual(0, len(list(self.session.query(Input))))
                self.assertEqual(0, len(list(self.session.query(InputSet))))
                #self.assertEqual(0, len(list(self.session.query(input_association_table))))

                # BTL: I can't easily figure out how to delete the entries in the association table

                os.remove('.tmp.csv')

        sys.argv.remove('test')
        unittest.main()

    elif len(sys.argv) >= 3 and sys.argv[1] == 'add-input':
        if len(sys.argv) < 10:
            raise ValueError('add-input requires 8 arguments')
        with open(sys.argv[2]) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        url_1, url_2, url_3 = sys.argv[3:6]
        checksum_1, checksum_2, checksum_3 = sys.argv[6:9]
        retrieval_method = sys.argv[9]
        print(add_input(url_1, url_2, url_3,
                        checksum_1, checksum_2, checksum_3,
                        retrieval_method, Session()))

    elif len(sys.argv) >= 3 and sys.argv[1] == 'add-input-set':
        if len(sys.argv) < 4:
            raise ValueError('add-input-set requires 1 argument')
        with open(sys.argv[2]) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        name = sys.argv[3]
        print(add_input_set(name, Session()))

    elif len(sys.argv) >= 3 and sys.argv[1] == 'add-input-to-set':
        if len(sys.argv) < 5:
            raise ValueError('add-input-set requires 2 arguments')
        with open(sys.argv[2]) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        set_id, input_id = sys.argv[3], sys.argv[4]
        set_id, input_id = int(set_id), int(input_id)
        print(add_input_to_set(set_id, input_id, Session()))

    elif len(sys.argv) >= 3 and sys.argv[1] == 'import-input-set':
        if len(sys.argv) < 5:
            raise ValueError('import-input-set requires 2 arguments')
        with open(sys.argv[2]) as cfg_gh:
            Session = session_maker_from_config(cfg_gh)
        name, csv_fn = sys.argv[3], sys.argv[4]
        input_set_id, n_added_input = import_input_set(name, csv_fn, Session())
        print('%d %d' % (input_set_id, n_added_input))

    else:
        print_usage()
        sys.exit(1)
