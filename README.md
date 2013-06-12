dev-host-cl
===========

Upload files to http://d-h.st (Dev-Host) from the command line.

Usage
=====

* Usage: devhost.py [-h] [-u USERNAME] [-p PASSWORD] [-d FILE_DESC]
                    [-c FILE_CODE] [-pb {0,1}] [-f UPLOAD_FOLDER]
                    file

* You can either upload as an Anonymous user or use your credentials to login.
  If no username & password combination is given, the file will be uploaded
  anonymously.

Dependencies
============
* python 2.x (http://python.org/)
* requests (http://python-requests.org/)
* lxml (http://lxml.de/)


Todo
====
* Add options other than uploading:
  * File getinfo, setinfo, delete, move
  * Folder getinfo, setinfo, delete, move, create, content

Notes
=====
It's not possible to have streaming uploads wuth the requests module and d-h.
This means the whole file will be loaded to your memory before being uploaded.
I might look into other modules if I have the time, but it's not a priority.
