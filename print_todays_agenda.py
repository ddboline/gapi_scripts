#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
    Print today's agenda using gcal api
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
import datetime
import pytz
import dateutil.parser
import re

TZOBJ = pytz.timezone("US/Eastern")
TAG_RE = re.compile(r'<[^>]+>')


class CalendarEvent(object):
    """ Hold data from google calendar, functions to print them out """

    def __init__(self, dt=datetime.datetime.now(TZOBJ)):
        """ init function """
        self.event_time = dt
        self.title = None
        self.description = None
        self.eventid = None

    def read_gcal_event(self, obj):
        """ read google calendar event """
        if 'start' in obj:
            if 'dateTime' in obj['start']:
                tstr = obj['start']['dateTime']
                self.event_time = dateutil.parser.parse(tstr)
        if 'summary' in obj:
            self.title = obj['summary']
        if 'description' in obj:
            self.description = TAG_RE.sub('', obj['description'])
        self.eventid = obj['id']

    def print_event(self):
        """ print gcal event """
        outstr = ['']
        outstr.append(self.event_time.strftime('%Y-%m-%dT%H:%M:%S%z'))
        if self.title:
            outstr.append('\t summary: %s' % self.title)
        if self.description:
            outstr.append('\t description: %s' % self.description.replace('\n', ' ')
                          .replace('  ', ' '))
        outstr.append('')
        return '\n'.join(outstr)


def print_todays_agenda():
    """ print today's agenda """
    force_update = False
    _args = os.sys.argv
    for _arg in _args:
        if _arg == 'force':
            force_update = True

    def process_response(response, outlist):
        """ call back function """
        for item in response['items']:
            evt = CalendarEvent()
            evt.read_gcal_event(item)
            kstr = '%s %s' % (evt.event_time, evt.eventid)
            outlist[kstr] = evt

    def get_agenda():
        """ print several events """
        outstr = []
        from gcal_instance import gcal_instance
        gcal = gcal_instance()
        exist = gcal.get_gcal_events(
            calid='ddboline@gmail.com', callback_fn=process_response, do_single_events=True)
        for k in sorted(exist.keys()):
            ex_ = exist[k]
            if ex_.event_time > datetime.datetime.now(TZOBJ) + \
                    datetime.timedelta(days=1):
                continue
            elif ex_.event_time > datetime.datetime.now(TZOBJ):
                outstr.append(ex_.print_event())
        return ('\n'.join(outstr)).encode(errors='ignore')

    cachefile = '/tmp/.todays_agenda.tmp'

    def convert_time_date(st_):
        """ date conversion... """
        t0_ = time.gmtime(st_)
        return datetime.date(year=t0_.tm_year, month=t0_.tm_mon, day=t0_.tm_mday)

    if not os.path.exists(cachefile) or convert_time_date(time.time()) > \
            convert_time_date(os.stat(cachefile).st_mtime) or force_update:
        with open(cachefile, 'w') as infile:
            try:
                infile.write(get_agenda())
            except TypeError:
                infile.write(get_agenda().decode())
    with open(cachefile, 'r') as infile:
        outstr = infile.readlines()
    return ''.join(outstr)


if __name__ == '__main__':
    print(print_todays_agenda())
