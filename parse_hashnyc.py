#!/usr/bin/python3
""" Parse HashNYC Webpage Calendar """
from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from parse_events import BaseEvent, parse_events, TZOBJ, strip_out_unicode_crap
try:
    requests.packages.urllib3.disable_warnings()
except AttributeError:
    pass

CALID = '8hfjg0d8ls2od3s9bd1k1v9jtc@group.calendar.google.com'


class HashNYCEvents(BaseEvent):
    """ NYC Hash Event Class """

    def __init__(self, dt=None, ev_name='', ev_url='', ev_desc='', ev_loc=''):
        ev_url = 'http://hashnyc.com/?days=all'
        BaseEvent.__init__(
            self, dt=dt, ev_name=ev_name, ev_url=ev_url, ev_desc=ev_desc, ev_loc=ev_loc)

    def compare(self, obj, partial_match=None):
        comp_list = []
        attr_list = ('event_time', 'event_end_time', 'event_url', 'event_location', 'event_name')
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


def parse_hashnyc(url='http://hashnyc.com/?days=all'):
    """ parsing function """
    current_event = None

    resp = requests.get(url)

    soup = BeautifulSoup(resp.text, 'html.parser')

    for table in soup.find_all('table'):
        if 'future_hashes' in table.attrs['class']:
            for td in table.find_all('td'):
                if 'deeplink_container' in td.attrs.get('class', {}):
                    clean_text = '%s' % td
                    clean_text = clean_text.replace('<br>', ' ').replace('<br/>', ' ')
                    current_event = HashNYCEvents()
                    current_event.event_time = parse(BeautifulSoup(clean_text, 'html.parser').text)
                    current_event.event_time = TZOBJ.localize(current_event.event_time)
                    current_event.event_end_time = (
                        current_event.event_time + datetime.timedelta(minutes=60))
                else:
                    for b in td.find_all('b'):
                        current_event.event_name = b.text
                    clean_text = '%s' % td
                    clean_text = clean_text.replace('<br>', '\n').replace('<td>', '\n')
                    clean_text = BeautifulSoup(clean_text, 'html.parser').text
                    for line in clean_text.split('\n'):
                        if not current_event.event_name:
                            current_event.event_name = line
                        if 'Start:' in line:
                            current_event.event_location = \
                                line.replace('Start:', '').replace('.',
                                                                   ',').strip()
                            current_event.event_location += ' New York, NY'
                    current_event.event_desc = clean_text
                    if 'Hares Needed' not in current_event.event_name:
                        yield current_event


if __name__ == "__main__":
    parse_events(
        parser_callback=parse_hashnyc,
        script_name='parse_hashnyc',
        callback_class=HashNYCEvents,
        calid=CALID,
        replace=True)
