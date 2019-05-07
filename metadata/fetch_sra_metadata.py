#script to write out jobs to download all of SRA human & mouse RNA-seq metadata
import sys
from Bio import Entrez as e
#required to set an email
e.email="downloadsRUs@dos.com"
#capture 1) Illumina 2) RNA-Seq 3) human 4) transriptome sources 5) public access (non-dbgap)
#for scRNA maybe use "TRANSCRIPTOMIC SINGLE CELL" as Source argument instead of transcriptomic?
#base_query = '((((illumina[Platform]) AND rna seq[Strategy]) AND transcriptomic[Source]) AND public[Access])'
base_query = '((((illumina[Platform]) AND rna seq[Strategy]) AND transcriptomic single cell[Source]) AND public[Access])'
#prepend "[Organism]" to each of these in the search text
organisms=['human','mouse']
if len(sys.argv) > 1:
    organisms = [sys.argv[1]]

#max number of records allowed to be fetched at once using EFetch
#return_max=1000
return_max=1000

for orgn in organisms:
    es_ = e.esearch(db="sra",retmax=1,term=base_query+" AND %s[Organism]" % orgn,usehistory=True)
    es = e.read(es_)
    #number of records is # of EXPERIMENTs (SRX) NOT # RUNs (SRR)
    total_records = int(es["Count"])
    sys.stderr.write("Total # of records is %d for %s using query %s\n" % (total_records, orgn, base_query+" and %s[Organism]" % orgn))
    num_fetches = int(total_records / return_max) + 1
    for retstart_idx in range(0,num_fetches):
        start_idx = retstart_idx * return_max
        end_idx = (start_idx + return_max)-1
        #jobs to fetch the raw xml records
        sys.stdout.write('curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=sra&query_key=%s&WebEnv=%s&api_key=737c03e5774d846960b50f1c90848fed3e08&retmode=xml&retstart=%d&retmax=%d" > sra_xmls/%s.sra.rnaseq.illumina.public.xml.%d\n' % (es["QueryKey"], es["WebEnv"], start_idx, return_max, orgn, start_idx))
