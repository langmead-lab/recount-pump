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
  input import-json [options] <json-file> <input-set-name>

Options:
  --limit <ceiling>        Import at most this many records.
  --max-bases <max>        Filter out datasets larger than this.
  --profile=<profile>      AWS credentials profile section [default: default].
  --endpoint-url=<url>     Endpoint URL for S3 API.  If not set, uses AWS default.
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
import gzip
import json
import codecs
import tempfile
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

    @classmethod
    def parse_job_string(cls, st):
        """
        Do some mild data validation and return parsed job-attempt parameters.
        """
        toks = st.split(',')
        assert 10 == len(toks)
        my_id = int(toks[0])
        acc_r, acc_s = toks[1:3]
        assert acc_r[1:3] == 'RR'
        assert acc_s[1:3] == 'RP'
        url_1, url_2, url_3, checksum_1, checksum_2, checksum_3 = toks[3:9]

        def noneize(x):
            if x == 'None' or x == 'NA':
                return None
            else:
                return x

        url_1 = noneize(url_1)
        url_2 = noneize(url_2)
        url_3 = noneize(url_3)
        checksum_1 = noneize(checksum_1)
        checksum_2 = noneize(checksum_2)
        checksum_3 = noneize(checksum_3)
        retrieval_method = toks[9]
        assert retrieval_method != 'None' and retrieval_method != 'NA'
        return my_id, acc_r, acc_s, url_1, url_2, url_3, \
               checksum_1, checksum_2, checksum_3, retrieval_method

    def to_job_string(self):
        """
        Return the string that should represent this input in a queued job.
        It should be enough information so that any cluster that obtains the
        job knows how to obtain the input.
        """
        assert self.acc_r[1:3] == 'RR'
        assert self.acc_s[1:3] == 'RP'
        assert (self.url_1 or self.url_2 or self.url_3) is not None
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
    log.info('Added 1 input', 'input.py')
    return i.id


def add_input_set(name, my_session):
    """
    Add new input set with given name.  It's empty at first.  Needs to be
    populated with, e.g., add-input-to-set.
    """
    iset = InputSet(name=name)
    my_session.add(iset)
    my_session.commit()
    log.info('Added input set "%s"' % name, 'input.py')
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
    log.info('Imported %d inputs to sets' % len(input_ids), 'input.py')
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
    log.info('Imported %d items from input set' % len(input_set.inputs), 'input.py')
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
    log.info('Added %d inputs' % len(input_ids), 'input.py')
    return set_id, input_ids


def import_json(json_fn, input_set_name, session, limit=None, max_bases=None):
    js = json.load(codecs.getreader("utf-8")(gzip.open(json_fn)) if json_fn.endswith('.gz') else open(json_fn))
    inputs = []
    for rec in js:
        bases = rec['_source']['run_bases']
        if bases is not None and max_bases is not None and bases > int(max_bases):
            continue
        acc_r = rec['_id']
        acc_s = rec['_source']['study_accession']
        inp = Input(acc_r=acc_r, acc_s=acc_s,
                    url_1=acc_r, url_2=None, url_3=None,
                    checksum_1=None, checksum_2=None, checksum_3=None,
                    retrieval_method='sra')
        inputs.append(inp)
        session.add(inp)
        if limit is not None and len(inputs) >= int(limit):
            break
    session.commit()
    set_id = add_input_set(input_set_name, session)
    add_inputs_to_set([set_id] * len(inputs),
                      list(map(lambda x: x.id, inputs)),
                      session)
    return set_id


def add_inputs_to_set(set_ids, input_ids, my_session):
    """
    Add inputs to input set.
    """
    for set_id, input_id in zip(set_ids, input_ids):
        inp = my_session.query(Input).get(input_id)
        input_set = my_session.query(InputSet).get(set_id)
        input_set.inputs.append(inp)
    log.info('Imported %d inputs to sets' % len(input_ids), 'input.py')
    my_session.commit()


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


def test_import_json_1(session):
    json = '[ { "_id": "SRR123", "_source": { "study_accession": "SRP123", "run_bases": 500 } } ]\n'
    tmpdir = tempfile.mkdtemp()
    json_fn = os.path.join(tmpdir, 'import.json')
    with open(json_fn, 'w') as fh:
        fh.write(json)
    iset_id = import_json(json_fn, 'iset1', session)
    iset = session.query(InputSet).get(iset_id)
    assert 1 == len(iset.inputs)


def test_import_json_2(session):
    json = """[ { "_id": "SRR123", "_source": { "study_accession": "SRP123", "run_bases": 500 } },
{ "_id": "SRR1234", "_source": { "study_accession": "SRP1234", "run_bases": 500 } },
{ "_id": "SRR12345", "_source": { "study_accession": "SRP12345", "run_bases": 500 } },
{ "_id": "SRR123456", "_source": { "study_accession": "SRP123456", "run_bases": 500 } } ]
"""
    tmpdir = tempfile.mkdtemp()
    json_fn = os.path.join(tmpdir, 'import.json')
    with open(json_fn, 'w') as fh:
        fh.write(json)
    iset_id = import_json(json_fn, 'iset1', session)
    iset = session.query(InputSet).get(iset_id)
    assert 4 == len(iset.inputs)
    assert 'SRR123' == iset.inputs[0].acc_r
    assert 'SRR1234' == iset.inputs[1].acc_r
    assert 'SRR12345' == iset.inputs[2].acc_r
    assert 'SRR123456' == iset.inputs[3].acc_r


def test_job_string1():
    inp1 = Input(id=1, acc_r='SRR123', acc_s='SRP123', retrieval_method="web",
                 url_1='url1', checksum_1='checksum1')
    assert inp1.url_2 is None
    assert inp1.url_3 is None
    assert inp1.checksum_2 is None
    assert inp1.checksum_3 is None
    st = inp1.to_job_string()
    assert '1,SRR123,SRP123,url1,None,None,checksum1,None,None,web' == st


def test_job_string2():
    st = '1,SRR123,SRP123,url1,None,None,checksum1,None,None,web'
    my_id, srr, srp, url1, url2, url3, checksum1, checksum2, checksum3, retrieval = Input.parse_job_string(st)
    assert 1 == my_id
    assert 'SRR123' == srr
    assert 'SRP123' == srp
    assert 'url1' == url1
    assert url2 is None
    assert url3 is None
    assert 'checksum1' == checksum1
    assert checksum2 is None
    assert checksum3 is None
    assert 'web' == retrieval


if __name__ == '__main__':
    args = docopt(__doc__)
    log_ini = os.path.expanduser(args['--log-ini'])
    log.init_logger(log.LOG_GROUP_NAME, log_ini=log_ini, agg_level=args['--log-level'])
    log.init_logger('sqlalchemy', log_ini=log_ini, agg_level=args['--log-level'],
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
        elif args['import-json']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(import_json(args['<json-file>'], args['<input-set-name>'],
                              Session(), limit=args['--limit'],
                              max_bases=args['--max-bases']))
    except Exception:
        log.error('Uncaught exception:', 'input.py')
        raise
