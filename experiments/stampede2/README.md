Experiments with the goal of:

* Trying to figure out how to build and run Singularity containers for Stampede 2
    * Wrangling input and output conveniently, so that running containerized tool is similar to running tool itself
    * Comports with the properties of the Stampede file systems

I have hit various dead ends.  It's possible singularity could be used, but at this point I think it's advisable to give up on that and to use conda environments as the next-best-thing.

* Trying to maximize throughput on Stampede 2
    * Downloading from archive
    * Mixing multithreading and multiprocessing well

Ancillary issues:

* Getting our thread scaling changes into HISAT2

### Bioconda recipes

* https://bioconda.github.io/contribute-a-recipe.html
* https://github.com/bioconda/bioconda-recipes/tree/master/recipes/multiqc
* https://github.com/bioconda/bioconda-recipes/tree/master/recipes/hisat2
* https://github.com/bioconda/bioconda-recipes/tree/master/recipes/sra-tools
* https://github.com/bioconda/bioconda-recipes/tree/master/recipes/ucsc-bedgraphtobigwig

### Related links
* https://quay.io/organization/biocontainers
* https://quay.io/repository/biocontainers/hisat2?tab=info