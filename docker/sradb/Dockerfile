FROM bioconductor/release_core2

RUN Rscript -e 'BiocManager::install("SRAdb", version = "3.8")'

ENV R_DEFAULT_PACKAGES SRAdb

COPY getdb.R /getdb.R

ENTRYPOINT [ "R" ]
