# Genome Reference and Annotation Preparation for Monorail

This is where the scripts for adding the human/mouse references are as well as the basis for adding new organisms' references and annotations.

## Genome Reference Preparation

https://github.com/langmead-lab/recount-pump/blob/master/populate/from_igenomes.sh
is the script to use as the basis for adding a new genome reference.  

It was used for both human and mouse and includes the links used to get the original FASTA files.

It does the following (genome reference FASTA section):

1) downloads the whole genome FASTA
2) removes any strings after the first whitespace character in the the headers of the whole genome FASTA file (this is for problem free indexing downstream)
3) adds ERCC and SIRV FASTA sequences to the main genome FASTA (for spike-in support when running synthetic reads in addition to actual reads)
4) this results in a finalized FASTA file which will be used for aligner indexing: `genome.fa`

It also gets the gene annotation GTF file for the organism (genome annotation section):

1) downloads the GTF file for a specific version (pre-determined, e.g. gencode v26)
2) subsets the GTF to only the chromosomes/contigs in the already formatted whole genome FASTA file
3) uses `gffread` (version 0.9.12) to extract out just the DNA sequence for the transcripts in the gene annotation file
4) adds ERCC and SIRV gene/transcript sequences to the extracted transcript FASTA from the previous step
5) adds ERCC and SIRV gene/transcript annotations to the gene annotation GTF file
6) creates a `salmon` index using the combination transcript FASTA file created in the previous step
7) this results in 2 additional items needed for `recount/monorail pump`: a) `genes.gtf` b) `salmon_index` (directory)

Finally, 2 additional indexes are created:
1) HISAT2 index of whole genome FASTA (this can be skipped for production versions of Monorail as it's no longer used)
2) STAR index of whole genome FASTA (this is required for Monorail)

Monorail also requires a secondary aligner index using HISAT2, which is not covered in any of the build steps above.
This is for reads which don't map to the whole genome FASTA index (typically ones which don't originate from the organism, e.g. contamination/viruses).
Unless you're specifically interested in building your own version of this index, it's most efficient to simply use the one that's already built for human/mouse:

https://recount-ref.s3.amazonaws.com/hg38/unmapped_hisat2_idx.tar.gz

