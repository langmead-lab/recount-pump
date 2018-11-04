#!/usr/bin/env Rscript

'usage: disjoin.R <url> <outfile> [options]

options:
 --exclude-olaps   Exclude disjoint exons assocaited with >1 gene [default: false]
 --organism <org>  Name of organism [default: "unknown"]
 --source <name>   Name of source [default: "unknown"]
 --taxid <int>     Taxonomy id [default: 9606]' -> doc

# To install dependencies:
#
# source("https://bioconductor.org/biocLite.R")
# biocLite("GenomicFeatures")
# biocLite("GenomicRanges")
# biocLite("rtracklayer")
# library(devtools)
# install_github("docopt/docopt.R")

library(docopt)
library(GenomicFeatures)
library(GenomicRanges)
library(rtracklayer)

opts <- docopt(doc, commandArgs(T))

gtf <- makeTxDbFromGFF(opts[['<url>']], format='gtf',
    dataSource=opts[['--source']], organism=opts[['--organism']],
    taxonomyId=as.integer(opts[['--taxid']]))

export(exonicParts(gtf,
    linked.to.single.gene.only=as.logical(opts['--exclude-olaps'])),
    opts[['<outfile>']], 'bed')
