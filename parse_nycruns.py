#!/usr/bin/python
""" Parse NYCRuns Webpage Calendar """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime
import requests
from bs4 import BeautifulSoup
from parse_events import (BaseEvent, parse_events, MONTHS_SHORT, TZOBJ,
                          strip_out_unicode_crap)
try:
    requests.packages.urllib3.disable_warnings()
except AttributeError:
    pass
CALID = 'ufdpqtvophgg2qn643rducu1a4@group.calendar.google.com'


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


def parse_event_tag(li_tag):
    current_event = NycRunsEvent()
    yr_, mn_, dy_, hr_, me_ = 2015, 1, 1, 9, 0
    for div in li_tag.find_all('div'):
        if 'event-year' in div.attrs.get('class', []):
            yr_ = int(div.text)
        elif 'event-month' in div.attrs.get('class', []):
            ent = div.text.strip()
            if ent in MONTHS_SHORT:
                mn_ = MONTHS_SHORT.index(ent)+1
        elif 'event-day' in div.attrs.get('class', []):
            dy_ = int(div.text)
        elif 'event-name' in div.attrs.get('class', []):
            current_event.event_name = div.text
        elif 'event-location' in div.attrs.get('class', []):
            current_event.event_location = div.text

    for a in li_tag.find_all('a'):
        if 'event-link' in a.attrs.get('class', []):
            current_event.event_url = a.attrs.get('href')

    url = current_event.event_url
    if 'nycruns.com' not in url:
        url = '%s%s' % ('https://nycruns.com', url)
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    for div in soup.find_all('div'):
        if 'race-display-date' in div.attrs.get('class', []):
            clean_text = '%s' % div
            clean_text = clean_text.replace('>', '>\n')
            clean_text = BeautifulSoup(clean_text, 'html.parser').text
            clean_text = clean_text.split('Start time:')
            if len(clean_text) < 2:
                continue
            clean_text = clean_text[1].strip()
            clean_text = clean_text.lower()
            clean_text = clean_text.replace('am', ' am').replace('pm', ' pm')
            ent = clean_text.split('\n')[0].split()
            for num in range(len(ent)-1):
                try:
                    hr_, me_ = [int(x) for x in ent[num].split(':')[:2]]
                except:
                    continue
                if 'pm' in ent[num+1]:
                    hr_ += 12

    for script in soup.find_all('script'):
        if 'initialize' in script.text:
            clean_text = script.text.replace("'", "")
            clean_text = clean_text.replace('initialize(', '').replace(')', '')
            try:
                lat, lon = [float(x) for x in clean_text.split(',')[:2]]
                current_event.event_lat, current_event.event_lon = lat, lon
            except ValueError:
                pass

    current_event.event_time = datetime.datetime(year=yr_, month=mn_, day=dy_,
                                                 hour=hr_, minute=me_)
    current_event.event_time = TZOBJ.localize(current_event.event_time)
    current_event.event_end_time = (current_event.event_time +
                                    datetime.timedelta(minutes=60))
    return current_event


def parse_nycruns(url='http://nycruns.com/races/?show=registerable'):
    """ parsing function """
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')

    for li in soup.find_all('li'):
        if 'event' in li.attrs.get('class', []) \
                and 'event-training' not in li.attrs.get('class', []):
            yield parse_event_tag(li)


if __name__ == "__main__":
    parse_events(parser_callback=parse_nycruns, script_name='parse_nycruns',
                 callback_class=NycRunsEvent, calid=CALID)
