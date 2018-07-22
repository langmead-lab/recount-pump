#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""input

Usage:
  input add-input [options] <acc-r> <acc-s>
                  <url-1> <url-2> <url-3>
                  <checksum-1> <checksum-2> <checksum-3>
                  <retrieval-method>
  input add-input-set [options] <name>
  input add-inputs-to-set [options] (<set-id> <input-id>)...
  input list-input-set [options] <name>
  input filter-table [options] <prefix> <species> <sql-filter>
  input inputs-from-table [options] <prefix> <species>
                          <sql-filter> <input-set-name>

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
from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, Table
from sqlalchemy.orm import relationship
from base import Base
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

    def __repr__(self):
        return ','.join(map(str, [self.id, self.acc_r, self.acc_s, self.url_1, self.url_2, self.url_3,
                                  self.checksum_1, self.checksum_2, self.checksum_3,
                                  self.retrieval_method]))

    def to_job_string(self):
        """
        Return the string that should represent this input in a queued job.
        It should be enough information so that any cluster that obtains the
        job knows how to obtain the input.
        """
        return str(self)


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

    def deepdict(self, session):
        d = self.__dict__.copy()
        del d['_sa_instance_state']
        d['inputs'] = []
        for inp in self.inputs:
            d2 = inp.__dict__.copy()
            del d2['_sa_instance_state']
            d['inputs'].append(d2)
        return d


def retrieve(input_id, my_session, toolbox, retries=0, timeout=None):
    inp = list(my_session.query(Input).filter_by(id=input_id))
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


def add_input(acc_r, acc_s, url_1, url_2, url_3,
              checksum_1, checksum_2, checksum_3,
              retrieval_method, my_session):
    """
    Add new input with associated retrieval info.
    """
    i = Input(acc_r=acc_r, acc_s=acc_s, url_1=url_1, url_2=url_2, url_3=url_3,
              checksum_1=checksum_1, checksum_2=checksum_2, checksum_3=checksum_3,
              retrieval_method=retrieval_method)
    my_session.add(i)
    my_session.commit()
    log.info(__name__, 'Added 1 input', 'input.py')
    return i.id


def add_input_set(name, my_session):
    """
    Add new input set with given name.  It's empty at first.  Needs to be
    populated with, e.g., add-input-to-set.
    """
    iset = InputSet(name=name)
    my_session.add(iset)
    my_session.commit()
    log.info(__name__, 'Added input set "%s"' % name, 'input.py')
    return iset.id


def list_input_set(name, my_session):
    """
    Add new input set with given name.  It's empty at first.  Needs to be
    populated with, e.g., add-input-to-set.
    """
    input_set = my_session.query(InputSet).filter_by(name=name).first()
    if input_set is None:
        raise RuntimeError('No InputSet with name "%s"' % name)
    for input in input_set.inputs:
        print(name + ' ' + str(input))


def add_inputs_to_set(set_ids, input_ids, my_session):
    """
    Add inputs to input set.
    """
    for set_id, input_id in zip(set_ids, input_ids):
        inp = my_session.query(Input).get(input_id)
        input_set = my_session.query(InputSet).get(set_id)
        input_set.inputs.append(inp)
    log.info(__name__, 'Imported %d inputs to sets' % len(input_ids), 'input.py')
    my_session.commit()


def import_input_set(name, csv_fn, my_session):
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
            my_session.add(input)
            input_set.inputs.append(input)
            n_added_input += 1
    log.info(__name__, 'Imported %d items from input set' % len(input_set.inputs), 'input.py')
    my_session.add(input_set)
    my_session.commit()
    return input_set.id, n_added_input


def _fetcher(prefix, species, sql_filter, session):
    """
    Helper function for fetching data from a metadata table with name given by
    prefix/species, with optional SQL filter criteria specified
    """
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


def inputs_from_table(prefix, species, sql_filter, input_set_name, session):
    input_ids = []
    for tup in _fetcher(prefix, species, sql_filter, session):
        run_acc, study_acc = tup
        input_ids.append(add_input(run_acc, study_acc, None, None, None, None, None, None, None, session))
    set_id = add_input_set(input_set_name, session)
    add_inputs_to_set([set_id] * len(input_ids), input_ids, session)
    log.info(__name__, 'Added %d inputs' % len(input_ids), 'input.py')
    return set_id, input_ids


_lambda_reads_1 = 'http://www.cs.jhu.edu/~langmea/resources/reads_1.fq'
_lambda_reads_1_md5 = '8f4a7d568d2e930922e25c9d6e1b482f'
_lambda_reads_2 = 'http://www.cs.jhu.edu/~langmea/resources/reads_2.fq'
_lambda_reads_2_md5 = '899e197478a235b2fd29d8501aea4104'
_longreads = 'longreads.fq'
_longreads_md5 = '076b0e9f81aa599043b9e4be204a8014'


def test_integration(db_integration):
    if not db_integration:
        pytest.skip('db integration testing disabled')


def test_simple_source_insert(session):
    d1 = Input(retrieval_method='url', url_1=_lambda_reads_1, url_2=_lambda_reads_2)
    assert 0 == len(list(session.query(Input)))
    session.add(d1)
    session.commit()
    inputs = list(session.query(Input))
    assert 1 == len(inputs)
    assert _lambda_reads_1 == inputs[0].url_1
    assert _lambda_reads_2 == inputs[0].url_2
    session.delete(d1)
    session.commit()
    assert 0 == len(list(session.query(Input)))


def test_simple_inputset_insert(session):
    inp1 = Input(retrieval_method="url",
                 url_1=_lambda_reads_1, checksum_1=_lambda_reads_1_md5,
                 url_2=_lambda_reads_2, checksum_2=_lambda_reads_2_md5)
    inp2 = Input(retrieval_method="url", url_1=_longreads, checksum_1=_longreads_md5)
    inp3 = Input(retrieval_method="url", url_1=_lambda_reads_2, checksum_1=_lambda_reads_2_md5)

    # add inputs
    assert 0 == len(list(session.query(Input)))
    assert 0 == len(list(session.query(InputSet)))
    session.add(inp1)
    session.add(inp2)
    session.add(inp3)
    session.commit()
    assert 3 == len(list(session.query(Input)))

    # add input sets with associations
    session.add(InputSet(inputs=[inp1, inp2]))
    session.add(InputSet(inputs=[inp1, inp2, inp3]))
    session.commit()
    assert 2 == len(list(session.query(InputSet)))
    sss = list(session.query(InputSet))
    assert 2 == len(sss[0].inputs)
    assert 3 == len(sss[1].inputs)
    assert 5 == len(list(session.query(input_association_table)))


def test_import_inputset(session):
    assert 0 == len(list(session.query(Input)))
    assert 0 == len(list(session.query(InputSet)))
    assert 0 == len(list(session.query(input_association_table)))
    csv_text = '''NA,NA,ftp://genomi.cs/1.fastq.gz,ftp://genomi.cs/2.fastq.gz,NA,NA,NA,NA,wget'''
    with open('.tmp.csv', 'w') as ofh:
        ofh.write(csv_text)
    import_input_set('test_inputset', '.tmp.csv', session)
    inputs, input_sets, input_assocs = list(session.query(Input)), \
                                       list(session.query(InputSet)), \
                                       list(session.query(input_association_table))
    assert 1 == len(inputs)
    assert 1 == len(input_sets)
    assert 1 == len(input_assocs)
    os.remove('.tmp.csv')


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
        if args['add-input']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_input(args['<acc-r>'], args['<acc-s>'],
                            args['<url-1>'], args['<url-2>'], args['<url-3>'],
                            args['<checksum-1>'], args['<checksum-2>'], args['<checksum-3>'],
                            args['<retrieval-method>'], Session()))
        elif args['add-input-set']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_input_set(args['<name>'], Session()))
        elif args['list-input-set']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(list_input_set(args['<name>'], Session()))
        elif args['add-inputs-to-set']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_inputs_to_set(args['<set-id>'], args['<input-id>'], Session()))
        elif args['filter-table']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(filter_table(args['<prefix>'], args['<species>'], args['<sql-filter>'], Session()))
        elif args['inputs-from-table']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(inputs_from_table(args['<prefix>'], args['<species>'],
                                    args['<sql-filter>'], args['<input-set-name>'], Session()))
    except Exception:
        log.error(__name__, 'Uncaught exception:', 'input.py')
        raise
