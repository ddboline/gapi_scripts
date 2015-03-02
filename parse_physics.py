#!/usr/bin/python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os, time
import datetime, pytz
from urllib2 import urlopen
import random
from util import dateTimeString
from gcal_instance import gcal_instance

from parse_events import base_event, parse_events,\
    months_short as months, months_long, buildings,\
    weekdays, tzobj

def datetimefromstring(tstr):
    import dateutil.parser
    return dateutil.parser.parse(tstr)


class physics_event(base_event):
    def __init__(self, dt=None, room='', title='', speaker='', talk_type=''):
        base_event.__init__(self, dt=dt)
        self.room = room
        self.talk_type = talk_type
        self.title = title
        self.speaker = speaker

    def compare(self, obj, partial_match=None):
        comp_list = []
        if self and not obj:
            return False
        if self.title.replace('"', '') == obj.title.replace('"', ''):
            comp_list.append(True)
        else:
            comp_list.append(False)
        for attr in ['event_time', 'room', 'talk_type', 'speaker']:
            if getattr(self, attr) == getattr(obj, attr):
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

    def define_new_event_object(self):
        return {'creator': {'self': True, 'displayName': 'Daniel Boline', 'email': 'ddboline@gmail.com'},
                'originalStartTime': {'dateTime': dateTimeString(self.event_time)},
                'organizer': {'self': True, 'displayName': 'Daniel Boline', 'email': 'ddboline@gmail.com'},
                'location': self.room,
                'summary': self.talk_type,
                'description': '\"%s\"\n%s\n' % (self.title, self.speaker),
                'start': {'dateTime': dateTimeString(self.event_time)},
                'end': {'dateTime': dateTimeString(self.event_time + datetime.timedelta(hours=1))},}

    def read_gcal_event(self, obj):
        if 'start' in obj:
            if 'dateTime' in obj['start']:
                tstr = obj['start']['dateTime']
                self.event_time = datetimefromstring(tstr)
        if 'description' in obj:
            self.title = obj['description'].split('\n')[0]
            self.speaker = ''.join(obj['description'].split('\n')[1:])
        if 'location' in obj:
            self.room = obj['location']
        if 'summary' in obj:
            self.talk_type = obj['summary']
        self.eventId = obj['id']

    def print_event(self):
        if not self.eventId:
            self.generate_id()
        ostr = [dateTimeString(self.event_time),
                      '\t room: %s' % self.room,
                      '\t type: %s' % self.talk_type,
                      '\t speaker: %s' % self.speaker,
                      '\t title: %s' % self.title,
                      '\t eventId: %s' % self.eventId]
        try:
            print('\n'.join(ostr))
        except UnicodeEncodeError:
            print('\n'.join(x.encode(errors='ignore') for x in ostr))

def parse_physics(url='http://physics.sunysb.edu/Physics/', is_main_page=True):
    ''' parse physics web page to get the week's events '''
    try:
        f = urlopen(url)
    except Exception:
        time.sleep(5)
        f = urlopen(url)

    current_event = None

    in_thisweek = False
    in_table = False
    in_tbody = False
    in_table_entry = False
    table_entry = []
    last_filled = None
    for line in f:
        if is_main_page:
            if '<!-- thisweek.php starts -->' in line:
                in_thisweek = True
            if '<!-- thisweek.php ends -->' in line:
                in_thisweek = False
            if not in_thisweek:
                continue

        if '<table border="2"' in line:
            in_table = True
        if '<tbody>' in line:
            in_tbody = True

        if all([in_thisweek, in_table, in_tbody]):
            out_line = []
            if line.find('<td') >= 0:
                in_table_entry = True
            if not in_table_entry:
                continue
            for c in line:
                if c == '<':
                    in_table_entry = False
                    continue
                if c == '>':
                    in_table_entry = True
                    continue
                if in_table_entry:
                    out_line.append(c)
            out_line = ''.join(out_line)
            out_line = out_line.strip().replace('&nbsp;', ' ').replace('&amp;', '&')
            if len(out_line) == 0:
                continue
            table_entry.append(out_line)

            if line.find('</td') >= 0:
                in_table_entry = False
            if '</tbody>' in line:
                in_tbody = False
            if '</table>' in line:
                in_table = False

            ents = out_line.split()
            if len(ents) == 0:
                continue
            if ents[0].replace(',', '').strip() in weekdays:
                d = datetime.datetime(year=datetime.datetime.now(tzobj).year, month=months.index(ents[1])+1, day=int(ents[2]))
                if current_event:
                    yield current_event
                    table_entry = []
                    last_filled = 'Date'
                current_event = physics_event()
            elif ents[0] == 'Time:':
                h = int(ents[1].split('/')[0].split(':')[0])
                m = int(ents[1].split('/')[0].split(':')[1])
                if ents[2] == 'a.m.' and h == 12:
                    h = 0
                if ents[2] == 'p.m.' and h != 12:
                    h += 12
                try:
                    dt = datetime.datetime(year=d.year, month=d.month, day=d.day, hour=h, minute=m, tzinfo=tzobj)
                except Exception as exc:
                    print('Exception',exc,d, h, m, ents)
                current_event.event_time = dt - tzobj.dst(d)
                last_filled = 'Time'
            elif ents[0] == 'Room:':
                current_event.room = ' '.join(ents[1:])
                last_filled = 'Room'
            elif ' '.join(ents[0:2]).replace(',', '') in buildings and last_filled == 'Room':
                current_event.room = '%s %s' % (current_event.room, ' '.join(ents))
            elif current_event.talk_type == '':
                current_event.talk_type = ' '.join(ents)
                last_filled = 'Type'
            elif ents[0].find('"') >= 0 or ents[0].find('\xe2') >= 0:
                if len(current_event.title) == 0:
                    current_event.title = ' '.join(ents).replace('"', '').replace('\xe2', '')
                else:
                    current_event.title = ' '.join([current_event.title, ' '.join(ents).replace('"', '').replace('\xe2', '')])
                last_filled = 'Title'
            elif ents[0] == 'TBA':
                current_event.title = ents[0]
                last_filled = 'Title'
            elif ents[0] == 'Coffee':
                continue
            elif current_event.speaker == '':
                st = ' '.join(ents)
                if out_line.find('"') > 0:
                    current_event.speaker = st.split('"')[0]
                    current_event.title = st.split('"')[1]
                elif out_line.find('\xe2') > 0:
                    current_event.speaker = st.split('\xe2')[0]
                    current_event.title = st.split('\xe2')[1]
                else:
                    current_event.speaker = st
                last_filled = 'Title'
            elif last_filled == 'Title':
                current_event.title = ' '.join([current_event.title, out_line])
            else:
                print(out_line)
                continue

    yield current_event


if __name__ == "__main__":
    parse_events(parser_callback=parse_physics, script_name='parse_physics',
                 calid='1enjsutpgucsid46mde8ffdtf4@group.calendar.google.com',
                 callback_class=physics_event)
