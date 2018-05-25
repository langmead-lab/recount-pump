#!/usr/bin/env python

import ftplib
import unittest


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


def open_era_ftp():
    ftps = ftplib.FTP('ftp.sra.ebi.ac.uk')
    ftps.login('anonymous', 'guest')
    return ftps


def enaize_accession(srr, ftps=None):
    srr_pre = srr[:6]
    if len(srr) == 10:
        srr00 = '00' + srr[-1]
        dir = '/vol1/fastq/%s/%s/%s' % (srr_pre, srr00, srr)
    else:
        dir = '/vol1/fastq/%s/%s' % (srr_pre, srr)
    fn_1, fn_2 = srr + '_1.fastq.gz', srr + '_2.fastq.gz'
    if ftps is not None:
        if not ftp_dir_exists(dir, ftps):
            raise RuntimeError('Dir does not exist: "%s"' % dir)
        files = ftps.nlst()
        if fn_1 not in files:
            fn = srr + '.fastq.gz'
            if fn not in files:
                raise RuntimeError('Neither "%s" nor "%s" are among contents of dir "%s": %s', fn, fn_1, dir, str(files))
            url = 'ftp://ftp.sra.ebi.ac.uk' + dir + '/' + fn
            return url, None
        if fn_2 not in files:
            raise RuntimeError('"%s" is in dir "%s" but not "%s": %s', fn_1, dir, fn_2, str(files))
    url_1 = 'ftp://ftp.sra.ebi.ac.uk' + dir + '/' + fn_1
    url_2 = 'ftp://ftp.sra.ebi.ac.uk' + dir + '/' + fn_2
    return url_1, url_2


class TestArchive(unittest.TestCase):

    def test_success_1(self):
        enaize_accession('ERR204819')  # from GEUVADIS

    def test_success_2(self):
        ftps = open_era_ftp()
        enaize_accession('ERR204819', ftps=ftps)  # from GEUVADIS
        ftps.quit()

    def test_failure_1(self):
        enaize_accession('ERXXXXXX')

    def test_failure_2(self):
        ftps = open_era_ftp()
        with self.assertRaises(RuntimeError):
            enaize_accession('ERXXXXXX', ftps=ftps)
        ftps.quit()


if __name__ == '__main__':
    import sys

    if '--test' in sys.argv:
        sys.argv.remove('--test')
        unittest.main()
