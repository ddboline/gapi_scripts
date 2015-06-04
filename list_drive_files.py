#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Script to interact with google drive api """
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
import gzip
try:
    import cPickle as pickle
except ImportError:
    import pickle
from apiclient import sample_tools
from apiclient.errors import HttpError

from util import get_md5
from dateutil.parser import parse

from collections import defaultdict

GDRIVE_MIMETYPES = [
'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
'text/csv', 'image/png', 'application/vnd.oasis.opendocument.text',
'application/pdf']

class GdriveInstance(object):
    """ class to make use of google python api """

    def __init__(self, app='drive', version='v2', number_to_process=-1):
        """ init function """

        self.list_of_keys = {}
        self.list_of_mimetypes = {}
        self.items_processed = 0
        self.list_of_folders = {}
        self.list_of_items = {}

        self.service, self.flags = \
            sample_tools.init([], app, version, __doc__, __file__,\
                scope='https://www.googleapis.com/auth/%s' % app)
        self.number_to_process = number_to_process

        self.gdrive_md5_cache_file = '%s/.gdrive_md5_cache.pkl.gz'\
                                      % os.getenv('HOME')
        self.gdrive_md5_cache = {}
        self.gdrive_base_dir = '%s/gDrive' % os.getenv('HOME')

    def read_cache_file(self):
        """ read cache file """
        if not os.path.exists(self.gdrive_md5_cache_file):
            return
        with gzip.open(self.gdrive_md5_cache_file, 'rb') as cachefile:
            self.gdrive_md5_cache = pickle.load(cachefile)
        return

    def write_cache_file(self):
        """ write cache file """
        with gzip.open(self.gdrive_md5_cache_file, 'wb') as cachefile:
            pickle.dump(self.gdrive_md5_cache, cachefile, protocol=2)
        return

    def process_item(self, item, list_dirs=False):
        """ process item from gdrive api """
        if self.number_to_process > 0\
                and self.items_processed > self.number_to_process:
            return
        self.items_processed += 1
        for k in item:
            if k not in self.list_of_keys:
                self.list_of_keys[k] = 0
            self.list_of_keys[k] += 1
        if item['mimeType'] not in self.list_of_mimetypes:
            self.list_of_mimetypes[item['mimeType']] = 0
        self.list_of_mimetypes[item['mimeType']] += 1
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            if item['id'] not in self.list_of_folders:
                pid = None
                if item['parents']:
                    pid = item['parents'][0]['id']
                self.list_of_folders[item['id']] = [item['title'], pid]
        elif not list_dirs:
            if item['id'] not in self.list_of_items:
                pid = None
                if item['parents']:
                    pid = item['parents'][0]['id']
                dlink = None
                fext = None
                is_export = False
                md5chksum = None
                mtime = None
                if 'modifiedDate' in item:
                    mtime = item['modifiedDate']
                if 'downloadUrl' in item:
                    if 'md5Checksum' in item:
                        md5chksum = item['md5Checksum']
                    dlink = item['downloadUrl']
                    if 'fileExtension' in item:
                        fext = item['fileExtension']
                elif 'exportLinks' in item:
                    is_export = True
                    elmime = []
                    for el_ in item['exportLinks']:
                        if 'application/x-vnd.oasis.opendocument' in el_:
                            elmime.append(el_)
                    for other_type in GDRIVE_MIMETYPES:
                        if not elmime and other_type in item['exportLinks']:
                            elmime = [el_ for el_ in item['exportLinks']
                                      if other_type in el_]
                    if elmime:
                        dlink = item['exportLinks'][elmime[0]]
                        fext = dlink.split('exportFormat=')[1]
                    else:
                        print('not sure what happened...', item['title'],
                              item['mimeType'], item['exportLinks'])
                        raw_input()
                if dlink:
                    self.list_of_items[item['id']] = {
                        'title': item['title'], 'fext': fext, 'pid': pid,
                        'link': dlink, 'export': is_export, 'md5': md5chksum,
                        'mtime': parse(mtime).strftime("%s")}

    def process_response(self, response, list_dirs=False):
        """ process response from gdrive api """
        ### mimeType, parents
        if self.number_to_process > 0\
                and self.items_processed > self.number_to_process:
            return 0
        for item in response['items']:
            self.process_item(item, list_dirs)

    def delete_file(self, fileid):
        """ delete file by fileid """
        request = self.service.files().delete(fileId=fileid)
        response = request.execute()
        return response

    def upload_file(self, filelist, parent_id=None, directory_name=None):
        """ upload files """
        output = []
        if directory_name:
            qstr = 'title contains "%s"' % directory_name.split('/')[-1]
            request = self.service.files().list(q=qstr, maxResults=10)
            response = request.execute()

            new_request = True
            while new_request:
                if self.process_response(response, list_dirs=True) == 0:
                    break
                print('N processed: %d' % self.items_processed)

                new_request = self.service.files().list_next(request, response)
                if not new_request:
                    break
                request = new_request
                try:
                    response = request.execute()
                except HttpError:
                    time.sleep(5)
                    response = request.execute()
            for did in self.list_of_folders:
                title, pid = self.list_of_folders[did]
                parent_id = did
                break

        for fname in filelist:
            if not os.path.exists(fname):
                print('File %s not found, try using absolute path!' % fname)
                continue
            fn_ = fname.split('/')[-1]

            body_obj = {'title': fn_,}

            request = self.service.files().insert(body=body_obj,
                                                  media_body=fname)
            response = request.execute()

            fid = response['id']
            print('%s %s %s' % (fid, response['md5Checksum'],
                                response['title'],))

            request = self.service.parents().list(fileId=fid)
            response = request.execute()

            output.append('%s' % response['items'])

            current_pid = response['items'][0]['id']

            output.append('%s %s' % (parent_id, current_pid))

            request = self.service.files().update(fileId=fid,
                                                  addParents=parent_id,
                                                  removeParents=current_pid)
            response = request.execute()
        return '\n'.join(output)

    def get_parents(self, fids=None):
        """ function to list files in drive """
        if not fids:
            return

        parents_output = []
        for fid in fids:
            request = self.service.files().get(fileId=fid)
            response = request.execute()
            parents_output.extend(response['parents'])
        return parents_output

    def download_file_by_id(self, fid=None):
        """ function to list files in drive """
        if not fid:
            return

        request = self.service.files().get(fileId=fid)
        response = request.execute()

        self.process_item(response)
        self.download_or_list_files(do_download=True, do_export=False)

    def list_files(self, do_download=False, number_to_list=100, searchstr=None,
                   list_dirs=False):
        """ function to list files in drive """
        qstr = None
        if searchstr:
            qstr = 'title contains "%s"' % searchstr

        if number_to_list > 0:
            request = self.service.files().list(q=qstr,
                                                maxResults=number_to_list)
        else:
            request = self.service.files().list(q=qstr)
        response = request.execute()

        new_request = True
        while new_request:
            if self.process_response(response, list_dirs=list_dirs) == 0:
                break
            print('N processed: %d' % self.items_processed)

            new_request = self.service.files().list_next(request, response)
            if not new_request:
                break
            request = new_request
            try:
                response = request.execute()
            except HttpError:
                time.sleep(5)
                response = request.execute()
        return self.download_or_list_files(do_download, list_dirs=list_dirs)

    def download_or_list_files(self, do_download=False, do_export=False,
                               list_dirs=False):
        """ download or list files """
        output = []
        if list_dirs:
            for did in self.list_of_folders:
                title, pid = self.list_of_folders[did]
                output.append('%s %s %s' % (did, title, pid))
            return '\n'.join(output)

        for itid in self.list_of_items:

            title, fext, pid, dlink, is_export, md5chksum, mtime =\
                [self.list_of_items[itid][k] for k in ('title', 'fext', 'pid',
                                                       'link', 'export', 'md5',
                                                       'mtime')]
            if do_download and (do_export and not is_export):
                continue
            if fext not in title.lower():
                title = '.'.join([title, fext])
            ptitle_list = [title]
            while pid:
                if pid in self.list_of_folders:
                    ptitle, ppid = self.list_of_folders[pid]
                    ptitle_list.append(ptitle)
                    pid = ppid
                else:
                    request = self.service.files().get(fileId=pid)
                    response = request.execute()
                    if response:
                        title = response['title']
                        ptitle_list.append(title)
                        if len(response['parents']) > 0:
                            ppid = response['parents'][0]['id']
                            self.list_of_folders[pid] = [title, ppid]
                            pid = ppid
                        else:
                            pid = None
                    else:
                        pid = None
            exportfile = '/'.join(ptitle_list[::-1])
            exportfile = exportfile.replace('My Drive/', '')
            exportfile = '%s/%s' % (self.gdrive_base_dir, exportfile)
            if not do_download:
                output.append('%s %s' % (itid, exportfile))
            if not do_download:
                continue
            if '/' in exportfile:
                exportpath = '/'.join(exportfile.split('/')[:-1])
                if not os.path.exists(exportpath):
                    os.makedirs(exportpath)

            if os.path.exists(exportfile):
                mtime_cur = int(os.stat(exportfile).st_mtime)
                if exportfile in self.gdrive_md5_cache:
                    _md5, mtime_ = self.gdrive_md5_cache[exportfile]
                    if _md5 == md5chksum and mtime >= mtime_:
                        print('%s %s in cache %s %s' % (_md5, exportfile,
                                                        mtime, mtime_))
                        continue
                elif md5chksum == get_md5(exportfile):
                    print('%s %s exists' % (md5chksum, exportfile))
                    self.gdrive_md5_cache[exportfile] = (md5chksum, mtime_cur)
                    continue
                elif not md5chksum:
                    md5chksum = get_md5(exportfile)
                else:
                    print('md5 %s' % md5chksum)

            resp, url_ = self.service._http.request(dlink)
            if resp['status'] != '200':
                print(title, dlink)
                print('something bad happened %s' % resp)
                continue
            tempfile = '%s.tmp' % exportfile
            with open(tempfile, 'wb') as outfile:
                for line in url_:
                    outfile.write(line)
            os.rename(tempfile, exportfile)
            md5chksum = get_md5(exportfile)
            print('%s %s download' % (md5chksum, exportfile))
            self.gdrive_md5_cache[exportfile] = (md5chksum, mtime)
        return '\n'.join(output)

    def scan_local_directory(self):
        """ scan local directory """
        md5_file_index = defaultdict(list)
        files_not_in_cache = defaultdict(list)
        def parse_dir(_, path, filelist):
            """ callback function for walk """
            for fn_ in filelist:
                exportfile = '%s/%s' % (path, fn_)
                if os.path.isdir(exportfile):
                    continue
                if exportfile in self.gdrive_md5_cache:
                    md5_, _ = self.gdrive_md5_cache[exportfile]
                    md5_file_index[md5_].append(exportfile)
                else:
                    md5sum = get_md5(exportfile)
#                    print('%s %s' % (md5sum, exportfile))
                    files_not_in_cache[md5sum].append(exportfile)

        os.path.walk(self.gdrive_base_dir, parse_dir, None)
        for md5sum in files_not_in_cache:
            if md5sum in md5_file_index:
                print('%s %s inmd5' % (md5sum, files_not_in_cache[md5sum]))
            print('%s %s' % (md5sum, files_not_in_cache[md5sum]))
#            os.remove(files_not_in_cache[md5sum][0])
        return

COMMANDS = ('list', 'sync', 'search', 'download', 'upload', 'directories',
            'parent', 'delete', 'new')

def list_drive_files():
    """ main routine, parse arguments """
    cmd = 'list'
    search_strings = []
    parent_directory = None
    number_to_list = 100

    for arg in os.sys.argv:
        if 'list_drive_files.py' in arg:
            continue
        elif arg in ['h', '--help', '-h']:
            print(
                'list_drive_files <%s> <file/key> directory=<id of directory>'\
                    % '|'.join(COMMANDS))
            exit(0)
        elif arg in COMMANDS:
            cmd = arg
        elif 'directory=' in arg:
            parent_directory = arg.replace('directory=', '')
        else:
            try:
                number_to_list = int(arg)
            except ValueError:
                search_strings.append(arg)
    if cmd == 'sync':
        number_to_list = -1
    gdrive = GdriveInstance(number_to_process=number_to_list)
    if cmd == 'list':
        print(gdrive.list_files(do_download=False,
                                number_to_list=number_to_list))
    elif cmd == 'search':
        if search_strings:
            for search_string in search_strings:
                print(gdrive.list_files(do_download=False,
                                        searchstr=search_string,
                                        number_to_list=number_to_list))
    elif cmd == 'new':
        gdrive.read_cache_file()
        gdrive.scan_local_directory()
    elif cmd == 'sync':
        gdrive.read_cache_file()
        gdrive.scan_local_directory()
        gdrive.list_files(do_download=True, number_to_list=number_to_list)
        gdrive.write_cache_file()
    elif cmd == 'directories':
        if search_strings:
            for search_string in search_strings:
                print(gdrive.list_files(do_download=False, number_to_list=100,
                                        searchstr=search_string,
                                        list_dirs=True))
    elif cmd == 'download':
        gdrive.read_cache_file()
        for search_string in search_strings:
            gdrive.download_file_by_id(fid=search_string)
        gdrive.write_cache_file()
    elif cmd == 'upload':
        print(number_to_list, search_strings)
        gdrive.upload_file(filelist=search_strings,
                           directory_name=parent_directory)
    elif cmd == 'parent':
        print(number_to_list, search_strings)
        for parent in gdrive.get_parents(fids=search_strings):
            print(parent['id'])
    elif cmd == 'delete':
        for search_string in search_strings:
            gdrive.delete_file(fileid=search_string)

if __name__ == '__main__':
    list_drive_files()
