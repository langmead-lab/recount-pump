#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""input

Usage:
  input add-input <db-config> <url-1> <url-2> <url-3>
                 <checksum-1> <checksum-2> <checksum-3>
                 <retrieval-method>
  input add-input-set <db-config> <name>
  input add-inputs-to-set <db-config> (<set-id> <input-id>)...
  input filter-table <db-config> <prefix> <species> <sql-filter>
  input inputs-from-table <db-config> <prefix> <species> <sql-filter>
  input test

Options:
  -h, --help    Show this screen.
  --version     Show version.
"""

from __future__ import print_function
import os
import sys
import unittest
from docopt import docopt
from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, Table, create_engine
from base import Base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import text
from toolbox import session_maker_from_config


class Input(Base):
    """
    An input sample.  Initial location of raw data is specified with urls.
    This needs to specify enough info so that the analysis can download all the
    needed input data and the right tools can be run, in the right modes.
    """
    __tablename__ = 'input'

    id = Column(Integer, Sequence('input_id_seq'), primary_key=True)
    acc_r = Column(String(64))        # run accession
    acc_s = Column(String(64))        # study accession
    url_1 = Column(String(1024))      # URL for sample, or for just mate 1
    url_2 = Column(String(1024))      # URL for mate 2
    url_3 = Column(String(1024))      # unlikely to be used; maybe for barcode?
    checksum_1 = Column(String(256))  # checksum for file at url_1
    checksum_2 = Column(String(256))  # checksum for file at url_2
    checksum_3 = Column(String(256))  # checksum for file at url_3
    retrieval_method = Column(String(64))  # suggested retrieval method


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


def add_input(acc_r, acc_s, url_1, url_2, url_3, checksum_1, checksum_2, checksum_3, retrieval_method, session):
    """
    Add new input with associated retrieval info.
    """
    i = Input(acc_r=acc_r, acc_s=acc_s, url_1=url_1, url_2=url_2, url_3=url_3,
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


def add_inputs_to_set(set_ids, input_ids, session):
    """
    Add inputs to input set.
    """
    for input_id, set_id in zip(set_ids, input_ids):
        inp = session.query(Input).get(input_id)
        input_set = session.query(InputSet).get(set_id)
        input_set.inputs.append(inp)
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
            if len(toks) != 9:
                raise ValueError('Line did not have 9 tokens: "%s"' % ln)
            toks = list(map(lambda x: None if x == 'NA' else x, toks))
            acc_r, acc_s, url_1, url_2, url_3, checksum_1, checksum_2, checksum_3, retrieval_method = toks
            input = Input(acc_r=acc_r, acc_s=acc_s, url_1=url_1, url_2=url_2, url_3=url_3,
                          checksum_1=checksum_1, checksum_2=checksum_2, checksum_3=checksum_3,
                          retrieval_method=retrieval_method)
            session.add(input)
            input_set.inputs.append(input)
            n_added_input += 1
    session.add(input_set)
    session.commit()
    return input_set.id, n_added_input


def _fetcher(prefix, species, sql_filter, session):
    table_name = '_'.join([prefix, species])
    sql = "SELECT run_accession, study_accession FROM %s" % table_name
    if sql_filter is not None and len(sql_filter) > 0:
        sql += ' WHERE ' + sql_filter
    sql += ';'
    return session.execute(text(sql)).fetchall()


def filter_table(prefix, species, sql_filter, session):
    for tup in _fetcher(prefix, species, sql_filter, session):
        run_acc, study_acc = tup
        print('%s,%s' % (run_acc, study_acc))
    return 'DONE'


def inputs_from_table(prefix, species, sql_filter, session):
    for tup in _fetcher(prefix, species, sql_filter, session):
        run_acc, study_acc = tup
        inp = Input(acc_r=run_acc, acc_s=study_acc,
                    url_1=None, url_2=None, url_3=None,
                    checksum_1=None, checksum_2=None, checksum_3=None,
                    retrieval_method='sra')
        session.add(inp)
    session.commit()
    return 'DONE'


_lambda_reads_1 = 'http://www.cs.jhu.edu/~langmea/resources/reads_1.fq'
_lambda_reads_1_md5 = '8f4a7d568d2e930922e25c9d6e1b482f'
_lambda_reads_2 = 'http://www.cs.jhu.edu/~langmea/resources/reads_2.fq'
_lambda_reads_2_md5 = '899e197478a235b2fd29d8501aea4104'
_longreads = 'longreads.fq'
_longreads_md5 = '076b0e9f81aa599043b9e4be204a8014'


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
        d1 = Input(retrieval_method='url', url_1=_lambda_reads_1, url_2=_lambda_reads_2)
        self.assertEqual(0, len(list(self.session.query(Input))))
        self.session.add(d1)
        self.session.commit()
        inputs = list(self.session.query(Input))
        self.assertEqual(1, len(inputs))
        self.assertEqual(_lambda_reads_1, inputs[0].url_1)
        self.assertEqual(_lambda_reads_2, inputs[0].url_2)
        self.session.delete(d1)
        self.session.commit()
        self.assertEqual(0, len(list(self.session.query(Input))))

    def test_simple_inputset_insert(self):
        inp1 = Input(retrieval_method="url",
                     url_1=_lambda_reads_1, checksum_1=_lambda_reads_1_md5,
                     url_2=_lambda_reads_2, checksum_2=_lambda_reads_2_md5)
        inp2 = Input(retrieval_method="url", url_1=_longreads, checksum_1=_longreads_md5)
        inp3 = Input(retrieval_method="url", url_1=_lambda_reads_2, checksum_1=_lambda_reads_2_md5)

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
        csv_text = '''NA,NA,ftp://genomi.cs/1.fastq.gz,ftp://genomi.cs/2.fastq.gz,NA,NA,NA,NA,wget'''
        with open('.tmp.csv', 'w') as ofh:
            ofh.write(csv_text)
        import_input_set('test_inputset', '.tmp.csv', self.session)
        inputs, input_sets, input_assocs = list(self.session.query(Input)), \
                                           list(self.session.query(InputSet)), \
                                           list(self.session.query(input_association_table))

        self.assertEqual(1, len(inputs))
        self.assertEqual(1, len(input_sets))
        self.assertEqual(1, len(input_assocs))
        # self.session.query(input_association_table).delete()
        self.session.query(Input).delete()
        self.session.query(InputSet).delete()
        self.assertEqual(0, len(list(self.session.query(Input))))
        self.assertEqual(0, len(list(self.session.query(InputSet))))
        # self.assertEqual(0, len(list(self.session.query(input_association_table))))

        # BTL: I can't easily figure out how to delete the entries in the association table

        os.remove('.tmp.csv')


if __name__ == '__main__':
    args = docopt(__doc__)
    if args['add-input']:
        Session = session_maker_from_config(args['<db-config>'])
        print(add_input(args['<url-1>'], args['<url-2>'], args['<url-3>'],
                        args['<checksum-1>'], args['<checksum-2>'], args['<checksum-3>'],
                        args['<retrieval-method>'], Session()))
    elif args['add-input-set']:
        Session = session_maker_from_config(args['<db-config>'])
        print(add_input_set(args['<name>'], Session()))
    elif args['add-inputs-to-set']:
        Session = session_maker_from_config(args['<db-config>'])
        print(add_inputs_to_set(args['<set-id>'], args['<input-id>'], Session()))
    elif args['filter-table']:
        Session = session_maker_from_config(args['<db-config>'])
        print(filter_table(args['<prefix>'], args['<species>'], args['<sql-filter>'], Session()))
    elif args['inputs-from-table']:
        Session = session_maker_from_config(args['<db-config>'])
        print(filter_table(args['<prefix>'], args['<species>'], args['<sql-filter>'], Session()))
    elif args['test']:
        sys.argv.remove('test')
        unittest.main()
