#! /usr/bin/env python3
# -*- coding: utf-8 -*-
""" Utility functions """
from __future__ import (absolute_import, division, print_function, unicode_literals)
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
    chars_to_escape = ' ()"[]&,!;$' + "'"
    for ch_ in chars_to_escape:
        orig_path = orig_path.replace(ch_, r'\%c' % ch_)
    return orig_path


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
    if urlout.status_code not in [200, 300, 301]:
        print('something bad happened %d %s' % (urlout.status_code, url_))
        raise HTTPError
    return urlout.text.split('\n')


def test_run_command():
    cmd = 'echo "HELLO"'
    out = run_command(cmd, do_popen=True).read().strip()
    print(out, cmd)
    assert out == b'HELLO'


def test_cleanup_path():
    INSTR = '/home/ddboline/THIS TEST PATH (OR SOMETHING LIKE IT) ' \
            '[OR OTHER!] & ELSE $;,""'
    OUTSTR = r'/home/ddboline/THIS\ TEST\ PATH\ ' \
             r'\(OR\ SOMETHING\ LIKE\ IT\)\ \[OR\ OTHER\!\]\ \&\ ' \
             r'ELSE\ \$\;\,\"\"'
    print(cleanup_path(INSTR))
    assert cleanup_path(INSTR) == OUTSTR


def test_datetimestring():
    import datetime
    dt = datetime.datetime(year=1980, month=11, day=17, hour=5, minute=12, second=13)
    assert datetimestring(dt) == '1980-11-17T05:12:13Z'


def test_datetimefromstring():
    import datetime
    from pytz import UTC
    dt0 = '1980-11-17T05:12:13Z'
    dt1 = datetime.datetime(year=1980, month=11, day=17, hour=5, minute=12, second=13, tzinfo=UTC)
    assert datetimefromstring(dt0) == dt1


def test_get_md5():
    import tempfile
    with tempfile.NamedTemporaryFile() as tfi:
        tfi.write(b'HELLO\n')
        tfi.flush()
        out = get_md5(tfi.name)
        assert out == b'0084467710d2fc9d8a306e14efbe6d0f'
