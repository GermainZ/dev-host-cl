#!/usr/bin/env python

# dev-host-cl Copyright (c) 2013 by GermainZ <germanosz@gmail.om>
# Cross Python Version Copyright (c) 2014 by Cybojenix <anthonydking@slimroms.net>
# Requirements: python 2.6 - 3.x
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

from __future__ import division, print_function
import xml.etree.ElementTree as ET
from getpass import getpass
from sys import version_info, exc_info
import os
import binascii
import argparse
import time
import json
import threading
import signal

try:
    from requests import get, post
    import requests.exceptions
except ImportError:
    print("The requests module is required to use this script.")
    exit(1)

def arg_parser():
    """Parse command line arguments, and return a dict containing them."""
    # Create the top level parser
    parser = argparse.ArgumentParser(description=("d-h.st (Dev-Host) command"
                                                  "line tool"))
    parser.add_argument('-u', "--username",
                        help=("Username. If none is provided, uploads are"
                              " done anonymously, and only public files are"
                              " accessible"))
    parser.add_argument('-p', "--password",
                        help=("Password. If only a username is provided, the"
                              " user will be prompted for one without it"
                              " appearing on the screen"))
    subparsers = parser.add_subparsers(metavar="ACTION", dest="action",
                                       help="Use %(prog)s ACTION -h for help")
    # Parent parsers
    # We use a parent parser to get the user's info again so that args can be
    # after the actions too. For example, this would raise an unknown arg error
    # otherwise:
    # devhost.py upload file.txt -u myusername -p mypassword
    parser_u = argparse.ArgumentParser(add_help=False)
    parser_u.add_argument('-u', "--username",
                          help=("Username. If none is provided, uploads are"
                                " done anonymously, and only public files are"
                                " accessible"))
    parser_u.add_argument('-p', "--password",
                          help=("Password. If only a username is provided, the"
                                " user will be prompted for one without it"
                                " appearing on the screen"))
    # Other parent parsers
    parser_c = argparse.ArgumentParser(add_help=False)
    parser_c.add_argument("file_code", metavar="file-code",
                          help=("File code of an existing file. Multiple file"
                                " code may be specified for certain commands"
                                " (separated by commas, without spaces)"))
    parser_fo = argparse.ArgumentParser(add_help=False)
    parser_fo.add_argument("folder_id", metavar="folder-id",
                           help="ID of an existing folder")
    # Create the parser for the "upload" command
    parser_upload = subparsers.add_parser("upload", parents=[parser_u],
                                          help="Upload file")
    parser_upload.add_argument("my_file", type=argparse.FileType('rb'),
                               metavar="file", help="File to upload")
    parser_upload.add_argument('-d', "--file-desc", help="Description of file")
    parser_upload.add_argument('-c', "--file-code",
                               help=("File code of an existing file to update/"
                                     "replace"))
    parser_upload.add_argument('-pb', "--public", choices=['0', '1'],
                               default='0', help=("File is public or private,"
                                                  " 0 - private, 1 - public"))
    parser_upload.add_argument('-f', "--upload-folder", dest="uploadfolder",
                               default='0',
                               help=("Folder id to upload file to. The root"
                                     " folder is chosen by default"))
    # Create the parser for the "get-file-info" command
    subparsers.add_parser("file-get-info", parents=[parser_c, parser_u],
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
    parser_setf.add_argument('-f', "--folder-id",
                             help="Use to change the file's folder")
    # Create the parser for the "file-delete" command
    subparsers.add_parser("file-delete", parents=[parser_c, parser_u],
                          help="Delete file")
    # Create the parser for the "file-move" command
    parser_mvf = subparsers.add_parser("file-move",
                                       parents=[parser_c, parser_u],
                                       help="Move file")
    parser_mvf.add_argument('-f', "--folder-id",
                            help=("Use if you want to change the folder."
                                  " Specify folder_id or 0 for root directory"))
    # Create the parser for the "get-folder-info" command
    subparsers.add_parser("folder-get-info", parents=[parser_fo, parser_u],
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
                              help=("Use to change the parent folder. Specify"
                                    " the folder ID or 0 for root directory"))
    # Create the parser for the "folder-delete" command
    subparsers.add_parser("folder-delete", parents=[parser_fo, parser_u],
                          help="Delete folder")
    # Create the parser for the "folder-move" command
    parser_mvfo = subparsers.add_parser("folder-move",
                                        parents=[parser_fo, parser_u],
                                        help="Move folder")
    parser_mvfo.add_argument('-f', "--parent-folder-id",
                             help=("Use if you want to change the folder."
                                   " Specify the folder ID or 0 for root"
                                   " directory"))
    # Create the parser for the "folder-create" command
    parser_cfo = subparsers.add_parser("folder-create",
                                       parents=[parser_u],
                                       help="Create folder")
    parser_cfo.add_argument("name", metavar="folder-name",
                            help="Folder name")
    parser_cfo.add_argument('-d', "--folder-desc", dest="description",
                            help="Folder description")
    parser_cfo.add_argument('-f', "--parent-folder-id",
                            help="Create the folder inside this one")
    # Create the parser for the "folder-content" command
    parser_confo = subparsers.add_parser("folder-content",
                                         parents=[parser_fo, parser_u],
                                         help="Get folder content")
    parser_confo.add_argument("--user",
                              help=("Username of the person you want to"
                                    " retrieve the folder's content for"))
    parser_confo.add_argument("--user-id",
                              help=("User ID of the person you want to"
                                    " retrieve the folder content for"))
    # Parse the args and return them as a dict
    args = parser.parse_args()
    if args.action is None:
        parser.print_help()
        exit(0)
    return vars(args)

def h_empty(s):
    """Substitute keyword and return repetitive help message for arg parser"""
    s = ("Use to change the {0}. Choosing an empty value \"\" will"
         " clear the data.").format(s)
    return s

def pretty_print(result):
    """Print XML object line by line, capitalizing the tag"""
    try:
        for field in parse_info(result):
            print("{0}: {1}".format(field.tag.capitalize(), field.text))
    except ET.ParseError:
        print("Something went wrong. Here's the raw result we got back:")
        print(result)

def login(username, password):
    """Login and return the token, which is used for identification.

    The token lasts for one hour.

    """
    args = {'action': "user/auth", 'user': username, 'pass': password}
    resp = api_do(args)
    resp = ET.XML(resp)
    try:
        token = resp.findall(".//token")[0].text
    except IndexError:
        pretty_print(ET.tostring(resp))
        exit(1)
    return token

def parse_info(xml):
    """Parse XML and return its elements as a list"""
    xml = ET.XML(xml)
    return xml.findall(".//*")

def upload(args):
    """Handle file upload

    Generate XID, build request and call the upload_file method.
    Also run get_progress as a thread to print the progress from the server.

    """
    xid = binascii.hexlify(os.urandom(8))
    if version_info >= (3, 0):
        xid = xid.decode()
    files_data = {'file': args.pop('my_file')}
    if 'file_desc' in args:
        args['file_description[]'] = args.pop('file_desc')
    if 'file_code' in args:
        args['file_code[]'] = args.pop('file_code')
    upload_data = args
    # Get and print the progress using a daemon thread
    t = threading.Thread(target=get_progress, args=(xid,))
    t.daemon = True
    t.start()
    result = upload_file(files_data, upload_data, xid)
    return result

def upload_file(files_data, upload_data, xid=None):
    """Upload file and return the parsed response"""
    # xid is optional, and can be used to track progress
    url = 'http://api.d-h.st/upload'
    if xid is not None:
        url = '{0}?X-Progress-ID={1}'.format(url, xid)
    r = post(url, data=upload_data, files=files_data)
    return r.content

def get_progress(xid):
    """Prints the upload's progress, using the xid

    This should be run in a separate thread.

    """
    url = 'http://api.d-h.st/progress?X-Progress-ID={0}'.format(xid)
    # Wait a bit more before getting the progress for the first time. This is
    # to (hopefully) avoid the "Max retries exceeded" error, which seems to
    # happen when we request the progress too many times while the the upload
    # is still starting.
    time.sleep(5)
    while True:
        # We're getting the progress from the website, so there's a slight
        # traffic overhead, which is why we're waiting a few seconds between
        # refreshes.
        time.sleep(5)
        try:
            request = get(url)
        # It doesn't matter if we fail to get the progress, as long as
        # the upload is still going on. Should that fail, this thread will
        # terminate anyway.
        except requests.exceptions:
            continue
        except Exception:
            e = exc_info()[1]
            print("An error has occured: {0}".format(repr(e)))
            print("Continuing...")
            continue
        resp = request.content.strip()[1:-2]
        progress = json.loads(resp.decode())
        if progress.get('state') == "uploading":
            percentage = progress.get('received') / progress.get('size') * 100
            percentage = '{n:.{d}f}'.format(n=percentage, d=2)
            print("Progress: {0}%".format(percentage), end='\r')
        elif progress.get('state') == "starting":
            pass
        else:
            print(progress.get('state'))

def api_do(args):
    """Generates a URL using the passed args, gets the data from it,
    and returns the content of the response

    Refer to the gen_url docstring for more info.

    """
    url = gen_url(args)
    try:
        r = get(url)
    except requests.exceptions:
        print(exc_info()[1])
        exit(1)
    return r.content

def gen_url(args):
    """Generate a URL using the keys/values of args, and return it

    args is a dict that has the following items:
    'action': one of "file/getinfo", "file/setinfo", "file/delete",
              "file/move", "folder/getinfo", "folder/setinfo", "folder/delete",
              "folder/move", "folder/create", "folder/content"
    'parameter': parameter value

    For example, to delete a file:
      args = {'action': "file/delete", 'token': token, 'file_code': "ygH"}

    Refer to the Dev-Host API for more information.

    """
    url = "http://d-h.st/api/{0}".format(args['action'])
    del args['action']
    params = "&".join("%s=%s" % i for i in args.items())
    return "?".join((url, params))

def signal_handler(signal, frame):
    """Handle SIGINT"""
    print("\nAborted by user.")
    exit(0)

def clean_dict(args):
    """Remove None items from the dict and return it"""
    result = {}
    result.update((k, v) for k, v in args.items() if v is not None)
    return result


def main():
    args = arg_parser()
    args = clean_dict(args)
    signal.signal(signal.SIGINT, signal_handler)
    methods = {'upload': "uploadapi", 'file-get-info': "file/getinfo",
               'file-set-info': "file/setinfo", 'file-delete': "file/delete",
               'file-move': "file/move", 'folder-get-info': "folder/getinfo",
               'folder-set-info': "folder/setinfo", 'folder-delete':
               "folder/delete", 'folder-move': "folder/move", 'folder-create':
               "folder/create", 'folder-content': "folder/content"}
    if 'username' in args:
        if 'password' not in args:
            args['password'] = getpass("Password? ")
        print("Logging in...")
        args['token'] = login(args['username'], args['password'])
        del args['password']
        del args['username']
    elif 'password' in args:
        del args['password']
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
        pretty_print(result)

if __name__ == "__main__":
    main()

