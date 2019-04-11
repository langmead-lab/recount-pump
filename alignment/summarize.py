#!/usr/bin/env python

from __future__ import print_function
import os
import sys

with open('accuracy.csv', 'wt') as ofh:
    ofh.write('samp,tool,paired,ann,twopass,inton,alignment,softclip,baselev,measure,value\n')
    for dir, subdirs, files in os.walk('output'):
        for fn in files:
            if fn == 'perform_summary' or fn == 'perform_intron_recovery_summary' or \
               fn == 'perform_mapping_accuracy_summary' or fn == 'perform_mapping_accuracy_SC_summary':
                print("Found summary: %s/%s" % (dir, fn), file=sys.stderr)
                dir_parts = dir.split('/')
                #expt, tool, samp = dir_parts[-1], dir_parts[-2], dir_parts[-3]
                assert dir_parts[0] == 'output'
                tool = 'star'
                samp = dir_parts[1]
                expt = dir_parts[2]
                if expt.endswith('_male'):
                    expt = expt[:-5]
                if expt.endswith('_female'):
                    expt = expt[:-7]
                intron = 'T' if fn == 'perform_intron_recovery_summary' else 'F'
                alignment = 'T' if 'mapping' in fn else 'F'
                softclip = 'T' if 'accuracy_SC' in fn else 'F'
                paired = 'T' if '_paired_' in expt else 'F'
                ann = 'F'
                pass2 = 'F'
                #ann = 'T' if expt.startswith('ann_') else 'F'
                #pass2 = 'T' if expt.endswith('_2pass') else 'F'
                with open(os.path.join(dir, fn), 'rt') as fh:
                    for ln in fh:
                        toks = ln.rstrip().split('\t')
                        assert len(toks) == 2 or len(toks) == 3, (dir, fn, str(toks))
                        if len(toks) == 3:
                            rec1 = [samp, tool, paired, ann, pass2, intron, alignment, softclip, 'T', toks[0], toks[1]]
                            rec2 = [samp, tool, paired, ann, pass2, intron, alignment, softclip, 'F', toks[0], toks[2]]
                            ofh.write(','.join(rec1) + '\n')
                            ofh.write(','.join(rec2) + '\n')
                        else:
                            rec = [samp, tool, paired, ann, pass2, intron, alignment, softclip, 'F'] + toks
                            ofh.write(','.join(rec) + '\n')
    

# with open('times.csv', 'wt') as ofh:
#     for dir, subdirs, files in os.walk('output'):
#         for file in files:
#             if file.endswith('_times.log'):
#                 print("Found timing results: %s/%s" % (dir, file), file=sys.stderr)
#                 #tool = file.split('_')[0]
#                 tool = 'star'
#                 samp = file[len(tool)+1:-len('_times.log')]
#                 recs = []
#                 with open(os.path.join(dir, file), 'rt') as fh:
#                     for ln in fh:
#                         if len(ln.strip()) == 0:
#                             continue
#                         if ln.split()[0] == 'real':
#                             time = ln.rstrip().split()[-1]
#                             recs.append(time)
#                 if len(recs) == 4:
#                     ofh.write(','.join([samp, tool] + recs) + '\n')
