#!/usr/bin/python
# -*- coding: utf-8 -*-
from wsgiref.simple_server import make_server
from server import app

httpd = make_server('', 5000, app)
print "Serving HTTP on port 5000..."

# Respond to requests until process is killed
httpd.serve_forever()
