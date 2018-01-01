#!/bin/sh

# Author: Ben Langmead
#   Date: 1/1/18

set -ex

sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Arabidopsis_thaliana/NCBI/TAIR10/Arabidopsis_thaliana_NCBI_TAIR10.tar.gz tair10 Arabidopsis_thaliana NCBI
sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Bos_taurus/UCSC/bosTau8/Bos_taurus_UCSC_bosTau8.tar.gz bosTau8 Bos_taurus UCSC
sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Caenorhabditis_elegans/UCSC/ce10/Caenorhabditis_elegans_UCSC_ce10.tar.gz ce10 Caenorhabditis_elegans UCSC
sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Danio_rerio/UCSC/danRer10/Danio_rerio_UCSC_danRer10.tar.gz danRer10 Danio_rerio UCSC
sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Drosophila_melanogaster/UCSC/dm6/Drosophila_melanogaster_UCSC_dm6.tar.gz dm6 Drosophila_melanogaster UCSC
sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Homo_sapiens/UCSC/hg38/Homo_sapiens_UCSC_hg38.tar.gz hg38 Homo_sapiens UCSC
sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Mus_musculus/UCSC/mm10/Mus_musculus_UCSC_mm10.tar.gz mm10 Mus_musculus UCSC
sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Rattus_norvegicus/UCSC/rn6/Rattus_norvegicus_UCSC_rn6.tar.gz rn6 Rattus_norvegicus UCSC
sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Saccharomyces_cerevisiae/UCSC/sacCer3/Saccharomyces_cerevisiae_UCSC_sacCer3.tar.gz sacCer3 Saccharomyces_cerevisiae UCSC
sh from_igenomes.sh ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Zea_mays/Ensembl/AGPv4/Zea_mays_Ensembl_AGPv4.tar.gz AGPv4 Zea_mays Ensembl
