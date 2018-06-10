#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""meta

Usage:
  meta fetch-species (<species-name> <dest-fn>)... [options]
  meta fetch-species-default [options]
  meta load-species <csv-file> <dest-table> [options]
  meta fail [options]
  meta nop [options]

Options:
  <dest-fn>                Destination filename (CSV) [default: 'meta.csv'].
  <species-name>           Species name like "danio rerio".
  <dest-table>             Table name to install in db.
  <db-config>              Database ini file, w/ section named 'client' [default: ~/.recount/db.ini].
  --log-ini <ini>          ini file for log aggregator [default: ~/.recount/log.ini].
  --log-section <section>  ini file section for log aggregator [default: log].
  --log-level <level>      set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  -a, --aggregate          enable log aggregation.
  -h, --help               Show this screen.
  --version                Show version.
"""

import os
import shutil
import pandas
import sys
from docopt import docopt
import log
from toolbox import session_maker_from_config
from sqlalchemy import Column, ForeignKey, Integer, Float, String, DateTime, Sequence, Table, create_engine
from base import Base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import text

try:
    from urllib.parse import urlparse, urlencode, quote
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode, quote
    from urllib2 import urlopen, Request, HTTPError, URLError
    sys.exc_clear()


_default_species = ['arabidopsis thaliana',     # 3702
                    'bos taurus',               # 9913
                    'caenorhabditis elegans',   # 6239
                    'danio rerio',              # 7955
                    'drosophila melanogaster',  # 7227
                    'homo sapiens',             # 9606
                    'mus_musculus',             # 10090
                    'ovis_aries',               # 9940
                    'rattus_norvegicus',        # 10116
                    'saccharomyces_cerevisiae', # 4932
                    'zea_mays']                 # 4577



"""
class SraRunInfo(Base):
    # Run, ReleaseDate, LoadDate, spots, bases, spots_with_mates, avgLength, size_MB, AssemblyName, download_path, Experiment, LibraryName, LibraryStrategy, LibrarySelection, LibrarySource, LibraryLayout, InsertSize, InsertDev, Platform, Model, SRAStudy, BioProject, Study_Pubmed_id, ProjectID, Sample, BioSample, SampleType, TaxID, ScientificName, SampleName, g1k_pop_code, source, g1k_analysis_group, Subject_ID, Sex, Disease, Tumor, Affection_Status, Analyte_Type, Histological_Type, Body_Site, CenterName, Submission, dbgap_study_accession, Consent, RunHash, ReadHash
    run_accession = Column(String(16))         # run accession
    release_date = Column(DateTime())          # date released
    load_date = Column(DateTime())             # date released
    spots = Column(Integer())                  # # spots
    bases = Column(Integer())                  # # bases
    spots_with_mates = Column(Integer())       #
    avg_length = Column(Float())               #
    size_MB = Column(Integer())                #
    assembly_name = Column(String(32))         # assembly name
    download_path = Column(String(1024))       #
    experiment_accession = Column(String(16))  # experiment accession
    library_name = Column(String(32))          # library name
    library_strategy = Column(String(32))      # library strategy
    library_selection = Column(String(32))     # library selection method
    library_source = Column(String(32))        # library source (e.g. TRANSCRIPTOMIC)
    library_layout = Column(String(32))        # library layout (e.g. SINGLE)
    insert_size
    insert_dev
"""

"""
Run,object,10
ReleaseDate,datetime64[ns],0
LoadDate,datetime64[ns],0
spots,int64,0
bases,int64,0
spots_with_mates,int64,0
avgLength,int64,0
size_MB,int64,0
AssemblyName,object,36
download_path,object,73
Experiment,object,10
LibraryName,object,315
LibraryStrategy,object,7
LibrarySelection,object,22
LibrarySource,object,14
LibraryLayout,object,6
InsertSize,int64,0
InsertDev,float64,0
Platform,object,8
Model,object,28
SRAStudy,object,9
BioProject,object,11
Study_Pubmed_id,float64,0
ProjectID,int64,0
Sample,object,10
BioSample,object,14
SampleType,object,6
TaxID,int64,0
ScientificName,object,12
SampleName,object,126
g1k_pop_code,object,3
source,object,3
g1k_analysis_group,object,12
Subject_ID,object,23
Sex,object,22
Disease,object,21
Tumor,object,3
Affection_Status,float64,0
Analyte_Type,object,50
Histological_Type,object,77
Body_Site,object,55
CenterName,object,150
Submission,object,10
dbgap_study_accession,object,9
Consent,object,24
RunHash,object,32
ReadHash,object,32

Questions:
- Affection_Status is float64?
"""


def load_species(csv_fn, dest_tab, session):
    log.info(__name__, 'Loading from "%s"' % csv_fn, 'meta.py')
    parse_dates = ['LoadDate', 'ReleaseDate']
    df = pandas.read_csv(csv_fn, parse_dates=parse_dates)
    log.info(__name__, 'Installing into "%s"' % dest_tab, 'meta.py')
    df.to_sql(dest_tab, session.connection(), if_exists='fail')
    session.commit()


def fetch_sra_metadata(speciess, dest_fns,
                       filters=quote('rna seq[Strategy] transcriptomic[Source] illumina[Platform]')):
    sra_prefix = 'http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi'
    qstr = quote('?save=efetch&db=sra&rettype=runinfo&term=', safe='')
    for species, dest_fn in zip(speciess, dest_fns):
        termstr = quote('%s[Organism]'  % species, safe='')
        if os.path.exists(dest_fn):
            raise RuntimeError('Destination file "%s" exists' % dest_fn)
        url = sra_prefix + qstr + termstr + filters
        log.info(__name__, 'Fetching metadata from url "%s"' % url, 'meta.py')
        response = urlopen(url)
        log.info(__name__, 'Response from metadata fetch from "%s": "%s"' % (url, response.info()), 'meta.py')
        with open(dest_fn, 'wb') as ofh:
            log.info(__name__, 'Starting to fetch data from "%s"' % url, 'meta.py')
            shutil.copyfileobj(response, ofh)
        sz = os.stat(dest_fn).st_size
        log.info(__name__, 'Finished fetching and writing %d bytes of data from "%s"' % (sz, url), 'meta.py')


if __name__ == '__main__':
    args = docopt(__doc__)
    agg_ini = os.path.expanduser(args['--log-ini']) if args['--aggregate'] else None
    log.init_logger(__name__, aggregation_ini=agg_ini,
                     aggregation_section=args['--log-section'],
                     agg_level=args['--log-level'])
    try:
        log.info(__name__, 'In main', 'meta.py')
        if args['fetch-species']:
            fetch_sra_metadata(args['<species-name>'], args['<dest-fn>'])
        elif args['fetch-species-default']:
            dest_fns = list(map(lambda x: x.replace(' ', '_') + '.csv', _default_species))
            fetch_sra_metadata(_default_species, dest_fns)
        elif args['load-species']:
            Session = session_maker_from_config(args['<db-config>'])
            load_species(args['<csv-file>'], args['<dest-table>'], Session())
        elif args['fail']:
            raise RuntimeError('Fake error')
        elif args['nop']:
            pass
    except Exception:
        log.error(__name__, 'Uncaught exception:', 'meta.py')
        raise
