#!/usr/bin/python
from __future__ import print_function

import os
import datetime, pytz
from urllib2 import urlopen
import random
from util import dateTimeString, datetimefromstring
from gcal_instance import gcal_instance

import gzip
try:
    import cPickle as pickle
except ImportError:
    import pickle

months_short = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
months_long = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
buildings = ['Math Tower', 'Harriman Hall', 'Grad. Physics', 'ESS']

tzobj = pytz.timezone("US/Eastern")

def strip_out_unicode_crap(inpstr):
    import re
    return re.sub(r'[^\x00-\x7F]','', inpstr)

class base_event(object):
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
                'end': {'dateTime': dateTimeString(self.event_end_time)},}

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
        ostr = ['%s %s' % (dateTimeString(self.event_time), dateTimeString(self.event_end_time)),
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


def parse_events(parser_callback=None, script_name='', calid=None, callback_class=None):
    
    def process_response(response, outlist):
        for item in response['items']:
            t = callback_class()
            t.read_gcal_event(item)
            kstr = '%s %s' % (t.event_time, t.eventId)
            outlist[kstr] = t

    def simple_response(response, outlist=None):
        for item in response['items']:
            for k, it in item.items():
                print('%s: %s' % (k, it))
            print('')
    
    if not parser_callback:
        return
    if not callback_class:
        callback_class = base_event
    
    if not calid:
        calid = 'ufdpqtvophgg2qn643rducu1a4@group.calendar.google.com'
    commands = ['h', 'list', 'new', 'post', 'cal', 'pcal', 'listcal', 'rm', 'search', 'week', 'dupe']

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
        print('./%s <%s>' % (script_name, '|'.join(commands)))
        exit(0)

    if _command == 'list':
        for l in parser_callback():
            if l.event_time >= datetime.datetime.now(tzobj):
                l.print_event()
    if _command == 'new':
        new_events = []
        new_events_dict = {}
        existing_events = {}
        exist = gcal_instance().get_gcal_events(calid=_arg, callback_fn=process_response)
        for e in exist.values():
            ev_key = '%s_%s' % (e.event_time.strftime('%Y-%m-%d'), e.event_name)
            existing_events[ev_key] = True
        for l in parser_callback():
            if _args and l.generate_id() not in _args:
                continue
            ev_key = '%s_%s' % (l.event_time.strftime('%Y-%m-%d'), l.event_name)
            if ev_key not in existing_events:
                if ev_key not in new_events_dict:
                    l.print_event()
                    new_events.append(l)
                    new_events_dict[ev_key] = l
        if new_events:
            with gzip.open('.tmp_%s.pkl.gz' % script_name, 'wb') as pkl_file:
                pickle.dump(new_events, pkl_file, pickle.HIGHEST_PROTOCOL)
    if _command == 'post':
        new_events = []
        c = gcal_instance()
        try:
            with gzip.open('.tmp_%s.pkl.gz' % script_name, 'rb') as pkl_file:
                new_events = pickle.load(pkl_file)
            os.remove('.tmp_%s.pkl.gz' % script_name)
        except:
            print('no pickle file')
            exist = c.get_gcal_events(calid=_arg, callback_fn=process_response)
            for l in parser_callback():
                if _args and l.generate_id() not in _args:
                    continue
                if not any([e.compare(l) for e in exist.values()]):
                    l.print_event()
                    new_events.append(l)
        for l in new_events:
            c.add_to_gcal(ev_entry=l, calid=_arg)
    if _command == 'dupe':
        keep_dict = {}
        remove_dict = {}
        c = gcal_instance()
        exist = c.get_gcal_events(calid=_arg, callback_fn=process_response)
        for k in sorted(exist.keys()):
            e = exist[k]
            ev_key = '%s_%s' % (e.event_time.strftime('%Y-%m-%d'), e.event_name)
            if ev_key not in keep_dict:
                keep_dict[ev_key] = e
            else:
                print(ev_key)
                e.print_event()
                remove_dict[ev_key] = e
        print('number %d %d' % (len(keep_dict), len(remove_dict)))
        for k in remove_dict:
            e = remove_dict[k]
            c.delete_from_gcal(calid=_arg, evid=e.eventId)
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
        print(len(exist.keys()))
        for k in sorted(exist.keys()):
            e = exist[k]
            if e.event_time >= datetime.datetime.now(tzobj):
                e.print_event()
            elif 'past' in _args:
                e.print_event()
        base_events = []
    if _command == 'listcal':
        gcal_instance().list_gcal_calendars()
    if _command == 'rm':
        c = gcal_instance()
        for arg in _args:
            c.delete_from_gcal(calid=_arg, evid=arg)
    if _command == 'search':
        current_event = callback_class()
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


if __name__ == "__main__":
    print('this doesn\'t work by itself')
    exit(0)
