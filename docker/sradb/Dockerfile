FROM bioconductor/release_core2

RUN Rscript -e 'BiocManager::install("SRAdb", version = "3.8")'

COPY entry.R /entry.R

ENTRYPOINT [ "Rscript", "/entry.R" ]
