# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from Queue import Queue
from threading import Thread

from websocket import trigger_event


import logging
logger = logging.getLogger('oml.websocket')

class Tasks(Thread):

    def __init__(self, app):
        self.q = Queue()
        self.connected = True
        self._app = app
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        import item.scan
        while self.connected:
            m = self.q.get()
            if m:
                print m
                action, data = m
                if action == 'ping':
                    trigger_event('pong', data)
                elif action == 'import':
                    item.scan.run_import(data)
                elif action == 'scan':
                    item.scan.run_scan()
                elif action == 'update':
                    trigger_event('error', {'error': 'not implemented'})
                else:
                    trigger_event('error', {'error': 'unknown action'})
            self.q.task_done()

    def join(self):
        self.connected = False
        self.put(None)
        self.q.join()
        return Thread.join(self)

    def queue(self, action, data):
        self.q.put((action, data))

