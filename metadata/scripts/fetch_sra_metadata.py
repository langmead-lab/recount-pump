#script to write out jobs to download all of SRA human & mouse RNA-seq metadata
import sys
import argparse
from Bio import Entrez as e

scriptpath = os.path.dirname(sys.argv[0])
#required to set an email
e.email="downloadsRUs@dos.com"
#capture 1) Illumina 2) RNA-Seq 3) human 4) transriptome sources 5) public access (non-dbgap)
#from Princy Parsana:
#add "NOT size fractionation[Selection]" to remove smallRNA runs

parser = argparse.ArgumentParser(description='query NCBI SRA')
parser.add_argument('--org', metavar='organism', type=str, default='human', help='biological organism to query (human [default], mouse)')
parser.add_argument('--xml-path', metavar='path to save XML downloads', type=str, default='xmls', help='XML files from SRA will be downloaded here, default="xmls"')
parser.add_argument('--err-path', metavar='path to save error output files', type=str, default='errs', help='error files from SRA will be stored here, default="errs"')
parser.add_argument('--batch-size', metavar='0', type=int, default=500, help='number of full records to retrieve in a single curl job')
parser.add_argument('--non-transcriptomic', action='store_const', const=True, default=False, help='switch to non-transcriptomic querying')
parser.add_argument('--start-date', metavar='YYYY/MM/DD', type=str, default=None, help='start of date range to query within, applied against both Modification Date & Publication Date, if set assume incremental querying, default: None')
    
args = parser.parse_args()

#always query for: Illumina + RNA-seq + Transcriptomic source + public while skipping smallRNAs
base_query = '(((((illumina[Platform]) AND rna seq[Strategy]) AND transcriptomic[Source]) AND public[Access]) NOT size fractionation[Selection])'

xml_path = args.xml_path
err_path = sys.err_path

#example data range: AND (("2019/10/06"[Publication Date] : "5000"[Publication Date]) OR ("2019/10/06"[Modification Date] : "5000"[Modification Date]))

if args.non_transcriptomic:
    base_query = base_query.replace('AND transcriptomic','NOT transcriptomic')

#check if we're doing an incremental
if args.start_date is not None:
    base_query = '(' + base_query + ' AND (("%s"[Publication Date] : "5000"[Publication Date]) OR ("%s"[Modification Date] : "5000"[Modification Date]))' % (args.start_date, args.start_date)

sys.stdout.write("REMEMBER: NCBI query history is only good for so long (typically <1 day), so the fetch jobs must be run shortly after runnning this script!\n")

patt = re.compile(r'\s+')
orgn_nospace = re.sub(patt, r'_', args.orgn)
fetchOut = open("fetch_%s.jobs" % (orgn_nospace),"w")
parseOut = open("parse_%s.sh" % (orgn_nospace),"w")

es_ = e.esearch(db="sra",retmax=1,term=base_query+" AND %s[Organism]" % args.orgn, usehistory=True)
es = e.read(es_)

#number of records is # of EXPERIMENTs (SRX) NOT # RUNs (SRR)
total_records = int(es["Count"])
sys.stderr.write("Total # of records is %d for %s using query %s\n" % (total_records, orgn, base_query+" and %s[Organism]" % orgn))

num_fetches = int(total_records / args.batch_size) + 1
parseOut.write("python %s/sraXML2TSV.py %s/%s.sra.rnaseq.illumina.public.xml.%d > all_%s_sra.tsv 2> %s/%s.sra.rnaseq.illumina.public.xml.%d.parse_err\n" % (scriptpath, xml_path, orgn_nospace, 0, orgn_nospace, err_path, orgn_nospace, 0))

for retstart_idx in range(0,num_fetches):
    start_idx = retstart_idx * args.batch_size
    end_idx = (start_idx + args.batch_size)-1
    #jobs to fetch the raw xml records
    fetchOut.write('curl --retry-all-errors 10 --retry-max-time 600 "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=sra&query_key=%s&WebEnv=%s&api_key=737c03e5774d846960b50f1c90848fed3e08&retmode=xml&retstart=%d&retmax=%d" > %s/%s.sra.rnaseq.illumina.public.xml.%d 2> %s/%s.sra.rnaseq.illumina.public.xml.%d.err\n' % (es["QueryKey"], es["WebEnv"], start_idx, args.batch_size, xml_path, orgn_nospace, start_idx, err_path, orgn_nospace, start_idx))
    #write out post-fetch parsing job as well (separately run)
    if retstart_idx > 0:
        parseOut.write("python %s/sraXML2TSV.py %s/%s.sra.rnaseq.illumina.public.xml.%d >> all_%s_sra.tsv 2> %s/%s.sra.rnaseq.illumina.public.xml.%d.parse_err\n" % (scriptpath, xml_path, orgn_nospace, start_idx, orgn_nospace, err_path, orgn_nospace, start_idx))
fetchOut.close()
parseOut.close()
