# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import logging

from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
from Queue import Queue
import json
from threading import Thread

from oxflask.shortcuts import json_dumps

import state

logger = logging.getLogger('oml.websocket')

class Background:

    def __init__(self, handler):
        self.handler = handler
        self.q = Queue()
        self.connected = True
        self.main = IOLoop.instance()

    def worker(self):
        while self.connected:
            message = self.q.get()
            action, data = json.loads(message)
            import item.scan
            if action == 'ping':
                self.post(['pong', data])
            elif action == 'import':
                item.scan.run_import(data)
            elif action == 'scan':
                item.scan.run_scan()
            elif action == 'update':
                self.post(['error', {'error': 'not implemented'}])
            else:
                self.post(['error', {'error': 'unknown action'}])
            self.q.task_done()

    def join(self):
        self.q.join()

    def put(self, data):
        self.q.put(data)

    def post(self, data):
        if not isinstance(data, basestring):
            data = json_dumps(data)
        self.main.add_callback(lambda: self.handler.write_message(data))


class Handler(WebSocketHandler):
    background = None

    def open(self):
        if self.request.host not in self.request.headers['origin']:
            logger.debug('reject cross site attempt to open websocket %s', self.request)
            self.close()
        self.background = Background(self)
        state.websockets.append(self.background)
        self.t = Thread(target=self.background.worker)
        self.t.daemon = True
        self.t.start()

    #websocket calls
    def on_message(self, message):
        self.background.put(message)

    def on_close(self):
        if self.background:
            state.websockets.remove(self.background)
            self.background.connected = False

def trigger_event(event, data):
    if len(state.websockets):
        logger.debug('trigger event %s %s %s', event, data, len(state.websockets))
    for ws in state.websockets:
        try:
            ws.post([event, data])
        except:
            import traceback
            traceback.print_exc()
            logger.debug('failed to send to ws %s %s %s', ws, event, data)
