#! /usr/bin/env python
# -*- coding: utf-8 -*-
""" Utility functions """
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from subprocess import call, Popen, PIPE

HOMEDIR = os.getenv('HOME')

def run_command(command, do_popen=False, turn_on_commands=True):
    ''' wrapper around os.system '''
    if not turn_on_commands:
        print(command)
        return command
    elif do_popen:
        return Popen(command, shell=True, stdout=PIPE, close_fds=True).stdout
    else:
        return call(command, shell=True)

def cleanup_path(orig_path):
    """ cleanup path string using escape character """
    return orig_path.replace(' ', r'\ ').replace('(', r'\(')\
                    .replace(')', r'\)').replace('\'', r'\\\'')\
                    .replace('[', r'\[').replace(']', r'\]')\
                    .replace('"', r'\"').replace("'", r"\'")\
                    .replace('&', r'\&').replace(',', r'\,')\
                    .replace('!', r'\!').replace(';', r'\;')\
                    .replace('$', r'\$')

def datetimestring(dt_):
    ''' input should be datetime object, output is string '''
    if not hasattr(dt_, 'strftime'):
        return dt_
    st_ = dt_.strftime('%Y-%m-%dT%H:%M:%S%z')
    if len(st_) == 24 or len(st_) == 20:
        return st_
    elif len(st_) == 19 and 'Z' not in st_:
        return '%sZ' % st_

def datetimefromstring(tstr, ignore_tz=False):
    """ wrapper around dateutil.parser.parse """
    from dateutil.parser import parse
    return parse(tstr, ignoretz=ignore_tz)

def get_md5(fname):
    """ wrapper around md5sum """
    _cmd = 'md5sum %s 2> /dev/null' % cleanup_path(fname)
    return run_command(_cmd, do_popen=True).read().split()[0]

def openurl(url_):
    """ wrapper around requests.get.text simulating urlopen """
    import requests
    from requests import HTTPError
    try:
        requests.packages.urllib3.disable_warnings()
    except AttributeError:
        pass
    urlout = requests.get(url_, verify=False)
    if urlout.status_code != 200:
        print('something bad happened %d %s' % (urlout.status_code, url_))
        raise HTTPError
    return urlout.text.split('\n')
