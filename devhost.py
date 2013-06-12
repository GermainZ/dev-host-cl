#!/usr/bin/env python3
from requests import session
from lxml import etree
import os
import binascii
import argparse
import time
import json # Use json from requests instead?
import threading
import signal


def arg_parser():
    """Parses command line arguments, and returns a dict containing them."""
    parser = argparse.ArgumentParser(description='d-h.st (Dev-Host) command line tool')
    parser.add_argument('my_file', type=argparse.FileType('rb'), metavar='file', help='File to upload')
    parser.add_argument('-u', '--username', help='Username')
    parser.add_argument('-p', '--password', help='Password')
    parser.add_argument('-d', '--file-desc', help='Description of file')
    parser.add_argument('-c', '--file-code', help='File code of an existing file to update/replace')
    parser.add_argument('-pb', '--public', choices=['0', '1'], default='0', help='File is public or private, 0 - private, 1 - public')
    parser.add_argument('-f', '--upload-folder', default='0', help='Folder id to upload file too or specify 0 for root or leave blank implies root (0); if file_code is specified and valid then the location of the the file will change to the folder id specified')
    args = parser.parse_args()
    return vars(args)

def upload_file(files_data, upload_data, xid):
    """Uploads file and returns parsed response."""
    # xid is optional, and can be used to track progress
    if xid is None:
        url = 'http://api.d-h.st/upload'
    else:
        url = 'http://api.d-h.st/upload?X-Progress-ID=%s' % xid
    print("STARTING UPLOAD")
    time.sleep(1)
    r = s.post(url, data=upload_data, files=files_data)
    # Parse the response, format then return it
    resp = etree.XML(r.content)
    result = []
    for field in resp.xpath("//file_info/*"):
        result.append( "%s: %s" % (field.tag, field.text))
    return result
 
def gen_data(args, xid, token):
    """Constructs data needed for the HTTP POST request."""
    files_data = {'file': args['my_file']}
    upload_data = {'action': "uploadapi", 'token': token,
                   'public': args['public'],
                   'upload_folder': args['upload_folder'],
                   'file_description[]': args['file_desc'],
                   'file_code[]': args['file_code']}
    return files_data, upload_data

def login(username, password):
    """Login and return the token, which is used for identification."""
    request = s.get('http://d-h.st/api/user/auth?user=%s&pass=%s' % (username, password))
    content = request.content
    resp = etree.XML(content)
    token = resp.xpath('//token/text()')[0]
    return token

def get_progress(xid):
    """Gets the upload's progress, using the xid."""
    while True:
        time.sleep(5)
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

def signal_handler(signal, frame):
    """Handles SIGINT"""
    print("\nAborted by user")
    exit(0)


signal.signal(signal.SIGINT, signal_handler)
s = session()
args = arg_parser()

def upload(args):
    """Handles file upload.
    
    Optionally handles authentication. Generates XID, builds request and calls
    the upload_file method. Also runs get_progress as a thread to periodically
    get the progress from the server.
    """
    token = None
    xid = None
    if args['username'] is not None and args['password'] is not None:
        print("Logging in...")
        token = login(args['username'], args['password'])
    print("Uploading...\n")
    xid = binascii.hexlify(os.urandom(8))
    files_data, upload_data = gen_data(args, xid, token)
    t = threading.Thread(target=get_progress, args=(xid,))
    t.daemon = True
    t.start()
    result = upload_file(files_data, upload_data, xid)
    print('\n')
    for line in result:
        print(line)

# Upload is the only function of this script right now, but this is likely to
# change in the future.
upload(args)
