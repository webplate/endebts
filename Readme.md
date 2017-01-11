# Simple mutual endebtment manager on your home server for peaceful housesharing.

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

Activate and restart:

    sudo a2ensite endebts.conf
    sudo service apache2 restart

Reload it and visit http://localhost/endebts

Add some users to get started.


et hop !
