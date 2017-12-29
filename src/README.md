## Inputs & Metadata

Relevant links to how we did things in other projects:
* [`create_metadata.R`](https://github.com/leekgroup/recount-website/blob/master/metadata/create_metadata.R) from `recount-website` project
* [`gen.py`](https://github.com/nellore/runs/blob/c7223c206850ba03e52da568644c3934b11b6192/sra/v2/hg38/gen.py) from Intropolis, which gives the SRA search string used to obtain the `SraRunInfo.csv` used by Leo's scripts
* [`define_and_get_fields_SRA.R`](https://github.com/nellore/runs/blob/c7223c206850ba03e52da568644c3934b11b6192/sra/v2/define_and_get_fields_SRA.R) on which I am modeling some of my `SRAdb` using code

### Human SRA

Here's an attempt.

```R
library('SRAdb')

# If you have SRAmetadb already, set this directory, or setwd appropriately
# to save yourself a large download
sqlfile <- file.path('.', 'SRAmetadb.sqlite')
if(!file.exists('SRAmetadb.sqlite')) sqlfile <<- getSRAdbFile()
sra_con <- dbConnect(SQLite(),sqlfile)
q <- function(x) { dbGetQuery(sra_con, x) }

species_to_tax_id = list(
  'arabidopsis_thaliana'=3702,     # 4. arabidopsis
  'bos_taurus'=9913,               # 9: cow
  'caenorhabditis_elegans'=6239,   # >10: roundworm
  'danio_rerio'=7955,              # 3: zebrafish
  'drosophila_melanogaster'=7227,  # 5: fruitfly
  'homo_sapiens'=9606,             # 2: human
  'mus_musculus'=10090,            # 1: mouse
  'ovis_aries'=9940,               # 10: sheep
  'rattus_norvegicus'=10116,       # 7: rat
  'saccharomyces_cerevisiae'=4932, # 6: yeast
  'zea_mays'=4577)                 # 8: corn

# > sort(table(taxids),decreasing=TRUE)[1:10]
# taxids
#  10090   9606   7955   3702   7227   4932  10116   4577   9913   9940 
# 195878 156394  23590  17296  17006   7997   7098   7018   5173   5018 

species_table <- function(taxid) {
  q(paste(
    'SELECT * FROM sra, study, submission, fastq, run',
    'WHERE sra.platform = "ILLUMINA"',
    '  AND sra.library_strategy = "RNA-Seq"',
    '  AND sra.library_source = "TRANSCRIPTOMIC"',
    '  AND sra.submission_accession = submission.submission_accession',
    '  AND sra.study_accession = study.study_accession',
    '  AND sra.run_accession = fastq.run_accession',
    '  AND sra.run_accession = run.run_accession',
    '  AND fastq.FASTQ_FILES > 0',
    sprintf('AND sra.taxon_id = %d', taxid)))
}
runs_by_species <- lapply(species_to_tax_id, species_table)
```

Now that we can make a table like this, we have a few more issues to tackle:

* Need to separate open from controlled-access.  (Maybe whether `fastq.FASTQ_FILES` equals 0?)
* Need to associate URLs with accessions, and for that we might have a choice of mirrors, or otherwise need to look in multiple places to get the right URL.  See the implementation `getFASTQinfo` function in `sradb`.  Also see the related `sraConvert` function which can get all the runs for a given accession.
* Need to consider how to get the metadata into the overall data model.  If all data were in the SRA and if all relevant metadata were in the various "attribute" fields (`run_attribute`, `sample_attribute`, `study_attribute`, `experiment_attribute`) then we could simply move this table into the data model.  But actually the metadata table will vary from project to project.  E.g. TCGA's is different.
* Now how do I connect these results with the SQLAlchemy stuff in the rest of the infrastructure?

```r
sraConvert('SRA003625', out_type = c("run"), sra_con)$run
```

### Transfer clients

#### MARCC

Has `ascp` in an Aspera module:

```bash
$ module load aspera/3.7.2.354
$ ascp --version
Aspera CLI version 3.7.2.354.010c3b8
ascp version 3.7.2.137926
Operating System: Linux
FIPS 140-2-validated crypto ready to configure
AES-NI Supported
(hang)
```

```bash
$ time ascp-marcc -i /cm/shared/apps/aspera-cli/3.7.2.354/etc/asperaweb_id_dsa.openssh -Tr -Q -l 100M -P33001 -L- era-fasp@fasp.sra.ebi.ac.uk:vol1/fastq/ERR204/ERR204938/ERR204938_1.fastq.gz ./
...
real	1m29.602s
user	0m1.587s
sys	0m2.755s
```

`hisat2` uses the SRA API.  Does this allow it to do fast alignment simultaneous with download?  Here's a little experiment:

```bash
$ time hisat2 -p 32 --sra-acc ERR204938 -x /scratch/groups/blangme2/indexes/hisat2/hg38 -S /scratch/groups/blangme2/langmead/ERR204938.sam
...
96.54% overall alignment rate

real	3m19.671s
user	68m31.668s
sys	3m14.528s
```

Impressive, considering simply downloading the data using Aspera takes 1m30s.  Can we do much better?  I tried `-p 64` and it finished much slower: in `8m32.800s`.  Then I tried `-p 20` and it was 3m8.798s.  I also notice that `hisat2` takes only 100% of a CPU for a while even with these high `-p` settings.

#### Stampede 2

Has aspera as a module too:

```bash
$ module load aspera-connect/3.6.1.110647
$ ascp --version
ascp version 3.5.6.110366
Operating System: Linux
FIPS 140-2-validated crypto ready to configure
AES-NI Supported
License max rate=(unlimited), account no.=1, license no.=1
```

It works:

```bash
$ time $TACC_ASPERA_ASCP -i $TACC_ASPERA_KEY -Tr -Q -l 100M -P33001 -L- era-fasp@fasp.sra.ebi.ac.uk:vol1/fastq/ERR204/ERR204938/ERR204938_1.fastq.gz ./
...
LOG Source bytes transferred                    : 1032735305
LOG ======= end File Transfer statistics =======

real    1m29.155s
user    0m1.370s
sys     0m6.340s
```

Strange that there's a version mismatch between the module name and the actual binary.

Also has SRA toolkit:

```bash
$ module load sratoolkit/2.8.2
```

The TACC folks have a couple good recommendations in the documentation for the module:

* To improve download speed, the prefetch command has been aliased to always use aspera
* We also suggest running `scratch_cache` to change your cache directory to use the scratch filesystem

So I have set my `scratch_cache` on Stampede 2:

```bash
$ cat .ncbi/user-settings.mkfg
/repository/user/main/public/root = "/scratch/04265/benbo81/ncbi"
```

```bash
$ time prefetch ERR204938

2017-11-23T14:50:02 prefetch.2.8.2: 1) Downloading 'ERR204938'...
2017-11-23T14:50:02 prefetch.2.8.2:  Downloading via fasp...
2017-11-23T14:50:19 prefetch.2.8.2:  fasp download succeed
2017-11-23T14:50:19 prefetch.2.8.2: 1) 'ERR204938' was downloaded successfully

real    0m18.220s
user    0m0.947s
sys     0m4.827s

$ time fastq-dump ERR204938
Read 14881101 spots for ERR204938
Written 14881101 spots for ERR204938

real    1m19.164s
user    1m3.930s
sys     0m7.356s
```

```bash
time ascp -QT -L- -l 1000M era-fasp@fasp.sra.ebi.ac.uk:vol1/fastq/ERR204/ERR204938/ERR204938.fastq.gz .
```

This doesn't work for me.

## Clusters & Containers

### Stampede 2

To load singularity:

```bash
module load tacc-singularity
```

But (a) you can't run it on the login node, and (b) that doesn't add it to the PATH.  To run Singularity:

```bash
$ singularity --version
2.3.1-dist
```
* [Singularity @ TACC](https://github.com/TACC/TACC-Singularity)

Tried to set up my environment similarly to what is described below for MARCC but failed:

```bash
$ sing hisat2 align
ERROR  : Failed invoking the NEWUSER namespace runtime: Invalid argument
ABORT  : Retval = 255
```

But this was trying on the head node.  Maybe it works on the worker nodes?

### HHPC

```bash
$ module load singularity
$ singularity --version
2.3-master.gadf5259
```

And it goes in the path.

### MARCC

```bash
$ module load singularity
$ singularity --version
2.4-dist
$ which singularity
/cm/shared/apps/singularity/2.4/bin/singularity
```

And it goes in the path.  Loading the module also sets these variables:

```bash
SINGULARITY_BINDPATH=/scratch,/data,/work-zfs
SINGULARITY_DIR=/cm/shared/apps/singularity/2.4
SINGULARITY_HOME=/home-1/blangme2@jhu.edu:/home/blangme2@jhu.edu
```

The setting for `SINGULARITY_BINDPATH` seems to require that those directories exist in the image already.

Here's how I suggest we run `singularity` on MARCC:

```bash
# We don't want to require the bind paths that MARCC assumes
unset SINGULARITY_BINDPATH
export SINGULARITY_CACHEDIR="$GS/singularity_cache"
export SINGULARITY_WORK="$US/singularity_work"
export SINGULARITY_REFS="${SINGULARITY_WORK}/reference"

# My singularity wrapper function
sing() {
    image=$1
    shift
    # use env to avoid warnings from perl
    env -u LANG singularity \
        run \
        -H "${HOME}:/home1/blangme2" \
        -B /tmp:/scratch \
        -B "${SINGULARITY_WORK}:/work" \
        "${SINGULARITY_CACHEDIR}/${image}.simg" $*
}
```

### Amazon instance

Important, since sometimes you need root to do important things.

```bash
$ singularity --version
2.2.1
```

That was the default version, but I built from source an upgraded to 2.4 because I wanted the "build" command:

```bash

```

## Making containers

General theory is to make Docker containers that are modeled closely on per-tool containers in BioContainers.  In particular, we 

```bash
$ singularity pull --name 
```

Note that on MARCC, it will mount the home directory as `/home`, clobbering the `/home` in the original container.

## Compiling into recount & Snaptron

### recount

* [example_prep.sh](https://github.com/leekgroup/recount-website/blob/master/recount-prep/example_prep.sh) is a script of Leo's that shows examples of how to compile bigWig and junction files for a study consisting of many samples.  Uses `bwtool summary`, `wiggletools mean`, `wiggletools sum`, `wiggletools scale`, `wiggletools AUC`, `wigToBigWig`.  Also uses gene annotation (`Gencode-v25.bed`), including some R objects that seem to be derived from the annotation such as `introns_unique.Rdata` and `count_groups.Rdata`
    * [`prep_setup.R`](https://github.com/leekgroup/recount-website/blob/master/recount-prep/prep_setup.R) called once at the beginning of `example_prep.sh`.  Downloads some dependencies like chromosome sizes and gene annotation.
    * [`prep_sample.R`](https://github.com/leekgroup/recount-website/blob/master/recount-prep/prep_sample.R)
        * Uses `bwtool`, `wiggletools`
        * Runs `bwtool summary` on BED file defining exons and bigWig file, then writes `counts_exon_<name>.tsv`
        * Also creates a `SummarizedExperiment` for exons and writes to `rse_exon_<name>.Rdata`
        * Uses a file called `count_groups_file` (based on GENCODE?) to sum up exon counts into gene counts
        * Writes table to `counts_gene_<name>.tsv` and `SummarizedExperiment` to `rse_gene_<name>.Rdata`
    * [`prep_merge.R`](https://github.com/leekgroup/recount-website/blob/master/recount-prep/prep_merge.R)
        * Does a `cbind` to merge all the per-sample gene quantification files.  Writes it into `rse_gene.Rdata`.
        * Does same for exons, `rse_exon.Rdata`.
        * Optionally quantifies mean bigWig.  Uses `wiggletools` and then `wigToBigWig`.
        * Gathers all junction-level information and merges.  This is relatively involved.  Looks like there's code to annotation junctions with gene annotations and search for gene fusions in there.  Outputs `rse_jx.Rdata`.

### Snaptron

* [`setup_generic_snaptron_instance.sh`](https://github.com/ChristopherWilks/snaptron/blob/master/deploy/setup_generic_snaptron_instance.sh); overall driver of Snaptron compilation process 
    * Calls `convert_rail_raw_cross_sample_junctions.py` and immediately pipes to `bgzip`
    * Does a join between the junctions table and the metadata, in a file called `samples.tsv` to begin with
    * `rip_annotated_junctions.py`
    * `process_introns.py`, which combines junctions with one or more annotations in `.gtf` files.  Oddly, this doesn't seem to actually output the annotations themselves.  Where do they go?
    * `tabix` to index the junctions
    * `build_sqlite_junction_db.sh`, which creates SQLite db with one `intron` table, imports the table, and indexes it  
    * `infer_sample_metadata_field_types.pl` infers the type of each column in a metadata file
    * `lucene_indexer.py`
* [`convert_rail_raw_cross_sample_junctions.py`](https://github.com/ChristopherWilks/snaptron/blob/master/deploy/convert_rail_raw_cross_sample_junctions.py) converts a Rail-style compiled junctions file into a Snaptron-style file

Questions:
* To what degree are the activities of the compiling cluster coordinated through the mothership?  Is the cluster reacting to files as they arrive, or does the mothership know what's stored on the cluster and explicitly send commands to it, perhaps via a queue?
* How does the compiling cluster know when all the runs in a study  or compilation have arrived?
* How and when does metadata get folded in?  The `SummarizedExperiment` objects in recount need for this to have been folded in already. 
* Is the compiling cluster going to take advantage of the fact that analyses might be identical across projects?