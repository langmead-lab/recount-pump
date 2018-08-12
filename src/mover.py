#!/usr/bin/env python

"""mover -- copy files around, supporting local, web, S3 and Globus

Usage:
  mover get <source> <dest> [options]
  mover put <source> <dest> [options]
  mover exists <file> [options]
  mover nop

Options:
  -h, --help                 Show this screen.
  --version                  Show version.
  --profile=<profile>        AWS credentials profile section [default: default].
  --endpoint-url=<url>       Endpoint URL for S3 API.  If not set, uses AWS default.
  --curl=<curl>              curl executable [default: curl].
  --globus-ini=<path>        Path to globus ini file [default: ~/.recount/globus.ini].
  --globus-section=<string>  Section header for globus in ini file [default: globus].
  --log-ini <ini>            ini file for log aggregator [default: ~/.recount/log.ini].
  --log-section <section>    ini file section for log aggregator [default: log].
  --log-level <level>        set level for log aggregation; could be CRITICAL,
                             ERROR, WARNING, INFO, DEBUG [default: INFO].
  -a, --aggregate            enable log aggregation.
"""


from __future__ import print_function
import os
import re
import time
import pytest
import globus_sdk
import log
from docopt import docopt
import subprocess
from functools import wraps
from shutil import copyfile
import threading
import sys
import boto3
import botocore

try:
    from urllib.parse import urlparse, urlencode, quote_plus
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode, quote_plus
    from urllib2 import urlopen, Request, HTTPError, URLError
    sys.exc_clear()
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser
    sys.exc_clear()

"""
mover.py
Adapted from Dooplicity/Rail

Tools for interacting with local filesystems, the web, and cloud services.

Licensed under the MIT License:

Copyright (c) 2014 Abhi Nellore and Ben Langmead.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


def path_join(unix, *args):
    """ Performs UNIX-like os.path.joins on Windows systems if necessary.
        unix: True iff UNIX-like path join should be performed; else False
        Return value: joined path
    """
    args_list = []
    if unix:
        for i in range(len(args) - 1):
            try:
                if args[i][-1] != '/':
                    args_list.append(args[i] + '/')
            except IndexError:
                # Empty element
                pass
        args_list.append(args[-1])
        return ''.join(args_list)
    else:
        return os.path.join(*args)


def parse_s3_url(url):
    """
    Parses s3:// URL and returns (bucket name, key, basename)
    """
    if not url.startswith('s3://') and not url.startswith('s3n://'):
        raise RuntimeError('Bad S3 URL: "%s"' % url)
    start_index = 5 if url[:5] == 's3://' else 6
    while url[start_index] == '/':
        start_index += 1
    next_slash = url.index('/', start_index)
    last_slash = url.rindex('/')
    return url[start_index:next_slash], url[next_slash+1:], url[last_slash+1:]


class S3Mover(object):

    def __init__(self, profile=None, endpoint_url=None):
        self.session = boto3.Session(profile_name=profile)
        self.s3 = self.session.resource('s3', endpoint_url=endpoint_url)

    def close(self):
        pass

    def exists(self, url):
        bucket_str, path_str, _ = parse_s3_url(url)
        try:
            self.s3.Object(bucket_str, path_str).load()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise  # Something else has gone wrong.
        return True

    def make_bucket(self, bucket):
        self.s3.create_bucket(Bucket=bucket).wait_until_exists()

    def put(self, source, destination):
        if not os.path.exists(source):
            raise RuntimeError('Source file "%s" does not exist')
        bucket_str, path_str, file_str = parse_s3_url(destination)
        bucket = self.s3.Bucket(bucket_str)
        with open(source, 'rb') as data:
            bucket.put_object(Key=path_str, Body=data)

    def remove(self, url):
        bucket_str, path_str, _ = parse_s3_url(url)
        self.s3.Object(bucket_str, path_str).delete()

    def remove_bucket(self, bucket):
        bucket = self.s3.Bucket(bucket)
        bucket.delete()

    def get(self, source, destination):
        bucket_str, path_str, file_str = parse_s3_url(source)
        if os.path.isdir(destination):
            destination = os.path.join(destination, file_str)
        if os.path.exists(destination):
            raise RuntimeError('Destination of get already exists: "%s"' % destination)
        bucket = self.s3.Bucket(bucket_str)
        bucket.download_file(path_str, destination)


def parse_globus_url(url):
    """
    Parses globus:// URL and returns (endpoint id, path, basename)
    """
    if not url.startswith('globus://'):
        raise RuntimeError('Bad globus URL: "%s"' % url)
    start_index = 9
    while url[start_index] == '/':
        start_index += 1
    next_slash = url.index('/', start_index)
    last_slash = url.rindex('/')
    return url[start_index:next_slash], url[next_slash:], url[last_slash+1:]


def replace_endpoint(url, replacement):
    if not url.startswith('globus://'):
        raise RuntimeError('Bad globus URL: "%s"' % url)
    start_index = 9
    while url[start_index] == '/':
        start_index += 1
    next_slash = url.index('/', start_index)
    return 'globus://' + replacement + url[next_slash:]


def read_globus_config(config_fn, section='globus'):
    cfg = RawConfigParser()
    if not os.path.exists(config_fn):
        raise RuntimeError('No such globus ini file: "%s"' % config_fn)
    cfg.read(config_fn)
    print(cfg.sections())
    if section not in cfg.sections():
        raise RuntimeError('No [%s] section in log ini file "%s"' % (section, config_fn))
    return cfg


class GlobusMover(object):
    """
    Does not currently handle endpoint activation.  Next step might be to look
    at MyProxy.
    """

    UUID_RE = re.compile(r'^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$', re.IGNORECASE)

    @classmethod
    def is_uuid(cls, st):
        return bool(cls.UUID_RE.search(st))

    def eid_from_name(self, name):
        return self.cfg.get(self.section, name)

    def __init__(self, ini_fn, section):
        self.section = section
        self.cfg = read_globus_config(ini_fn, section=section)
        auth_client = globus_sdk.ConfidentialAppAuthClient(client_id=self.cfg.get(section, 'id'),
                                                           client_secret=self.cfg.get(section, 'secret'))
        tokens = auth_client.oauth2_client_credentials_tokens()
        transfer_data = tokens.by_resource_server['transfer.api.globus.org']
        authorizer = globus_sdk.AccessTokenAuthorizer(transfer_data['access_token'])
        self.client = globus_sdk.TransferClient(authorizer=authorizer)

    def close(self):
        pass

    def exists(self, url):
        endpoint_id, path, basename = parse_globus_url(url)
        orig_endpoint_id = endpoint_id
        if not self.is_uuid(endpoint_id):
            endpoint_id = self.eid_from_name(endpoint_id)
        r = self.client.endpoint_autoactivate(endpoint_id, if_expires_in=3600)
        if r["code"] == "AutoActivationFailed":
            raise RuntimeError('Failed to autoactivate endpoint "%s": %s' % (orig_endpoint_id, str(r)))
        for entry in self.client.operation_ls(endpoint_id, path=path):
            assert entry['endpoint'] == endpoint_id
            assert entry['path'] == path
            return True
        return False

    def make_bucket(self, url):
        raise RuntimeError('No way to make path with Globus mover')

    def put(self, source, destination, type='put', timeout=100000, poll_interval=60):
        endpoint_id_src, path_src, basename_src = parse_globus_url(source)
        endpoint_id_dst, path_dst, basename_dst = parse_globus_url(destination)
        if not self.is_uuid(endpoint_id_src):
            endpoint_id_src = self.eid_from_name(endpoint_id_src)
            source = replace_endpoint(source, endpoint_id_src)
        if not self.is_uuid(endpoint_id_dst):
            endpoint_id_dst = self.eid_from_name(endpoint_id_dst)
            destination = replace_endpoint(destination, endpoint_id_dst)
        assert self.is_uuid(endpoint_id_src)
        assert self.is_uuid(endpoint_id_dst)
        tdata = globus_sdk.TransferData(
            self.client,
            endpoint_id_src,
            endpoint_id_dst,
            label='GlobusMover ' + type,
            sync_level="checksum",
            verify_checksum=True,
            encrypt_data=True)
        tdata.add_item(path_src, path_dst)
        transfer_result = self.client.submit_transfer(tdata)
        task_id = transfer_result['task_id']
        while self.client.get_task(task_id)['status'] == 'ACTIVE':
            log.info('Waiting for globus cp "%s" -> "%s" (task %s)' %
                      (source, destination, task_id), 'mover.py')
            self.client.task_wait(task_id, timeout, poll_interval)
        final_status = self.client.get_task(task_id)['status']
        log.info('Finished globus cp "%s" -> "%s" (task %s) with final status %s' %
                  (source, destination, task_id, final_status), 'mover.py')

    def get(self, source, destination):
        self.put(source, destination, type='get')


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """ Retry calling the decorated function using an exponential backoff.

        http://www.saltycrane.com/blog/2009/11/
            trying-out-retry-decorator-python/
        Original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

        ExceptionToCheck: the exception to check. May be a tuple of
            exceptions to check
        tries: number of times to try (not retry) before giving up
        delay: initial delay between retries in seconds
        backoff: backoff multiplier e.g. value of 2 will double the delay
            each retry
        logger: logger to use. If None, print

        Return value: retry wrapper.
    """
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = '%s, Retrying in %d seconds...' % (str(e), mdelay)
                    if logger is not None:
                        logger.warning(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry  # true decorator
    return deco_retry


class Url(object):
    def __init__(self, url):
        """ Uses prefix to determine type of URL.

            Prefix is part of URL before colon, if it's present.

            url: URL string
        """
        if ':' in url:
            colon_index = url.index(':')
            prefix = url[:colon_index].lower()
            if prefix[:3] == 's3n':
                self.type = 's3n'
            elif prefix[:2] == 's3':
                self.type = 's3'
            elif prefix[:5] == 'https':
                self.type = 'https'
            elif prefix[:4] == 'http':
                self.type = 'http'
            elif prefix[:4] == 'ftp':
                self.type = 'ftp'
            elif prefix[:5] == 'local':
                self.type = 'local'
            elif prefix[:3] == 'sra':
                self.type = 'sra'
            elif prefix[:5] == 'dbgap':
                self.type = 'dbgap'
            elif prefix[:6] == 'globus':
                self.type = 'globus'
            else:
                raise RuntimeError(('Unrecognized URL %s; it\'s not S3, '
                                    'HTTP, FTP, or local.') % url)
            self.suffix = url[colon_index+1:]
        else:
            self.type = 'local'
            self.suffix = url
        self.is_s3 = self.type[:2] == 's3'
        self.is_curlable = self.type in ['ftp', 'http', 'https']
        self.is_local = self.type == 'local'
        self.is_sra = (self.type == 'sra' or self.type == 'dbgap')
        self.is_dbgap = self.type == 'dbgap'
        self.is_globus = self.type == 'globus'

    def to_url(self, caps=False):
        """ Returns URL string: an absolute path if local or an URL.

            Return value: URL string
        """
        if self.type == 'local':
            absolute_path = os.path.abspath(self.suffix)
            return (absolute_path + '/') if self.suffix[-1] == '/' \
                else absolute_path
        elif self.type[:2] == 's3' and caps:
            return self.type.upper() + ':' + self.suffix
        elif self.type[:3] == 'sra' or self.type[:5] == 'dbgap':
            return self.suffix.upper()
        else:
            return self.type + ':' + self.suffix


class CommandThread(threading.Thread):
    """ Runs a command on a separate thread. """
    def __init__(self, command_list):
        super(CommandThread, self).__init__()
        self.command_list = command_list
        self.process_return = None
        self._osdevnull = open(os.devnull, 'w')
        self.process = None

    def run(self):
        self.process = subprocess.Popen(self.command_list, stdout=self._osdevnull,
                                        stderr=self._osdevnull)
        self.process_return = self.process.wait()


class WebMover(object):
    """ Ultimate goal: seamless communication with various web services.

        For now, just distinguishes among S3, the local filesystem, and the
        web.
    """
    def __init__(self, curl_exe='curl'):
        """ curl_exe: curl executable
        """
        self.curl = curl_exe
        self._osdevnull = open(os.devnull, 'w')

    def close(self):
        pass

    def exists(self, path):
        curl_process = subprocess.Popen(
                                ['curl', '--head', path],
                                bufsize=-1, stdout=subprocess.PIPE,
                                stderr=self._osdevnull
                            )
        curl_err = curl_process.stdout.read()
        return_code = curl_process.wait()
        curl_err = curl_err.lower()
        if ('resolve host' in curl_err or 'not found' in curl_err
             or return_code in [19, 6]):
            # 19 is file doesn't exist; 6 is couldn't resolve host
            return False
        return True

    def make_bucket(self, url):
        raise RuntimeError('No way to make path with Web mover')

    def put(self, source, destination):
        raise RuntimeError('Cannot upload to FTP, HTTP, or HTTPS.')

    def get(self, source, destination='.'):
        """ Retrieves file from web (http, https, ftp) source.

            Note that if the destination has a file whose name is the same
            as the source name, THAT FILE IS DELETED -- EVEN IF the destination
            has a different filename! This is a curl quirk, and if it
            becomes a problem in pipelines, it will be addressed.

            source: filename of source
            destination: filename of destination
        """
        oldp = os.getcwd()
        try:
            os.chdir(destination)
        except OSError:
            # destination doesn't exist; the filename is the destination
            filename = os.path.abspath(destination)
            try:
                os.makedirs(os.path.dirname(os.path.abspath(filename)))
            except OSError:
                pass
        else:
            filename = os.path.join(os.path.abspath(destination),
                                    source.rpartition('/')[2])
        command_list = ['curl', '-o', filename,
                        '-s', '-O', '--connect-timeout', '600', source]
        command = ' '.join(command_list)
        tries = 0
        curl_thread = None
        while tries < 5:
            break_outer_loop = False
            curl_thread = CommandThread(command_list)
            curl_thread.start()
            last_print_time = time.time()
            try:
                last_size = os.path.getsize(filename)
            except OSError:
                last_size = 0
            while curl_thread.is_alive():
                now_time = time.time()
                if now_time - last_print_time > 160:
                    try:
                        new_size = os.path.getsize(filename)
                    except OSError:
                        new_size = 0
                    if new_size == last_size:
                        # Download stalled
                        break_outer_loop = True
                        break
                    else:
                        last_size = new_size
                    last_print_time = now_time
                    time.sleep(1)
                time.sleep(1)
            if break_outer_loop:
                tries += 1
                print('Download stalled on try %d.' % tries, file=sys.stderr)
                try:
                    curl_thread.process.kill()
                except AttributeError:
                    pass
                try:
                    os.remove(filename)
                except OSError:
                    pass
                time.sleep(2)
                continue
            if curl_thread.process_return > 89 or curl_thread.process_return == 56:
                '''If the exit code is greater than the highest-documented
                curl exit code, there was a timeout.'''
                print('Too many simultaneous connections; '
                      'restarting in 10 s.', file=sys.stderr)
                time.sleep(5)
            else:
                break
        os.chdir(oldp)
        if curl_thread is not None and curl_thread.process_return > 0:
            raise RuntimeError(('Nonzero exitlevel %d from curl command '
                                '"%s"')
                               % (curl_thread.process_return, command))


class Mover(object):
    """ Ultimate goal: seamless communication with various web services.

        For now, just distinguishes among S3, the local filesystem, and the
        web. Perhaps class structure could be improved.
    """
    def __init__(self, profile=None, endpoint_url=None,
                 curl_exe='curl',
                 globus_ini='~/.recount/globus.ini',
                 globus_section='globus', enable_web=False, enable_s3=False,
                 enable_globus=False):
        self.enable_web = enable_web
        self.enable_s3 = enable_s3
        self.enable_globus = enable_globus
        if enable_s3:
            self.s3_mover = S3Mover(profile=profile, endpoint_url=endpoint_url)
        if enable_globus:
            self.globus_mover = GlobusMover(ini_fn=os.path.expanduser(globus_ini), section=globus_section)
        if enable_web:
            self.web_mover = WebMover(curl_exe=curl_exe)

    def close(self):
        if self.enable_s3:
            self.s3_mover.close()
        if self.enable_globus:
            self.globus_mover.close()
        if self.enable_web:
            self.web_mover.close()

    def exists(self, url):
        """ Returns whether a given file exists. 

            Note that on S3, this refers to an exact key name, so "directories"
            and filenames with the same name are allowed to coexist. This
            function returns whether the input key is actually a _file_, not
            whether the key + a terminal slash is present. On the other hand,
            if a file is local, this function returns True whether or not the
            file is a directory. The idea here is to return whether the URL
            would have to be overwritten if writing to it.

            url: URL-- can be local, on S3, or on the web

            Return value: True iff the file exists, else False.
        """
        url = Url(url)
        if url.is_local:
            log.info('Local exists for "%s"' % url, 'mover.py')
            return os.path.exists(os.path.abspath(url.to_url()))
        elif url.is_s3:
            if not self.enable_s3:
                raise RuntimeError('exists called on S3 URL "%s" but S3 not enabled' % url)
            log.info('S3 exists for "%s"' % url, 'mover.py')
            return self.s3_mover.exists(url.to_url())
        elif url.is_globus:
            if not self.enable_globus:
                raise RuntimeError('exists called on Globus URL "%s" but Globus not enabled' % url)
            log.info('Globus exists for "%s"' % url, 'mover.py')
            return self.globus_mover.exists(url.to_url())
        elif url.is_curlable:
            if not self.enable_web:
                raise RuntimeError('exists called on web URL "%s" but web not enabled' % url)
            log.info('Web exists for "%s"' % url, 'mover.py')
            return self.web_mover.exists(url.to_url())

    def make_bucket(self, url):
        url = Url(url)
        if url.is_local:
            log.info('Local make_bucket for "%s"' % url, 'mover.py')
            return os.path.exists(os.path.abspath(url.to_url()))
        elif url.is_s3:
            if not self.enable_s3:
                raise RuntimeError('make_bucket called on S3 URL "%s" but S3 not enabled' % url)
            log.info('S3 make_bucket for "%s"' % url, 'mover.py')
            return self.s3_mover.make_bucket(url.to_url())
        elif url.is_globus:
            if not self.enable_globus:
                raise RuntimeError('make_bucket called on Globus URL "%s" but Globus not enabled' % url)
            log.info('Globus make_bucket for "%s"' % url, 'mover.py')
            return self.globus_mover.make_bucket(url.to_url())
        elif url.is_curlable:
            if not self.enable_web:
                raise RuntimeError('make_bucket called on web URL "%s" but web not enabled' % url)
            log.info('Web make_bucket for "%s"' % url, 'mover.py')
            return self.web_mover.make_bucket(url.to_url())

    def get(self, url, destination='.'):
        """ Copies a file at url to the local destination.

            url: URL-- can be local, on S3, or on the web
            destination: destination on local filesystem

            No return value.
        """
        url = Url(url)
        src, dst = url.to_url(), destination
        if url.is_local:
            log.info('Local get from "%s" to "%s"' % (src, dst), 'mover.py')
            copyfile(src, dst)
        elif url.is_s3:
            if not self.enable_s3:
                raise RuntimeError('get called on S3 URL "%s" but S3 not enabled' % url)
            log.info('S3 get from "%s" to "%s"' % (src, dst), 'mover.py')
            self.s3_mover.get(src, dst)
        elif url.is_globus:
            if not self.enable_globus:
                raise RuntimeError('get called on Globus URL "%s" but Globus not enabled' % url)
            log.info('Globus get from "%s" to "%s"' % (src, dst), 'mover.py')
            self.globus_mover.get(src, dst)
        elif url.is_curlable:
            if not self.enable_web:
                raise RuntimeError('get called on web URL "%s" but web not enabled' % url)
            log.info('Web get from "%s" to "%s"' % (src, dst), 'mover.py')
            self.web_mover.get(src, dst)

    def put(self, source, url):
        """ Copies a file from source to the url .

            source: where to retrieve file from local filesystem
            destination: destination URL

            No return value.
        """
        url = Url(url)
        dst = url.to_url()
        if url.is_local:
            log.info('Local put from "%s" to "%s"' % (source, dst), 'mover.py')
            copyfile(source, dst)
        elif url.is_s3:
            if not self.enable_s3:
                raise RuntimeError('put called on S3 URL "%s" but S3 not enabled' % url)
            log.info('S3 put from "%s" to "%s"' % (source, dst), 'mover.py')
            self.s3_mover.put(source, dst)
        elif url.is_globus:
            if not self.enable_globus:
                raise RuntimeError('put called on Globus URL "%s" but Globus not enabled' % url)
            log.info('Globus put from "%s" to "%s"' % (source, dst), 'mover.py')
            self.globus_mover.put(source, dst)
        elif url.is_curlable:
            if not self.enable_web:
                raise RuntimeError('put called on web URL "%s" but web not enabled' % url)
            log.info('Web put from "%s" to "%s"' % (source, dst), 'mover.py')
            self.web_mover.put(source, dst)


@pytest.yield_fixture(scope='session')
def test_file():
    fn = '.TestMover.1'
    with open(fn, 'w') as ofh:
        ofh.write('test')
    yield fn
    if os.path.exists(fn):
        os.remove(fn)


def test_url1():
    u = Url('http://www.test.com/xyz')
    assert u.is_curlable
    assert not u.is_local
    assert not u.is_s3
    assert not u.is_sra
    assert not u.is_globus


def test_url2():
    u = Url('s3://recount-pump/ref/test')
    assert not u.is_curlable
    assert not u.is_local
    assert u.is_s3
    assert not u.is_sra
    assert not u.is_globus


def test_url3():
    u = Url('globus://recount-pump/ref/test')
    assert not u.is_curlable
    assert not u.is_local
    assert not u.is_s3
    assert not u.is_sra
    assert u.is_globus


def test_parse_url1():
    for proto in ['s3', 's3n']:
        a, b, c = parse_s3_url(proto + '://recount-pump/ref/test')
        assert 'recount-pump' == a
        assert 'ref/test' == b
        assert 'test' == c


def test_parse_url2():
    a, b, c = parse_globus_url('globus://recount-pump/ref/test')
    assert 'recount-pump' == a
    assert '/ref/test' == b
    assert 'test' == c


def test_exists(test_file):
    m = Mover()
    assert m.exists(test_file)


def test_put(test_file):
    m = Mover()
    dst = test_file + '.put'
    assert not os.path.exists(dst)
    m.put(test_file, dst)
    assert os.path.exists(dst)
    os.remove(dst)


def test_get(test_file):
    m = Mover()
    dst = test_file + '.get'
    assert not os.path.exists(dst)
    m.get(test_file, dst)
    assert os.path.exists(dst)
    os.remove(dst)


def test_s3_1(s3_enabled, s3_service, test_file):
    if not s3_enabled: pytest.skip('Skipping S3 tests')
    bucket_name = 'mover-test'
    s3_service.make_bucket(bucket_name)
    dst = ''.join(['s3://', bucket_name, '/', test_file, '.put'])
    assert not s3_service.exists(dst)
    s3_service.put(test_file, dst)
    assert s3_service.exists(dst)
    s3_service.remove(dst)
    s3_service.remove_bucket(bucket_name)


if __name__ == '__main__':
    args = docopt(__doc__)
    agg_ini = os.path.expanduser(args['--log-ini']) if args['--aggregate'] else None
    log.init_logger(log.LOG_GROUP_NAME, log_ini=agg_ini, agg_level=args['--log-level'])
    log.init_logger('sqlalchemy', log_ini=agg_ini, agg_level=args['--log-level'],
                    sender='sqlalchemy')
    globus_ini = args['--globus-ini']
    globus_ini = os.path.expanduser(globus_ini)
    enable_globus = os.path.exists(globus_ini)
    try:
        log.info('In main', 'mover.py')
        if args['exists']:
            m = Mover(profile=args['--profile'],
                      endpoint_url=args['--endpoint-url'],
                      curl_exe=args['--curl'],
                      globus_ini=args['--globus-ini'],
                      globus_section=args['--globus-section'],
                      enable_globus=enable_globus, enable_s3=True, enable_web=True)
            print(m.exists(args['<file>']))
        if args['get']:
            m = Mover(profile=args['--profile'],
                      endpoint_url=args['--endpoint-url'],
                      curl_exe=args['--curl'],
                      globus_ini=args['--globus-ini'],
                      globus_section=args['--globus-section'],
                      enable_globus=enable_globus, enable_s3=True, enable_web=True)
            m.get(args['<source>'], args['<dest>'])
        elif args['put']:
            m = Mover(profile=args['--profile'],
                      endpoint_url=args['--endpoint-url'],
                      curl_exe=args['--curl'],
                      globus_ini=args['--globus-ini'],
                      globus_section=args['--globus-section'],
                      enable_globus=enable_globus, enable_s3=True, enable_web=True)
            m.put(args['<source>'], args['<dest>'])
        elif args['nop']:
            pass
    except Exception:
        log.error('Uncaught exception:', 'mover.py')
        raise
