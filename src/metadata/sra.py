#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

import log
import sys
import shutil
import os
if sys.version[:1] == '2':
    from urllib import quote
    from urllib2 import urlopen
else:
    from urllib.request import urlopen
    from urllib.parse import quote


def fetch_sra_metadata(speciess, dest_fns,
                       filters=quote('rna seq[Strategy] transcriptomic[Source] illumina[Platform]')):
    sra_prefix = 'http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi'
    qstr = quote('?save=efetch&db=sra&rettype=runinfo&term=', safe='')
    for species, dest_fn in zip(speciess, dest_fns):
        termstr = quote('%s[Organism]'  % species, safe='')
        if os.path.exists(dest_fn):
            raise RuntimeError('Destination file "%s" exists' % dest_fn)
        url = sra_prefix + qstr + termstr + filters
        log.info('Fetching metadata from url "%s"' % url, 'meta.py')
        response = urlopen(url)
        log.info( 'Response from metadata fetch from "%s": "%s"' % (url, response.info()), 'meta.py')
        with open(dest_fn, 'wb') as ofh:
            log.info('Starting to fetch data from "%s"' % url, 'meta.py')
            shutil.copyfileobj(response, ofh)
        sz = os.stat(dest_fn).st_size
        log.info('Finished fetching and writing %d bytes of data from "%s"' % (sz, url), 'meta.py')
