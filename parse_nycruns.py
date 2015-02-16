#!/usr/bin/python
from __future__ import print_function

import os
import datetime, pytz
from urllib2 import urlopen
import random
from gcal_instance import gcal_instance

from parse_events import base_event, parse_events,\
    months_short, months_long,\
    weekdays, tzobj, strip_out_unicode_crap


class nycruns_event(base_event):
    def __init__(self, dt=None, ev_name='', ev_url='', ev_desc='', ev_loc=''):
        base_event.__init__(self, dt=dt, ev_name=ev_name, ev_url=ev_url, ev_desc=ev_desc, ev_loc=ev_loc)

    def compare(self, obj, partial_match=None):
        comp_list = []
        attr_list = ['event_time', 'event_end_time', 'event_url', 'event_location', 'event_name']
        out_list = []
        for attr in attr_list:
            c0 = getattr(self, attr)
            c1 = getattr(obj, attr)
            out_list.append([c0, c1])
            if type(c0) == str or type(c0) == unicode:
                c0 = strip_out_unicode_crap(c0)
            if type(c1) == str or type(c1) == unicode:
                c1 = strip_out_unicode_crap(c1)
            if type(c0) == str:
                c0 = c0.replace('  ', ' ').strip()
            if type(c1) == str:
                c1 = c1.replace('  ', ' ').strip()
            if c0 == c1:
                comp_list.append(True)
            else:
                comp_list.append(False)
        if all(comp_list):
            return True
        else:
            if partial_match:
                if sum(comp_list) > partial_match:
                    return True
            return False


def parse_nycruns(url='http://nycruns.com/races/?show=registerable'):
    inurl = urlopen(url)

    current_event = None
    event_buffer = []
    for line in urlopen(url):
        if 'class="event"' in line:
            current_event = nycruns_event()
        if not current_event:
            continue
        else:
            event_buffer.append(line.strip())

        if '</li>' in line:
            event_string = ''.join(event_buffer)
            for ch in ['div', 'a']:
                event_string = event_string.replace('<%s' % ch, '\n').replace('</%s' % ch, '').replace('>', ' ')
            for ch in ['span']:
                event_string = event_string.replace('<%s' % ch, '').replace('</%s' % ch, '').replace('>', ' ')
            event_string = event_string.replace('style=""', '').replace(' "', '"')
            yr, mn, dy, hr, me = 2015, 1, 1, 9, 0
            for l in event_string.split('\n'):
                ent = l.split()
                if len(ent) == 0:
                    continue
                if 'event-year' in ent[0]:
                    yr = int(ent[1])
                if 'event-month' in ent[0]:
                    mn = months_short.index(ent[1])+1
                if 'event-day' in ent[0]:
                    dy = int(ent[1])
                if 'event-link' in ent[0]:
                    current_event.event_url = ent[1].replace('href=', '').replace('"', '')
                if 'event-name' in ent[0]:
                    current_event.event_name = ' '.join(ent[2:]).strip()
                if 'event-location' in ent[0]:
                    current_event.event_location = ' '.join(ent[2:]).replace('|', ',')
            event_buffer2 = []
            try:
                _url = urlopen(current_event.event_url)
            except ValueError:
                print(current_event.event_url)
                continue
            if _url.getcode() != 200:
                continue
            for l in _url:
                if 'race-info' in l:
                    event_buffer2.append(l)
                if not event_buffer2:
                    continue

                event_buffer2.append(l.strip())
                if 'race-display-terms' in l:
                    break
            event_string = ''.join(event_buffer2)
            for ch in ['div', 'a', 'h2', 'script', 'strong']:
                event_string = event_string.replace('<%s' % ch, '\n').replace('</%s' % ch, '').replace('>', ' ')
            for l in event_string.split('\n'):
                ent = l.replace('time:', '').replace('Start time:', '').split()
                if len(ent)<2:
                    continue
                if 'Start time:' in l:
                    for n in range(len(ent)):
                        if ':' not in ent[n]:
                            continue
                        try:
                            hr, me = map(int, ent[n].split(':'))
                            s = ent[n+1].lower()
                        except ValueError:
                            try:
                                v, s = ent[n].lower().replace(';', ' ').replace('am', ' am').replace('pm', ' pm').split()
                                hr, me = map(int, v.split(':')[:2])
                            except ValueError:
                                continue
                        if 'pm' in s.lower() and hr != 12:
                            hr += 12
                if 'initialize(' in ent[0]:
                    lat, lon = [float(s) for s in
                                ent[0].replace("'",'').replace(
                                    'initialize(','').split(',')[:2]]
                    current_event.event_lat, current_event.event_lon = lat, lon
            current_event.event_time = datetime.datetime(year=yr, month=mn, day=dy, hour=hr, minute=me, tzinfo=tzobj)
            current_event.event_end_time = current_event.event_time + datetime.timedelta(minutes=60)
            yield current_event
            current_event = nycruns_event()
            event_buffer = []

def process_response(response, outlist):
    for item in response['items']:
        t = nycruns_event()
        t.read_gcal_event(item)
        kstr = '%s %s' % (t.event_time, t.eventId)
        outlist[kstr] = t

def simple_response(response, outlist=None):
    for item in response['items']:
        for k, it in item.items():
            print('%s: %s' % (k, it))
        print('')


if __name__ == "__main__":
    parse_events(parser_callback=parse_nycruns, script_name='parse_nycruns',
                 simple_callback=simple_response,
                 full_callback=process_response,
                 callback_class=nycruns_event)
