url=$1
output=$2
errout=$3

curl --retry 10 --retry-max-time 600 "$url" > $output 2> $errout
ecode=$?
ERRORS=$(fgrep '<ERROR>' $output)
FINISHED=$(tail -n1 $output | fgrep '</EXPERIMENT_PACKAGE_SET>')

while [[ $ecode -ne 0 || ! -z $ERRORS  || -z $FINISHED ]]; do
    curl --retry 10 --retry-max-time 600 "$url" > $output 2> $errout
    ecode=$?
    ERRORS=$(fgrep "<ERROR>" $output)
    FINISHED=$(tail -n1 $output | fgrep '</EXPERIMENT_PACKAGE_SET>')
done

#example error
#<?xml version="1.0" encoding="UTF-8" ?>
#<!DOCTYPE eEfetchResult PUBLIC "-//NLM//DTD efetch 20131226//EN" "https://eutils.ncbi.nlm.nih.gov/eutils/dtd/20131226/efetch.dtd">
#<eFetchResult>
#        <ERROR>Cannot retrieve history data. query_key: 1, WebEnv: MCID_5f9318713073fb183e652822, retstart: 12000, retmax: 500</ERROR>
#        <ERROR>Can't fetch uids from history because of: NCBI C++ Exception:
#    Error: UNK_MODULE(CException::eInvalid) "UNK_FILE", line 18446744073709551615: UNK_FUNC ---
#</ERROR>
#</eFetchResult>
