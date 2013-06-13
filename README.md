dev-host-cl
===========
dev-host-cl is a python script that allows you to upload and manage files to
http://d-h.st (Dev-Host) from a shell. It can be used anonymously or using
your account credentials.

Download
========
You can directly download and place the script in ~/bin to use directly.
For example:

         $ git clone git://github.com/GermainZ/dev-host-cl.git dev-host-cl
         $ cp dev-host-cl/devhost.py ~/bin/devhost
         $ chmod +x ~/bin/devhost

Replace ````devhost.py```` by ````devhost-py2.py```` if you use python2.

Usage
=====
* Syntax: ````devhost [-h] [-u USERNAME] [-p PASSWORD] ACTION ...````
* Actions:
    * ````upload```` - Upload file (anonymously if no credentials are specified)
    * For the actions below, you must be the owner of the file and use your
    credentials to login, unless otherwise noted:
        * ````file-get-info```` - Get file info (public files need no authentication)
        * ````file-set-info```` - Set file info
        * ````file-delete```` - Delete file
        * ````file-move```` - Move file
    * For more help about an action: 
         ````devhost ACTION -h````
* Example (to upload a file Anonymously):
         ````devhost upload file.txt````

Dependencies
============
* python3 or python2 (http://python.org/)
* python-requests or python2-requests (http://python-requests.org/)
* python-lxml or python2-lxml (http://lxml.de/)

Todo
====
* Add options for:
    * Folder getinfo, setinfo, delete, move, create, content

Notes
=====
* It's not possible to have streaming uploads with the requests module and d-h.
  This means the whole file is loaded into your memory before being uploaded.
  I might look into other modules if I have the time, but it's not a priority
  at the moment.
* The python2 version of the script is created using the excellent 3to2 script,
  with only minor extra modifications from my part. You can find 3to2 here:
  https://pypi.python.org/pypi/3to2
