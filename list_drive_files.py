#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os, time
from urllib2 import urlopen
from apiclient import sample_tools

class gdrive_instance(object):
    """ class to make use of google python api """

    def __init__(self, app='drive', version='v2', number_to_process=-1):
        """ init function """

        self.list_of_keys = {}
        self.list_of_mimetypes = {}
        self.items_processed = 0
        self.list_of_folders = {}
        self.list_of_items = {}

        curdir = os.curdir

        self.service, self.flags = \
            sample_tools.init([], app, version, __doc__, __file__,\
                scope='https://www.googleapis.com/auth/%s' % app)
        self.number_to_process = number_to_process
        #os.chdir(curdir)

    def process_item(self, it, output=None, list_dirs=False):
        if self.number_to_process > 0 and self.items_processed > self.number_to_process:
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
                if 'downloadUrl' in it:
                    if 'md5Checksum' in it:
                        md5chksum = it['md5Checksum']
                    dlink = it['downloadUrl']
                    if 'fileExtension' in it:
                        fext = it['fileExtension']
                elif 'exportLinks' in it:
                    isExport = True
                    elmime = [el for el in it['exportLinks'] if 'application/x-vnd.oasis.opendocument' in el]
                    for other_type in ['text/csv', 'image/png', 'application/vnd.oasis.opendocument.text', 'application/pdf']:
                        if not elmime and other_type in it['exportLinks']:
                            elmime = [el for el in it['exportLinks'] if other_type in el]
                    if elmime:
                        dlink = it['exportLinks'][elmime[0]]
                        fext = dlink.split('exportFormat=')[1]
                    else:
                        print('not sure what happened...', it['title'], it['mimeType'], it['exportLinks'])
                        raw_input()
                if fext and pid and dlink:
                    self.list_of_items[it['id']] = [it['title'], fext, pid, dlink, isExport, md5chksum]


    def process_response(self, response, output=None, list_dirs=False):
        ### mimeType, parents
        if self.number_to_process > 0 and self.items_processed > self.number_to_process:
            return 0
        for it in response['items']:
            self.process_item(it, output, list_dirs)

    def delete_file(self, fileid):
        request = self.service.files().delete(fileId=fileid)
        response = request.execute()
    
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
                except apiclient.errors.HttpError:
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

            request = self.service.files().insert(body=body_obj, media_body=fname)
            response = request.execute()
    
            fid = response['id']
            print('%s %s %s' % (fid, response['md5Checksum'], response['title'], ))
            
            request = self.service.parents().list(fileId=fid)
            response = request.execute()
            
            output.append('%s' % response['items'])
            
            current_pid = response['items'][0]['id']

            output.append('%s %s' % (parent_id, current_pid))

            request = self.service.files().update(fileId=fid, addParents=parent_id, removeParents=current_pid)
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

    def list_files(self, do_download=False, number_to_list=100, searchstr=None, list_dirs=False):
        """ function to list files in drive """
        qstr = None
        if searchstr:
            qstr = 'title contains "%s"' % searchstr
        
        if number_to_list > 0:
            request = self.service.files().list(q=qstr, maxResults=number_to_list)
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
            except apiclient.errors.HttpError:
                time.sleep(5)
                response = request.execute()
        return self.download_or_list_files(do_download, list_dirs=list_dirs)

    def download_or_list_files(self, do_download=False, do_export=True, list_dirs=False):
        output = []
        if list_dirs:
            for did in self.list_of_folders:
                title, pid = self.list_of_folders[did]
                output.append('%s %s %s' % (did, title, pid))
            return '\n'.join(output)
        
        for itid in self.list_of_items:
            title, fext, pid, dlink, isExport, md5chksum = self.list_of_items[itid]
            if (do_export and not isExport) and do_download:
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
            ptitle_list.append('DriveExport')
            exportfile = '/'.join(ptitle_list[::-1])
            output.append('%s %s' % (itid, exportfile))
            if not do_download:
                continue
            if '/' in exportfile:
                exportpath = '/'.join(exportfile.split('/')[:-1])
                if not os.path.exists(exportpath):
                    os.makedirs(exportpath)
            resp, f = self.service._http.request(dlink)
            if resp['status'] != '200':
                print(dlink)
                print('something bad happened %s' % resp)
                continue
            with open(exportfile, 'wb') as outfile:
                for line in f:
                    outfile.write(line)
        return '\n'.join(output)

if __name__ == '__main__':
    cmd = 'list'
    search_strings = []
    parent_directory = None
    number_to_list = 100
    COMMANDS = ['list', 'sync', 'search', 'download', 'upload', 'directories', 'parent', 'delete']
    for arg in os.sys.argv:
        if 'list_drive_files.py' in arg:
            continue
        elif arg in ['h', '--help', '-h']:
            print('list_drive_files <%s> <file/key> directory=<id of directory>' % '|'.join(COMMANDS))
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
        print(gdrive.list_files(do_download=False, number_to_list=number_to_list))
    elif cmd == 'search':
        if search_strings:
            for search_string in search_strings:
                print(gdrive.list_files(do_download=False, searchstr=search_string, number_to_list=number_to_list))
    elif cmd == 'sync':
        print(gdrive.list_files(do_download=True, number_to_list=number_to_list))
    elif cmd == 'directories':
        if search_strings:
            for search_string in search_strings:
                print(gdrive.list_files(do_download=False, number_to_list=100, searchstr=search_string, list_dirs=True))
    elif cmd == 'download':
        for search_string in search_strings:
            gdrive.download_file_by_id(fid=search_string)
    elif cmd == 'upload':
        print(number_to_list, search_strings)
        gdrive.upload_file(filelist=search_strings, directory_name=parent_directory)
    elif cmd == 'parent':
        print(number_to_list, search_strings)
        for parent in gdrive.get_parents(fids=search_strings):
            print(parent['id'])
    elif cmd == 'delete':
        for search_string in search_strings:
            gdrive.delete_file(fileid=search_string)
