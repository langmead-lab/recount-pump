#script to write out jobs to download all of SRA human & mouse RNA-seq metadata
import sys
from Bio import Entrez as e
#required to set an email
e.email="downloadsRUs@dos.com"
#capture 1) Illumina 2) RNA-Seq 3) human 4) transriptome sources 5) public access (non-dbgap)
#from Princy Parsana:
#add "NOT size fractionation[Selection]" to remove smallRNA runs
#main SRA rna-seq query (public)
incremental_query = '((((((illumina[Platform]) AND rna seq[Strategy]) AND transcriptomic[Source]) AND public[Access]) AND (("2019/04/01"[Publication Date] : "2019/10/01"[Publication Date]) OR ("2019/04/01"[Modification Date] : "2019/10/01"[Modification Date]))) NOT size fractionation[Selection])'

#human incremental_query = '((((((illumina[Platform]) AND rna seq[Strategy]) AND transcriptomic[Source]) AND public[Access]) AND (("2019/10/06"[Publication Date] : "3000"[Publication Date]) OR ("2019/10/06"[Modification Date] : "3000"[Modification Date]))) NOT size fractionation[Selection]) AND human[Organism]'

#human original_query = '((((((illumina[Platform]) AND rna seq[Strategy]) AND transcriptomic[Source]) AND public[Access]) AND (("2000/10/06"[Publication Date] : "2019/10/06"[Publication Date]) OR ("2000/10/06"[Modification Date] : "2019/10/06"[Modification Date]))) NOT size fractionation[Selection]) AND human[Organism]'

#mouse original_query = '((((((illumina[Platform]) AND rna seq[Strategy]) AND transcriptomic[Source]) AND public[Access]) AND (("2000/10/06"[Publication Date] : "2020/01/08"[Publication Date]) OR ("2000/01/08"[Modification Date] : "2020/01/08"[Modification Date]))) NOT size fractionation[Selection]) AND mouse[Organism]'

#mouse incremental_query = '((((((illumina[Platform]) AND rna seq[Strategy]) AND transcriptomic[Source]) AND public[Access]) AND (("2020/01/08"[Publication Date] : "3000"[Publication Date]) OR ("2020/01/08"[Modification Date] : "3000"[Modification Date]))) NOT size fractionation[Selection]) AND mouse[Organism]'

base_query = '(((((illumina[Platform]) AND rna seq[Strategy]) AND transcriptomic[Source]) AND public[Access]) NOT size fractionation[Selection])'

if len(sys.argv) < 4:
    sys.stderr.write("must submit 1) >= 1 organisms (e.g. \"human,mouse\") 2) path to output of raw SRA XMLs (e.g. sra_xmls) 3) path to output of parsing errors (e.g. parse_errs), exiting\n")
    sys.exit(-1)

organisms = sys.argv[1].split(',')
organisms_nospaces = sys.argv[2].split(',')
xml_path = sys.argv[3]
err_path = sys.argv[4]
if len(sys.argv) > 5:
    flag = int(sys.argv[5])
    if flag > 1:
        base_query = incremental_query
    if flag == 1 or flag == 3:
        base_query = base_query.replace('AND transcriptomic','NOT transcriptomic')

sys.stdout.write("REMEMBER: NCBI query history is only good for so long (typically <1 day), so the fetch jobs must be run shortly after runnning this script!\n")
#number of records to be fetched at once using EFetch
return_max=1000
for (i,orgn) in enumerate(organisms):
    orgn_nospace = organisms_nospaces[i]
    fetchOut = open("fetch_%s.jobs" % (orgn_nospace),"w")
    parseOut = open("parse_%s.sh" % (orgn_nospace),"w")
    es_ = e.esearch(db="sra",retmax=1,term=base_query+" AND %s[Organism]" % orgn,usehistory=True)
    es = e.read(es_)
    #number of records is # of EXPERIMENTs (SRX) NOT # RUNs (SRR)
    total_records = int(es["Count"])
    sys.stderr.write("Total # of records is %d for %s using query %s\n" % (total_records, orgn, base_query+" and %s[Organism]" % orgn))
    num_fetches = int(total_records / return_max) + 1
    parseOut.write("python sraXML2TSV.py %s/%s.sra.rnaseq.illumina.public.xml.%d > all_%s_sra.tsv 2> %s/%s.sra.rnaseq.illumina.public.xml.%d.parse_err\n" % (xml_path, orgn_nospace, 0, orgn_nospace, err_path, orgn_nospace, 0))
    for retstart_idx in range(0,num_fetches):
        start_idx = retstart_idx * return_max
        end_idx = (start_idx + return_max)-1
        #jobs to fetch the raw xml records
        fetchOut.write('curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=sra&query_key=%s&WebEnv=%s&api_key=737c03e5774d846960b50f1c90848fed3e08&retmode=xml&retstart=%d&retmax=%d" > %s/%s.sra.rnaseq.illumina.public.xml.%d 2> %s/%s.sra.rnaseq.illumina.public.xml.%d.err\n' % (es["QueryKey"], es["WebEnv"], start_idx, return_max, xml_path, orgn_nospace, start_idx, err_path, orgn_nospace, start_idx))
        #write out post-fetch parsing job as well (separately run)
        if retstart_idx > 0:
            parseOut.write("python sraXML2TSV.py %s/%s.sra.rnaseq.illumina.public.xml.%d >> all_%s_sra.tsv 2> %s/%s.sra.rnaseq.illumina.public.xml.%d.parse_err\n" % (xml_path, orgn_nospace, start_idx, orgn_nospace, err_path, orgn_nospace, start_idx))
    fetchOut.close()
    parseOut.close()
