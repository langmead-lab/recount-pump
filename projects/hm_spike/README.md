A collection of run accessions that we want to include consistently in future projects so we can sanity-check that the pipeline is deterministic and hasn't undergone unexpected changes.  This collection includes both human and mouse RNA-seq, and both bulk and single-cell.  The idea is for this collection to represent an interesting breadth of cases, including the case where the donor genome is mismatched with the reference files.

## GEUV

We took a list of 28 samples, chosen to represent different ethnicities, from the GEUVADIS study:

https://raw.githubusercontent.com/nellore/rail/master/eval/GEUVADIS_28.manifest

```bash
# GEUVADIS
url="https://raw.githubusercontent.com/nellore/rail/master/eval/GEUVADIS_28.manifest"
for srr in $(curl ${url} | awk '{print $1}' | grep '^ftp' | awk -v FS='/' '{print $7}')
do
    python -m metadata.sradbv2 search "study.run:${srr}"
    grep '"_id' search.json | sed 's/.*: "//' | sed 's/".*//' | sed 's/^/human_bulk_spike /'
done
```

## Human single-cell

From [study abstract](https://www.ncbi.nlm.nih.gov/sra/SRX1457279[accn]):

"Cells were loaded into the Fluidigm C1 microfluidic platform, where single cells were captured. Lysis of single cells, reverse-transcription of mRNA into cDNA as well as preamplification of cDNA occured within the microfluidic device using reagents provided by Fluidigm as well as the SMARTer Ultra Low RNA kit for Illumina (Clontech). External RNA spike-in transcripts (ERCC spike-in Mix, Ambion) were added to all single cell lysis reactions at a dilution of 1:40,000. Libraries were prepared using Illumina Nextera XT kit per illumina's protocols."

```bash
python -m metadata.sradbv2 search-random-subset 'study.accession:SRP066834' 20
grep '"_id' search.json | sed 's/.*: "//' | sed 's/".*//' | sed 's/^/human_sc_spike /'
```

## Mouse

From MouseENCODE:

```bash
python -m metadata.sradbv2 search-random-subset 'study.accession:SRP006787' 20
grep '"_id' search.json | sed 's/.*: "//' | sed 's/".*//' | sed 's/^/mouse_bulk_spike /'
```

## Mouse single-cell

10x data from Tabular Muris study:

```bash
python -m metadata.sradbv2 search-random-subset 'study.accession:SRP131661' 20 --stop-after 1000
grep '"_id' search.json | sed 's/.*: "//' | sed 's/".*//' | sed 's/^/mouse_sc_spike /'
```
