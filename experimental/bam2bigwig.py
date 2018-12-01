import sys
import pyBigWig

#takes 0-base bedGraph input (not samtools depth output)

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
    prev_chrm = None
    prev_end = None
    for line in bedGraphFileHandle:
        fields = line.rstrip().split('\t')
        #first lines should be BAM header, to get the chromosome sizes and order
        if line[0] == '@':
            if fields[0] != '@SQ':
                continue
            #parse sam formatted chromsome size fields: e.g. @SQ     SN:11   LN:135006516
            chromSizes.append((fields[1].split(':')[1], int(fields[2].split(':')[1])))
            continue
        #input from mosdepth
        (chrm, start, end, cov) = fields[:4]
        start = int(start)
        end = int(end)
        cov = float(cov)
        if FIRST:
            bw.addHeader(chromSizes, maxZooms=10)
            chromSizesMap = dict(chromSizes)
            FIRST = False
        if prev_chrm is not None and chrm != prev_chrm and prev_end != chromSizesMap[prev_chrm]:
            starts.append(prev_end)
            ends.append(chromSizesMap[prev_chrm])
            vals.append(0.0)
        # Buffer up to a million entries
        if len(starts) >= 1000000 or (prev_chrm is not None and prev_chrm != chrm):
            #print (prev_chrm, starts, ends)
            bw.addEntries([prev_chrm] * len(starts), starts, ends=ends, values=vals)
            starts = []
            ends = []
            vals = []
        if chrm != prev_chrm and start != 0:
            starts.append(0)
            ends.append(start)
            vals.append(0.0)
        prev_chrm = chrm
        prev_end = end 
        starts.append(start)
        ends.append(end)
        vals.append(cov)

    if len(starts) > 0:
        if prev_end != chromSizesMap[prev_chrm]:
            starts.append(prev_end)
            ends.append(chromSizesMap[prev_chrm])
            vals.append(0.0)
        bw.addEntries([prev_chrm] * len(starts), starts, ends=ends, values=vals)
    bw.close()


def go():
    bedGraphToBigWig(sys.stdin, sys.argv[1])


if __name__ == '__main__':
    go()
