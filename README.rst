SMIT
-----

Installation
==============

Install python3.6 64 bits from https://www.python.org/ftp/python/3.6.0/python-3.6.0-amd64.exe

Make sure to tick "Add Python to System PATH" in the installer settings.

Download SMIT from https://github.com/ksamuel/smit/archive/master.zip and unzip it where you wish.

Open a terminal in the SMIT directory, where the requirements.txt file is, and run::

    pip install -r requirements.txt

Start SMIT
===========

In the SMIT directory there is a .crossbar directory, containing a config.json file. You can start SMIT by running:

    crossbar start -c "absolute path to config file".

E.G::

    crossbar start -c "C:/SMIT/.crossbar/config.json"

The program will start.

You can begin using SMIT by opening a browser to: http:127.0.0.1:3333.

You should setup Windows to run the command when the computer starts.

Default parameters
======================

When the program starts, in the output, among other lines, you will see:

Starting to log in "path to a file.log"

This will be where the log file is.

Most settings are in the administration pages, and you will be greated with a prompt to enter them after your first login. The default login and password are "admin" and have administrators rights.

One setting is not in the administration pages: the SMIT port. You can change this in .crossbar/config.json.

After your first login, you should go to the administration pages (link at the top right of the SMIT dashboard) to change the default login and password. Then create users with no administrator rights and belonging to only either the pilot group, or the operator group.

Helping the user
================

You can add the SMIT url in the browser bookmarks, but you can also put shortcut on the desktop. To do so, create a text file named "SMIT.url", and containing::

    [InternetShortcut]
    URL=http://127.0.0.1:3333/
