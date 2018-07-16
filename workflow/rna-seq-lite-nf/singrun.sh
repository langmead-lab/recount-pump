#!/bin/bash

# Author: Ben Langmead
#  Email: langmea@cs.jhu.edu
#   Date: 1/5/2018

# Runs a singularity container containing the next flowscript and its
# in-container driver, setting up appropriate directory mappings ahead
# of time.

usage() {
    echo "./singrun.sh <job_name> <input_dir> <output_dir> [options]*"
    echo ""
    echo "<input_dir> and <output_dir> must already exist"
    echo "<input_dir> must contain CSV files, each line having 3 fields: SRR,SRP,species"
    echo ""
    echo "Options:"
    echo ""
    echo "   -i/--image <image>   path or URL for singularity image to use"
    echo "   -k/--keep            do not remove temp directory upon success"
    echo "   -h/--help            print this message"
}

[ -z "${1}" ] && usage && exit 1

job_name=$1
input_dir=`realpath $2`
output_dir=`realpath $3`
shift 3

image="shub://langmead-lab/recount-pump:recount-pump"
keep=0

while [ "$1" != "" ]; do
    case $1 in
        -i | --image ) image=$2 ; shift 2 ;;
        -k | --keep )  keep=1 ; shift 1 ;;
        -h | --help )  usage ; exit ;;
        * )            usage ; exit 1 ;;
    esac
done

if ! echo ${image} | grep -q '^shub' ; then
    # not a URL, so must be extant file
    if [ ! -f "${image}" ] ; then echo "No such image file: \"${image}\"" ; exit 1 ; fi
fi 
echo "Image set to \"${image}\""

if [   -z "${input_dir}" ] ; then echo "Input directory not set" ; exit 1 ; fi
if [ ! -d "${input_dir}" ] ; then echo "Input directory \"${input_dir}\" does not exist" ; exit 1 ; fi
echo "Input dir \"${input_dir}\" exists"

if [   -z "${output_dir}" ] ; then echo "Output directory not set" ; exit 1 ; fi
if [ ! -d "${output_dir}" ] ; then echo "Output directory \"${output_dir}\" does not exist" ; exit 1 ; fi
echo "Output dir \"${output_dir}\" exists"

if [   -z "${RECOUNT_REF}" ] ; then echo "RECOUNT_REF directory not set" ; exit 1 ; fi
if [ ! -d "${RECOUNT_REF}" ] ; then echo "RECOUNT_REF directory \"${RECOUNT_REF}\" does not exist" ; exit 1 ; fi
echo "RECOUNT_REF dir \"${RECOUNT_REF}\" exists"

if [   -z "${RECOUNT_TEMP}" ] ; then echo "RECOUNT_TEMP directory not set" ; exit 1 ; fi
if [ ! -d "${RECOUNT_TEMP}" ] ; then echo "RECOUNT_TEMP directory \"${RECOUNT_TEMP}\" does not exist" ; exit 1 ; fi
echo "RECOUNT_TEMP dir \"${RECOUNT_TEMP}\" exists"

REF2=${RECOUNT_REF}
TEMP2=${RECOUNT_TEMP}

set -ex

export INPUT="/recount-input" && \
export OUTPUT="/recount-output" && \
export RECOUNT_REF="/recount-ref" && \
export RECOUNT_TEMP="/recount-temp" && \
singularity exec \
    -c \
    -B ${input_dir}:${INPUT} \
    -B ${output_dir}:${OUTPUT} \
    -B ${REF2}:${RECOUNT_REF} \
    -B ${TEMP2}:${RECOUNT_TEMP} \
    ${image} \
    /bin/bash -c \
    "source activate rnaseq_lite && bash /recount-bin/rna_seq_lite.bash"

set +x

if [[ ${keep} == 0 ]] ; then
    echo "Removing temp directory"
    rm -rf "${INPUT_DIR}" "${TEMP_DIR}"
fi
