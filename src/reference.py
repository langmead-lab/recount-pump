#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

import os
import unittest
import tempfile
import shutil
import logging

from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, Table, create_engine
from base import Base
from sqlalchemy.orm import relationship, sessionmaker
from toolbox import generate_file_md5
from mover import Mover


class Source(Base):
    """
    Supporting files used to analyze input data, like reference genomes,
    indexes, gene annotations, etc.
    """
    __tablename__ = 'source'

    id = Column(Integer, Sequence('source_id_seq'), primary_key=True)
    retrieval_method = Column(String(64))
    url_1 = Column(String(1024))  # URL where obtained
    url_2 = Column(String(1024))  # URL where obtained
    url_3 = Column(String(1024))  # URL where obtained
    checksum_1 = Column(String(256))
    checksum_2 = Column(String(256))
    checksum_3 = Column(String(256))


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


class Annotation(Base):
    """
    Packages gene annotation files needed to study the annotated transcriptome
    of a species
    """
    __tablename__ = 'annotation'

    id = Column(Integer, Sequence('annotation_id_seq'), primary_key=True)
    tax_id = Column(Integer)  # refers to NCBI tax ids
    url1 = Column(String(1024))
    md5 = Column(String(32))


def download_reference(session, dest_dir='.', ref_name=None,
                       profile='default', curl_exe='curl', decompress=True):
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
    mover = Mover(profile=profile, curl_exe=curl_exe, enable_web=True)
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
                logging.info('retrieving "%s" into "%s"' % (url, dest_dir))
                mover.get(url, dest_dir)
                if not os.path.exists(dest_fn):
                    raise IOError('Failed to obtain "%s"' % url)
                if cksum is not None and len(cksum) > 0:
                    logging.info('checking checksum for "%s"' % dest_fn)
                    dest_md5 = generate_file_md5(dest_fn)
                    if cksum != dest_md5:
                        raise IOError('MD5 mismatch; expected %s got %s' % (cksum, dest_md5))
                if fn.endswith('.gz'):
                    logging.info('decompressing "%s"' % dest_fn)
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


def _setup():
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)
    session_mk = sessionmaker(bind=engine)
    return session_mk()


class TestReference(unittest.TestCase):

    def setUp(self):
        self.session = _setup()

    def tearDown(self):
        self.session.close()

    def test_simple_source_insert(self):
        src = Source(retrieval_method="url", url_1=_elegans_url, checksum_1=_elegans_md5)
        self.assertEqual(0, len(list(self.session.query(Source))))
        self.session.add(src)
        self.session.commit()
        sources = list(self.session.query(Source))
        self.assertEqual(1, len(sources))
        self.assertEqual(_elegans_url, sources[0].url_1)
        self.assertEqual(_elegans_md5, sources[0].checksum_1)
        self.assertIsNone(sources[0].url_2)
        self.assertIsNone(sources[0].url_3)
        self.assertIsNone(sources[0].checksum_2)
        self.assertIsNone(sources[0].checksum_3)
        self.session.delete(src)
        self.session.commit()
        self.assertEqual(0, len(list(self.session.query(Source))))

    def test_simple_sourceset_insert(self):
        src1 = Source(retrieval_method="url", url_1=_elegans_url, checksum_1=_elegans_md5)
        src2 = Source(retrieval_method="url", url_1=_elegans_url, checksum_1=_elegans_md5)
        src3 = Source(retrieval_method="url", url_1=_elegans_url, checksum_1=_elegans_md5)

        # add sources
        self.assertEqual(0, len(list(self.session.query(Source))))
        self.assertEqual(0, len(list(self.session.query(SourceSet))))
        self.session.add(src1)
        self.session.add(src2)
        self.session.add(src3)
        self.session.commit()
        self.assertEqual(3, len(list(self.session.query(Source))))
        srcs = list(self.session.query(Source))

        # add source sets with associations
        self.session.add(SourceSet(sources=[src1, src2]))
        self.session.add(SourceSet(sources=[src1, src2, src3]))
        self.session.commit()
        self.assertEqual(2, len(list(self.session.query(SourceSet))))
        sss = list(self.session.query(SourceSet))
        self.assertEqual(2, len(sss[0].sources))
        self.assertEqual(3, len(sss[1].sources))
        self.assertEqual(5, len(list(self.session.query(source_association_table))))

        for obj in srcs + sss:
            self.session.delete(obj)
        self.assertEqual(0, len(list(self.session.query(Source))))
        self.assertEqual(0, len(list(self.session.query(SourceSet))))
        self.assertEqual(0, len(list(self.session.query(source_association_table))))

    def test_download_all(self):
        src1 = Source(retrieval_method="url", url_1=_lambda_fa, checksum_1=_lambda_fa_md5)
        src2 = Source(retrieval_method="url", url_1=_phix_fa, checksum_1=_phix_md5)
        self.session.add(src1)
        self.session.add(src2)
        ss = SourceSet(sources=[src1, src2])
        self.session.add(ss)
        self.session.commit()
        an1 = Source(retrieval_method="url", url_1=_lambda_annot, checksum_1=_lambda_annot_md5)
        anset = AnnotationSet(annotations=[an1])
        ref1 = Reference(tax_id=10710, name='lambda', longname='Enterobacteria phage lambda',
                         conventions='', comment='', source_set=ss.id, annotation_set=anset.id)
        self.session.add(ref1)
        self.session.commit()
        tmpd = tempfile.mkdtemp()
        download_reference(self.session, dest_dir=tmpd, ref_name='lambda')
        self.assertTrue(os.path.exists(os.path.join(tmpd, 'GCF_000840245.1_ViralProj14204_genomic.fna')))
        self.assertTrue(os.path.exists(os.path.join(tmpd, 'phix.fa')))
        shutil.rmtree(tmpd)

        for obj in [src1, src2, ss, ref1]:
            self.session.delete(obj)
        self.assertEqual(0, len(list(self.session.query(SourceSet))))
        self.assertEqual(0, len(list(self.session.query(Source))))
        self.assertEqual(0, len(list(self.session.query(Reference))))
        self.assertEqual(0, len(list(self.session.query(source_association_table))))


if __name__ == '__main__':
    import sys

    if '--test' in sys.argv:
        sys.argv.remove('--test')
        unittest.main()

    # Set up session; maybe use a config file to establish 
