#!/usr/bin/env python2.7

# Authors: Chris Wilks (original) and Ben Langmead (modifications)
#    Date: 7/3/2018

import sys
import json
import cgi
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
import argparse
import time
import os

SRAdbV2_URL = 'https://api-omicidx.cancerdatasci.org/sra/1.0/full'
KEY_VALUE_DELIM = '::'
SUBFIELD_DELIM = '|'

nested_fields = {'attributes': ['tag', 'value'],
                 'identifiers': ['id', 'namespace'],
                 'xrefs': ['db', 'id']}


def download_and_extract_fields(args, run_acc, study_acc, header_fields):
    url = "%s/%s" % (SRAdbV2_URL, run_acc)
    response = urlopen(url)
    j, ct = cgi.parse_header(response.headers.get('Content-type', ''))
    encodec = ct.get('charset', 'utf-8')
    payload = response.read().decode(encodec)
    with open("%s.%s.json.temp" % (run_acc, study_acc), "wb") as fout:
        fout.write(str(payload))
    jfields = json.loads(payload)
    header_fields.update(jfields['_source'].keys())


def process_run(args, run_acc, study_acc, header_fields, outfile):
    jfields = None
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
            if subfield_type == 'identifiers':
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


def process_study(args, study_acc, runs_per_study, header_fields):
    header_fields = sorted(list(header_fields))
    outfile = sys.stdout
    if args.nostdout:
        outfile = open('%s.metadata.tsv' % study_acc, 'wb')
    if not args.noheader:
        outfile.write('\t'.join(header_fields) + '\n')
    [process_run(args, run_acc, study_acc, header_fields, outfile) for run_acc in runs_per_study]
    if args.nostdout:
        outfile.close()

def query_iterator(args):
    if args.query_file is not None:
        with open(args.query_file, "rb") as fin:
            for line in fin:
                study_acc, run_acc = line.rstrip().split(b'\t')
                yield study_acc, run_acc
    elif args.queries is not None:
        for pair in args.queries.split(';'):
            if 2 != len(pair.split(',')):
                raise ValueError('Bad argument to --queries')
            study_acc, run_acc = pair.split(',')
            yield study_acc, run_acc
    else:
        raise RuntimeError('Must specify either --queries or --query-file')


def main(args):
    prev_study = None
    runs_per_study = set()
    header_fields = set()
    for study_acc, run_acc in query_iterator(args):
        if study_acc != prev_study:
            if prev_study is not None:
                process_study(args, prev_study, runs_per_study, header_fields)
            runs_per_study = set()
            header_fields = set()
        prev_study = study_acc
        runs_per_study.add(run_acc)
        download_and_extract_fields(args, run_acc, study_acc, header_fields)
        if args.delay > 0:
            time.sleep(args.delay)
    if prev_study is not None:
        process_study(args, prev_study, runs_per_study, header_fields)


def create_parser(disable_header=False):
    parser = argparse.ArgumentParser(
        description='Given a list of SRA run accessions (e.g. SRR2126175) pull down the full metadata from the SRAdbV2 API')
    parser.add_argument('--query-file', metavar='/path/to/file_with_run_accessions', type=str, default=None,
                        help='path to file with list of SRA run accessions')
    parser.add_argument('--queries', metavar='<study1>,<run1>;<study2>,<run2>;...', type=str, default=None,
                        help='list of study/run accession pairs')
    parser.add_argument('--delay', type=int, default=1, help='time to sleep between requests, defaults to 1 sec (1)')
    parser.add_argument('--noheader', action='store_const', const=True, default=False,
                        help='turn off printing header in output')
    parser.add_argument('--nostdout', action='store_const', const=True, default=False,
                        help='output to files named by study accession')
    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    main(args)