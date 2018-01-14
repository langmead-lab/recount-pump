#!/usr/bin/env python

from __future__ import print_function
import sys
import pandas


def ftp_dir_exists(dir, ftps):
    import ftplib
    try:
        ftps.cwd(dir)
    except ftplib.error_perm as err:
        if err[0].startswith('550'):
            return False
        else:
            raise err
    return True


def enaize_accession(srr, ftps):
    srr_pre = srr[:6]
    if len(srr) == 10:
        srr00 = '00' + srr[-1]
        dir = '/vol1/fastq/%s/%s/%s' % (srr_pre, srr00, srr)
    else:
        dir = '/vol1/fastq/%s/%s' % (srr_pre, srr)
    if not ftp_dir_exists(dir, ftps):
        raise RuntimeError('Dir does not exist: "%s"' % dir)
    fn_1, fn_2 = srr + '_1.fastq.gz', srr + '_2.fastq.gz'
    files = ftps.nlst()
    if fn_1 not in files:
        fn = srr + '.fastq.gz'
        if fn not in files:
            raise RuntimeError('Neither "%s" nor "%s" are among contents of dir "%s": %s', fn, fn_1, dir, str(files))
        url = 'ftp://ftp.sra.ebi.ac.uk' + dir + '/' + fn
        return url, 'NA'
    if fn_2 not in files:
        raise RuntimeError('"%s" is in dir "%s" but not "%s": %s', fn_1, dir, fn_2, str(files))
    url_1 = 'ftp://ftp.sra.ebi.ac.uk' + dir + '/' + fn_1
    url_2 = 'ftp://ftp.sra.ebi.ac.uk' + dir + '/' + fn_2
    return url_1, url_2


def go(csv_fn, sanity_check=True, enaize=False):
    print("Parsing CSV \"%s\"..." % csv_fn, file=sys.stderr)
    # Need low_memory=False so we can get the column types right
    df = pandas.read_csv(csv_fn, low_memory=False)

    if 'run_accession' not in df.columns:
        raise ValueError('Expected column named "run_accession"')

    accessions = set()
    enaize_first, ftps = True, None
    for index, row in df.iterrows():
        acc = row['run_accession']
        if sanity_check and acc in accessions:
            raise ValueError('Accession "%s" occurred more than once' % acc)
        elif sanity_check:
            accessions.add(acc)
        if enaize:
            if enaize_first:
                import ftplib
                ftps = ftplib.FTP('ftp.sra.ebi.ac.uk')
                ftps.login('anonymous', 'guest')
                enaize_first = False
            url_1, url_2 = enaize_accession(acc, ftps)
            rec = [url_1, url_2, 'NA', 'NA', 'NA', 'NA', 'wget']
        else:
            rec = [acc, 'NA', 'NA', 'NA', 'NA', 'NA', 'sra']
        print(','.join(rec))
    if not enaize_first:
        ftps.quit()


if __name__ == '__main__':
    argv = sys.argv[1:]
    enaize, sanity_check = False, True
    if '--enaize' in argv:
        argv.remove('--enaize')
        enaize = True
    if '--no-sanity-check' in argv:
        argv.remove('--no-sanity-check')
        sanity_checks = False
    if len(argv) == 0:
        raise RuntimeError('Must specify csv file')
    go(argv[0], sanity_check=sanity_check, enaize=enaize)
