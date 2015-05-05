dev-host-cl
===========
dev-host-cl is a python script that allows you to upload and manage files to
http://d-h.st (Dev-Host) from a shell. It can be used anonymously or with
your account's credentials.

Warning
=======
dev-host-cl is now deprecated. This is due to changes in the Dev-Host service,
including but not limited to:

* An onslaught of ads.
* Fake download buttons styled in the same manner as the actual download
  buttons.
* The site being marked as untrustworthy by most major browser vendors,
  resulting in files not downloading.
* The slow service provided to unregistered users and free users.
* Dev-Host not responding to support requests when their API is broken or
  behaves differently than their documentation,
  [which also seems unmaintained](http://d-h.st/api).

In light of this, we will now warn the user when using this tool, and will
delay the program executing by 10 seconds.

To disable this, please use the
``--I-like-devhost-even-though-it-is-one-of-the-worst-services-around`` option.

If you're interested in alternatives, please check https://ptpb.pw/ or
https://pomf.se/ for smaller downloads (<60M and <50M respectively), or
https://androidfilehost.com/
Download
========
You can download and place the script in ~/bin to use it directly.
For example:

         $ git clone git://github.com/GermainZ/dev-host-cl.git dev-host-cl
         $ cp dev-host-cl/devhost.py ~/bin/devhost
         $ chmod +x ~/bin/devhost

Usage
=====
* Syntax: ````devhost [-h] [-u USERNAME] [-p PASSWORD] ACTION ...````
* If only a username is specified, the password will be prompted for without having it display on screen.
* Actions:
    * ````upload```` - Upload file (anonymously if no credentials are specified)
    * For the actions below, you must be the owner of the file and use your
    credentials to login, unless otherwise noted:
        * ````file-get-info```` - Get file info (public files need no authentication)
        * ````file-set-info```` - Set file info
        * ````file-delete```` - Delete file
        * ````file-move```` - Move file
        * ````folder-get-info```` - Return folder info (public folders need no authentication)
        * ````folder-set-info```` - Set folder info
        * ````folder-delete```` - Delete folder
        * ````folder-move```` - Move folder
        * ````folder-create```` - Create new folder
        * ````folder-content```` - Return folder content (public folders need no authentication)
    * For more help about an action: 
         ````devhost ACTION -h````
* Example (to upload a file Anonymously):
         ````devhost upload file.txt````

Dependencies
============
* python3 or python2 (http://python.org/)
* python-requests or python2-requests (http://python-requests.org/)

Installing python-requests
==========================
If you have root, Use pip, easy_install or your package manager to install
requests
```shell
pip install requests
easy_install requests
apt-get install python-requests
pacman -S python-requests
```

If you do not have root, then install requests locally
```shell
curl -L https://github.com/kennethreitz/requests/tarball/master | tar xz
cd kennethreitz-requests*
python setup.py install --user
cd ..
rm -rf master kennethreitz-requests*
```

Notes
=====
* It's not possible to have streaming uploads with the requests module and d-h.
  This means the whole file is loaded into your memory before being uploaded.
  I might look into other modules if I have the time, but it's not a priority
  at the moment.
