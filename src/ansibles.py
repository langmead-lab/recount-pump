#!/usr/bin/env python
"""
ansibles.py
Part of Dooplicity framework

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

from __future__ import print_function
import os
import time
try:
    from urllib.parse import urlparse, urlencode, quote_plus
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode, quote_plus
    from urllib2 import urlopen, Request, HTTPError, URLError
import hashlib
import hmac
import binascii
import subprocess
import json
from functools import wraps
from shutil import copyfile
import threading
import sys
import socket


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


def clean_url(url):
    """ Tacks an s3:// onto the beginning of a URL if necessary. 

        url: an S3 URL, or what should be one

        Return value: S3 URL
    """
    if url[:6] == 's3n://':
        return ('s3://' + url[6:])
    elif url[:5] != 's3://':
        return ('s3://' + url)
    else:
        return url


def bucket_from_url(url):
    """ Extracts a bucket name from an S3 URL.

        url: an S3 URL, or what should be one

        Return value: bucket name from S3 URL
    """
    if url[:6] == 's3n://':
        start_index = 6
    elif url[:5] == 's3://':
        start_index = 5
    elif url[0] == '/':
        start_index = 1
    else:
        start_index = 0
    while url[start_index] == '/':
        start_index += 1
    return url[start_index:start_index+url[start_index:].index('/')]


class S3Ansible(object):
    """ Permits simple interactions with S3 via the AWS CLI. 

        Another option is to use Boto directly, but it comes with a lot of
        unused classes --- tools never touched by Dooplicity/Rail. Further, my
        preference is to integrate tools with good command-line APIs so
        languages can be mixed and matched. It should be noted that the AWS
        CLI "uses the boto successor botcore under the hood."
        -http://stackoverflow.com/questions/15287724
        /aws-s3-client-for-linux-with-multipart-upload .
    """

    def __init__(self, aws_exe='aws', profile='default', iface=None):
        """ Initializes S3Ansible.

            aws_exe: path to aws executable. Should be unnecessary on all
                platforms if the AWS CLI is installed properly, but users
                may want to specify a different executable if multiple versions
                are installed on their systems.
            iface: object of type DooplicityInterface to which to write status
                updates or None if no such updates should be written.
        """
        self.aws = aws_exe
        self.profile = profile
        self._osdevnull = open(os.devnull, 'w')
        self.iface = iface

    def create_bucket(self, bucket, region='us-east-1'):
        """ Creates a new bucket only if it doesn't already exist.

            Raises subprocess.CalledProcessError if a bucket already exists.

            bucket: string with bucket name to create; can have an s3:// at
                the beginning or not.

            No return value.
        """
        cleaned_url = clean_url(bucket)
        # Check if bucket exists
        check_bucket_command = [self.aws, '--profile', self.profile,
                                    's3', 'ls', cleaned_url, '--region',
                                    region]
        try:
            subprocess.check_output(check_bucket_command, bufsize=-1,
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            if 'AccessDenied' in e.output:
                raise RuntimeError(('Error "{}" encountered trying to list '
                                    'bucket with command "{}".').format(
                                            e.output, ' '.join(
                        check_bucket_command
                                                )
                                        ))
            if 'NoSuchBucket' in e.output:
                create_bucket_command = [self.aws, '--profile', self.profile,
                                         's3', 'mb', cleaned_url, '--region',
                                         region]
                try:
                    subprocess.check_output(create_bucket_command,
                                            bufsize=-1,
                                            stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    raise RuntimeError(
                            'Error "{}" encountered trying to make bucket '
                            'with command "{}".'.format(
                                            e.output, ' '.join(
                                                    create_bucket_command
                                                )
                                        ))

    def exists(self, path):
        """ Checks whether a file on S3 exists.

            A file and a directory on S3 can have the same name since
            directories are just included in key names.

            path: file on S3

            Return value: True iff file exists; else False
        """
        cleaned_url = clean_url(path)
        # Extract filename from URL; everything after terminal slash
        filename = cleaned_url[::-1][:cleaned_url[::-1].index('/')][::-1]
        aws_command = [self.aws, '--profile', self.profile, 
                        's3', 'ls', cleaned_url]
        aws_process = subprocess.Popen(aws_command,
                                       stdout=subprocess.PIPE,
                                       stderr=self._osdevnull,
                                       bufsize=-1)
        filename_size = len(filename)
        for line in aws_process.stdout:
            line = line.strip()
            if line[:3] != 'PRE' and filename == line[-filename_size:]:
                return True
        return False

    def is_dir(self, path):
        """ Checks whether a directory on S3 exists.

            There are no directories on S3, really, so is_dir() actually
            returns True if there are object keys on S3 that begin with the
            directory name plus a slash.

            path: directory name on S3, including bucket

            Return value: True iff directory exists; else False
        """
        cleaned_url = clean_url(path) + '/'
        while cleaned_url[-2] == '/':
            cleaned_url = cleaned_url[:-1]
        # Now the URL has just one trailing slash
        aws_command = [self.aws, '--profile', self.profile,
                       's3', 'ls', cleaned_url]
        try:
            list_out = \
                subprocess.check_output(aws_command,
                                        stderr=self._osdevnull,
                                        bufsize=-1).strip()
        except subprocess.CalledProcessError:
            # Bucket doesn't exist
            return False
        if list_out:
            # Even if the directory is empty, aws s3 ls outputs something
            return True
        return False

    def remove_dir(self, path):
        """ Removes a directory on S3.

            Technically, this function deletes all object keys that begin with
            the specified identifier; so it's VERY important to append a 
            slash to the end of a path so other directories aren't deleted.

            path: directory name on S3, including bucket

            No return value.
        """
        cleaned_url = clean_url(path) + '/'
        while cleaned_url[-2] == '/':
            cleaned_url = cleaned_url[:-1]
        # Now the URL has just one trailing slash
        aws_command = [self.aws, '--profile', self.profile,
                       's3', 'rm', '--recursive', cleaned_url]
        if self.iface:
            rm_process = subprocess.Popen(aws_command,
                                          bufsize=-1,
                                          stdout=subprocess.PIPE,
                                          stderr=self._osdevnull)
            lim = 70 # Max number of chars to print in delete message
            process_start = time.time()
            printed = False
            self.iface.status(
                    'Searching for existing files on S3 to delete...'
                )
            line = rm_process.stdout.readline()
            try:
                to_print = line.split('\r')[1].strip('\r\n')
            except IndexError:
                to_print = line.strip('\r\n')
            self.iface.status(
                    to_print[:lim] + ('...' if len(to_print) > lim else '')
                )
            for line in rm_process.stdout:
                if time.time() - process_start > 10:
                    self.iface.status('**If deletion is taking too long, '
                                      'CTRL+C out and choose different '
                                      'output directories.**')
                    process_start = time.time()
                    printed = False
                elif not printed and time.time() - process_start > 5:
                    try:
                        to_print = line.split('\r')[1].strip('\r\n')
                    except IndexError:
                        to_print = line.strip('\r\n')
                    self.iface.status(
                            to_print[:lim] + ('...' if len(to_print) > lim else '')
                        )
                    printed = True
            if rm_process.wait():
                '''Bucket does not exist; OR there's another error, but fail
                silently.'''
                pass
        else:
            try:
                subprocess.check_call(aws_command, bufsize=-1,
                                            stdout=self._osdevnull,
                                            stderr=self._osdevnull)
            except subprocess.CalledProcessError:
                # Bucket does not exist
                pass

    def put(self, source, destination):
        """ Copies a file to S3. 

            source: file from local filesystem
            destination: destination on S3

            No return value.
        """
        # Always use SSE
        aws_command = [self.aws, '--profile', self.profile,
                       's3', 'cp', os.path.abspath(source),
                       clean_url(destination), '--sse']
        subprocess.check_call(aws_command, bufsize=-1,
                              stdout=self._osdevnull,
                              stderr=sys.stderr)

    def get(self, source, destination='.'):
        """ Gets a file from S3.

            source: file from S3
            destination: destination on local filesystem

            No return value.
        """
        aws_command = [self.aws, '--profile', self.profile, 's3', 'cp',
                       clean_url(source), os.path.abspath(destination)]
        subprocess.check_call(aws_command, bufsize=-1,
                              stdout=self._osdevnull,
                              stderr=sys.stderr)

    def expire_prefix(self, prefix, days=4):
        """ Expires object prefix after specified number of days.

            Rule is added iff no other rule exists for prefix.

            prefix: prefix to expire, including bucket name
            days: number of days

            No return value.
        """
        cleaned_prefix = clean_url(prefix)
        bucket = bucket_from_url(cleaned_prefix)
        # Create bucket if it doesn't exist
        try:
            self.create_bucket(bucket)
        except subprocess.CalledProcessError as e:
            print(dir(e))
            raise RuntimeError(('Bucket %s already exists on S3. Change '
                                'affected output directories in job flow '
                                'and try again. The more distinctive the '
                                'name chosen, the less likely it\'s '
                                'already a bucket on S3. It may be '
                                'easier to create a bucket first on S3 '
                                'and use its name + a subdirectory as '
                                'the output directory.') % bucket)
        # Remove bucket name from prefix
        prefix = cleaned_prefix[cleaned_prefix[6:].index('/')+7:]
        aws_command = [self.aws, '--profile', self.profile,
                       's3api', 'get-bucket-lifecycle', '--bucket', bucket]
        lifecycle_process = subprocess.Popen(aws_command, 
                                             bufsize=-1,
                                             stderr=subprocess.PIPE,
                                             stdout=subprocess.PIPE)
        errors = lifecycle_process.stderr.read()
        try:
            rules = json.loads(lifecycle_process.stdout.read())['Rules']
        except ValueError:
            # No Lifecycle Configuration
            rules = []
        return_value = lifecycle_process.wait()
        if return_value:
            if 'AccessDenied' in errors:
                # Just proceed with a warning
                print(('Warning: account does not have access to bucket '
                       'lifecycle. Skipping scheduling of deletion of '
                       'data with prefix "{}". Perform this deletion '
                       'manually with the console or the AWS CLI after the '
                       'job flow is complete.').format(prefix), file=sys.stderr)
                return
            if 'NoSuchLifecycleConfiguration' in errors:
                # Raise exception iff lifecycle config exists
                raise RuntimeError(errors)
        add_rule = True
        for rule in rules:
            try:
                if rule['Prefix'] == prefix:
                    add_rule = False
            except KeyError:
                pass
        if add_rule:
            rules.append(
                    {
                        'Expiration': {'Days': days},
                        'Status': 'Enabled',
                        'Prefix': prefix
                    }
                )
            aws_command = [self.aws, '--profile', self.profile,
                           's3api', 'put-bucket-lifecycle', '--bucket',
                           bucket, '--lifecycle-configuration',
                                    '{"Rules":%s}'
                                    % json.dumps(rules)]
            try:
                subprocess.check_call(aws_command, bufsize=-1,
                                      stdout=self._osdevnull,
                                      stderr=sys.stderr)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(('Error encountered changing lifecycle'
                                    'parameters with command "{}".').format(
                                                ' '.join(aws_command)
                                            ))


def aws_params_from_json(json_object, prefix=''):
    """ Parses JSON object to generate AWS query string params.

        If recursion depth is exceeded, there is no justice in the universe.
        This function may be useful for generating simple GET requests
        from JSON but is not currently in use in the code.

        json_object: subset of JSON object to parse.

        Return value: parsed URL dictionary.
    """
    params = {}
    if isinstance(json_object, dict):
        for key in json_object:
            for subkey, value in aws_params_from_json(
                                                        json_object[key],
                                                        prefix + key + '.'
                                                ).items():
                params[subkey] = value
    elif isinstance(json_object, list):
        for i, item in enumerate(json_object):
            for key, value in aws_params_from_json(
                                                    json_object[i],
                                                    prefix + ('member.%d.'
                                                                % (i+1))
                                                ).items():
                params[key] = value
    elif isinstance(json_object, str):
        params = {prefix[:-1]: json_object}
    return params


def sign(key, message):
    """ Helper function for outputting AWS signatures.

        See docstring of aws_signature() for more information.
    """
    return hmac.new(key, message.encode('utf-8'), hashlib.sha256).digest()


def aws_signature(string_to_sign, secret_key,
                  datestamp=time.strftime('%Y%m%d', time.gmtime()),
                  region='us-east-1', service='elasticmapreduce'):
    """ Outputs AWS Signature v4 for a string to sign from a secret key.

        Taken from 
        http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html
        .

        string_to_sign: string to sign.
        secret_key: AWS secret key
        datestamp: time.gmtime(), a struct_time object

        Return value: precisely the signature; no need to URL encode it.
    """
    return binascii.hexlify(
        sign(
            sign(
                sign(
                    sign(
                        sign(
                            ('AWS4' + secret_key).encode('utf-8'),
                            datestamp),
                        region),
                    service),
                'aws4_request'), string_to_sign
            )
        )


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


@retry(socket.error, tries=4, delay=3, backoff=2)
@retry(URLError, tries=4, delay=3, backoff=2)
@retry(HTTPError, tries=4, delay=3, backoff=2)
def urlopen_with_retry(request):
    """ Facilitates retries when opening URLs.

        request: urllib2.Request object

        Return value: file-like object of type urllib2.urlopen with
            response
    """
    return urlopen(request)


def parsed_credentials(profile='default', base=None):
    """ Parses credentials according to (approximately) AWS CLI's rules

        profile: AWS CLI profile to use
        base: if None, raise RuntimeError on error; otherwise, append to
            base.errors

        Return value: tuple (aws access key id, aws secret access key,
                                region, service role, instance profile)
    """
    (aws_access_key_id, aws_secret_access_key, region, service_role,
        instance_profile) = None, None, None, None, None
    if profile == 'default':
        # Search environment variables for keys first if profile is default
        try:
            aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID']
            aws_secret_access_key \
                = os.environ['AWS_SECRET_ACCESS_KEY']
        except KeyError:
            to_search = '[default]'
        else:
            to_search = None
        try:
            # Also grab region
            region = os.environ['AWS_DEFAULT_REGION']
        except KeyError:
            pass
    else:
        to_search = ['[profile ' + profile + ']', '[' + profile + ']']
    # Now search AWS CLI config file for the right profile
    if to_search is not None:
        cred_file = os.path.join(os.environ['HOME'], '.aws', 'credentials')
        config_file = os.path.join(os.environ['HOME'], '.aws', 'config')
        try:
            (region_set, access_key_id_set, secret_access_key_set,
                service_role_set, instance_profile_set) = (
                    False, False, False, False, False
                )
            for to_open in [cred_file, config_file]:
                with open(to_open) as config_stream:
                    for line in config_stream:
                        if line.strip() in to_search:
                            break
                    grab_roles = False
                    for line in config_stream:
                        tokens = [token.strip() for token
                                    in line.strip().split('=')]
                        if tokens[0] == 'region' and not region_set:
                            region = tokens[1]
                            region_set = True
                        elif (tokens[0] == 'aws_access_key_id'
                                and not access_key_id_set):
                            aws_access_key_id = tokens[1]
                            access_key_id_set = True
                        elif (tokens[0] == 'aws_secret_access_key'
                                and not secret_access_key_set):
                            aws_secret_access_key = tokens[1]
                            secret_access_key_set = True
                        elif tokens[0] == 'emr':
                            grab_roles = True
                        elif (tokens[0] == 'service_role' and grab_roles
                                and not service_role_set):
                            service_role = tokens[1]
                            service_role_set = True
                        elif (tokens[0] == 'instance_profile'
                                and grab_roles
                                and not instance_profile_set):
                            instance_profile = tokens[1]
                            instance_profile_set = True
                        else:
                            line = line.strip()
                            if line[0] == '[' and line[-1] == ']':
                                # Break on start of new profile
                                break
        except IOError:
            message = ('No valid AWS CLI configuration found. '
                       'Make sure the AWS CLI is installed '
                       'properly and that one of the following '
                       'is true:\n\na) The environment variables '
                       '"AWS_ACCESS_KEY_ID" and '
                       '"AWS_SECRET_ACCESS_KEY" are set to '
                       'the desired AWS access key ID and '
                       'secret access key, respectively, and '
                       'the profile (--profile) is set to an existing one.\n\n'
                       'b) The file(s) ".aws/config" and/or '
                       '".aws/credentials" exist(s) in your '
                       'home directory encoding a valid profile. '
                       'To set this/these up, run "aws configure" '
                       'after installing the AWS CLI.')
            if base is not None:
                base.errors.append(message)
            else:
                raise RuntimeError(message)
    return (aws_access_key_id, aws_secret_access_key, 
            region, service_role, instance_profile)


class AWSAnsible(object):
    """ Interacts with AWS via POST requests (so far). See AWS API
        documentation. GET requests are cheaper, and if ever a GET request
        need be implemented, the function aws_params_from_json() in this file
        converts JSON into parameters from a query string.

        Uses Signature Version 4, the latest version as of 5/15/14.
        Important: relies on proper installation of AWS CLI to obtain
        keys.

        http://stackoverflow.com/questions/1088715/
        how-to-sign-amazon-web-service-requests-from-the-python-app-engine

        helped make this class.
    """
    def __init__(self, profile='default', region=None, valid_regions=None,
                    base_uri='https://elasticmapreduce.amazonaws.com'):
        # Set service and job flow roles to None for now
        self.service_role, self.instance_profile = None, None
        if base_uri[:8] == 'https://':
            base_suffix = base_uri[8:]
            self.base_prefix = base_uri[:8]
        elif base_uri[:7] == 'http://':
            base_suffix = base_uri[7:]
            self.base_prefix = base_uri[:7]
        else:
            raise RuntimeError('Base URI for POST request must begin with '
                               'http:// or https://.')
        split_base_suffix = [segment for segment in base_suffix.split('/')
                                if segment]
        self.service = split_base_suffix[0].partition('.')[0]
        try:
            self.canonical_uri = '/' + '/'.join([quote_plus(segment) 
                for segment in split_base_suffix[1:]])
        except IndexError:
            # No segments
            self.canonical_uri = '/'
        self.algorithm = 'AWS4-HMAC-SHA256'
        (self._aws_access_key_id,
            self._aws_secret_access_key, 
            self.region,
            self.service_role,
            self.instance_profile) = parsed_credentials(profile)
        if region is not None:
            # Always override region
            self.region = region
        if self.region is None:
            # If after all this, the region is None, default to us-east-1
            self.region = 'us-east-1'
        # Check for region validity
        if valid_regions is not None:
            if self.region not in valid_regions:
                raise RuntimeError(('Region "%s" is invalid for service '
                                    '"%s". Region must be one of {%s}.') % 
                                        (self.region, self.service,
                                        ', '.join(['"%s"' % a_region
                                                   for a_region
                                                   in valid_regions]))
                                    )
        self.host_header = '.'.join([self.region, split_base_suffix[0]])

    def post_request(self, json_object, target='ElasticMapReduce.RunJobFlow'):
        """ Submits JSON payload to AWS using Signature Version 4.

            Reference: http://docs.aws.amazon.com/general/latest/gr/
                sigv4-create-canonical-request.html

            json_object: object containing json payload
            target: the X-Amz-Target from the request header. Google for more
                information; for submitting job flows, this is
                ElasticMapReduce.RunJobFlow.

            Return value: file-like object of type urllib2.urlopen with
                response
        """
        payload = json.dumps(json_object)
        hashed_payload = hashlib.sha256(payload).hexdigest()
        headers = {
                'Content-Type': 'application/x-amz-json-1.1',
                'X-Amz-Target': target,
                'Content-Length': str(len(payload)),
                'User-Agent': 'Dooplicity',
                'Host': self.host_header,
                'X-Amz-Content-Sha256': hashed_payload
            }
        # For POST request, no canonical query string
        canonical_query_string = ''
        # Construct full query string dictionary
        gmtime = time.gmtime()
        datestamp = time.strftime('%Y%m%d', gmtime)
        headers['X-Amz-Date'] = time.strftime('%Y%m%dT%H%M%SZ', gmtime)
        canonical_headers = '\n'.join([(key.lower().strip() + ':' 
                                        + value.strip())
                                        for key, value 
                                        in sorted(headers.items())]) \
                                     + '\n'
        signed_headers \
            = ';'.join([header.lower() for header in sorted(headers)]) 
        canonical_request = \
            '\n'.join(['POST', self.canonical_uri, canonical_query_string,
                       canonical_headers, signed_headers, hashed_payload])
        hashed_canonical_request = hashlib.sha256(
                                            canonical_request
                                        ).hexdigest()
        credential_scope = '/'.join([datestamp, self.region, self.service,
                                        'aws4_request'])
        string_to_sign = '\n'.join([self.algorithm, headers['X-Amz-Date'],
                                    credential_scope,
                                    hashed_canonical_request])
        signature = aws_signature(
                            string_to_sign,
                            self._aws_secret_access_key,
                            datestamp=datestamp,
                            region=self.region,
                            service=self.service
                        )
        headers['Authorization'] = ('%s Credential=%s/%s/%s/%s/aws4_request, '
                'SignedHeaders=%s, Signature=%s'
            ) % (self.algorithm, self._aws_access_key_id, datestamp,
                 self.region, self.service, signed_headers, signature)
        request = Request(''.join([self.base_prefix, self.host_header,
                                   self.canonical_uri]),
                                  headers=headers,
                                  data=payload)
        return urlopen_with_retry(request)


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
            elif prefix[:4] == 'hdfs':
                self.type = 'hdfs'
            elif prefix[:5] == 'https':
                self.type = 'https'
            elif prefix[:4] == 'http':
                self.type = 'http'
            elif prefix[:4] == 'ftp':
                self.type = 'ftp'
            elif prefix[:5] == 'local':
                self.type = 'local'
            elif prefix[:3] == 'nfs':
                self.type = 'nfs'
            elif prefix[:3] == 'sra':
                self.type = 'sra'
            elif prefix[:5] == 'dbgap':
                self.type = 'dbgap'
            else:
                raise RuntimeError(('Unrecognized URL %s; it\'s not S3, HDFS, '
                                    'HTTP, FTP, or local.') % url)
            self.suffix = url[colon_index+1:]
        else:
            self.type = 'local'
            self.suffix = url
        self.is_s3 = self.type[:2] == 's3'
        self.is_curlable = self.type in ['ftp', 'http', 'https']
        self.is_local = self.type == 'local'
        self.is_hdfs = self.type == 'hdfs'
        self.is_nfs = self.type == 'nfs'
        self.is_sra = (self.type == 'sra' or self.type == 'dbgap')
        self.is_dbgap = self.type == 'dbgap'

    def to_url(self, caps=False):
        """ Returns URL string: an absolute path if local or an URL.

            Return value: URL string
        """
        if self.type in ['local', 'nfs']:
            absolute_path = os.path.abspath(self.suffix)
            return (absolute_path + '/') if self.suffix[-1] == '/' \
                else absolute_path
        elif self.type[:2] == 's3' and caps:
            return self.type.upper() + ':' + self.suffix
        elif self.type[:3] == 'sra' or self.type[:5] == 'dbgap':
            return self.suffix.upper()
        else:
            return self.type + ':' + self.suffix

    def plus(self, file_or_subdirectory):
        """ Returns a new URL + file_or_subdirectory.

            file_or_subdirectory: file or subdirectory of URL

            Return value: Url object with file_or_directory tacked on
        """
        original_url = self.to_url()
        if self.is_local:
            return Url(os.path.join(original_url, file_or_subdirectory))
        else:
            return Url(path_join(True, original_url, file_or_subdirectory))

    def upper_url(self):
        """ Uppercases an URL's prefix or gives a local URL's absolute path.

            This is Useful for hiding protocol names from Elastic MapReduce so
            it doesn't mistake a URL passed as a mapper argument as an input
            URL.

            Return value: transformed URL string
        """
        if self.type == 'local':
            absolute_path = os.path.abspath(self.suffix)
            return (absolute_path + '/') if self.suffix[-1] == '/' \
                else absolute_path
        else:
            return self.type.upper() + ':' + self.suffix

    def to_nonnative_url(self):
        """ Converts s3n:// URLs to s3:// URLs 

            Return value: converted URL
        """
        if self.type[:2] == 's3':
            return 's3:' + self.suffix
        else:
            return self.type + ':' + self.suffix

    def to_native_url(self):
        """ Converts s3:// URLs to s3n:// URLs 

            Return value: converted URL
        """
        if self.type[:2] == 's3':
            return 's3n:' + self.suffix
        else:
            return self.type + ':' + self.suffix


class CommandThread(threading.Thread):
    """ Runs a command on a separate thread. """
    def __init__(self, command_list):
        super(CommandThread, self).__init__()
        self.command_list = command_list
        self.process_return = None
        self._osdevnull = open(os.devnull, 'w')

    def run(self):
        self.process_return \
            = subprocess.Popen(self.command_list, stdout=self._osdevnull,
                               stderr=self._osdevnull).wait()


class WebAnsible(object):
    """ Ultimate goal: seamless communication with various web services.

        For now, just distinguishes among S3, the local filesystem, and the
        web.
    """
    def __init__(self, curl_exe='curl', keep_alive=False):
        """ curl_exe: curl executable
            keep_alive: True iff status messages should be written to stderr
        """
        self.curl = curl_exe
        self.keep_alive = keep_alive
        self._osdevnull = open(os.devnull, 'w')

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
                    if self.keep_alive:
                        print('\nreporter:status:alive', file=sys.stderr)
                        sys.stderr.flush()
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


class Ansible(object):
    """ Ultimate goal: seamless communication with various web services.

        For now, just distinguishes among S3, the local filesystem, and the
        web. Perhaps class structure could be improved.
    """
    def __init__(self, aws_exe='aws', profile='default', curl_exe='curl',
                 keep_alive=False):
        self.s3_ansible = S3Ansible(aws_exe=aws_exe, profile=profile)
        self.web_ansible = WebAnsible(curl_exe=curl_exe, keep_alive=keep_alive)

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
            return os.path.exists(os.path.abspath(url.to_url()))
        elif url.is_s3:
            return self.s3_ansible.exists(url.to_url())
        elif url.is_curlable:
            return self.web_ansible.exists(url.to_url())

    def get(self, url, destination='.'):
        """ Copies a file at url to the local destination.

            url: URL-- can be local, on S3, or on the web
            destination: destination on local filesystem

            No return value.
        """
        url = Url(url)
        if url.is_local:
            copyfile(url.to_url(), destination)
        elif url.is_s3:
            self.s3_ansible.get(url.to_url(), destination)
        elif url.is_curlable:
            self.web_ansible.get(url.to_url(), destination)

    def put(self, source, url):
        """ Copies a file from source to the url .

            source: where to retrieve file from local filesystem
            destination: destination URL

            No return value.
        """
        url = Url(url)
        if url.is_local:
            copyfile(source, url.to_url())
        elif url.is_s3:
            self.s3_ansible.put(source, url.to_url())
        elif url.is_curlable:
            self.web_ansible.put(source, url.to_url())
