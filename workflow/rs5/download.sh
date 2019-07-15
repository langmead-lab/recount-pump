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
#bam2fastq,study,is_gzipped,is_zstded,prefetch_args,fd_args,url0,url1,url2,gdc_token,reads_in_bam

SUCCESS=0
TIMEOUT=10
#gdc timeout is in minutes
GDC_TIMEOUT=30
PARAMS=""
TMP="${temp}/dl-${srr}"
! test -d ${TMP}

#----------SRA----------#
if [[ ${method} == "sra" ]] ; then
    USE_FASTERQ=1
    for i in { 1..${retries} } ; do
        if time prefetch ${prefetch_args} -t fasp -O ${TMP} ${srr} 2>&1 >> ${log} ; then
            SUCCESS=1
            echo "COUNT_FASPDownloads 1"
            break
        else
            #try http/s as a fallback before retrying
            if time prefetch ${prefetch_args} -t http -O ${TMP} ${srr} 2>&1 >> ${log} ; then
                SUCCESS=1
                echo "COUNT_HTTPDownloads 1"
                break
            else
                echo "COUNT_SraRetries 1"
                TIMEOUT=$((${TIMEOUT} * 2))
                sleep ${TIMEOUT}
            fi
        fi
    done
    if (( $SUCCESS == 0 )) ; then
        echo "COUNT_SraFailures 1"
        rm -rf ${TMP}
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
    TOKEN=${gdc_token}
    use_token="-t ${TOKEN}"
    #if we have a token but it doesn't exist, throw an error
    if [[ ! -z ${TOKEN} && ! -f ${TOKEN} ]] ; then
        echo "ERROR: no GDC token file found at ${TOKEN}"
        exit 1
    elif [[ -z ${TOKEN} ]] ; then
        #e.g. CCLE
        use_token=""
    fi
    mkdir -p ${TMP}
    for i in { 1..${retries} } ; do
        if timeout -s 9 -k 5s ${GDC_TIMEOUT}m gdc-client download \
            $use_token --log-file ${TMP}/log.txt \
            -n ${threads} \
            -d ${TMP} \
            --no-verify \
            --no-annotations \
            --retry-amount ${retries} \
            --wait-time 3 \
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
        rm -rf ${TMP}
        exit 1
    fi
    test -d ${TMP}/${srr}
    if [[ ${study} == "ccle" || ${reads_in_bam} -eq 1 ]] ; then
        test -f ${TMP}/${srr}/*.bam
        echo "=== gdc-client log.txt begin ===" >> ${log}
        cat ${TMP}/log.txt >> ${log}
        echo "=== gdc-client log.txt end===" >> ${log}
        
        size=$(cat ${TMP}/${srr}/*.bam | wc -c)
        echo "COUNT_GdcBytesDownloaded ${size}"
        BAM=$(ls ${TMP}/${srr}/*.bam)
        ${bam2fastq} $BAM --threads ${threads} --bam2fastq ${srr} --filter-out 256 --re-reverse 2>&1 >> ${log}
        
        test -s ${srr}.fastq && \
            mv ${srr}.fastq ${srr}_0.fastq
    else
        echo "=== gdc-client log.txt begin ===" >> ${log}
        cat ${TMP}/log.txt >> ${log}
        echo "=== gdc-client log.txt end===" >> ${log}

        if test -f ${TMP}/${srr}/*.tar.gz; then
            size=$(cat ${TMP}/${srr}/*.tar.gz | wc -c)
            echo "COUNT_GdcBytesDownloaded ${size}"
            tar zxvf ${TMP}/${srr}/*.tar.gz
        else
            test -f ${TMP}/${srr}/*.tar
            size=$(cat ${TMP}/${srr}/*.tar | wc -c)
            echo "COUNT_GdcBytesDownloaded ${size}"
            tar xvf ${TMP}/${srr}/*.tar
            gunzip *.gz
        fi 
        rm -rf ${TMP}

        num_fastqs=`ls -1 *.fastq | wc -l`

        if (( ${num_fastqs} == 1 )) ; then
            # unpaired
            mv *.fastq ${srr}_0.fastq
        fi
        if (( ${num_fastqs} == 2 )) ; then
            mv *_1.fastq ${srr}_1.fastq
            mv *_2.fastq ${srr}_2.fastq
        fi
        if (( ${num_fastqs} == 3 )) ; then
            mv *_1.fastq ${srr}_1.zfastq
            mv *_2.fastq ${srr}_2.zfastq
            mv *.fastq ${srr}_0.fastq
            mv *_1.zfastq ${srr}_1.fastq
            mv *_2.zfastq ${srr}_2.fastq
        fi
        if (( ${num_fastqs} >= 4 )) ; then
            echo -n "" > ${srr}_1.zfastq
            echo -n "" > ${srr}_2.zfastq
            for f in `ls *_1.fastq`; do cat $f >> ${srr}_1.zfastq; done
            for f in `ls *_2.fastq`; do cat $f >> ${srr}_2.zfastq; done
            mv ${srr}_1.zfastq ${srr}_1.fastq
            mv ${srr}_2.zfastq ${srr}_2.fastq
        fi
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
        rm -rf ${TMP}
        exit 1
    fi
#----------LOCAL----------#
elif [[ ${method} == "local" ]] ; then
    additional_cmd='cat'
    if [[ ${is_gzipped} == "1" ]] ; then
        additional_cmd='gzip -cd'
    fi
    if [[ ${is_zstded} == "1" ]] ; then
        additional_cmd='zstd -cd'
    fi
    for i in { 1..${retries} } ; do
        if $additional_cmd "${url1}" > ${srr}_0.fastq 2>> {log} ; then
            SUCCESS=1
            break
        else
            echo "COUNT_LOCALRetries1 1"
            TIMEOUT=$((${TIMEOUT} * 2))
            sleep ${TIMEOUT}
        fi
    done
    if (( $SUCCESS == 1 )) && [[ ${num_urls} -gt 1 ]] ; then
        SUCCESS=0
        for i in { 1..${retries} } ; do
            if time $additional_cmd "${url2}" > ${srr}_2.fastq 2>> {log} ; then
                SUCCESS=1
                mv ${srr}_0.fastq ${srr}_1.fastq
                break
            else
                echo "COUNT_LOCALRetries2 1"
                TIMEOUT=$((${TIMEOUT} * 2))
                sleep ${TIMEOUT}
            fi
        done
    fi
    if (( $SUCCESS == 1 )) && [[ ${num_urls} -gt 2 ]] ; then
        SUCCESS=0
        for i in { 1..${retries} } ; do
            if time $additional_cmd "${url0}" 2>> {log} > ${srr}_0.fastq 2>> {log} ; then
                SUCCESS=1
                break
            else
                echo "COUNT_LOCALRetries0 1"
                TIMEOUT=$((${TIMEOUT} * 2))
                sleep ${TIMEOUT}
            fi
        done
    fi
    if (( $SUCCESS == 0 )) ; then
        echo "COUNT_LOCALFailures 1"
        rm -rf ${TMP}
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
