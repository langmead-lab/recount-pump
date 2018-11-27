import os
import sys
import os
import shutil
from collections import OrderedDict
import pyBigWig

#from https://github.com/deeptools/deepTools/blob/38cfe39e3b3c82bbc0c2013e3068bd71adc3a9cb/deeptools/writeBedGraph.py#L284
#chromSizes is just a list of chromosome IDs and sizes, e.g.: [("1", 1000000), ("2", 1500000)]
#this is modified to do streaming conversion and extracts the list of chromosomes and their lenth from the BAM as the first part of the stream
def bedGraphToBigWig(bedGraphFileHandle, bigWigPath):
    """
    Takes a stream of  sorted list of bedgraph-formatted intervals and write them to a single bigWig file using pyBigWig.
    The order of chromosomes and length of chromosomes from the BAM header is expected as the first part of the stream.
    """
    bw = pyBigWig.open(bigWigPath, "w")
    assert(bw is not None)
    starts = []
    ends = []
    vals = []
    chromSizes = []
    FIRST = True
    for line in bedGraphFileHandle:
        fields = line.rstrip().split('\t')
        #first lines should be BAM header, to get the chromosome sizes and order
        if line[0] == '@':
            if fields[0] != '@SQ':
                continue
            #parse sam formatted chromsome size fields: e.g. @SQ     SN:11   LN:135006516
            chromSizes.append((fields[1].split(':')[1], int(fields[2].split(':')[1])))
            continue
        #input: samtools depth output format: chrm pos count
        (chrm, pos, cov) = fields
        pos = int(pos)
        cov = float(cov)
        # Buffer up to a million entries
        if FIRST or (chrm == prev_chrm and cov == prev_cov and pos == prev_end+1):
            if FIRST:
                bw.addHeader(chromSizes, maxZooms=10)
                #[sys.stdout.write("%s\t%d\n" % (x[0],x[1])) for x in chromSizes]
                prev_start = pos
            FIRST = False
        else:
            if prev_chrm is not None:
                starts.append(prev_start - 1)
                ends.append(prev_end)
                vals.append(prev_cov)
            if len(starts) >= 1000000 or (prev_chrm is not None and chrm != prev_chrm):
                bw.addEntries([prev_chrm] * len(starts), starts, ends=ends, values=vals)
                starts = []
                ends = []
                vals = []
            prev_start = pos
        prev_chrm = chrm
        prev_end = pos
        prev_cov = cov

    if prev_chrm is not None:
        starts.append(prev_start - 1)
        ends.append(prev_end)
        vals.append(prev_cov)
        bw.addEntries([prev_chrm] * len(starts), starts, ends=ends, values=vals)
    bw.close()

bedgraphfile = sys.argv[1]
bedGraphToBigWig(sys.stdin, "%s.bw" % (bedgraphfile))
