#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""meta

Usage:
  meta [-a] species (<species-name> <dest-fn>)...
  meta [-a] species-default
  meta [-a] fail
  meta [-a] nop

Options:
  <dest-fn>             Destination filename (CSV).
  <species-name>        Species name like "danio rerio".
  -h, --help            Show this screen.
  --version             Show version.
  -a, --aggregate-logs  Send log messages to aggregator.
"""

import os
import shutil
import logging
from docopt import docopt
from log import new_logger

try:
    from urllib.parse import urlparse, urlencode, quote
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode, quote
    from urllib2 import urlopen, Request, HTTPError, URLError


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


def _log_info(st):
    logging.getLogger(__name__).info('meta.py: ' + st)


def fetch_sra_metadata(speciess, dest_fns,
                       filters=quote('rna seq[Strategy] transcriptomic[Source] illumina[Platform]')):
    sra_prefix = 'http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi'
    qstr = quote('?save=efetch&db=sra&rettype=runinfo&term=', safe='')
    for species, dest_fn in zip(speciess, dest_fns):
        termstr = quote('%s[Organism]'  % species, safe='')
        if os.path.exists(dest_fn):
            raise RuntimeError('Destination file "%s" exists' % dest_fn)
        url = sra_prefix + qstr + termstr + filters
        _log_info('Fetching metadata from url "%s"' % url)
        response = urlopen(url)
        _log_info('Response from metadata fetch from "%s": "%s"' % (url, response.info()))
        with open(dest_fn, 'wb') as ofh:
            _log_info('Starting to fetch data from "%s"' % url)
            shutil.copyfileobj(response, ofh)
        sz = os.stat(dest_fn).st_size
        _log_info('Finished fetching and writing %d bytes of data from "%s"' % (sz, url))


if __name__ == '__main__':
    args = docopt(__doc__)
    new_logger(__name__, with_aggregation=args['--aggregate-logs'], level=logging.INFO)
    try:
        _log_info('In main')
        if args['species']:
            fetch_sra_metadata(args['<species-name>'], args['<dest-fn>'])
        if args['species-default']:
            dest_fns = list(map(lambda x: x.replace(' ', '_') + '.csv', _default_species))
            fetch_sra_metadata(_default_species, dest_fns)
        elif args['fail']:
            raise RuntimeError('Fake error')
        elif args['nop']:
            pass
    except Exception:
        logging.getLogger(__name__).error('meta.py: Uncaught exception:', exc_info=True)
        raise
