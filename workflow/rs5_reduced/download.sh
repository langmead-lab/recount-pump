#!/usr/bin/env bash
#place this in /container-mounts/recount/ref
#and place ../pump_config.json there was well

#script do do all downloads for Monorail
#Currently supported (as of 2022-10-12):
#1) SRA via HTTPS (prefetch 3.0.2) and extracted via parallel-fastq-dump|fastq-dump (3.0.2)
#includes choice to use different versions of prefetch via the PREFETCH_PATH env var
#2) URL (passed in)
#3) limited S3 + MD5 support
set -xeo pipefail

#container reachable path to prefetch
if [[ -z $PREFETCH_PATH ]]; then
    export PREFETCH_PATH=/monorail_bin/prefetch
fi
#if downloading from dbGaP, need to set NGC to container reachable path to .ngc key file for specific dbGaP study, e.g.:
#NGC=/container-mounts/recount/ref/prj_<study_id>.ngc
if [[ -z $MD5 ]]; then
    export MD5="MD5.txt"
fi

quad=$1
srr=$2
method=$3
num_urls=$4
threads=$5
retries=$6
temp=$7
log=$8

#these are expected to be set from in the environment
#study,is_gzipped,is_zstded,prefetch_args,fd_args,url0,url1,url2,gdc_token,reads_in_bam,out0,out1,out2

SUCCESS=0
TIMEOUT=10
#gdc timeout is in minutes
GDC_TIMEOUT=30
PARAMS=""
TMP="${temp}/dl-${srr}"
! test -d ${TMP}
TMP_HOLD="${temp}/hold-${srr}"
mkdir -p $TMP_HOLD
pushd $TMP_HOLD

#----------SRA----------#
if [[ ${method} == "sra" ]] ; then
    USE_FASTERQ=1
    mkdir -p ${temp}
    pushd ${temp}
    prefetch_cmd="$PREFETCH_PATH"
    if [[ -z $PREFETCH_PATH ]]; then
        prefetch_cmd="prefetch"
    fi
    if [[ -n $NGC ]]; then
        prefetch_args="--ngc $NGC $prefetch_args"
    fi
    for i in { 1..${retries} } ; do
        if [[ ! -f dl-${srr}/$srr/${srr}.sra  && ! -f dl-${srr}/$srr/${srr}.sralite ]]; then
            if time $prefetch_cmd ${prefetch_args} -t http -O dl-${srr} ${srr} 2>&1 >> ${log} ; then
                SUCCESS=1
                echo "COUNT_HTTPDownloads 1"
                break
            else
                echo "COUNT_SraRetries 1"
                TIMEOUT=$((${TIMEOUT} * 2))
                sleep ${TIMEOUT}
            fi
        else
                SUCCESS=1
                echo "COUNT_HTTPDownloads 1"
                break
        fi
    done
    popd
    if (( $SUCCESS == 0 )) ; then
        echo "COUNT_SraFailures 1"
        rm -rf ${TMP}
        exit 1
    fi
    sraf=$(find ${TMP} -name "*.sra")
    if [[ -z $sraf ]]; then
        sraf=$(find ${TMP} -name "*.sralite")
    fi
    test $sraf
    size=$(cat $sraf | wc -c)
    echo "COUNT_SraBytesDownloaded ${size}"
    ##parallel-fastq-dump
    if (( ${USE_FASTERQ} == 1 )) ; then
        time parallel-fastq-dump --sra-id $sraf \
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
        time fastq-dump $sraf \
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
#----------S3----------#
elif [[ ${method} == "s3" ]] ; then
    additional_cmd='cat'
    if [[ ${is_gzipped} == "1" ]] ; then
        additional_cmd='gzip -cd'
    fi
    if [[ ${is_zstded} == "1" ]] ; then
        additional_cmd='zstd -cd'
    fi
    for i in { 1..${retries} } ; do
        if [[ -n $MD5 && ${is_gzipped} == "1" ]]; then
            if aws s3 cp ${url1} ${srr}_0.fastq.gz 2>> "${log}" ; then
                md5=$(md5sum ${srr}_0.fastq.gz | cut -d' ' -f 1)
                s3url=$(dirname $url1)
                md5_good=$(aws s3 cp ${url1}.md5 - | fgrep "$md5")
                if [[ -n $md5_good ]]; then
                    gunzip -f ${srr}_0.fastq.gz
                    SUCCESS=1
                    break
                fi
            fi
        else
            if time aws s3 cp "${url1}" - 2>> "${log}" | $additional_cmd > "${srr}_0.fastq" 2>> "${log}" ; then
                SUCCESS=1
                break
            fi
        fi
        if [[ $SUCCESS -ne 1 ]]; then
            echo "COUNT_S3Retries1 1"
            TIMEOUT=$((${TIMEOUT} * 2))
            sleep ${TIMEOUT}
        fi
    done
    if (( $SUCCESS == 1 )) && [[ ${num_urls} -gt 1 ]] ; then
        SUCCESS=0
        for i in { 1..${retries} } ; do
            if [[ -n $MD5 && ${is_gzipped} == "1" ]]; then
                if aws s3 cp ${url2} ${srr}_2.fastq.gz 2>> "${log}" ; then
                    md5=$(md5sum ${srr}_2.fastq.gz | cut -d' ' -f 1)
                    s3url=$(dirname $url2)
                    md5_good=$(aws s3 cp ${url2}.md5 - | fgrep "$md5")
                    if [[ -n $md5_good ]]; then
                        gunzip -f ${srr}_2.fastq.gz
                        mv "${srr}_0.fastq" "${srr}_1.fastq"
                        SUCCESS=1
                        break
                    fi
                fi
            else
                if time aws s3 cp "${url2}" - 2>> "${log}" | $additional_cmd > "${srr}_2.fastq" 2>> "${log}" ; then
                    SUCCESS=1
                    mv "${srr}_0.fastq" "${srr}_1.fastq"
                    break
                fi
            fi
            if [[ $SUCCESS -ne 1 ]]; then
                echo "COUNT_S3Retries2 1"
                TIMEOUT=$((${TIMEOUT} * 2))
                sleep ${TIMEOUT}
            fi
        done
    fi
    if (( $SUCCESS == 1 )) && [[ ${num_urls} -gt 2 ]] ; then
        SUCCESS=0
        for i in { 1..${retries} } ; do
            if [[ -n $MD5 && ${is_gzipped} == "1" ]]; then
                if aws s3 cp ${url0} ${srr}_0.fastq.gz 2>> "${log}" ; then
                    md5=$(md5sum ${srr}_2.fastq.gz | cut -d' ' -f 1)
                    s3url=$(dirname $url0)
                    md5_good=$(aws s3 cp ${url0}.md5 - | fgrep "$md5")
                    if [[ -n $md5_good ]]; then
                        gunzip -f ${srr}_0.fastq.gz
                        SUCCESS=1
                        break
                    fi
                fi
            else
                if time aws s3 "${url0}" - 2>> "${log}" | $additional_cmd > "${srr}_0.fastq" 2>> "${log}" ; then
                    SUCCESS=1
                    break
                fi
            fi
        done
        if [[ $SUCCESS -ne 1 ]]; then
            echo "COUNT_S3Retries0 1"
            TIMEOUT=$((${TIMEOUT} * 2))
            sleep ${TIMEOUT}
        fi
    fi
    if (( $SUCCESS == 0 )) ; then
        echo "COUNT_S3Failures 1"
        rm -rf ${TMP}
        exit 1
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
done
mv "${srr}_0.fastq" $out0
mv "${srr}_1.fastq" $out1
mv "${srr}_2.fastq" $out2
popd
rm -rf $TMP_HOLD
echo "COUNT_BytesDownloaded ${size}"
echo "COUNT_DownloadComplete 1"
