#!/usr/bin/env python

# Authors: Chris Wilks (original) and Ben Langmead (modifications)
#    Date: 7/3/2018
# License: MIT

"""sradbv2

Usage:
  sradbv2 search <lucene-search> [options]
  sradbv2 search-random-subset <lucene-search> <subset-size> [options]
  sradbv2 count <lucene-search> [options]
  sradbv2 size-dist <lucene-search> <n> [options]
  sradbv2 bases <lucene-search> [options]
  sradbv2 summarize-rna [options]

Options:
  --size <size>            Number of records to fetch per call [default: 300].
  --stop-after <num>       Stop processing results after this many [default: 1000000].
  --include-dbgap          Include records from studies that have a dbGaP identifier
                           among the study identifiers.
  --log-ini <ini>          .ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>      Set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  --gzip                   Gzip outputs.
  --quiet                  Don't complain about bad records.
  --output <name>          Output filename [default: search.json].
  -h, --help               Show this screen.
"""

from __future__ import print_function
import sys
import json
import cgi
import gzip
import random
import itertools
import os
from docopt import docopt
from collections import defaultdict
import log
if sys.version[:1] == '2':
    from urllib import quote
    from urllib2 import urlopen
else:
    from urllib.request import urlopen
    from urllib.parse import quote


# TODO: what sort of filter allows us to know whether something is dbGaP-protected?

sradbv2_api_url = 'https://api-omicidx.cancerdatasci.org/sra/1.0'
sradbv2_full_url = sradbv2_api_url + '/full'
sradbv2_scroll_url = sradbv2_api_url + '/scroll'
sradbv2_search_url = sradbv2_api_url + '/search/full'
KEY_VALUE_DELIM = '::'
SUBFIELD_DELIM = '|'

nested_fields = {'attributes': ['tag', 'value'],
                 'identifiers': ['id', 'namespace'],
                 'xrefs': ['db', 'id']}


class ReservoirSampler(object):
    """ Simple reservoir sampler """

    def __init__(self, k):
        """ Initialize given k, the size of the reservoir """
        self.k = k
        self.r = []
        self.n = 0

    def add(self, obj):
        """ Add object to sampling domain """
        if self.n < self.k:
            self.r.append(obj)
        else:
            j = random.randint(0, self.n)
            if j < self.k:
                self.r[j] = obj
        self.n += 1

    def __iter__(self):
        """ Return iterator over the sample """
        return iter(self.r)


def openex(fn, mode, use_gzip):
    if use_gzip:
        return gzip.open(fn + '.gz', mode)
    else:
        return open(fn, mode)


def sanity_check_json(fn, use_gzip):
    with openex(fn, 'rt', use_gzip) as fh:
        json.loads(fh.read())
        return True


def get_payload(search, size):
    url = '%s?q=%s&size=%d' % (sradbv2_search_url, quote(search), size)
    log.info('GET ' + url, 'sradbv2.py')
    response = urlopen(url)
    j, ct = cgi.parse_header(response.headers.get('Content-type', ''))
    encodec = ct.get('charset', 'utf-8')
    payload = response.read().decode(encodec)
    return json.loads(payload), encodec


def dbgap_filter(hit):
    """
    Filter to apply to a single hit object.  Returns true if hit passes the
    filter.  Filter checks if there is a key in the study->identifier
    dictionary list that indicates this might be a dbGap project.
    """
    assert '_source' in hit
    assert 'study' in hit['_source']
    assert 'identifiers' in hit['_source']['study']
    for ident in hit['_source']['study']['identifiers']:
        if 'namespace' in ident and ident['namespace'] == 'dbGaP':
            return False
    return True


def filter_hits(hits, hit_filter=None):
    if hit_filter is not None:
        return filter(hit_filter, hits)
    return hits


def search_iterator(search, size, hit_filter=None):
    jn, encodec = get_payload(search, size)
    tot_hits = jn['hits']['total']
    num_hits = len(jn['hits']['hits'])
    assert num_hits <= tot_hits
    log.info('Writing hits [%d, %d) out of %d' % (0, num_hits, tot_hits), 'sradbv2.py')
    for hit in jn['hits']['hits']:
        if hit_filter is None or hit_filter(hit):
            yield hit
    nscrolls = 1
    while num_hits < tot_hits:
        url = sradbv2_scroll_url + '?scroll_id=' + jn['_scroll_id']
        log.info('GET ' + url, 'sradbv2.py')
        response = urlopen(url)
        payload = response.read().decode(encodec)
        jn = json.loads(payload)
        old_num_hits = num_hits
        num_hits += len(jn['hits']['hits'])
        assert num_hits <= tot_hits
        log.info('Writing hits [%d, %d) out of %d, scroll=%d' %
                 (old_num_hits, num_hits, tot_hits, nscrolls), 'sradbv2.py')
        for hit in jn['hits']['hits']:
            if hit_filter is None or hit_filter(hit):
                yield hit
        nscrolls += 1


def count_search(search):
    """
    Return the number of hits satisfying the query; doesn't interrogate the
    hits themselves
    """
    jn, _ = get_payload(search, 1)
    return int(jn['hits']['total'])


def process_search(search, size, gzip_output, output_fn, hit_filter=None):
    jn, encodec = get_payload(search, size)
    with openex(output_fn, 'wb', gzip_output) as fout:
        tot_hits = jn['hits']['total']
        num_hits = len(jn['hits']['hits'])
        assert num_hits <= tot_hits
        hits = jn['hits']['hits']
        filtered_hits = hits
        if hit_filter is not None:
            filtered_hits = list(filter(hit_filter, hits))
        log.info('Writing hits [%d, %d) out of %d' % (0, num_hits, tot_hits), 'sradbv2.py')
        dump = json.dumps(filtered_hits, indent=4).encode('UTF-8')
        if num_hits < tot_hits:
            assert dump.endswith(b']'), dump
            dump = dump[:-1] + b','  # don't prematurely end list
        fout.write(dump)
        nscrolls = 1
        while num_hits < tot_hits:
            url = sradbv2_scroll_url + '?scroll_id=' + jn['_scroll_id']
            log.info('GET ' + url, 'sradbv2.py')
            response = urlopen(url)
            payload = response.read().decode(encodec)
            jn = json.loads(payload)
            old_num_hits = num_hits
            num_hits += len(jn['hits']['hits'])
            assert num_hits <= tot_hits
            hits = jn['hits']['hits']
            filtered_hits = hits
            if hit_filter is not None:
                filtered_hits = list(filter(hit_filter, hits))
            log.info('Writing hits [%d, %d) out of %d, scroll=%d' %
                     (old_num_hits, num_hits, tot_hits, nscrolls), 'sradbv2.py')
            dump = json.dumps(filtered_hits, indent=4).encode('UTF-8')
            assert dump.startswith(b'[')
            dump = dump[1:]  # make one big list, not many little ones
            if num_hits < tot_hits:
                assert dump.endswith(b']'), dump  # don't prematurely end list
                dump = dump[:-1] + b','
            fout.write(dump)
            nscrolls += 1


def hit_search_random(search, limit, size, stop_after, gzip_output, output_fn, hit_filter=None):
    samp = ReservoirSampler(limit)
    for hit in itertools.islice(enumerate(search_iterator(search, size, hit_filter=hit_filter)), stop_after):
        samp.add(hit[1])
    first = True
    with openex(output_fn, 'wt', gzip_output) as fout:
        for hit in samp:
            dump = json.dumps(hit, indent=4).encode('UTF-8')
            dump = ('[' if first else ',') + dump
            first = False
            fout.write(dump)
        fout.write(']')
    assert sanity_check_json(output_fn, gzip_output)


taxa = {'A thaliana': 3702,      # 4. arabidopsis
        'B taurus': 9913,        # 9: cow
        'C elegans': 6239,       # >10: roundworm
        'D rerio': 7955,         # 3: zebrafish
        'D melanogaster': 7227,  # 5: fruitfly
        'H sapiens': 9606,       # 2: human
        'M musculus': 10090,     # 1: mouse
        'O aries': 9940,         # 10: sheep
        'R norvegicus': 10116,   # 7: rat
        'S cerevisiae': 4932,    # 6: yeast
        'Z mays': 4577}          # 8: corn


# experiment.library_selection:"size fractionation"
rna_seq_query = ['experiment.library_strategy:"rna seq"',
                 'experiment.library_source:transcriptomic',
                 'experiment.platform:illumina',
                 'Status:live']

single_cell_query = ['study.abstract:"single-cell"',
                     'experiment.library_construction_protocol:"single-cell"',
                     'study.title:"single-cell"']


def summarize_rna():
    summary = 'Name,Taxon ID,Count,scCount,% sc\n'
    summ_h = defaultdict(list)
    for name, taxid in taxa.items():
        query = 'sample.taxon_id:%d AND %s' % (taxid, ' AND '.join(rna_seq_query))
        #query += ' AND NOT experiment.library_selection:"size fractionation"'
        count = count_search(query)
        sc_query = query + ' AND (' + ' OR '.join(single_cell_query) + ')'
        sc_count = count_search(sc_query)
        summ_h[count].append((name, taxid, count, sc_count))
    for count, tups in sorted(summ_h.items(), reverse=True):
        for tup in tups:
            name, taxid, count, sc_count = tup
            summary += ('%s,%d,%d,%d,%0.1f\n' % (name, taxid, count, sc_count, (100.0 * sc_count) / count))
    return summary


def size_dist(search, size, stop_after, max_n):
    samp = ReservoirSampler(max_n)
    for i, hit in enumerate(search_iterator(search, size)):
        if '_source' not in hit or 'run.bases' not in hit['_source']:
            print('Bad record: ' + str(hit), file=sys.stderr)
        else:
            samp.add(hit['_source']['run.bases'])
            if i >= stop_after-1:
                break
    for n in samp:
        print(n)


def size_bases(search, size, quiet):
    tot = 0
    for i, hit in enumerate(search_iterator(search, size)):
        if '_source' not in hit or 'run.bases' not in hit['_source']:
            if not quiet:
                print('Bad record: ' + str(hit), file=sys.stderr)
        else:
            tot += int(hit['_source']['run.bases'])
    print(tot)


if __name__ == '__main__':
    args = docopt(__doc__)
    log.init_logger(log.LOG_GROUP_NAME,
                    log_ini=os.path.expanduser(args['--log-ini']),
                    agg_level=args['--log-level'])
    try:
        hit_filter = dbgap_filter
        if args['--include-dbgap']:
            hit_filter = None
        if args['search']:
            process_search(args['<lucene-search>'], int(args['--size']),
                           args['--gzip'], args['--output'],
                           hit_filter=hit_filter)
        if args['search-random-subset']:
            hit_search_random(args['<lucene-search>'], int(args['<subset-size>']),
                              int(args['--size']), int(args['--stop-after']),
                              args['--gzip'], args['--output'],
                              hit_filter=hit_filter)
        if args['count']:
            print(count_search(args['<lucene-search>']))
        elif args['summarize-rna']:
            print(summarize_rna())
        elif args['size-dist']:
            size_dist(args['<lucene-search>'], int(args['--size']), int(args['--stop-after']), int(args['<n>']))
        elif args['bases']:
            size_bases(args['<lucene-search>'], int(args['--size']), args['--quiet'])
    except Exception:
        log.error('Uncaught exception:', 'sradbv2.py')
        raise
