import os
import sys
import os
import shutil
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
    chromSizesMap = {}
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
                chromSizesMap = dict(chromSizes)
                prev_start = pos
                if prev_start > 1:
                    starts.append(0)
                    ends.append(prev_start - 1)
                    vals.append(0.0)
            FIRST = False
        else:
            if prev_chrm is not None:
                starts.append(prev_start - 1)
                ends.append(prev_end)
                vals.append(prev_cov)
                prev_chrm_size = chromSizesMap[prev_chrm]
                if chrm != prev_chrm and prev_end < prev_chrm_size:
                    starts.append(prev_end)
                    ends.append(prev_chrm_size)
                    vals.append(0.0)
            if len(starts) >= 1000000 or (prev_chrm is not None and chrm != prev_chrm):
                bw.addEntries([prev_chrm] * len(starts), starts, ends=ends, values=vals)
                starts = []
                ends = []
                vals = []
            #need to fill in the 0'd bases which are left as gaps by samtools depth
            if chrm != prev_chrm and pos > 1:
                starts.append(0)
                ends.append(pos - 1)
                vals.append(0.0)
            elif chrm == prev_chrm and pos > prev_end + 1:
                starts.append(prev_end)
                ends.append(pos - 1)
                vals.append(0.0)

            prev_start = pos
        prev_chrm = chrm
        prev_end = pos
        prev_cov = cov

    if prev_chrm is not None:
        starts.append(prev_start - 1)
        ends.append(prev_end)
        vals.append(prev_cov)
        prev_chrm_size = chromSizesMap[prev_chrm]
        if prev_end < prev_chrm_size:
            starts.append(prev_end)
            ends.append(prev_chrm_size)
            vals.append(0.0)
        bw.addEntries([prev_chrm] * len(starts), starts, ends=ends, values=vals)
    bw.close()

bedgraphfile = sys.argv[1]
bedGraphToBigWig(sys.stdin, "%s.bw" % (bedgraphfile))
