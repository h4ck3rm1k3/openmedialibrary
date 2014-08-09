#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import os
import sys

import api
import commands
import server

if len(sys.argv) > 1 and sys.argv[1] == 'server':
    server.run()
else:
    names = [c[8:] for c in dir(commands) if  c.startswith('command_')]
    command = sys.argv[1] if len(sys.argv) > 1 else None
    if command and command in names:
        getattr(commands, "command_%s"%command)(sys.argv[1:])
    else:
        print 'usage: %s [action]' % 'ctl'
        indent = max([len(command) for command in names]) + 4
        for command in sorted(names):
            space = ' ' * (indent - len(command))
            info = getattr(commands, "command_%s"%command).__doc__.split('\n')
            info = ['  %s%s' % (' ' * indent, i.strip()) for i in info]
            info = '\n'.join(info).strip()
            print "  %s%s%s"%(command, space, info)
        sys.exit(1)
