#!/usr/bin/python
from __future__ import print_function

import os
import datetime, pytz
from urllib2 import urlopen
import random
from util import dateTimeString, datetimefromstring
from gcal_instance import gcal_instance

months_short = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
months_long = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
buildings = ['Math Tower', 'Harriman Hall', 'Grad. Physics', 'ESS']

tzobj = pytz.timezone("US/Eastern")

def strip_out_unicode_crap(inpstr):
    import re
    return re.sub(r'[^\x00-\x7F]','', inpstr)
    # return str(''.join(x for x in inpstr if ord(x) <= 0x7f))

class nycruns_event(object):
    def __init__(self, dt=None, ev_name='', ev_url='', ev_desc='', ev_loc=''):
        self.event_time = dt
        self.event_end_time = dt
        self.event_url = ev_url
        self.event_name = ev_name
        self.event_desc = ev_desc
        self.event_location = ev_loc
        self.event_lat = None
        self.event_lon = None
        self.eventId = None

    def compare(self, obj, partial_match=None):
        comp_list = []
        attr_list = ['event_time', 'event_end_time', 'event_url', 'event_desc', 'event_location', 'event_name']
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
        if type(self.event_lat) == float and type(self.event_lon) == float:
            loc_str = '%f,%f' % (self.event_lat, self.event_lon)
        else:
            loc_str = self.event_location
        return {'creator': {'self': True, 'displayName': 'Daniel Boline', 'email': 'ddboline@gmail.com'},
                'originalStartTime': {'dateTime': dateTimeString(self.event_time)},
                'organizer': {'self': True, 'displayName': 'Daniel Boline', 'email': 'ddboline@gmail.com'},
                'location': loc_str,
                'summary': self.event_name,
                'description': 'Location: %s\nDescription: %s\n%s' % (self.event_location, self.event_desc, self.event_url),
                'start': {'dateTime': dateTimeString(self.event_time)},
                'end': {'dateTime': dateTimeString(self.event_end_time)},
  }

    def read_gcal_event(self, obj):
        if 'dateTime' in obj['start']:
            tstr = obj['start']['dateTime']
            self.event_time = datetimefromstring(tstr)
            tstr = obj['end']['dateTime']
            self.event_end_time = datetimefromstring(tstr)
        elif 'date' in obj['start']:
            tstr = obj['start']['date']
            t = map(int, [tstr[0:4], tstr[5:7], tstr[8:10]])
            self.event_time = datetime.datetime(year=t[0], month=t[1], day=t[2], hour=9, minute=0, tzinfo=tzobj)
            self.event_end_time = self.event_time + datetime.timedelta(minutes=60)
        else:
            print(obj)
            exit(0)
        self.event_name = obj['summary']
        if 'description' in obj:
            for ent in obj['description'].split('\n'):
                if 'http' in ent:
                    self.event_url = ent
                elif 'Location:' in ent:
                    self.event_location = ' '.join(ent.split()[1:])
                elif 'Description:' in ent:
                    self.event_desc = ' '.join(ent.split()[1:])
        if 'location' in obj:
            try:
                self.event_lat, self.event_lon = [float(x) for x in
                                                  obj['location'].split(',')[:2]]
            except ValueError:
                print('bad location')
                pass
        self.eventId = obj['id']

    def print_event(self):
        ostr = [
                '%s %s' % (dateTimeString(self.event_time), dateTimeString(self.event_end_time)),
                '\t url: %s' % self.event_url,
                '\t name: %s' % strip_out_unicode_crap(self.event_name),
                '\t description: %s' % self.event_desc,
                '\t location: %s' %  self.event_location]
        if type(self.event_lat) == float and type(self.event_lon) == float:
            ostr[-1] += ' %f,%f' % (self.event_lat, self.event_lon)
        if not self.eventId:
            self.generate_id()
        ostr.append('\t eventId: %s' % self.eventId)
        print('\n'.join(ostr))

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
                    current_event.event_name = ' '.join(ent[2:])
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
    calid = 'ufdpqtvophgg2qn643rducu1a4@group.calendar.google.com'

    commands = ['h', 'list', 'new', 'post', 'cal', 'pcal', 'listcal', 'rm', 'search', 'week']

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
        print('./parse_nycruns.py <%s>' % '|'.join(commands))
        exit(0)

    if _command == 'list':
        for l in parse_nycruns():
            if l.event_time >= datetime.datetime.now(tzobj):
                l.print_event()
    if _command == 'new':
        new_events = []
        exist = gcal_instance().get_gcal_events(calid=_arg, callback_fn=process_response)
        for l in parse_nycruns():
            if _args and l.generate_id() not in _args:
                continue
            if not any([e.compare(l) for e in exist.values()]):
                for e in exist.values():
                    if e.compare(l, 3):
                        e.print_event()
                l.print_event()
                new_events.append(l)
        if new_events:
            with gzip.open('.tmp_nycruns.pkl.gz', 'wb') as pkl_file:
                pickle.dump(new_events, pkl_file, pickle.HIGHEST_PROTOCOL)
    if _command == 'post':
        new_events = []
        c = gcal_instance()
        try:
            with gzip.open('.tmp_nycruns.pkl.gz', 'rb') as pkl_file:
                new_events = pickle.load(pkl_file)
            os.remove('.tmp_nycruns.pkl.gz')
        except:
            print('no pickle file')
            exist = c.get_gcal_events(calid=_arg, callback_fn=process_response)
            for l in parse_nycruns():
                if _args and l.generate_id() not in _args:
                    continue
                if not any([e.compare(l) for e in exist.values()]):
                    l.print_event()
                    new_events.append(l)
        for l in new_events:
            c.add_to_gcal(ev_entry=l, calid=_arg)
    if _command == 'cal':
        gcal_instance().get_gcal_events(calid=_arg, callback_fn=simple_response)
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
        nycruns_events = []
        print('\nNEW FROM WEB\n')
        for l in parse_nycruns():
            nycruns_events.append(l)
            if not any([e.compare(l) for e in exist.values()]):
                if l.event_time >= datetime.datetime.now(tzobj):
                    l.print_event()
    if _command == 'listcal':
        gcal_instance().list_gcal_calendars()
    if _command == 'rm':
        c = gcal_instance()
        for arg in _args:
            c.delete_from_gcal(calid=_arg, evid=arg)
    if _command == 'search':
        current_event = nycruns_event()
        if _args[0] not in [k.replace('event_', '').replace('event', '') for k in current_event.__dict__.keys()]:
            print(_args)
            exit(0)
        if len(_args) < 2:
            print(_args)
            exit(0)
        exist = gcal_instance().get_gcal_events(calid=_arg, callback_fn=process_response)

        def search_event(e):
            k = 'event_%s' % _args[0]
            v0 = _args[1]
            if k == 'event_time' or k == 'event_end_time':
                import dateutil.parser
                v0 = dateutil.parser.parse(v0)
            v = None
            if k in e.__dict__:
                v = getattr(e, k)
                if not v:
                    return
            else:
                k = 'event%s' % _args[0]
                if k in e.__dict__:
                    v = getattr(e, k)
                    if not v:
                        return
            if type(v0) != datetime.datetime:
                if v0 not in v:
                    return
            else:
                if v < v0:
                    return
            e.print_event()

        print('gcal events')
        for k in sorted(exist.keys()):
            search_event(exist[k])
        #print('\nnew events')
        #for l in parse_nycruns():
            #if not any([e.compare(l) for e in exist.values()]):
                #search_event(l)
