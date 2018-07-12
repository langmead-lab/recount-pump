* `Dockerfile`
    * Docker build script.
        * Builds on `biocontainers/biocontainers:latest` from the [Biocontainers](http://biocontainers.pro) project
        * Installs the conda dependencies described in `rna_seq.yml`
        * Installs `globus-cli` with `pip`
        * Updates nextflow (or tries to; it seems to need yet further updates upon being run on a real workflow)
        * Builds and installs `regtools` from GitHub, since it's not on conda or pip.
        * Copies key files (like `rna_seq.bash` & `rna_seq.nf` into the image)
* `rna_seq.yml`
    * Conda environment file.  Contains almost everything needed to run the RNA-seq Nextflow workflow.
    * This should probably be moved up a directory, to be copied in here just prior to building along with `rna_seq.bash` and `rna_seq.nf`.
* `Singularity.recount-pump`
    * A singularity file that does little more than bootstrap from the `benlangmead/recount-pump` image.
    * This, used in concert with Singularity Hub, gives an alternate way of building a Singularity image of `recount-pump`.  But it's probably not backward-compatible with versions of Singularity older than 2.4, which is bad because Stampede 2 runs 2.3.1. 