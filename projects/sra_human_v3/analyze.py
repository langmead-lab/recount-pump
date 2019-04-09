#!/usr/bin/env python

from __future__ import print_function
import sys
import json
import re
import datetime


sc1 = re.compile('single.cell')
sc2 = re.compile('scrna')


def go():
    if len(sys.argv) < 2:
        raise RuntimeError('Must specify input JSON as first arg')
    for fn in sys.argv[1:]:
        with open(fn, 'rt') as fh:
            js = json.loads(fh.read())
            for j in js:
                single_cell = False
                jsrc = j['_source']
                assert 'study' in jsrc, j
                assert 'title' in jsrc['study'], j
                assert 'experiment' in jsrc, j
                srr = jsrc['accession']
                srp = jsrc['study']['accession']
                study_title = jsrc['study']['title'].lower()
                library_protocol, experiment_design, study_abstract = '', '', ''
                if 'abstract' in jsrc['study']:
                    study_abstract = jsrc['study']['abstract'].lower()
                if 'design' in jsrc['experiment']:
                    experiment_design = jsrc['experiment']['design'].lower()
                if 'library_construction_protocol' in jsrc['experiment']:
                    library_protocol = jsrc['experiment']['library_construction_protocol'].lower()
                if sc1.search(study_abstract) or sc2.search(study_abstract) or \
                        sc1.search(library_protocol) or sc2.search(library_protocol) or \
                        sc1.search(study_title) or sc2.search(study_title) or \
                        sc1.search(experiment_design) or sc2.search(experiment_design):
                    single_cell = True
                received_time = datetime.datetime.fromtimestamp(int(jsrc["Received"])/1000)
                last_update_time = datetime.datetime.fromtimestamp(int(jsrc["LastUpdate"])/1000)
                print(','.join(map(str, [srr, srp, single_cell,
                                         received_time.year, received_time.month, received_time.day,
                                         last_update_time.year, last_update_time.month, last_update_time.day])))


if __name__ == '__main__':
    go()
