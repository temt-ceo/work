#!/usr/bin/env python3
# coding: utf-8

import cgitb
cgitb.enable(display=0, logdir='log/server_error')

from wsgiref.handlers import CGIHandler
from flask_hosting import server

CGIHandler().run(server)