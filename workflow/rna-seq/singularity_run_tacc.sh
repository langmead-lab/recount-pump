#!/bin/bash

# Author: Ben Langmead
#  Email: langmea@cs.jhu.edu
#   Date: 1/5/2018

# Runs a singularity container containing the next flow script and its
# in-container driver.  Assumes we're running on TACC, where no user-
# defined directory binding is allowed.  Instead we have to use the
# TACC-standard bind points: $SCRATCH to /scratch, $WORK to /work, and
# $HOME to /home1.

# To accomplish this, we create a new subdirectory of
# $SCRATCH/recount-pump, inside which we create subdirectories input,
# output, and temp.

# $WORK/recount-pump/ref contains ref files.

usage() {
    echo "./singularity_run_tacc.sh <job_name> <input_dir> [options]*"
    echo ""
    echo "<input_dir> must already exist"
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
input_dir=$2
shift 2

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
    test -f "${image}" || (echo "No such image file: \"${image}\"" && exit 1)
fi 
echo "Image set to \"${image}\""

test -n "${job_name}"

test -n "${input_dir}" || (echo "Input directory not set" && exit 1)
test -d "${input_dir}" || (echo "Input directory \"${input_dir}\" does not exist" && exit 1)
echo "Input dir \"${input_dir}\" exists"

REF_DIR="${WORK}/recount-pump/ref"
test -d "${REF_DIR}" || (echo "Reference dir \"\" does not exist" && exit 1)
echo "Reference dir \"${REF_DIR}\" exists"

mkdir -p "${SCRATCH}/recount-pump"
job_dir="${SCRATCH}/recount-pump/${job_name}"
test -d "${job_dir}" && echo "Job directory already exists: \"${job_dir}\"" && exit 1

INPUT_DIR="${SCRATCH}/recount-pump/${job_name}/input"
OUTPUT_DIR="${SCRATCH}/recount-pump/${job_name}/output"
TEMP_DIR="${SCRATCH}/recount-pump/${job_name}/temp"

mkdir -p "${INPUT_DIR}" "${OUTPUT_DIR}" "${TEMP_DIR}"
echo "Copying input files..."
cp ${input_dir}/* "${INPUT_DIR}"

set -ex

export INPUT="${INPUT_DIR}" && \
export OUTPUT="${OUTPUT_DIR}" && \
export RECOUNT_REF="${REF_DIR}" && \
export RECOUNT_TEMP="${TEMP_DIR}" && \
singularity exec \
    $* \
    ${image} \
    /bin/bash -c \
    "source activate rnaseq && bash /tmp/rna_seq.bash"

set +x

if [[ $keep == 0 ]] ; then
    echo "Removing (copied) input directory and temp directory"
    rm -rf "${INPUT_DIR}" "${TEMP_DIR}"
fi
