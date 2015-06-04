#!/usr/bin/python
""" Parse NYCRuns Webpage Calendar """
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
from util import openurl
from parse_events import BaseEvent, parse_events, MONTHS_SHORT, TZOBJ,\
                         strip_out_unicode_crap


class NycRunsEvent(BaseEvent):
    """ NYC Runs Event Class """
    def __init__(self, dt=None, ev_name='', ev_url='', ev_desc='', ev_loc=''):
        BaseEvent.__init__(self, dt=dt, ev_name=ev_name, ev_url=ev_url,
                           ev_desc=ev_desc, ev_loc=ev_loc)

    def compare(self, obj, partial_match=None):
        comp_list = []
        attr_list = ('event_time', 'event_end_time', 'event_url',
                     'event_location', 'event_name')
        out_list = []
        for attr in attr_list:
            c0_ = getattr(self, attr)
            c1_ = getattr(obj, attr)
            out_list.append([c0_, c1_])
            if type(c0_) == str or type(c0_) == unicode:
                c0_ = strip_out_unicode_crap(c0_)
            if type(c1_) == str or type(c1_) == unicode:
                c1_ = strip_out_unicode_crap(c1_)
            if type(c0_) == str:
                c0_ = c0_.replace('  ', ' ').strip()
            if type(c1_) == str:
                c1_ = c1_.replace('  ', ' ').strip()
            if c0_ == c1_:
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
    """ parsing function """
    current_event = None
    event_buffer = []

    url_ = openurl(url)

    for line in url_:
        if 'class="event"' in line:
            current_event = NycRunsEvent()
        if not current_event:
            continue
        else:
            event_buffer.append(line.strip())

        if '</li>' in line:
            event_string = ''.join(event_buffer)
            for ch_ in ['div', 'a']:
                event_string = event_string.replace('<%s' % ch_, '\n')\
                                           .replace('</%s' % ch_, '')\
                                           .replace('>', ' ')
            for ch_ in ['span']:
                event_string = event_string.replace('<%s' % ch_, '')\
                                           .replace('</%s' % ch_, '')\
                                           .replace('>', ' ')
            event_string = event_string.replace('style=""', '')\
                                       .replace(' "', '"')
            yr_, mn_, dy_, hr_, me_ = 2015, 1, 1, 9, 0
            for line in event_string.split('\n'):
                ent = line.split()
                if len(ent) == 0:
                    continue
                if 'event-year' in ent[0]:
                    yr_ = int(ent[1])
                if 'event-month' in ent[0]:
                    mn_ = MONTHS_SHORT.index(ent[1])+1
                if 'event-day' in ent[0]:
                    dy_ = int(ent[1])
                if 'event-link' in ent[0]:
                    current_event.event_url = ent[1].replace('href=', '')\
                                                    .replace('"', '')
                if 'event-name' in ent[0]:
                    current_event.event_name = ' '.join(ent[2:]).strip()
                if 'event-location' in ent[0]:
                    current_event.event_location = ' '.join(ent[2:])\
                                                      .replace('|', ',')
            event_buffer2 = []

            if not current_event.event_url:
                continue
            url2_ = openurl(current_event.event_url)

            for line in url2_:
                if 'race-info' in line:
                    event_buffer2.append(line)
                if not event_buffer2:
                    continue

                event_buffer2.append(line.strip())
                if 'race-display-terms' in line:
                    break
            event_string = ''.join(event_buffer2)
            for ch_ in ['div', 'a', 'h2', 'script', 'strong']:
                event_string = event_string.replace('<%s' % ch_, '\n')\
                                           .replace('</%s' % ch_, '')\
                                           .replace('>', ' ')
            for line in event_string.split('\n'):
                ent = line.replace('time:', '').replace('Start time:', '')\
                          .split()
                if len(ent) < 2:
                    continue
                if 'Start time:' in line:
                    for num in range(len(ent)):
                        if ':' not in ent[num]:
                            continue
                        try:
                            hr_, me_ = [int(x) for x in ent[num].split(':')]
                            st_ = ent[num+1].lower()
                        except ValueError:
                            try:
                                val, st_ = ent[num].lower().replace(';', ' ')\
                                                   .replace('am', ' am')\
                                                   .replace('pm', ' pm')\
                                                   .split()
                                hr_, me_ = [int(x) for x in val.split(':')[:2]]
                            except ValueError:
                                continue
                        if 'pm' in st_.lower() and hr_ != 12:
                            hr_ += 12
                if 'initialize(' in ent[0]:
                    lat, lon = [float(x) for x in
                                ent[0].replace("'", '').replace(
                                    'initialize(', '').split(',')[:2]]
                    current_event.event_lat, current_event.event_lon = lat, lon
            current_event.event_time = datetime.datetime(year=yr_, month=mn_,
                                                         day=dy_, hour=hr_,
                                                         minute=me_,
                                                         tzinfo=TZOBJ)
            current_event.event_end_time = current_event.event_time + \
                                           datetime.timedelta(minutes=60)
            yield current_event
            current_event = NycRunsEvent()
            event_buffer = []


if __name__ == "__main__":
    parse_events(parser_callback=parse_nycruns, script_name='parse_nycruns',
                 callback_class=NycRunsEvent)
