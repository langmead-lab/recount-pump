It's easy to install a local RabbitMQ server using Docker.  It also helps with performing local testing of some of `recount-pump`'s functionality.  Scripts in this directory help with this process.  It's assumed you have Docker running.  Note that you may have to prepend `sudo` to docker commands.

Steps:

* `pull.sh` -- pull the appropriate RabbitMQ Docker image.
* `run.sh` -- run a Docker container using the image, mapping the appropriate ports on localhost to the same inside the image.
