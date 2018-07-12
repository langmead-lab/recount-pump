### Scripts

Scripts in this directory, in rough order of execution:

* On the build server:
    * `docker_push.sh`
        * Pull the most recently published `recount-pump` image.  Unless your internet uplink is very slow, doing this before `docker_build.sh` is usually a net speed win.
    * `docker_build.sh`
        * Build the docker container in the `container` subdirectory
    * `docker_push.sh`
        * Push the most recently built container to [Docker Hub](https://hub.docker.com/r/benlangmead/recount-pump/).
    * `singularity_convert.sh`
        * Convert the most recently built Docker image to a Singularity image.  Once finished, the singularity image will be in the current directory with a name like `benlangmead_recount-pump-2018-01-08-93d2c60d1ee8.img`.
    * **NOTE:** right now this process is tied by my Docker Hub account, `benlangmead`
* On the runtime server (but not within the container):
    * `prep_test.sh`
        * Creates and prepares `input` and `output` subdirectories for a small test run.
        * You still have to set `$RECOUNT_REF` and `$RECOUNT_TEMP` yourself.
    * `docker_run.sh <input> <output>`
        * Runs a Docker container using `<input>` as the input directory (containing csv files with an accession/reference-short-name pair on each line), `<output>` as the output directory, `$RECOUNT_REF` as the directory with the reference files within (see `/populate` directory in this repo) and `$RECOUNT_TEMP` as the temporary directory.
        * The `benlangmead/recount-pump` image must have already been built or pulled before this can work.  I.e. you should see it already when you run `docker image list`.
    * `singularity_run.sh <input> <output>`
        * Needs same arguments & environment variables as `docker_run.sh` above.
        * Does not depend on Docker image being present; doesn't even depend on Docker being installed.  You just need Singularity and the image file.
    * `singularity_run_tacc.sh <job-name> <input-dir> <image-file>`
        * Like `singularity_run.sh` but customized to TACC/Stampede 2 where special rules about directory binding exist.
        * `<job-name>` determines naming for the input, output and temporary directories, which are all under `$SCRATCH/recount-pump/<job-name>/X` where `X` = `input`, `output` or `temp`.
        * The contents of `<input-dir>` get copied into `$SCRATCH/recount-pump/<job-name>/input`
        * `<image-file>` points to the local Singularity image file to run.  Should be a result of the `singularity_convert.sh` script.
* Within the running container (you don't run these manually):
    * `rna_seq.bash`
        * Driver that checks for input files & appropriate directories.
        * Runs nextflow workflow
    * `rna_seq.nf`
        * Nextflow workflow itself

### Example input

* `accessions.txt`
    * Some small C elegans RNA-seq datasets for testing.  Mix of unpaired and paired-end.  Very few reads align for a couple of them; I haven't investigated why.