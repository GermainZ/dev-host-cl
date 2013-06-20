#!/usr/bin/env python3

# dev-host-cl Copyright (c) 2013 by GermainZ <germanosz@gmail.om>
# Requirements: python3
#               python-lxml
#               python-requests
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

from requests import session
from lxml import etree
import os
import binascii
import argparse
import time
import json
import threading
import signal


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
    # Other parent parsers
    parser_c = argparse.ArgumentParser(add_help=False)
    parser_c.add_argument("file_code", metavar="file-code", help="File Code")
    parser_fo = argparse.ArgumentParser(add_help=False)
    parser_fo.add_argument("folder_id", metavar="folder-id", help="Folder ID")
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
    parser_upload.add_argument('-f', "--upload-folder", dest="uploadfolder",
                               default='0',
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
    parser_setf.add_argument('-n', "--file-name", dest="name",
                             help=h_empty("name"))
    parser_setf.add_argument('-d', "--file-desc", dest="description",
                             help=h_empty("description"))
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
    # Create the parser for the "get-folder-info" command
    parser_getfo = subparsers.add_parser("folder-get-info",
                                        parents=[parser_fo, parser_u],
                                        help="Return folder info")
    # Create the parser for the "set-folder-info" command
    parser_setfo = subparsers.add_parser("folder-set-info",
                                        parents=[parser_fo, parser_u],
                                        help="Set folder info")
    parser_setfo.add_argument('-n', "--folder-name", dest="name",
                              help=h_empty("name"))
    parser_setfo.add_argument('-d', "--folder-desc", dest="description",
                             help=h_empty("description"))
    parser_setfo.add_argument('-f', "--parent-folder-id",
                             help=("Use to change the parent folder"))
    # Create the parser for the "folder-delete" command
    parser_delfo = subparsers.add_parser("folder-delete",
                                        parents=[parser_fo, parser_u],
                                        help="Delete folder")
    # Create the parser for the "folder-move" command
    parser_mvfo = subparsers.add_parser("folder-move",
                                       parents=[parser_fo, parser_u],
                                       help="Move folder")
    parser_mvfo.add_argument('-f', "--parent-folder-id",
                            help=("Use if you want to change the folder."
                            " Specify folder_id or 0 for root directory."))
    # Create the parser for the "folder-create" command
    parser_cfo = subparsers.add_parser("folder-create",
                                       parents=[parser_u],
                                       help="Create folder")
    parser_cfo.add_argument("name", metavar="folder-name",
                            help="Folder name")
    parser_cfo.add_argument('-d', "--folder-desc", dest="description",
                             help="Folder description")
    parser_cfo.add_argument('-f', "--parent-folder-id",
                             help="Create folder inside this one")
    # Create the parser for the "folder-content" command
    parser_confo = subparsers.add_parser("folder-content",
                                         parents=[parser_fo, parser_u],
                                         help="Get folder content")
    parser_confo.add_argument("--user", help=("Username of the person you"
                                              "want to retrieve the folder"
                                              "content for"))
    parser_confo.add_argument("--user-id", help=("User id of the person you"
                                                 "want to retrieve the folder"
                                                 "content for"))
    # TODO: merge some of the duplicate items into a parent parser
    # TODO: help text needs more info
    # Parse the args and return them as a dict
    args = parser.parse_args()
    if args.action is None:
        parser.print_help()
        exit(0)
    return vars(args)

def h_empty(s):
    """Substitute keyword and returns repetitive help message for arg parser"""
    s = ("Use to change the %s. Choosing an empty value \"\" will"
         " clear the data.") % s
    return s


def login(username, password):
    """Login and return the token, which is used for identification."""
    args = {'action': "user/auth", 'user': username, 'pass': password}
    url = gen_url(args)
    request = s.get(url)
    resp = etree.XML(request.content)
    token = resp.xpath('//token/text()')[0]
    return token

def parse_info(xml):
    """Parses the response and returns it."""
    xml = etree.XML(xml)
    return xml.xpath("//results/descendant::*")

def upload(args):
    """Handles file upload.

    Generates XID, builds request and calls the upload_file method. Also runs
    get_progress as a thread to print the progress from the server.
    """
    xid = binascii.hexlify(os.urandom(8))
    files_data = {'file': args.pop('my_file')}
    args['file_description[]'] = args.pop('file_desc')
    args['file_code[]'] = args.pop('file_code')
    upload_data = args
    # Get and print the progress using a daemon thread
    t = threading.Thread(target=get_progress, args=(xid,))
    t.daemon = True
    t.start()
    result = upload_file(files_data, upload_data, xid)
    return result

def upload_file(files_data, upload_data, xid):
    """Uploads file and returns parsed response."""
    # xid is optional, and can be used to track progress
    # TODO: Actually make progress tracking optional
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
            print("Progress: %s%%" % percentage, end='\r')
        elif progress.get('state') == "starting":
            pass
        else:
            print(progress.get('state'))

def api_do(args):
    """Generates URL using the passed args, gets the data from it,
    and returns the content of the response."""
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
    print("\nAborted by user")
    exit(0)


args = arg_parser()
signal.signal(signal.SIGINT, signal_handler)
s = session()
methods = {'upload': "uploadapi", 'file-get-info': "file/getinfo",
           'file-set-info': "file/setinfo", 'file-delete': "file/delete",
           'file-move': "file/move", 'folder-get-info': "folder/getinfo",
           'folder-set-info': "folder/setinfo", 'folder-delete':
           "folder/delete", 'folder-move': "folder/move", 'folder-create':
           "folder/create", 'folder-content': "folder/content"}

token = None
if args['username'] is not None and args['password'] is not None:
    print("Logging in...")
    args['token'] = login(args['username'], args['password'])
    del args['password']
    del args['username']


result = None
if args['action'] in methods:
    print("Starting...\n")
    args['action'] = methods[args['action']]
    if args['action'] == "uploadapi":
        result = upload(args)
    else:
        result = api_do(args)
else:
    print("Action not recognized.")

if result is not None:
    for field in parse_info(result):
        print("%s: %s" % (field.tag.capitalize(), field.text))

print()
