# Simple mutual endebtment manager on your home server for peaceful housesharing.

Built with Flask

    pip install Flask

Copy files to /var/www/endebts/

It's a wsgi app, to run it simply install apache and mod_wsgi.

Then set apache :

    LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi.so

    <VirtualHost *:80>
            ServerAdmin webmaster@localhost

            ServerName example.org

            WSGIDaemonProcess endebts user=www-data group=www-data threads=5
            WSGIScriptAlias /endebts /var/www/endebts/endebts.wsgi

            <Directory /var/www/endebts>
                WSGIProcessGroup endebts
                WSGIApplicationGroup %{GLOBAL}
                Order deny,allow
                Allow from all
            </Directory>

    </VirtualHost>

Reload it and visit http://localhost/endebts

Add some users to get started.


et hop !
