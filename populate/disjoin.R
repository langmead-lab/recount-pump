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

url <- opts[['<url>']]
source_name <- opts[['--source']]
organism_name <- opts[['--organism']]
tax_id <- as.integer(opts[['--taxid']])
exclude_olaps <- as.logical(opts['--exclude-olaps'])
outfn <- opts[['<outfile>']]

gtf <- makeTxDbFromGFF(url, format='gtf',  dataSource=source_name,
                       organism=organism_name, taxonomyId=tax_id)

export(exonicParts(gtf, linked.to.single.gene.only=exclude_olaps),
       outfn, 'bed')
