#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import sys

import api
import commands
import server

if len(sys.argv) > 1 and sys.argv[1] == 'server':
    server.run()
else:
    commands.main()
