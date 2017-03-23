SMIT
-----

Installation
==============

Install python3.6 64 bits from https://www.python.org/ftp/python/3.6.0/python-3.6.0-amd64.exe

Make sure to tick "Add Python to System PATH" in the installer settings.

Install the Microsoft compiler from http://landinghub.visualstudio.com/visual-cpp-build-tools.

It's a long and heavy install, but once SMIT is up and running, you can uninstall it if you wish to save disk space.

Download SMIT from https://github.com/ksamuel/smit/archive/master.zip and unzip it where you wish.

Open a terminal in the SMIT directory, where the requirements.txt file is, and run::

    py -3.6 -m pip install -r requirements.txt

Start SMIT
===========

In the SMIT directory there is a .crossbar directory. You can start SMIT by running:

    crossbar start --cbdir "absolute path to crossbar file".

E.G::

    crossbar start -c ""C:/Users/TEMP/Desktop/smit-master""

Use forward slashes, not backslaches.

The program will start.

You can begin using SMIT by opening a browser to: http:127.0.0.1:3333.

You should setup Windows to run the command when the computer starts.

Default parameters
======================

Most settings are in the administration pages, and you will be greated with a prompt to enter them after your first login. The default login and password are "admin" and have administrators rights.

One setting is not in the administration pages: the SMIT port. You can change this in .crossbar/config.json.

After your first login, you should go to the administration pages (link at the top right of the SMIT dashboard) to change the default login and password. Then create users with no administrator rights and belonging to only either the pilot group, or the operator group.

Helping the user
================

You can add the SMIT url in the browser bookmarks, but you can also put shortcut on the desktop. To do so, create a text file named "SMIT.url", and containing::

    [InternetShortcut]
    URL=http://127.0.0.1:3333/
