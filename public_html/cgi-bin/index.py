#!/usr/bin/env python3
# coding: utf-8

import site
site.addsitedir('/Users/taharatakashi/Library/Python/3.9/lib/python/site-packages')

import cgitb
cgitb.enable(display=0, logdir='log/server_error')

from wsgiref.handlers import CGIHandler
from flask_hosting import server

CGIHandler().run(server)