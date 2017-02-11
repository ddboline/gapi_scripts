#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
    gcal_instance class, used by parse_glirc and parse_physics
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
try:
    from util import datetimestring
except ImportError:
    from scripts.util import datetimestring
import datetime

from apiclient import sample_tools
from apiclient.errors import HttpError


def t_execute(request):
    timeout = 1
    while True:
        try:
            return request.execute()
        except HttpError as exc:
            if 'user rate limit exceeded' in exc.content.lower():
                if timeout > 1:
                    print('timeout %s' % timeout)
                time.sleep(timeout)
                timeout *= 2
                if timeout >= 64:
                    raise
            elif 'sufficient permissions' in exc.content.lower():
                raise
            else:
                print(dir(exc))
                print('content', exc.content)
                print('response', exc.resp)
                raise


class gcal_instance(object):
    ''' class to make use of google python api '''

    def __init__(self, app='calendar', version='v3'):
        ''' init function '''
        curdir = os.curdir

        if not os.path.isfile('%s.dat' % app):

            os.chdir(os.getenv('HOME'))

        self.service, self.flags = \
            sample_tools.init([], app, version, __doc__, __file__,
                              scope='https://www.googleapis.com/auth/%s' % app)

        os.chdir(curdir)

    def add_to_gcal(self, ev_entry, calid):
        '''
            add event to calendar,
            rely on define_new_event_object function to do actual work
        '''
        request = self.service.events()\
                              .insert(calendarId=calid,
                                      body=ev_entry.define_new_event_object())
        response = t_execute(request)
        return response

    def delete_from_gcal(self, calid, evid):
        ''' delete event from calendar '''
        request = self.service.events().delete(calendarId=calid, eventId=evid)
        response = t_execute(request)
        return response

    def get_gcal_events(self, calid='', callback_fn=None, do_single_events=False):
        '''
            get events from calendar
            use callback_fn to handle output
        '''
        list_of_gcal_events = {}

        if do_single_events:
            mintime = datetimestring(datetime.datetime.now() - datetime.timedelta(days=1))
            maxtime = datetimestring(datetime.datetime.now() + datetime.timedelta(days=7))

            request = self.service.events().list(
                calendarId=calid, singleEvents=True, timeMin=mintime, timeMax=maxtime)
            response = t_execute(request)
        else:
            request = self.service.events().list(calendarId=calid)
            response = t_execute(request)

        new_request = True
        while new_request:
            callback_fn(response, list_of_gcal_events)

            new_request = self.service.events().list_next(request, response)
            if not new_request:
                break
            request = new_request
            response = t_execute(request)
        return list_of_gcal_events

    def get_gcal_instances(self, calid='', evtid='', callback_fn=None):
        '''
            get instances of a recurring event
        '''
        mintime = datetimestring(datetime.datetime.now() - datetime.timedelta(days=1))
        maxtime = datetimestring(datetime.datetime.now() + datetime.timedelta(days=7))

        list_of_gcal_instances = {}
        request = self.service.events().instances(
            calendarId=calid, eventId=evtid, timeMin=mintime, timeMax=maxtime)
        response = t_execute(request)

        new_request = True
        while new_request:
            callback_fn(response, list_of_gcal_instances)

            new_request = self.service.events().list_next(request, response)
            if not new_request:
                break
            request = new_request
            response = t_execute(request)
        return list_of_gcal_instances

    def list_gcal_calendars(self):
        ''' list calendars '''
        request = self.service.calendarList().list()
        response = t_execute(request)

        for ent in response['items']:
            print('%s: %s' % (ent['summary'], ent['id']))
