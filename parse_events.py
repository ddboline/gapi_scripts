#!/usr/bin/python
""" Base module for Parsing events """
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import re
import gzip
import datetime
import pytz
from collections import defaultdict

from util import datetimestring, datetimefromstring
from gcal_instance import gcal_instance

try:
    import cPickle as pickle
except ImportError:
    import pickle

MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
                'Oct', 'Nov', 'Dec']
MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
               'August', 'September', 'October', 'November', 'December']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
            'Sunday']
BUILDINGS = ['Math Tower', 'Harriman Hall', 'Grad. Physics', 'ESS']

TZOBJ = pytz.timezone("US/Eastern")


def strip_out_unicode_crap(inpstr):
    """ remove non-ascii characters (could've used easier method) """
    return re.sub(r'[^\x00-\x7F]', '', inpstr)


class BaseEvent(object):
    """ Base Event Class """

    __slots__ = ['event_time', 'event_end_time', 'event_url', 'event_name',
                 'event_desc', 'event_location', 'event_lat', 'event_lon',
                 'event_id']

    def __init__(self, dt=None, ev_name='', ev_url='', ev_desc='', ev_loc=''):
        """ Init Method """
        for attr in self.__slots__:
            setattr(self, attr, None)
        self.event_time = dt
        self.event_end_time = dt
        self.event_url = ev_url
        self.event_name = ev_name
        self.event_desc = ev_desc
        self.event_location = ev_loc
        self.event_id = None
        self.event_lat = None
        self.event_lon = None

    def compare(self, obj, partial_match=None):
        """ Compre event objects """
        comp_list = []
        attr_list = ('event_time', 'event_end_time', 'event_url', 'event_desc',
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

    def generate_id(self):
        """ Create unique ID """
        import hashlib
        id_list = []
        for k in sorted(self.__slots__):
            if k == 'event_id':
                continue
            id_list.append('%s%s' % (k, getattr(self, k)))
        id_str = ''.join(id_list)
        md_ = hashlib.md5()
        md_.update(id_str.encode(errors='ignore'))
        self.event_id = md_.hexdigest()
        return self.event_id

    def define_new_event_object(self):
        """ Create new event object """
        if type(self.event_lat) == float and type(self.event_lon) == float:
            loc_str = '%f,%f' % (self.event_lat, self.event_lon)
        else:
            loc_str = self.event_location
        return {'creator':
                {'self': True, 'displayName': 'Daniel Boline',
                 'email': 'ddboline@gmail.com'},
                'originalStartTime':
                {'dateTime': datetimestring(self.event_time)},
                'organizer':
                {'self': True, 'displayName': 'Daniel Boline',
                 'email': 'ddboline@gmail.com'},
                'location': loc_str,
                'summary': self.event_name,
                'description': 'Location: %s\nDescription: %s\n%s'
                % (self.event_location, self.event_desc, self.event_url),
                'start':
                {'dateTime': datetimestring(self.event_time)},
                'end': {'dateTime': datetimestring(self.event_end_time)}}

    def read_gcal_event(self, obj):
        """ Read GCalendar Event """
        if 'dateTime' in obj['start']:
            tstr = obj['start']['dateTime']
            self.event_time = datetimefromstring(tstr)
            tstr = obj['end']['dateTime']
            self.event_end_time = datetimefromstring(tstr)
        elif 'date' in obj['start']:
            tstr = obj['start']['date']
            ts_ = [int(x) for x in (tstr[0:4], tstr[5:7], tstr[8:10])]
            self.event_time = datetime.datetime(year=ts_[0], month=ts_[1],
                                                day=ts_[2], hour=9, minute=0)
            self.event_time = TZOBJ.localize(self.event_time)
            self.event_end_time = (self.event_time
                                   + datetime.timedelta(minutes=60))
        else:
            print(obj)
            exit(0)
        self.event_name = obj.get('summary', '')
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
                self.event_lat, self.event_lon = [
                    float(x) for x in obj['location'].split(',')[:2]]
            except ValueError:
                pass
        self.event_id = obj['id']

    def print_event(self):
        """ Print Event """
        ostr = ['%s %s' % (datetimestring(self.event_time),
                           datetimestring(self.event_end_time)),
                '\t url: %s' % self.event_url,
                '\t name: %s' % strip_out_unicode_crap(self.event_name),
                '\t description: %s' % self.event_desc,
                '\t location: %s' % self.event_location]
        if type(self.event_lat) == float and type(self.event_lon) == float:
            ostr[-1] += ' %f,%f' % (self.event_lat, self.event_lon)
        if not self.event_id:
            self.generate_id()
        ostr.append('\t event_id: %s' % self.event_id)
        print('\n'.join(x for x in ostr))


def parse_events(parser_callback=None, script_name='', calid=None,
                 callback_class=None, replace=False):
    """ Parse GCalendar Events """

    def process_response(response, outlist):
        """ Callback to process response """
        for item in response['items']:
            ts_ = callback_class()
            ts_.read_gcal_event(item)
            kstr = '%s %s' % (ts_.event_time, ts_.event_id)
            outlist[kstr] = ts_
        return outlist

    def simple_response(response, outlist=None):
        """ Simple Responce fn """
        for item in response['items']:
            for key, it_ in item.items():
                try:
                    print('%s: %s' % (key, it_))
                except UnicodeEncodeError:
                    print('%s: %s' % (key.encode(errors='ignore'),
                                      it_.encode(errors='ignore')))
            print('')
        return outlist

    if not parser_callback:
        return
    if not callback_class:
        callback_class = BaseEvent

    if not calid:
        calid = 'ufdpqtvophgg2qn643rducu1a4@group.calendar.google.com'
    commands = ('h', 'list', 'new', 'post', 'cal', 'pcal', 'listcal', 'rm',
                'search', 'week', 'dupe')

    command_ = ''
    arg_ = calid

    for arg in os.sys.argv:
        if arg.split('=')[0] in commands:
            command_ = arg.split('=')[0]
        else:
            arg = 'h'
        if '=' in arg:
            arg_ = arg.split('=')[1]

    args_ = []
    for arg in os.sys.argv[1:]:
        if arg in commands:
            continue
        args_.append(arg)

    if command_ == 'h':
        print('./%s <%s>' % (script_name, '|'.join(commands)))
        exit(0)

    if command_ == 'list':
        for line in parser_callback():
            if line.event_time >= datetime.datetime.now(TZOBJ):
                line.print_event()
    if command_ == 'new':
        new_events = {}
        existing_events = defaultdict(list)
        remove_dict = {}
        exist = gcal_instance().get_gcal_events(calid=arg_,
                                                callback_fn=process_response)
        for ev_ in exist.values():
            ev_key = '%s_%s' % (ev_.event_time.strftime('%Y-%m-%d'),
                                ev_.event_name)
            existing_events[ev_key].append(ev_)
        for line in parser_callback():
            if not line:
                continue
            if args_ and line.generate_id() not in args_:
                continue
            ev_key = '%s_%s' % (line.event_time.strftime('%Y-%m-%d'),
                                line.event_name)
            if ev_key not in existing_events:
                if ev_key not in new_events:
                    line.print_event()
                    new_events[ev_key] = line
            elif replace:
                if ev_key not in new_events:
                    line.print_event()
                    new_events[ev_key] = line
                    remove_dict[ev_key] = existing_events[ev_key]
        if new_events:
            with gzip.open('.tmp_%s.pkl.gz' % script_name, 'wb') as pkl_file:
                pickle.dump(new_events.values(), pkl_file,
                            pickle.HIGHEST_PROTOCOL)
        if remove_dict:
            with gzip.open('.tmp_rm_%s.pkl.gz' % script_name,
                           'wb') as pkl_file:
                pickle.dump(remove_dict.values(), pkl_file,
                            pickle.HIGHEST_PROTOCOL)
    if command_ == 'post':
        new_events = []
        remove_events = defaultdict(list)
        gci = gcal_instance()
        if os.path.exists('.tmp_%s.pkl.gz' % script_name):
            with gzip.open('.tmp_%s.pkl.gz' % script_name, 'rb') as pkl_file:
                new_events = pickle.load(pkl_file)
            os.remove('.tmp_%s.pkl.gz' % script_name)
            if os.path.exists('.tmp_rm_%s.pkl.gz' % script_name):
                with gzip.open('.tmp_rm_%s.pkl.gz' % script_name,
                               'rb') as pkl_file:
                    remove_events = pickle.load(pkl_file)
                os.remove('.tmp_rm_%s.pkl.gz' % script_name)
        else:
            print('no pickle file')
            exist = gci.get_gcal_events(calid=arg_,
                                        callback_fn=process_response)
            for line in parser_callback():
                if args_ and line.generate_id() not in args_:
                    continue
                if not any([e.compare(line) for e in exist.values()]):
                    line.print_event()
                    new_events.append(line)
        for ev_ in new_events:
            gci.add_to_gcal(ev_entry=ev_, calid=arg_)
        for ev_list in remove_events:
            for ev_ in ev_list:
                gci.delete_from_gcal(calid=arg_, evid=ev_.event_id)
    if command_ == 'dupe':
        keep_dict = {}
        remove_dict = {}
        gci = gcal_instance()
        exist = gci.get_gcal_events(calid=arg_, callback_fn=process_response)
        for k in sorted(exist.keys()):
            ev_ = exist[k]
            ev_key = '%s_%s' % (ev_.event_time.strftime('%Y-%m-%d'),
                                ev_.event_name)
            if ev_key not in keep_dict:
                keep_dict[ev_key] = ev_
            else:
                print(ev_key)
                ev_.print_event()
                remove_dict[ev_key] = ev_
        print('number %d %d' % (len(keep_dict), len(remove_dict)))
        for k in remove_dict:
            ev_ = remove_dict[k]
            print(ev_.event_id)
            gci.delete_from_gcal(calid=arg_, evid=ev_.event_id)
    if command_ == 'cal':
        gcal_instance().get_gcal_events(calid=arg_,
                                        callback_fn=simple_response)
    if command_ == 'week':
        exist = gcal_instance().get_gcal_events(calid=arg_,
                                                callback_fn=process_response)
        for k in sorted(exist.keys()):
            ev_ = exist[k]
            if ev_.event_time < datetime.datetime.now(TZOBJ) or \
                    ev_.event_time > (datetime.datetime.now(TZOBJ)
                                      + datetime.timedelta(days=7)):
                continue
            ev_.print_event()
    if command_ == 'pcal':
        gci = gcal_instance()
        exist = gci.get_gcal_events(calid=arg_, callback_fn=process_response)
        print(len(exist.keys()))
        for k in sorted(exist.keys()):
            ev_ = exist[k]
            if ev_.event_time >= datetime.datetime.now(TZOBJ):
                ev_.print_event()
            elif 'past' in args_:
                ev_.print_event()
    if command_ == 'listcal':
        gcal_instance().list_gcal_calendars()
    if command_ == 'rm':
        gci = gcal_instance()
        for arg in args_:
            gci.delete_from_gcal(calid=arg_, evid=arg)
    if command_ == 'search':
        current_event = callback_class()
        if args_[0] not in [k.replace('event_', '').replace('event', '')
                            for k in current_event.__dict__.keys()]:
            print(args_)
            exit(0)
        if len(args_) < 2:
            print(args_)
            exit(0)
        exist = gcal_instance().get_gcal_events(calid=arg_,
                                                callback_fn=process_response)

        def search_event(ev_):
            """ Search withing event """
            key = 'event_%s' % args_[0]
            v0_ = args_[1]
            if key == 'event_time' or key == 'event_end_time':
                import dateutil.parser
                v0_ = dateutil.parser.parse(v0_)
            val = None
            if key in ev_.__dict__:
                val = getattr(ev_, key)
                if not val:
                    return
            else:
                key = 'event%s' % args_[0]
                if key in ev_.__dict__:
                    val = getattr(ev_, key)
                    if not val:
                        return
            if type(v0_) != datetime.datetime:
                if v0_ not in val:
                    return
            else:
                if val < v0_:
                    return
            ev_.print_event()

        print('gcal events')
        for key in sorted(exist.keys()):
            search_event(exist[key])


if __name__ == "__main__":
    parse_events(parser_callback=lambda : [], script_name='parse_event',
                 calid=None, callback_class=None)
