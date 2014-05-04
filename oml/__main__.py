#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import sys


import app
import server

if len(sys.argv) > 1 and sys.argv[1] == 'server':
    import server
    server.run()
else:
    app.manager.run()
