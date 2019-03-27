#### Build prerequisites

* `docker`
* Make sure `ver.txt` files have desired version numbers.  This version number will become the label in the registry.  Be careful as pushing an image with the same name and label as an existing one will clobber it.
* Make sure you have made any relevant changes to the files in the workflow subdirectories.  E.g. if there is a change to any of the software versions being used, you may need to update:
    * `more_conda.txt` in the workflow subdirectory
    * `env.yml` in the `common` subdirectory
    * A hard-coded version number in the workflow's `Dockerfile`

#### Build

To build the base image (if needed):

* `cd common && ./build-base.sh && cd ..`

To build `rs5lite`:

* `cd rs5lite && ../common/build.sh && cd ..`

#### Push prerequisites

* Be logged in to your public Docker registry account
    * For Docker Hub, just type `docker login` and follow prompts
    * For quay.io, type `docker login quay.io` and follow prompts
* Does repo have to already exist?

#### Push

If base image changed:

* `cd common && ./push.sh`

If workflow changed:

* `cd rs5lite && ../common/push.sh`

#### Post push

If you are using quay.io and this is the first image you've pushed for this particular repo, you may need to manually log into quay.io, go to the repo settings, and set the visibility to public.
