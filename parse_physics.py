#!/usr/bin/python
from __future__ import print_function

import os, time
import datetime, pytz
from urllib2 import urlopen
import random
from util import dateTimeString
from gcal_instance import gcal_instance

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
buildings = ['Math Tower', 'Harriman Hall', 'Grad. Physics', 'ESS']

tzobj = pytz.timezone("US/Eastern")

def datetimefromstring(tstr):
    import dateutil.parser
    return dateutil.parser.parse(tstr)

class physics_event(object):
    def __init__(self, dt=datetime.datetime.now(tzobj), room='', title='', speaker='', talk_type=''):
        self.event_time = dt
        self.room = room
        self.talk_type = talk_type
        self.title = title
        self.speaker = speaker
        self.eventId = None

    def compare(self, obj):
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
            return False

    def generate_id(self):
        import hashlib
        id_list = []
        for k in sorted(self.__dict__.keys()):
            if k == 'eventId':
                continue
            id_list.append('%s%s' % (k, self.__dict__[k]))
        id_str = ''.join(id_list)
        m = hashlib.md5()
        m.update(id_str)
        self.eventId = m.hexdigest()
        return self.eventId

    def define_new_event_object(self):
        return {'creator': {'self': True, 'displayName': 'Daniel Boline', 'email': 'ddboline@gmail.com'},
                'originalStartTime': {'dateTime': dateTimeString(self.event_time)},
                'organizer': {'self': True, 'displayName': 'Daniel Boline', 'email': 'ddboline@gmail.com'},
                'location': self.room,
                'summary': self.talk_type,
                'description': '\"%s\"\n%s\n' % (self.title, self.speaker),
                'start': {'dateTime': dateTimeString(self.event_time)},
                'end': {'dateTime': dateTimeString(self.event_time + datetime.timedelta(hours=1))},
  }

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
        print('\n'.join(ostr))

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
                d = datetime.datetime(year=2014, month=months.index(ents[1])+1, day=int(ents[2]))
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

    #for ev in list_of_events:
    #    ev.print_event()

    #return list_of_events

def process_response(response, outlist):
    for item in response['items']:
        t = physics_event()
        t.read_gcal_event(item)
        kstr = '%s %s' % (t.event_time, t.eventId)
        outlist[kstr] = t

def simple_response(response, outlist=None):
    for item in response['items']:
        for k, it in item.items():
            print('%s: %s' % (k, it))
        print('')

if __name__ == "__main__":
    calid = '1enjsutpgucsid46mde8ffdtf4@group.calendar.google.com'

    commands = ['h', 'list', 'new', 'post', 'cal', 'pcal', 'listcal', 'rm', 'week']

    _command = ''
    _arg = calid
    l = []

    for arg in os.sys.argv:
        if arg.split('=')[0] in commands:
            _command = arg.split('=')[0]
        else:
            arg = 'h'
        if '=' in arg:
            _arg = arg.split('=')[1]

    _args = []
    for arg in os.sys.argv[1:]:
        if arg in commands:
            continue
        _args.append(arg)

    if _command == 'h':
        print('./parse_physics.py <%s>' % '|'.join(commands))
        exit(0)

    if _command == 'list':
        for l in parse_physics():
            if not l:
                continue
            if 'all' in _args:
                l.print_event()
            elif l.event_time >= datetime.datetime.now(tzobj):
                l.print_event()
    if _command == 'new':
        c = gcal_instance()
        exist = c.get_gcal_events(calid=_arg, callback_fn=process_response)
        for l in parse_physics():
            if not l:
                continue
            if not any([e.compare(l) for e in exist.values()]):
                if l.event_time >= datetime.datetime.now(tzobj):
                    l.print_event()
    if _command == 'post':
        c = gcal_instance()
        exist = c.get_gcal_events(calid=_arg, callback_fn=process_response)
        for l in parse_physics():
            if not any([e.compare(l) for e in exist.values()]):
                c.add_to_gcal(ev_entry=l, calid=_arg)
    if _command == 'cal':
        c = gcal_instance()
        c.get_gcal_events(calid=_arg, callback_fn=simple_response)
    if _command == 'week':
        exist = gcal_instance().get_gcal_events(calid=_arg, callback_fn=process_response)
        for k in sorted(exist.keys()):
            e = exist[k]
            if e.event_time < datetime.datetime.now(tzobj) or e.event_time > datetime.datetime.now(tzobj) + datetime.timedelta(days=7):
                continue
            e.print_event()
    if _command == 'pcal':
        c = gcal_instance()
        exist = c.get_gcal_events(calid=_arg, callback_fn=process_response)
        for k in sorted(exist.keys()):
            e = exist[k]
            if e.event_time >= datetime.datetime.now(tzobj):
                e.print_event()
            elif 'past' in _args:
                e.print_event()
        print('\nNEW FROM WEB\n')
        for l in parse_physics():
            if not l:
                continue
            if not any([e.compare(l) for e in exist.values()]):
                if l.event_time >= datetime.datetime.now(tzobj):
                    l.print_event()
    if _command == 'listcal':
        c = gcal_instance()
        c.list_gcal_calendars()
    if _command == 'rm':
        c = gcal_instance()
        for arg in _args:
            c.delete_from_gcal(calid=_arg, evid=arg)
