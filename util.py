#! /usr/bin/env python
# -*- coding: utf-8 -*-
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
    return orig_path.replace(' ', '\ ').replace('(', '\(').replace(')', '\)')\
                    .replace('\'', '\\\'').replace('[', '\[')\
                    .replace(']', '\]').replace('"', '\"').replace("'", "\'")\
                    .replace('&', '\&').replace(',', '\,').replace('!', '\!')\
                    .replace(';', '\;').replace('$', '\$')

def dateTimeString(d):
    ''' input should be datetime object, output is string '''
    if not hasattr(d, 'strftime'):
        return d
    s = d.strftime('%Y-%m-%dT%H:%M:%S%z')
    if len(s) == 24 or len(s) == 20:
        return s
    elif len(s) == 19 and 'Z' not in s:
        return '%sZ' % s

def datetimefromstring(tstr, ignore_tz=False):
    import dateutil.parser
    #tstr = tstr.replace('-05:00', '-0500').replace('-04:00', '-0400')
    #print(tstr)
    return dateutil.parser.parse(tstr, ignoretz=ignore_tz)

def get_md5(fname):
    _cmd = 'md5sum %s 2> /dev/null' % cleanup_path(fname)
    return run_command(_cmd, do_popen=True).read().split()[0]
