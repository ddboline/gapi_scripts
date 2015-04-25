#!/usr/bin/python
# -*- coding: utf-8 -*-
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

GDRIVE_MIMETYPES = [
'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
'text/csv', 'image/png', 'application/vnd.oasis.opendocument.text',
'application/pdf']

class gdrive_instance(object):
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
        if not os.path.exists(self.gdrive_md5_cache_file):
            return
        with gzip.open(self.gdrive_md5_cache_file, 'rb') as cachefile:
            self.gdrive_md5_cache = pickle.load(cachefile)
        return

    def write_cache_file(self):
        with gzip.open(self.gdrive_md5_cache_file, 'wb') as cachefile:
            pickle.dump(self.gdrive_md5_cache, cachefile, protocol=2)
        return

    def process_item(self, it, output=None, list_dirs=False):
        if self.number_to_process > 0\
                and self.items_processed > self.number_to_process:
            return
        self.items_processed += 1
        for k in it:
            if k not in self.list_of_keys:
                self.list_of_keys[k] = 0
            self.list_of_keys[k] += 1
        if it['mimeType'] not in self.list_of_mimetypes:
            self.list_of_mimetypes[it['mimeType']] = 0
        self.list_of_mimetypes[it['mimeType']] += 1
        if it['mimeType'] == 'application/vnd.google-apps.folder':
            if it['id'] not in self.list_of_folders:
                pid = None
                if it['parents']:
                    pid = it['parents'][0]['id']
                self.list_of_folders[it['id']] = [it['title'], pid]
        elif not list_dirs:
            if it['id'] not in self.list_of_items:
                pid = None
                if it['parents']:
                    pid = it['parents'][0]['id']
                dlink = None
                fext = None
                isExport = False
                md5chksum = None
                mtime = None
                if 'modifiedDate' in it:
                    mtime = it['modifiedDate']
                if 'downloadUrl' in it:
                    if 'md5Checksum' in it:
                        md5chksum = it['md5Checksum']
                    dlink = it['downloadUrl']
                    if 'fileExtension' in it:
                        fext = it['fileExtension']
                elif 'exportLinks' in it:
                    isExport = True
                    elmime = []
                    for el in it['exportLinks']:
                        if 'application/x-vnd.oasis.opendocument' in el:
                            elmime.append(el)
                    for other_type in GDRIVE_MIMETYPES:
                        if not elmime and other_type in it['exportLinks']:
                            elmime = [el for el in it['exportLinks']
                                      if other_type in el]
                    if elmime:
                        dlink = it['exportLinks'][elmime[0]]
                        fext = dlink.split('exportFormat=')[1]
                    else:
                        print('not sure what happened...', it['title'],
                              it['mimeType'], it['exportLinks'])
                        raw_input()
                if fext and pid and dlink:
                    self.list_of_items[it['id']] = {
                        'title': it['title'], 'fext': fext, 'pid': pid, 
                        'link': dlink, 'export': isExport, 'md5': md5chksum,
                        'mtime': parse(mtime).strftime("%s")}


    def process_response(self, response, output=None, list_dirs=False):
        ### mimeType, parents
        if self.number_to_process > 0\
                and self.items_processed > self.number_to_process:
            return 0
        for it in response['items']:
            self.process_item(it, output, list_dirs)

    def delete_file(self, fileid):
        request = self.service.files().delete(fileId=fileid)
        response = request.execute()
        return response

    def upload_file(self, filelist, parent_id=None, directory_name=None):
        output = []
        if directory_name:
            qstr = 'title contains "%s"' % directory_name
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
            fn = fname.split('/')[-1]

            body_obj = {'title': fn,}

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
        output = []
        if list_dirs:
            for did in self.list_of_folders:
                title, pid = self.list_of_folders[did]
                output.append('%s %s %s' % (did, title, pid))
            return '\n'.join(output)

        for itid in self.list_of_items:
            
            title, fext, pid, dlink, isExport, md5chksum, mtime =\
                [self.list_of_items[itid][k] for k in ('title', 'fext', 'pid',
                                                       'link', 'export', 'md5',
                                                       'mtime')]
            if do_download and (do_export and not isExport):
                continue
            if not fext:
                print(title, pid, dlink)
            elif fext not in title:
                title = '.'.join([title,fext])
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
                        if len(response['parents'])>0:
                            pid = response['parents'][0]['id']
                        else:
                            pid = None
                    else:
                        pid = None
            exportfile = '/'.join(ptitle_list[::-1])
            exportfile = exportfile.replace('My Drive/', '')
            exportfile = '%s/%s' % (self.gdrive_base_dir, exportfile)
            output.append('%s %s' % (itid, exportfile))
            if not do_download:
                continue
            if '/' in exportfile:
                exportpath = '/'.join(exportfile.split('/')[:-1])
                try:
                    os.makedirs(exportpath)
                except:
                    pass

            if os.path.exists(exportfile):
                mtime_cur = os.stat(exportfile).st_mtime
                if mtime < mtime_cur:
                    print('%s %s %s unchanged' % (mtime_cur, mtime,
                                                  exportfile))
                if md5chksum == get_md5(exportfile):
                    print('%s %s exists' % (md5chksum, exportfile))
                    continue
                elif not md5chksum:
                    md5chksum = get_md5(exportfile)
                else:
                    print('md5 %s' % md5chksum)
                if exportfile in self.gdrive_md5_cache:
                    _md5, _mtime = self.gdrive_md5_cache[exportfile]
                    if _md5 == md5chksum and mtime >= _mtime:
                        print('%s %s in cache %s %s' % (_md5, exportfile, 
                                                        mtime, _mtime))
                        continue

            try:
                resp, f = self.service._http.request(dlink)
            except Exception as e:
                print('Exception %s' % e)
                continue
            if resp['status'] != '200':
                print(title, dlink)
                print('something bad happened %s' % resp)
                continue
            with open(exportfile, 'wb') as outfile:
                for line in f:
                    outfile.write(line)
            md5chksum = get_md5(exportfile)
            print('%s %s download' % (md5chksum, exportfile))
            self.gdrive_md5_cache[exportfile] = (md5chksum, mtime)
        return '\n'.join(output)

if __name__ == '__main__':
    cmd = 'list'
    search_strings = []
    parent_directory = None
    number_to_list = 100
    COMMANDS = ['list', 'sync', 'search', 'download', 'upload', 'directories',
                'parent', 'delete']
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
                pass
    if cmd == 'sync':
        number_to_list = -1
    gdrive = gdrive_instance(number_to_process=number_to_list)
    if cmd == 'list':
        print(gdrive.list_files(do_download=False,
                                number_to_list=number_to_list))
    elif cmd == 'search':
        if search_strings:
            for search_string in search_strings:
                print(gdrive.list_files(do_download=False,
                                        searchstr=search_string,
                                        number_to_list=number_to_list))
    elif cmd == 'sync':
        gdrive.read_cache_file()
        print(gdrive.list_files(do_download=True,
                                number_to_list=number_to_list))
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
