#!/usr/bin/python
""" Parse Glirc Webpage Calendar """
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
from util import openurl
from parse_events import BaseEvent, parse_events, MONTHS_LONG, TZOBJ
from requests import HTTPError

def parse_glirc(url='http://glirc.org/events.php?limit=100'):
    """ parsing function """
    url_ = openurl(url)

    current_ev = None

    get_next_line_0 = False
    get_next_line_1 = False
    for line in url_:
        if get_next_line_1:
            current_ev.event_desc = line.replace('<p>', '')\
                                        .replace('</p>', '').strip()
            get_next_line_1 = False
        if get_next_line_0:
            for ents in line.replace('<', '><').replace('>', '><').split('><'):
                if 'href' in ents and len(current_ev.event_url) == 0:
                    for ent in ents.split():
                        if 'href' in ent:
                            if 'http' not in ent:
                                current_ev.event_url = \
                                    'http://glirc.org/%s' % \
                                    ent.split('href=')[1].replace('"', '')
                            else:
                                current_ev.event_url = ent.split('href=')[1]\
                                                          .replace('"', '')
                elif len(ents.split()) > 0 and ents.split()[0]in MONTHS_LONG:
                    dstr = ents.replace('|', '').strip()
                    month = MONTHS_LONG.index(dstr.split()[0]) + 1
                    try:
                        day = int(dstr.split()[1].replace(',', ''))
                    except ValueError:
                        current_ev.event_name = dstr
                        continue
                    year = int(dstr.split()[2])
                    begin_time_str = ''
                    end_time_str = ''
                    if 'glirc.org' in current_ev.event_url:
                        try:
                            for line in openurl(current_ev.event_url):
                                if 'Time:' in line:
                                    for k in line.replace('<', '\n')\
                                                 .replace('>', '\n')\
                                                 .replace('-', '\n')\
                                                 .split('\n'):
                                        if 'AM' in k or 'PM' in k:
                                            if len(begin_time_str) == 0:
                                                begin_time_str = k.strip()
                                            elif len(end_time_str) == 0:
                                                end_time_str = k.strip()
                                elif 'Location:' in line:
                                    current_ev.event_location = \
                                        line.split('<span>')[1]\
                                            .split('</span>')[0]
                                elif 'var point' in line:
                                    try:
                                        lat, lng = [float(x) for x in
                                                    line.split('(')[1]\
                                                        .split(')')[0]\
                                                        .split(',')[:2]]
                                        current_ev.event_lat = lat
                                        current_ev.event_lon = lng
                                    except ValueError:
                                        pass
                        except HTTPError as exc:
                            print('%s failed %s' % (current_ev.event_url, exc))
                    dt_ = datetime.datetime(year=year, month=month, day=day,
                                           hour=9, minute=0, tzinfo=TZOBJ)
                    if len(begin_time_str) > 0:
                        bhr = int(begin_time_str[0:2])
                        bmn = int(begin_time_str[3:5])
                        if 'AM' in begin_time_str and bhr == 12:
                            bhr = 0
                        if 'PM' in begin_time_str and bhr != 12:
                            bhr += 12
                        dt_ = datetime.datetime(year=year, month=month,
                                                day=day, hour=bhr, minute=bmn,
                                                tzinfo=TZOBJ)
                    if len(end_time_str) > 0:
                        try:
                            ehr = int(end_time_str[0:2])
                            emn = int(end_time_str[3:5])
                            if 'AM' in end_time_str and ehr == 12:
                                ehr = 0
                            if 'PM' in end_time_str and ehr != 12:
                                ehr += 12
                            et_ = datetime.datetime(year=year, month=month,
                                                    day=day, hour=ehr,
                                                    minute=emn, tzinfo=TZOBJ)
                            if et_ <= dt_:
                                et_ = dt_ + datetime.timedelta(minutes=60)
                        except ValueError:
                            print('ValueError: %s' % end_time_str)
                    else:
                        et_ = dt_ + datetime.timedelta(minutes=60)
                    d__ = datetime.datetime(year=year, month=month, day=day)
                    dt_ -= TZOBJ.dst(d__)
                    et_ -= TZOBJ.dst(d__)
                    current_ev.event_time = dt_
                    current_ev.event_end_time = et_
                elif '<' not in ents and '>' not in ents and \
                        len(ents.strip()) > 0:
                    if len(current_ev.event_name) == 0:
                        current_ev.event_name = ents.strip()

            get_next_line_0 = False
            get_next_line_1 = True
        if 'e-listing-info' in line:
            if current_ev:
                yield current_ev
            current_ev = BaseEvent()

            #list_of_events.append(GlircEvent())
            get_next_line_0 = True
    yield current_ev


if __name__ == "__main__":
    parse_events(parser_callback=parse_glirc, script_name='parse_glirc',
                 callback_class=BaseEvent)
