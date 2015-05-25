#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
    gcal_instance class, used by parse_glirc and parse_physics
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

class gcal_instance(object):
    ''' class to make use of google python api '''
    def __init__(self, app='calendar', version='v3'):
        ''' init function '''
        from apiclient import sample_tools
        import os

        curdir = os.curdir

        if not os.path.isfile('%s.dat' % app):

            os.chdir(os.getenv('HOME'))

        self.service, self.flags = \
            sample_tools.init([], app, version, __doc__, __file__,\
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
        response = request.execute()
        return response

    def delete_from_gcal(self, calid, evid):
        ''' delete event from calendar '''
        request = self.service.events().delete(calendarId=calid, eventId=evid)
        response = request.execute()
        return response

    def get_gcal_events(self, calid='', callback_fn=None,
                        do_single_events=False):
        '''
            get events from calendar
            use callback_fn to handle output
        '''
        list_of_gcal_events = {}

        if do_single_events:
            from util import dateTimeString
            import datetime
            mintime = dateTimeString(datetime.datetime.now() -
                                     datetime.timedelta(days=1))
            maxtime = dateTimeString(datetime.datetime.now() +
                                     datetime.timedelta(days=7))

            request = self.service.events().list(calendarId=calid,
                                                 singleEvents=True,
                                                 timeMin=mintime,
                                                 timeMax=maxtime)
            response = request.execute()
        else:
            request = self.service.events().list(calendarId=calid)
            response = request.execute()


        new_request = True
        while new_request:
            callback_fn(response, list_of_gcal_events)

            new_request = self.service.events().list_next(request, response)
            if not new_request:
                break
            request = new_request
            response = request.execute()
        return list_of_gcal_events

    def get_gcal_instances(self, calid='', evtid='', callback_fn=None):
        '''
            get instances of a recurring event
        '''
        from util import dateTimeString
        import datetime
        mintime = dateTimeString(datetime.datetime.now() -
                                 datetime.timedelta(days=1))
        maxtime = dateTimeString(datetime.datetime.now() +
                                 datetime.timedelta(days=7))

        list_of_gcal_instances = {}
        request = self.service.events().instances(calendarId=calid,
                                                  eventId=evtid,
                                                  timeMin=mintime,
                                                  timeMax=maxtime)
        response = request.execute()

        new_request = True
        while new_request:
            callback_fn(response, list_of_gcal_instances)

            new_request = self.service.events().list_next(request, response)
            if not new_request:
                break
            request = new_request
            response = request.execute()
        return list_of_gcal_instances

    def list_gcal_calendars(self):
        ''' list calendars '''
        request = self.service.calendarList().list()
        response = request.execute()

        for ent in response['items']:
            print('%s: %s' % (ent['summary'], ent['id']))
