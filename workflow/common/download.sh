#!/usr/bin/env bash
#script do do all downloads for Monorail
#Currently supported (as of 4/3/2019):
#1) SRA via Apsera|HTTPS and extracted via parallel-fastq-dump|fastq-dump
#2) GDC (e.g. for TCGA, CCLE)
#3) URL (passed in)
set -xeo pipefail

quad=$1
srr=$2
method=$3
num_urls=$4
threads=$5
retries=$6
temp=$7
log=$8

#these are expected to be set from in the environment
#is_gzipped,is_zstded,prefetch_args,fd_args,url0,url1,url2

SUCCESS=0
TIMEOUT=10
PARAMS=""
TMP="${temp}/dl-${srr}"
! test -d ${TMP}

#----------SRA----------#
if [[ ${method} == "sra" ]] ; then
    USE_FASTERQ=1
    for i in { 1..${retries} } ; do
        if time prefetch ${prefetch_args} -O ${TMP} ${srr} 2>&1 >> ${log} ; then
            SUCCESS=1
            break
        else
            echo "COUNT_SraRetries 1"
            TIMEOUT=$((${TIMEOUT} * 2))
            sleep ${TIMEOUT}
        fi
    done
    if (( $SUCCESS == 0 )) ; then
        echo "COUNT_SraFailures 1"
        exit 1
    fi
    test -f ${TMP}/*.sra
    size=$(cat ${TMP}/*.sra | wc -c)
    echo "COUNT_SraBytesDownloaded ${size}"
    ##parallel-fastq-dump
    if (( ${USE_FASTERQ} == 1 )) ; then
        time parallel-fastq-dump --sra-id ${TMP}/*.sra \
            --threads ${threads} \
            --tmpdir ${TMP} \
            -L info \
            --split-3 \
            --skip-technical \
            --outdir . \
            2>&1 >> ${log}
        test -f ${srr}_2.fastq || \
            (test -f ${srr}_1.fastq && mv ${srr}_1.fastq ${srr}_0.fastq) || \
                            (test -f ${srr}.fastq && mv ${srr}.fastq ${srr}_0.fastq)
        # extra unpaired from --split-3
        test -f ${srr}_2.fastq && test -f ${srr}.fastq && mv ${srr}.fastq ${srr}_0.fastq
    ##original fastq-dump
    else
        time fastq-dump ${TMP}/*.sra \
            -L info \
            --split-3 \
            --skip-technical \
            -O . \
            2>&1 >> ${log}
        test -f ${srr}_2.fastq || \
            (test -f ${srr}_1.fastq && mv ${srr}_1.fastq ${srr}_0.fastq) || \
                            (test -f ${srr}.fastq && mv ${srr}.fastq ${srr}_0.fastq)
        # extra unpaired from --split-3
        test -f ${srr}_2.fastq && test -f ${srr}.fastq && mv ${srr}.fastq ${srr}_0.fastq
    fi
    rm -rf ${TMP}
#----------GDC----------#
elif [[ ${method} == "gdc" ]] ; then
    TOKEN=~/gdc/latest.txt
    if [[ ! -f ${TOKEN} ]] ; then
        echo "ERROR: no GDC token file found at ${TOKEN}"
        exit 1
    fi
    mkdir -p ${TMP}
    for i in { 1..${retries} } ; do
        if time gdc-client download \
            -t ${TOKEN} \
            --log-file ${TMP}/log.txt \
            -d ${TMP} \
            ${srr} 2>&1 >> ${log}
        then
            SUCCESS=1
            break
        else
            echo "COUNT_GdcRetries 1"
            TIMEOUT=$((${TIMEOUT} * 2))
            sleep ${TIMEOUT}
        fi
    done
    if (( $SUCCESS == 0 )) ; then
        echo "COUNT_GdcFailures 1"
        exit 1
    fi
    test -d ${TMP}/${srr}
    test -f ${TMP}/${srr}/*.tar.gz
    
    echo "=== gdc-client log.txt begin ===" >> ${log}
    cat ${TMP}/log.txt >> ${log}
    echo "=== gdc-client log.txt end===" >> ${log}
    
    size=$(cat ${TMP}/${srr}/*.tar.gz | wc -c)
    echo "COUNT_GdcBytesDownloaded ${size}"

    tar zxvf ${TMP}/${srr}/*.tar.gz
    rm -rf ${TMP}

    num_1s=$(ls -1 *_1.fastq | wc -l)
    num_2s=$(ls -1 *_2.fastq | wc -l)
    if (( ${num_1s} == 0 )) ; then
        echo "ERROR: No _1.fastq files output"
        exit 1
    fi
    if (( ${num_1s} > 1 )) ; then
        echo "ERROR: More than one _1.fastq file found"
        exit 1
    fi
    if (( ${num_2s} == 0 )) ; then
        # unpaired
        mv *_1.fastq ${srr}_0.fastq
    else
        # paired-end
        mv *_1.fastq ${srr}_1.fastq
        mv *_2.fastq ${srr}_2.fastq
    fi
#----------URL----------#
elif [[ ${method} == "url" ]] ; then
    additional_cmd='cat'
    if [[ ${is_gzipped} == "1" ]] ; then
        additional_cmd='gzip -cd'
    fi
    if [[ ${is_zstded} == "1" ]] ; then
        additional_cmd='zstd -cd'
    fi
    for i in { 1..${retries} } ; do
        if time curl "${url1}" 2>> "${log}" | $additional_cmd > "${srr}_0.fastq" 2>> "${log}" ; then
            SUCCESS=1
            break
        else
            echo "COUNT_URLRetries1 1"
            TIMEOUT=$((${TIMEOUT} * 2))
            sleep ${TIMEOUT}
        fi
    done
    if (( $SUCCESS == 1 )) && [[ ${num_urls} -gt 1 ]] ; then
        SUCCESS=0
        for i in { 1..${retries} } ; do
            if time curl "${url2}" 2>> "${log}" | $additional_cmd > "${srr}_2.fastq" 2>> "${log}" ; then
                SUCCESS=1
                mv "${srr}_0.fastq" "${srr}_1.fastq"
                break
            else
                echo "COUNT_URLRetries2 1"
                TIMEOUT=$((${TIMEOUT} * 2))
                sleep ${TIMEOUT}
            fi
        done
    fi
    if (( $SUCCESS == 1 )) && [[ ${num_urls} -gt 2 ]] ; then
        SUCCESS=0
        for i in { 1..${retries} } ; do
            if time curl "${url0}" 2>> "${log}" | $additional_cmd > "${srr}_0.fastq" 2>> "${log}" ; then
                SUCCESS=1
                break
            else
                echo "COUNT_URLRetries0 1"
                TIMEOUT=$((${TIMEOUT} * 2))
                sleep ${TIMEOUT}
            fi
        done
    fi
    if (( $SUCCESS == 0 )) ; then
        echo "COUNT_URLFailures 1"
        exit 1
    fi
fi

# Next chunk expects the FASTQ files to exist in the current directory
# named ${srr}_{0,1,2}.fastq
size=0
for i in {0..2} ; do
    fn=${srr}_${i}.fastq
    if [[ -f "${fn}" ]] ; then
        echo "COUNT_FilesDownloaded 1"
    else
        touch "${fn}"
    fi
    size=$((${size} + $(wc -c < "${fn}")))
    mv "${fn}" "${temp}/${quad}_${i}.fastq"
done
echo "COUNT_BytesDownloaded ${size}"
echo "COUNT_DownloadComplete 1"
