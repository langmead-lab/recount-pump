#!/usr/bin/env python

# Authors: Chris Wilks (original) and Ben Langmead (modifications)
#    Date: 7/3/2018
# License: MIT

"""sradbv2q

Usage:
  sradbv2q query [<SRP>,<SRR>]...  [options]
  sradbv2q query-file <file> [options]

Options:
  --delay                  Seconds to sleep between requests [default: 1].
  --log-ini <ini>          .ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>      Set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  --noheader               Suppress header in output.
  --nostdout               Output to files named by study accession.
  --output <name>          Output filename [default: search.json].
  -h, --help               Show this screen.
"""

from __future__ import print_function
import sys
import json
import cgi
if sys.version[:1] == '2':
    from urllib2 import urlopen
else:
    from urllib.request import urlopen
import time
import os
from docopt import docopt
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
        if field == 'run.reads':
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


if __name__ == '__main__':
    args = docopt(__doc__)
    log.init_logger(log.LOG_GROUP_NAME,
                    log_ini=os.path.expanduser(args['--log-ini']),
                    agg_level=args['--log-level'])
    try:
        if args['query']:
            query(args['--delay'], args['--nostdout'], args['--noheader'], query_string=args['<SRP>,<SRR>'])
        elif args['query-file']:
            query(args['--delay'], args['--nostdout'], args['--noheader'], query_file=args['<file>'])
    except Exception:
        log.error('Uncaught exception:', 'sradbv2q.py')
        raise
