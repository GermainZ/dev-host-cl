#!/usr/bin/env python2

# dev-host-cl Copyright (c) 2013 by GermainZ <germanosz@gmail.om>
# Requirements: python2
#               python2-lxml
#               python2-requests
#
# Dev-Host API documentation
# http://d-h.st/api
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
from requests import session
from lxml import etree
import os
import binascii
import argparse
import time
import json
import threading
import signal
import sys


def arg_parser():
    """Parses command line arguments, and returns a dict containing them."""
    # Create the top level parser
    parser = argparse.ArgumentParser(description=("d-h.st (Dev-Host) command"
                                                  "line tool"))
    parser.add_argument('-u', "--username", help="Username")
    parser.add_argument('-p', "--password", help="Password")
    subparsers = parser.add_subparsers(metavar="ACTION", dest="action",
                                       help="Use %(prog)s ACTION -h for help")
    # Parent parsers
    # We use a parent parser to get the user's info again so that args can be
    # after the actions too. For example, this would raise an unknown arg error
    # otherwise:
    # devhost.py upload file.txt -u myusername -p mypassword
    parser_u = argparse.ArgumentParser(add_help=False)
    parser_u.add_argument('-u', "--username", help="Username")
    parser_u.add_argument('-p', "--password", help="Password")
    parser_c = argparse.ArgumentParser(add_help=False)
    parser_c.add_argument("file-code", help="File Code")
    # Create the parser for the "upload" command
    parser_upload = subparsers.add_parser("upload", parents=[parser_u],
                                          help="Upload file")
    parser_upload.add_argument("my_file", type=argparse.FileType('rb'),
                               metavar="file", help="File to upload")
    parser_upload.add_argument('-d', "--file-desc", help="Description of file")
    parser_upload.add_argument('-c', "--file-code", help=("File code of an"
                               "existing file to update/replace"))
    parser_upload.add_argument('-pb', "--public", choices=['0', '1'],
                               default='0', help=("File is public or private,"
                               " 0 - private, 1 - public"))
    parser_upload.add_argument('-f', "--upload-folder", default='0',
                               help=("Folder id to upload file to. The root"
                                     " folder is chosen by default"))
    # Create the parser for the "get-file-info" command
    parser_getf = subparsers.add_parser("file-get-info",
                                        parents=[parser_c, parser_u],
                                        help="Return file info")
    # Create the parser for the "set-file-info" command
    parser_setf = subparsers.add_parser("file-set-info",
                                        parents=[parser_c, parser_u],
                                        help="Set file info")
    parser_setf.add_argument('-n', "--file-name", help=h_empty("name"))
    parser_setf.add_argument('-d', "--file-desc", help=h_empty("description"))
    parser_setf.add_argument('-pb', "--public", choices=['0', '1'],
                             default='0', help=h_empty("public status, 0 -"
                             " private, 1 - public"))
    parser_setf.add_argument('-f', "--folder-id", help=("Use to change the"
                                                        " file's folder"))
    # Create the parser for the "file-delete" command
    parser_delf = subparsers.add_parser("file-delete",
                                        parents=[parser_c, parser_u],
                                        help="Delete file")
    # Create the parser for the "file-move" command
    parser_mvf = subparsers.add_parser("file-move",
                                       parents=[parser_c, parser_u],
                                       help="Move file")
    parser_mvf.add_argument('-f', "--folder-id",
                            help=("Use if you want to change the folder."
                            " Specify folder_id or 0 for root directory."))
    # Parse the args and return them as a dict
    args = parser.parse_args()
    if args.action is None:
        parser.print_help()
    return vars(args)

def h_empty(s):
    """Substitute keyword and returns repetitive help message for arg parser"""
    s = ("Use to change the file's %s. Choosing an empty value \"\" will"
         " clear the data.") % s
    return s


def login(username, password):
    """Login and return the token, which is used for identification."""
    args = {'action': "user/auth", 'user': username, 'pass': password}
    url = gen_url(args)
    request = s.get(url)
    content = request.content
    resp = etree.XML(content)
    token = resp.xpath('//token/text()')[0]
    return token

def parse_info(xml):
    """Parses the response and returns it."""
    xml = etree.XML(xml)
    return xml.xpath("//results/descendant::*")

def upload(args, token):
    """Handles file upload.

    Generates XID, builds request and calls the upload_file method. Also runs
    get_progress as a thread to print the progress from the server.
    """
    xid = None
    xid = binascii.hexlify(os.urandom(8))
    files_data, upload_data = gen_data(args, xid, token)
    # Get and print the progress using a daemon thread
    t = threading.Thread(target=get_progress, args=(xid,))
    t.daemon = True
    t.start()
    result = upload_file(files_data, upload_data, xid)
    return result

def gen_data(args, xid, token):
    """Constructs data needed for the HTTP POST request for uploads."""
    files_data = {'file': args['my_file']}
    upload_data = {'action': "uploadapi", 'token': token,
                   'public': args['public'],
                   'upload_folder': args['upload_folder'],
                   'file_description[]': args['file_desc'],
                   'file_code[]': args['file_code']}
    return files_data, upload_data

def upload_file(files_data, upload_data, xid):
    """Uploads file and returns parsed response."""
    # xid is optional, and can be used to track progress
    url = 'http://api.d-h.st/upload'
    if xid is not None:
        url = '%s?X-Progress-ID=%s' % (url, xid)
    r = s.post(url, data=upload_data, files=files_data)
    return r.content

def get_progress(xid):
    """Prints the upload's progress, using the xid."""
    while True:
        # We're getting the progress from the website, so there's a slight
        # traffic overhead, which is why we're waiting a few seconds between
        # refreshes.
        time.sleep(3)
        request = s.get('http://api.d-h.st/progress?X-Progress-ID=%s' % xid)
        resp = request.content.strip()[1:-2]
        progress = json.loads(resp.decode())
        if progress.get('state') == "uploading":
            percentage = progress.get('received') / progress.get('size') * 100
            percentage = '{n:.{d}f}'.format(n=percentage, d=2)
            print "Progress: %s%%" % percentage,
            sys.stdout.write('\r')
            sys.stdout.flush()
        elif progress.get('state') == "starting":
            pass
        else:
            print progress.get('state')

def get_file_info(file_code, token):
    """Gets a file's info."""
    args = {'action': "file/getinfo", 'token': token, 'file_code': file_code}
    url = gen_url(args)
    r = s.get(url)
    return r.content

def set_file_info(args, token):
    """Sets a file's info."""
    args = {'action': "file/setinfo", 'token': token, 'file_code':
            args['file-code'], 'name': args['file_name'], 'description':
            args['file_desc'], 'public': args['public'], 'folder_id':
            args['folder_id']}
    url = gen_url(args)
    r = s.get(url)
    return r.content

def delete_file(file_code, token):
    """Deletes file(s)."""
    args = {'action': "file/delete", 'token': token, 'file_code': file_code}
    url = gen_url(args)
    r = s.get(url)
    return r.content

def move_file(file_code, token, folder_id):
    """Moves file(s)."""
    args = {'action': "file/move", 'token': token, 'file_code': file_code,
            'folder_id': folder_id}
    url = gen_url(args)
    r = s.get(url)
    return r.content

def gen_url(args):
    """Generates a URL using the keys/values of args, and returns it."""
    url = ["http://d-h.st/api/%s" % args['action']]
    del args['action']
    first = True
    for key, value in args.items():
        if value is None:
            continue
        if first == True:
            url.append("?")
            first = False
        else:
            url.append("&")
        url.append("%s=%s" % (key, value))
    url = ''.join(url)
    return url

def signal_handler(signal, frame):
    """Handles SIGINT"""
    print "\nAborted by user"
    exit(0)


signal.signal(signal.SIGINT, signal_handler)
s = session()
args = arg_parser()

token = None
if args['username'] is not None and args['password'] is not None:
    print "Logging in..."
    token = login(args['username'], args['password'])

print "Starting...\n"
result = None
if args['action'] == "upload":
    result = upload(args, token)
elif args['action'] == "file-get-info":
    result = get_file_info(args['file-code'], token)
elif args['username'] is None or args['password'] is None:
    print "You must specify your username and password for this action."
elif args['action'] == "file-set-info":
    result = set_file_info(args, token)
elif args['action'] == "file-delete":
    result = delete_file(args['file-code'], token)
elif args['action'] == "file-move":
    result = move_file(args['file-code'], token, args['folder_id'])
else:
    print args['action']

if result is not None:
    for field in parse_info(result):
        print "%s: %s" % (field.tag.capitalize(), field.text)

print
