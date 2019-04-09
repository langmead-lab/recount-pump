To adapt `recount-pump` to a new HPC system:

* Make a subdirectory 
* Install [miniconda](https://docs.conda.io/en/latest/miniconda.html) and some python packages:

```
(install miniconda)
conda config --add channels conda-forge
conda install watchtower docopt pytest psutil sqlalchemy psycopg2 awscli
```

* Install `globus_sdk` python module, which is only available via `pip`:

```
pip install globus_sdk
```

* You'll need your `~./aws/credentials` file populated for any AWS profiles you refer to in the configs
* Thins you may need to add to your `bash` profile:
    * Adding `conda` to the `PATH`
    * `module load singularity`
    * Set `SINGULARITY_CACHEDIR`
* In `projects/common/clusters/stampede2`
