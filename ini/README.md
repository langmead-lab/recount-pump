Example `.ini` files, which `recount-pump` generally expects to be located in `~/.recount`

* `db.ini` -- MySQL database url, username, password
    * See `src/recount_db.py` for example of how it's used
* `log.ini` -- log aggregator url, format strings
    * See `src/log.py` for example of how it's used
* `cluster.ini` -- for configuring directory mappings between host and container. These must be cluster-specific, since some clusters (e.g. Stampede 2) make certain prescribed mounts and allow no others.
    * See `workflow/*/singrun.sh` and `workflow/*/dockrun.sh` for how it's used