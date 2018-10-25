#!/usr/bin/env python

# Authors: Chris Wilks (original) and Ben Langmead (modifications)
#    Date: 7/3/2018
# License: MIT

"""sradbv2

Usage:
  sradbv2 search <lucene-search> [options]
  sradbv2 count <lucene-search> [options]
  sradbv2 size-dist <lucene-search> <n> [options]
  sradbv2 bases <lucene-search> [options]
  sradbv2 size <lucene-search> [options]
  sradbv2 summarize-rna [options]
  sradbv2 query [<SRP>,<SRR>]...  [options]
  sradbv2 query-file <file> [options]

Options:
  --size <size>            Number of records to fetch per call [default: 300].
  --stop-after <num>       Stop processing results after this many [default: 1000000].
  --delay                  Seconds to sleep between requests [default: 1].
  --log-ini <ini>          .ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>      Set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  --noheader               Suppress header in output.
  --nostdout               Output to files named by study accession.
  --gzip                   Gzip outputs.
  --quiet                  Don't complain about bad records.
  --output <name>          Output filename [default: search.json].
  -h, --help               Show this screen.
  --version                Show version.
"""

from __future__ import print_function
import sys
import json
import cgi
import gzip
import random
if sys.version[:1] == '2':
    from urllib import quote
    from urllib2 import urlopen
else:
    from urllib.request import urlopen
    from urllib.parse import quote
import time
import os
from docopt import docopt
from collections import defaultdict
import log


sradbv2_api_url = 'https://api-omicidx.cancerdatasci.org/sra/1.0'
sradbv2_full_url = sradbv2_api_url + '/full'
sradbv2_scroll_url = sradbv2_api_url + '/scroll'
sradbv2_search_url = sradbv2_api_url + '/search/full'
KEY_VALUE_DELIM = '::'
SUBFIELD_DELIM = '|'

nested_fields = {'attributes': ['tag', 'value'],
                 'identifiers': ['id', 'namespace'],
                 'xrefs': ['db', 'id']}


def search_iterator(search, size):
    url = '%s?q=%s&size=%d' % (sradbv2_search_url, quote(search), size)
    log.info('GET ' + url, 'sradbv2.py')
    response = urlopen(url)
    j, ct = cgi.parse_header(response.headers.get('Content-type', ''))
    encodec = ct.get('charset', 'utf-8')
    log.info('Charset: ' + encodec, 'sradbv2.py')
    payload = response.read().decode(encodec)
    jn = json.loads(payload)
    tot_hits = jn['hits']['total']
    num_hits = len(jn['hits']['hits'])
    assert num_hits <= tot_hits
    log.info('Writing hits [%d, %d) out of %d' % (0, num_hits, tot_hits), 'sradbv2.py')
    for hit in jn['hits']['hits']:
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
            yield hit
        nscrolls += 1


def download_and_extract_fields(run_acc, study_acc, header_fields):
    url = "%s/%s" % (sradbv2_full_url, run_acc)
    response = urlopen(url)
    j, ct = cgi.parse_header(response.headers.get('Content-type', ''))
    encodec = ct.get('charset', 'utf-8')
    payload = response.read().decode(encodec)
    with open("%s.%s.json.temp" % (run_acc, study_acc), "wb") as fout:
        fout.write(payload.encode())
    jfields = json.loads(payload)
    header_fields.update(jfields['_source'].keys())


def process_run(run_acc, study_acc, header_fields, outfile):
    infile = "%s.%s.json.temp" % (run_acc, study_acc)
    with open(infile, "rb") as fin:
        jfields = json.load(fin)
    os.unlink(infile)
    for (i, field) in enumerate(header_fields):
        if i != 0:
            outfile.write('\t')
        # skip missing field
        if field not in jfields['_source']:
            continue
        value = jfields['_source'][field]
        if field == 'run_reads':
            idx = 0
            if len(value) == 2:
                idx = 1
            outfile.write(str(value[idx]["base_coord"]))
            continue
        fields = field.split('_')
        subfield_type = fields[1]
        if len(fields) == 2 and subfield_type in nested_fields:
            tag_name = nested_fields[subfield_type][0]
            value_name = nested_fields[subfield_type][1]
            if subfield_type == b'identifiers':
                temp = tag_name
                tag_name = value_name
                value_name = temp
            for (j, subfield) in enumerate(value):
                if j != 0:
                    outfile.write(SUBFIELD_DELIM)
                outfile.write(subfield[tag_name] + KEY_VALUE_DELIM + subfield[value_name])
            continue
        # for the Unicode strings we assume to be here
        try:
            outfile.write(value.encode('utf-8'))
        # otherwise just convert non-string types to standard strings
        except AttributeError:
            outfile.write(str(value))
    outfile.write('\n')


def process_study(study_acc, runs_per_study, header_fields, nostdout, noheader):
    header_fields = sorted(list(header_fields))
    outfile = sys.stdout
    if nostdout:
        outfile = open('%s.metadata.tsv' % study_acc, 'wb')
    if not noheader:
        outfile.write(b'\t'.join(header_fields) + b'\n')
    [process_run(run_acc, study_acc, header_fields, outfile) for run_acc in runs_per_study]
    if nostdout:
        outfile.close()


def query_string_iterator(sts):
    for st in sts:
        if not st.count(',') == 1:
            raise ValueError('Bad query argument: "%s"' % st)
        study_acc, run_acc = st.split(',')
        yield study_acc, run_acc


def query_file_iterator(fn):
    with open(fn, "rb") as fin:
        for line in fin:
            study_acc, run_acc = line.rstrip().split(b'\t')
            yield study_acc, run_acc


def query(delay, nostdout, noheader, query_string=None, query_file=None):
    prev_study = None
    runs_per_study = set()
    header_fields = set()
    header_fields_vec = []
    it = query_string_iterator(query_string) if query_string else query_file_iterator(query_file)
    for study_acc, run_acc in it:
        if study_acc != prev_study:
            if prev_study is not None:
                process_study(prev_study, runs_per_study, header_fields, nostdout, noheader)
            runs_per_study = set()
            header_fields = set()
        prev_study = study_acc
        runs_per_study.add(run_acc)
        download_and_extract_fields(run_acc, study_acc, header_fields)
        header_fields_vec.append(len(header_fields))
        if delay > 0:
            time.sleep(delay)
    if prev_study is not None:
        process_study(prev_study, runs_per_study, header_fields, nostdout, noheader)


def openex(fn, mode, gzip_output):
    if gzip_output:
        return gzip.open(fn + '.gz', mode)
    else:
        return open(fn, mode)


def count_search(search):
    """
    Return the number of hits satisfying the query
    """
    url = '%s?q=%s&size=1' % (sradbv2_search_url, quote(search))
    log.info('GET ' + url, 'sradbv2.py')
    response = urlopen(url)
    j, ct = cgi.parse_header(response.headers.get('Content-type', ''))
    encodec = ct.get('charset', 'utf-8')
    log.info('Charset: ' + encodec, 'sradbv2.py')
    jn = json.loads(response.read().decode(encodec))
    return int(jn['hits']['total'])


def process_search(search, size, gzip_output, output_fn):
    url = '%s?q=%s&size=%d' % (sradbv2_search_url, quote(search), size)
    log.info('GET ' + url, 'sradbv2.py')
    response = urlopen(url)
    j, ct = cgi.parse_header(response.headers.get('Content-type', ''))
    encodec = ct.get('charset', 'utf-8')
    log.info('Charset: ' + encodec, 'sradbv2.py')
    payload = response.read().decode(encodec)
    with openex(output_fn, 'wb', gzip_output) as fout:
        jn = json.loads(payload)
        tot_hits = jn['hits']['total']
        num_hits = len(jn['hits']['hits'])
        assert num_hits <= tot_hits
        log.info('Writing hits [%d, %d) out of %d' % (0, num_hits, tot_hits), 'sradbv2.py')
        dump = json.dumps(jn['hits']['hits'], indent=4).encode('UTF-8')
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
            log.info('Writing hits [%d, %d) out of %d, scroll=%d' %
                     (old_num_hits, num_hits, tot_hits, nscrolls), 'sradbv2.py')
            dump = json.dumps(jn['hits']['hits'], indent=4).encode('UTF-8')
            assert dump.startswith(b'[')
            dump = dump[1:]  # make one big list, not many little ones
            if num_hits < tot_hits:
                assert dump.endswith(b']'), dump  # don't prematurely end list
                dump = dump[:-1] + b','
            fout.write(dump)
            nscrolls += 1


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


rna_seq_query = ['experiment_library_strategy:"rna seq"',
                 'experiment_library_source:transcriptomic',
                 'experiment_platform:illumina']

single_cell_query = ['study_abstract:"single-cell"',
                     'experiment_library_construction_protocol:"single-cell"',
                     'study_title:"single-cell"']


def summarize_rna():
    summary = 'Name,Taxon ID,Count,scCount,% sc\n'
    summ_h = defaultdict(list)
    for name, taxid in taxa.items():
        query = 'sample_taxon_id:%d AND %s' % (taxid, ' AND '.join(rna_seq_query))
        count = count_search(query)
        sc_query = query + ' AND (' + ' OR '.join(single_cell_query) + ')'
        sc_count = count_search(sc_query)
        summ_h[count].append((name, taxid, count, sc_count))
    for count, tups in sorted(summ_h.items(), reverse=True):
        for tup in tups:
            name, taxid, count, sc_count = tup
            summary += ('%s,%d,%d,%d,%0.1f\n' % (name, taxid, count, sc_count, (100.0 * sc_count) / count))
    return summary


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


def size_dist(search, size, stop_after, max_n):
    samp = ReservoirSampler(max_n)
    for i, hit in enumerate(search_iterator(search, size)):
        if '_source' not in hit or 'run_bases' not in hit['_source']:
            print('Bad record: ' + str(hit), file=sys.stderr)
        else:
            samp.add(hit['_source']['run_bases'])
            if i >= stop_after-1:
                break
    for n in samp:
        print(n)


def size_bases(search, size, quiet):
    tot = 0
    for i, hit in enumerate(search_iterator(search, size)):
        if '_source' not in hit or 'run_bases' not in hit['_source']:
            if not quiet:
                print('Bad record: ' + str(hit), file=sys.stderr)
        else:
            tot += int(hit['_source']['run_bases'])
    print(tot)


if __name__ == '__main__':
    args = docopt(__doc__)
    log.init_logger(log.LOG_GROUP_NAME,
                    log_ini=os.path.expanduser(args['--log-ini']),
                    agg_level=args['--log-level'])
    try:
        if args['search']:
            # sample_taxon_id:6239 AND experiment_library_strategy:"rna seq" AND experiment_library_source:transcriptomic AND experiment_platform:illumina
            process_search(args['<lucene-search>'], int(args['--size']), args['--gzip'], args['--output'])
        if args['count']:
            print(count_search(args['<lucene-search>']))
        elif args['query']:
            query(args['--delay'], args['--nostdout'], args['--noheader'], query_string=args['<SRP>,<SRR>'])
        elif args['query-file']:
            query(args['--delay'], args['--nostdout'], args['--noheader'], query_file=args['<file>'])
        elif args['summarize-rna']:
            print(summarize_rna())
        elif args['size-dist']:
            size_dist(args['<lucene-search>'], int(args['--size']), int(args['--stop-after']), int(args['<n>']))
        elif args['bases']:
            size_bases(args['<lucene-search>'], int(args['--size']), args['--quiet'])
    except Exception:
        log.error('Uncaught exception:', 'sradbv2.py')
        raise
