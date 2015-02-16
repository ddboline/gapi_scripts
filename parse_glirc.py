#!/usr/bin/python
from __future__ import print_function

import os
import datetime, pytz
from urllib2 import urlopen
import random
from gcal_instance import gcal_instance

from parse_events import base_event, parse_events,\
    months_short, months_long,\
    weekdays, tzobj


class glirc_event(base_event):
    def __init__(self, dt=None, ev_name='', ev_url='', ev_desc='', ev_loc=''):
        base_event.__init__(self, dt=dt, ev_name=ev_name, ev_url=ev_url, ev_desc=ev_desc, ev_loc=ev_loc)

def parse_glirc(url='http://glirc.org/events.php?limit=100'):
    f = urlopen(url)

    current_event = None

    current_year = datetime.date.today().year
    get_next_line_0 = False
    get_next_line_1 = False
    for line in f:
        if get_next_line_1:
            current_event.event_desc = line.replace('<p>', '').replace('</p>', '').strip()
            get_next_line_1 = False
        if get_next_line_0:
            for ent in line.replace('<', '><').replace('>', '><').split('><'):
                if 'href' in ent and len(current_event.event_url) == 0:
                    for e in ent.split():
                        if 'href' in e:
                            if 'http' not in e:
                                current_event.event_url = 'http://glirc.org/%s' % e.split('href=')[1].replace('"', '')
                            else:
                                current_event.event_url = e.split('href=')[1].replace('"', '')
                elif len(ent.split()) > 0 and ent.split()[0]in months_long:
                    dstr = ent.replace('|', '').strip()
                    month = months_long.index(dstr.split()[0]) + 1
                    try:
                        day = int(dstr.split()[1].replace(',', ''))
                    except ValueError:
                        current_event.event_name = dstr
                        continue
                    year = int(dstr.split()[2])
                    hour = 9
                    minute = 0
                    duration = 60
                    begin_time_str = ''
                    end_time_str = ''
                    if 'glirc.org' in current_event.event_url:
                        try:
                            for l in urlopen(current_event.event_url):
                                if 'Time:' in l:
                                    for k in l.replace('<', '\n').replace('>', '\n').replace('-', '\n').split('\n'):
                                        if 'AM' in k or 'PM' in k:
                                            if len(begin_time_str) == 0:
                                                begin_time_str = k.strip()
                                            elif len(end_time_str) == 0:
                                                end_time_str = k.strip()
                                elif 'Location:' in l:
                                    current_event.event_location = l.split('<span>')[1].split('</span>')[0]
                                elif 'var point' in l:
                                    try:
                                        lat, lng = [float(x) for x in
                                                    l.split('(')[1].split(')')[0].split(',')[:2]]
                                        current_event.event_lat = lat
                                        current_event.event_lon = lng
                                    except ValueError:
                                        pass
                        except Exception as htexc:
                            print('bad url %s' % current_event.event_url)
                            pass
                            #print("Exception:", htexc, current_event.event_url, current_event.print_event())
                    dt = datetime.datetime(year=year, month=month, day=day, hour=9, minute=0, tzinfo=tzobj)
                    if len(begin_time_str) > 0:
                        bhr = int(begin_time_str[0:2])
                        bmn = int(begin_time_str[3:5])
                        if 'AM' in begin_time_str and bhr == 12:
                            bhr = 0
                        if 'PM' in begin_time_str and bhr != 12:
                            bhr += 12
                        dt = datetime.datetime(year=year, month=month, day=day, hour=bhr, minute=bmn, tzinfo=tzobj)
                    if len(end_time_str) > 0:
                        try:
                            ehr = int(end_time_str[0:2])
                            emn = int(end_time_str[3:5])
                            if 'AM' in end_time_str and ehr == 12:
                                ehr = 0
                            if 'PM' in end_time_str and ehr != 12:
                                ehr += 12
                            et = datetime.datetime(year=year, month=month, day=day, hour=ehr, minute=emn, tzinfo=tzobj)
                            if et <= dt:
                                et = dt + datetime.timedelta(minutes=60)
                        except ValueError:
                            print('ValueError: %s' % end_time_str)
                    else:
                        et = dt + datetime.timedelta(minutes=60)

                    d = datetime.datetime(year=year, month=month, day=day)
                    dt -= tzobj.dst(d)
                    et -= tzobj.dst(d)

                    current_event.event_time = dt
                    current_event.event_end_time = et

                elif '<' not in ent and '>' not in ent and len(ent.strip()) > 0:
                    if len(current_event.event_name) == 0:
                        current_event.event_name = ent.strip()

            get_next_line_0 = False
            get_next_line_1 = True
        if 'e-listing-info' in line:
            if current_event:
                yield current_event
            current_event = glirc_event()

            #list_of_events.append(glirc_event())
            get_next_line_0 = True
    yield current_event


if __name__ == "__main__":
    parse_events(parser_callback=parse_glirc, script_name='parse_glirc',
                 callback_class=glirc_event)
