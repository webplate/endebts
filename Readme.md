# Simple mutual endebtment manager on your home server for peaceful housesharing.

    https://github.com/webplate/endebts

Buit with simplicity on mind. No database, only editable csv files.

## Demo

    https://lambda.casa/endebts/

## Install
Built with Flask

    sudo pip install Flask

Copy files to /var/www/endebts/

It's a wsgi app, to run it simply install apache and mod_wsgi.

    sudo apt-get install apache2 python-setuptools libapache2-mod-wsgi

Create apache configuration file in /etc/apache2/sites-available/endebts.conf :

    LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi.so

    WSGIDaemonProcess endebts user=www-data group=www-data threads=5
    WSGIScriptAlias /endebts /var/www/endebts/endebts.wsgi

    <Directory /var/www/endebts>
        WSGIProcessGroup endebts
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>

## Configure

Set the PATH to store csv files in _config.py_
It must be writable for _www-data_ user.

## Activate and restart:

    sudo a2ensite endebts.conf
    sudo service apache2 restart

## Use it

Visit :

    http://localhost/endebts/anyalphanumericstring

Add some users to get started.


et hop !


## General syntax of csv history file:

* {tabulation} to separate fields
* "#" starting line for commented line
* "," to separate names (no spaces after it !)
* "." for decimal notation (not ",")

