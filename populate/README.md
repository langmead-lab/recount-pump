# Genome Reference and Annotation Preparation for Monorail

This is where the scripts for adding the human/mouse references are as well as the basis for adding new organisms' references and annotations.

Applications required to be installed and in `$PATH`:
1) bedtools2
2) Docker
3) python2.7
4) gffread
http://ccb.jhu.edu/software/stringtie/dl/gffread-0.9.12.Linux_x86_64.tar.gz

## Genome Reference Preparation

https://github.com/langmead-lab/recount-pump/blob/master/populate/from_igenomes.sh
is the script to use as the basis for adding a new genome reference.  

This is *not* a turn key script, it can not just be run with a new genome annotation and expected to just work (though most parts should be able to be easily adapted to a new genome reference).

It was used for both human and mouse and includes the links used to get the original FASTA files.

It does the following (genome reference FASTA section):

1) downloads the whole genome FASTA
2) removes any strings after the first whitespace character in the the headers of the whole genome FASTA file (this is for problem free indexing downstream)
3) adds ERCC and SIRV FASTA sequences to the main genome FASTA (for spike-in support when running synthetic reads in addition to actual reads)
4) this results in a finalized FASTA file which will be used for aligner indexing: `genome.fa`

It also gets the gene annotation GTF file for the organism (genome annotation section):

5) downloads the GTF file for a specific version (pre-determined, e.g. gencode v26)
6) subsets the GTF to only the chromosomes/contigs in the already formatted whole genome FASTA file
7) uses `gffread` (version 0.9.12) to extract out just the DNA sequence for the transcripts in the gene annotation file
8) adds ERCC and SIRV gene/transcript sequences to the extracted transcript FASTA from the previous step
9) adds ERCC and SIRV gene/transcript annotations to the gene annotation GTF file
10) creates a `salmon` index using the combination transcript FASTA file created in the previous step
11) this results in 2 additional items needed for `recount/monorail pump`: a) `genes.gtf` b) `salmon_index` (directory)

The combined GTF file created in step 9 above is also used as the annotation for `

12) the `STAR` index of whole genome FASTA

Monorail also requires a secondary aligner index using `HISAT2`, which is not covered in any of the build steps above.
This is for reads which don't map to the whole genome FASTA index (typically ones which don't originate from the organism, e.g. contamination/viruses).
Unless you're specifically interested in building your own version of this index, it's most efficient to simply use the one that's already built for human/mouse:

https://recount-ref.s3.amazonaws.com/hg38/unmapped_hisat2_idx.tar.gz


## Genome Annotation Preparation

The above section covers mostly what's required to get `recount/Monorail pump` working.  However, `pump` also needs a `exons.bed` file to run `Megadepth` (aka `bamcount`) against to get the main coverage for the annotation across the BAMs produced by `STAR`.


This is a very nuanced process as it produces 2 sets of files:
1)  "split" versions of the annotated exons for more efficient coverage computation in `pump` per sample
2)  "rejoin" versions of the annotated exons to get coverage has been computed and aggregated over the original, annotated exons *and* gene regions

Only the first set is neeed by `pump`, while both sets of files are needed by the `recount/Monorail unifier` which does the post-pump/alignment aggergation of the coverage.

The script:

https://github.com/langmead-lab/recount-pump/blob/master/populate/disjoin_scripts/combine_annotations_and_disjoin_exons.sh

is only for re-creating the combined 4 human annotations (along with ERCC and SIRV), it should not necessarily be used as a basis for other genomes unless:
1) multiple different annoations are being used (other than ERCC and SIRV)
2) one or more of the annotations are from RefSeq

The main script for generating most of the required files for sets 1) and 2) above is:

https://github.com/langmead-lab/recount-pump/blob/master/populate/disjoin_scripts/create_rejoin_disjoint2annotation_mappings.sh

It only requires, as input, the combined GTF file with the main genome annotation GTF + ERCC and SIRV annotations created in step 9 in the Genome Reference Preparation section.
It does assume that Docker is running and you have the `populate` docker image built/downloaded, derived from:

https://github.com/langmead-lab/recount-pump/blob/master/populate/build.sh

which uses:

https://github.com/langmead-lab/recount-pump/blob/master/populate/Dockerfile

## Notes on the Final Annotation Assembly and Ordering

Even though this is technically a subsection of the preceding section, it get it's own section due to the complexities of the situation in setting up the final group of annotation files for 1) rejoining in the `unifier` and 2) recount3 loading.

The exon annotation file used by recount3 for 2) above need to be the *exact* same and ordered the same as the `exon_bitmask_coords.tsv` file output by the preceding section's run of `create_rejoin_disjoint2annotation_mappings.sh`.

The way to create these GTF files...

### Annotation Naming
Annotation short names should be exactly 4 characters and any organism other than human needs to have an annotation short name that starts with a capital `M`.

Some examples:

* Human Gencode v26: `G026`
* Human FANTOM v6: `F006`
* Mouse gencode M23: `M023`
* Rat Rbn 7.2 ensembl release 105: `M105`