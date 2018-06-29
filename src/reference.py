#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""reference

Usage:
  reference add-source <url-1> <url-2> <url-3>
                       <checksum-1> <checksum-2> <checksum-3>
                       <retrieval-method> [options]
  reference add-source-set <name> [options]
  reference add-sources-to-set (<set-id> <source-id>)... [options]
  reference list-source-set <name> [options]
  reference add-annotation <tax-id> <url> <md5>
                           <retrieval-method> [options]
  reference add-annotation-set <name> [options]
  reference add-annotations-to-set (<set-id> <annotation-id>)... [options]
  reference list-annotation-set <name> [options]
  reference nop [options]

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

import os
import pytest
import shutil
import log
from docopt import docopt
from tempfile import mkdtemp

from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, Table
from sqlalchemy.orm import relationship
from base import Base
from toolbox import generate_file_md5, session_maker_from_config
from mover import Mover


class Source(Base):
    """
    Supporting files used to analyze reference data, like reference genomes,
    indexes, gene annotations, etc.
    """
    __tablename__ = 'source'

    id = Column(Integer, Sequence('source_id_seq'), primary_key=True)
    url_1 = Column(String(1024))  # URL where obtained
    url_2 = Column(String(1024))  # URL where obtained
    url_3 = Column(String(1024))  # URL where obtained
    checksum_1 = Column(String(256))
    checksum_2 = Column(String(256))
    checksum_3 = Column(String(256))
    retrieval_method = Column(String(64))

    def __repr__(self):
        return ' '.join(map(str, [self.id, self.url_1, self.url_2, self.url_3,
                                  self.checksum_1, self.checksum_2, self.checksum_3,
                                  self.retrieval_method]))


# Creates many-to-many association between Sources and SourceSets
source_association_table = Table('source_set_association', Base.metadata,
    Column('source_id', Integer, ForeignKey('source.id')),
    Column('source_set_id', Integer, ForeignKey('source_set.id'))
)


class SourceSet(Base):
    """
    For gathering many sources under a single key.
    """
    __tablename__ = 'source_set'

    id = Column(Integer, Sequence('source_set_id_seq'), primary_key=True)
    sources = relationship("Source", secondary=source_association_table)


# Creates many-to-many association between Annotations and AnnotationSets
annotation_association_table = Table('annotation_set_association', Base.metadata,
    Column('annotation_id', Integer, ForeignKey('annotation.id')),
    Column('annotation_set_id', Integer, ForeignKey('annotation_set.id'))
)


class Annotation(Base):
    """
    Packages gene annotation files needed to study the annotated transcriptome
    of a species
    """
    __tablename__ = 'annotation'

    id = Column(Integer, Sequence('annotation_id_seq'), primary_key=True)
    tax_id = Column(Integer)  # refers to NCBI tax ids
    url = Column(String(1024))
    checksum = Column(String(32))
    retrieval_method = Column(String(64))


class AnnotationSet(Base):
    """
    For gathering many gene annotations under a single key.
    """
    __tablename__ = 'annotation_set'

    id = Column(Integer, Sequence('annotation_set_id_seq'), primary_key=True)
    annotations = relationship("Annotation", secondary=annotation_association_table)


class Reference(Base):
    """
    Packages reference files needed to do comparative analysis with respect to
    a species
    """
    __tablename__ = 'reference'

    id = Column(Integer, Sequence('reference_id_seq'), primary_key=True)
    tax_id = Column(Integer)  # refers to NCBI tax ids
    name = Column(String(64))  # assembly name, like GRCh38, etc
    longname = Column(String(256))  # assembly name, like GRCh38, etc
    conventions = Column(String(256))  # info about naming conventions, e.g. "chr"
    comment = Column(String(256))
    source_set = Column(Integer, ForeignKey('source_set.id'))
    annotation_set = Column(Integer, ForeignKey('annotation_set.id'))


def add_source(url_1, url_2, url_3,
               checksum_1, checksum_2, checksum_3,
               retrieval_method, session):
    """
    Add new source with associated retrieval info.
    """
    url_1 = None if url_1 == 'NA' else url_1
    url_2 = None if url_2 == 'NA' else url_2
    url_3 = None if url_3 == 'NA' else url_3
    checksum_1 = None if checksum_1 == 'NA' else checksum_1
    checksum_2 = None if checksum_2 == 'NA' else checksum_2
    checksum_3 = None if checksum_3 == 'NA' else checksum_3
    i = Source(url_1=url_1, url_2=url_2, url_3=url_3,
              checksum_1=checksum_1, checksum_2=checksum_2, checksum_3=checksum_3,
              retrieval_method=retrieval_method)
    session.add(i)
    session.commit()
    log.info(__name__, 'Added 1 source', 'reference.py')
    return i.id


def add_annotation(tax_id, url, checksum, retrieval_method, session):
    """
    Add new annotation.
    """
    i = Annotation(tax_id=tax_id, url=url, checksum=checksum, retrieval_method=retrieval_method)
    session.add(i)
    session.commit()
    log.info(__name__, 'Added 1 annotation', 'reference.py')
    return i.id


def add_source_set(name, session):
    """
    Add new source set with given name.  It's empty at first.  Needs to be
    populated with, e.g., add-source-to-set.
    """
    sset = SourceSet(name=name)
    session.add(sset)
    session.commit()
    log.info(__name__, 'Added source set "%s"' % name, 'reference.py')
    return sset.id


def add_annotation_set(name, session):
    """
    Add new annotation set with given name.  It's empty at first.  Needs to be
    populated with, e.g., add-annotation-to-set.
    """
    aset = AnnotationSet(name=name)
    session.add(aset)
    session.commit()
    log.info(__name__, 'Added annotation set "%s"' % name, 'reference.py')
    return aset.id


def list_source_set(name, session):
    """
    Print the names of all the sources in the set with the given name.
    """
    source_set = session.query(SourceSet).filter_by(name=name).first()
    if source_set is None:
        raise RuntimeError('No SourceSet with name "%s"' % name)
    for source in source_set.sources:
        print(name + ' ' + str(source))


def list_annotation_set(name, session):
    """
    Print the names of all the annotations in the set with the given name.
    """
    annotation_set = session.query(AnnotationSet).filter_by(name=name).first()
    if annotation_set is None:
        raise RuntimeError('No AnnotationSet with name "%s"' % name)
    for annotation in annotation_set.annotations:
        print(name + ' ' + str(annotation))


def add_sources_to_set(set_ids, source_ids, session):
    """
    Add sources to source set(s).
    """
    for set_id, source_id in zip(set_ids, source_ids):
        inp = session.query(Source).get(source_id)
        source_set = session.query(SourceSet).get(set_id)
        source_set.sources.append(inp)
    log.info(__name__, 'Imported %d sources to sets' % len(source_ids), 'reference.py')
    session.commit()


def add_annotations_to_set(set_ids, annotation_ids, session):
    """
    Add annotations to annotation set(s).
    """
    for set_id, annotation_id in zip(set_ids, annotation_ids):
        annotation = session.query(Annotation).get(annotation_id)
        annotation_set = session.query(AnnotationSet).get(set_id)
        annotation_set.annotations.append(annotation)
    log.info(__name__, 'Imported %d annotations to sets' % len(annotation_ids), 'reference.py')
    session.commit()


def download_reference(session, mover, dest_dir='.', ref_name=None):
    """
    Download all relevant supporting files for a reference, or for all
    references (when ref_name=None) to a directory.  This is something you will
    typically do on a new cluster, letting the destination directory be a
    shared filesystem.
    """
    if ref_name is not None:
        refs = list(session.query(Reference).filter_by(name=ref_name))
        if len(refs) == 0:
            raise ValueError('No references with name "%s"')
    else:
        refs = list(session.query(Reference))
        if len(refs) == 0:
            raise ValueError('No references')
    ss_key = refs[0].source_set
    sss = list(session.query(SourceSet).filter_by(id=ss_key))
    if len(sss) == 0:
        raise ValueError('Reference "%s" had invalid source_set key "%d"' % (ref_name, ss_key))
    ll = set()
    for ss in sss:
        for src in ss.sources:
            ll.add(src)
    # TODO: deal with gene annotations too
    for l in ll:
        for url, cksum in [(l.url_1, l.checksum_1),
                           (l.url_2, l.checksum_2),
                           (l.url_3, l.checksum_3)]:
            if url is not None and len(url) > 0:
                fn = os.path.basename(url)
                dest_fn = os.path.join(dest_dir, fn)
                if os.path.exists(dest_fn):
                    raise ValueError('Destination already exists: ' + dest_fn)
                log.info(__name__, 'retrieve "%s" into "%s"' % (url, dest_dir), 'reference.py')
                mover.get(url, dest_dir)
                if not os.path.exists(dest_fn):
                    raise IOError('Failed to obtain "%s"' % url)
                if cksum is not None and len(cksum) > 0:
                    log.info(__name__, 'check checksum for "%s"' % dest_fn, 'reference.py')
                    dest_checksum = generate_file_md5(dest_fn)
                    if cksum != dest_checksum:
                        raise IOError('MD5 mismatch; expected %s got %s' % (cksum, dest_checksum))
                if fn.endswith('.tar.gz'):
                    log.info(__name__, 'decompressing tarball "%s"' % dest_fn, 'reference.py')
                    os.system('cd %s && gzip -dc %s | tar xf -' % (dest_dir, os.path.basename(dest_fn)))
                elif fn.endswith('.gz'):
                    log.info(__name__, 'decompressing gz "%s"' % dest_fn, 'reference.py')
                    os.system('gunzip ' + dest_fn)

# This is ~29MB
_ensembl_fasta = 'ftp://ftp.ensembl.org/pub/release-90/fasta'
_species = 'caenorhabditis_elegans'
_fa_prefix = 'Caenorhabditis_elegans.WBcel235'
_elegans_url = '%s/%s/dna/%s.dna.toplevel.fa.gz' % (_ensembl_fasta, _species, _fa_prefix)
_elegans_md5 = '151011266f8af1de2ecb11ff4a43a134'

_ncbi_genomes = 'ftp://ftp.ncbi.nlm.nih.gov/genomes'
_acc = 'GCF_000840245.1_ViralProj14204'
_lambda_fa = _ncbi_genomes + '/all/GCF/000/840/245/%s/%s_genomic.fna.gz' % (_acc, _acc)
_lambda_fa_md5 = '7e74fba2c9e1107f228dbb12bada5c1c'
_lambda_annot = _ncbi_genomes + '/all/GCF/000/840/245/%s/%s_genomic.gff.gz' % (_acc, _acc)
_lambda_annot_md5 = 'df93ad945b341e7f1b225742f9d8ee6b'

_phix_fa = 'http://www.cs.jhu.edu/~langmea/resources/phix.fa'
_phix_md5 = 'a1c4cc91480cd3e9e7197d35dbba7929'


def test_integration(db_integration):
    if not db_integration:
        pytest.skip('db integration testing disabled')


def test_simple_source_insert(session):
    src = Source(retrieval_method="url", url_1=_elegans_url, checksum_1=_elegans_md5)
    assert 0 == len(list(session.query(Source)))
    session.add(src)
    session.commit()
    sources = list(session.query(Source))
    assert 1 == len(sources)
    assert _elegans_url == sources[0].url_1
    assert _elegans_md5 == sources[0].checksum_1
    assert sources[0].url_2 is None
    assert sources[0].url_3 is None
    assert sources[0].checksum_2 is None
    assert sources[0].checksum_3 is None
    session.delete(src)
    session.commit()
    assert 0 == len(list(session.query(Source)))


def test_simple_annotation_insert(session):
    annotation = Annotation(tax_id=9606, retrieval_method="url",
                            url=_lambda_annot, checksum=_lambda_annot_md5)
    assert 0 == len(list(session.query(Annotation)))
    session.add(annotation)
    session.commit()
    annotations = list(session.query(Annotation))
    assert 1 == len(annotations)
    assert _lambda_annot == annotations[0].url
    assert _lambda_annot_md5 == annotations[0].checksum
    session.delete(annotation)
    session.commit()
    assert 0 == len(list(session.query(Annotation)))


def test_simple_sourceset_insert(session):
    src1 = Source(retrieval_method="url", url_1=_elegans_url, checksum_1=_elegans_md5)
    src2 = Source(retrieval_method="url", url_1=_elegans_url, checksum_1=_elegans_md5)
    src3 = Source(retrieval_method="url", url_1=_elegans_url, checksum_1=_elegans_md5)

    # add sources
    assert 0 == len(list(session.query(Source)))
    assert 0 == len(list(session.query(SourceSet)))
    session.add(src1)
    session.add(src2)
    session.add(src3)
    session.commit()
    assert 3 == len(list(session.query(Source)))
    srcs = list(session.query(Source))

    # add source sets with associations
    session.add(SourceSet(sources=[src1, src2]))
    session.add(SourceSet(sources=[src1, src2, src3]))
    session.commit()
    assert 2 == len(list(session.query(SourceSet)))
    sss = list(session.query(SourceSet))
    assert 2 == len(sss[0].sources)
    assert 3 == len(sss[1].sources)
    assert 5 == len(list(session.query(source_association_table)))


def test_simple_annotationset_insert(session):
    annot1 = Annotation(retrieval_method="url", url=_lambda_annot, checksum=_lambda_annot_md5)
    annot2 = Annotation(retrieval_method="url", url=_lambda_annot, checksum=_lambda_annot_md5)
    annot3 = Annotation(retrieval_method="url", url=_lambda_annot, checksum=_lambda_annot_md5)

    # add annotations
    assert 0 == len(list(session.query(Annotation)))
    assert 0 == len(list(session.query(AnnotationSet)))
    session.add(annot1)
    session.add(annot2)
    session.add(annot3)
    session.commit()
    assert 3 == len(list(session.query(Annotation)))

    # add annotation sets with associations
    session.add(AnnotationSet(annotations=[annot1, annot2]))
    session.add(AnnotationSet(annotations=[annot1, annot2, annot3]))
    session.commit()
    assert 2 == len(list(session.query(AnnotationSet)))
    annot_sets = list(session.query(AnnotationSet))
    assert 2 == len(annot_sets[0].annotations)
    assert 3 == len(annot_sets[1].annotations)
    assert 5 == len(list(session.query(annotation_association_table)))


def test_download_all(session, s3_enabled, s3_service):
    if not s3_enabled: pytest.skip('Skipping S3 tests')
    src1 = Source(retrieval_method="s3",
                  url_1='s3://recount-pump/ref/ce10/ucsc_tracks.tar.gz', checksum_1='')
    src2 = Source(retrieval_method="s3",
                  url_1='s3://recount-pump/ref/ce10/fasta.tar.gz', checksum_1='')
    session.add(src1)
    session.add(src2)
    ss = SourceSet(sources=[src1, src2])
    session.add(ss)
    session.commit()
    an1 = Source(retrieval_method='s3',
                 url_1='s3://recount-pump/ref/ce10/gtf.tar.gz', checksum_1='')
    anset = AnnotationSet(annotations=[an1])
    ref1 = Reference(tax_id=6239, name='celegans', longname='caenorhabditis_elegans',
                     conventions='', comment='', source_set=ss.id, annotation_set=anset.id)
    session.add(ref1)
    session.commit()
    tmpd = mkdtemp()
    download_reference(session, s3_service, dest_dir=tmpd, ref_name='celegans')
    assert os.path.exists(os.path.join(tmpd, 'fasta/genome.fa'))
    # TODO: handle annotation
    #assert os.path.exists(os.path.join(tmpd, 'gtf/genes.gtf'))
    shutil.rmtree(tmpd)


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
        if args['add-source']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_source(args['<url-1>'], args['<url-2>'], args['<url-3>'],
                             args['<checksum-1>'], args['<checksum-2>'], args['<checksum-3>'],
                             args['<retrieval-method>'], Session()))
        elif args['add-source-set']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_source_set(args['<name>'], Session()))
        elif args['list-source-set']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(list_source_set(args['<name>'], Session()))
        elif args['add-sources-to-set']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_sources_to_set(args['<set-id>'], args['<source-id>'], Session()))
        if args['add-annotation']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_annotation(args['<tax-id>'], args['<url>'], args['<md5>'],
                                 args['<retrieval-method>'], Session()))
        elif args['add-annotation-set']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_annotation_set(args['<name>'], Session()))
        elif args['list-annotation-set']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(list_annotation_set(args['<name>'], Session()))
        elif args['add-annotations-to-set']:
            Session = session_maker_from_config(db_ini, args['--db-section'])
            print(add_annotations_to_set(args['<set-id>'], args['<annotation-id>'], Session()))
        elif args['nop']:
            pass
    except Exception:
        log.error(__name__, 'Uncaught exception:', 'reference.py')
        raise
