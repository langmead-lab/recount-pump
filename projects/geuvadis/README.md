### What we ran

* `get_hg38_parts.sh`
    * Downloads components of the hg38 reference from synapse to current directory
        * HISAT2 index
        * FASTA
        * GTF (GENCODE)
* `upload_hg38_parts.sh`
    * Uploads components of the hg38 reference to the expected spot in S3: `s3://recount-pump/ref/hg38`
* `get_meta.sh`
    * Get the metadata for the samples in question
* `upload_meta.sh`
    * Upload the `.json.gz` file produced by the previous script to S3 for safe & permanent keeping
* `init.bash`
    * Sets up the data model and stages the project
        * Sources
        * Analysis
        * Reference
        * Inputs/InputSet

### Notes for how users will use this

* First two steps (downloading then uploading the components of the h38 reference) will already be done and user will just have to download a bundle first, much like they already do with aligners 