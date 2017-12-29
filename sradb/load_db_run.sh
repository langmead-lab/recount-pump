#!/bin/sh

/usr/local/bin/R -e "rmarkdown::render('load_db.Rmd',output_file='load_db_output.html')"
