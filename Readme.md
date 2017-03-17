# Simple mutual endebtment manager on your home server for peaceful housesharing.


Built with simplicity on mind. No database, only editable csv files.

## [Demo](https://lambda.casa/endebts/)

## Install
Built with Flask

    pip install Flask
    pip install flask_babel

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

You cannot edit a transaction, just add the correct one and remove the unnecessary one(s) with the swipe icon at the bottom.

et hop !


## General syntax of csv history files:

* {tabulation} to separate fields
* "#" starting line for commented line
* "," to separate names (no spaces after it !)
* "." for decimal notation (not ",")

[Source](https://github.com/webplate/endebts)
