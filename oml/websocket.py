# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
import json

from oxtornado import json_dumps

import state

import logging
logger = logging.getLogger('oml.websocket')


class Handler(WebSocketHandler):

    def check_origin(self, origin):
        # allow access to websocket from site, installer and loader (local file)
        return self.request.host in origin or \
            origin in ('http://127.0.0.1:9842', 'null', 'file:///')

    def open(self):
        if self.request.headers['origin'] not in ('null', 'http://127.0.0.1:9842') \
            and self.request.host not in self.request.headers['origin']:
            logger.debug('reject cross site attempt to open websocket %s', self.request)
            self.close()
        if self not in state.websockets:
            state.websockets.append(self)


    #websocket calls
    def on_message(self, message):
        action, data = json.loads(message)
        if state.tasks:
            state.tasks.queue(action, data)

    def on_close(self):
        if self in state.websockets:
            state.websockets.remove(self)

    def post(self, event, data):
        message = json_dumps([event, data])
        main = IOLoop.instance()
        main.add_callback(lambda: self.write_message(message))

def trigger_event(event, data):
    if len(state.websockets):
        logger.debug('trigger event %s %s %s', event, data, len(state.websockets))
    for ws in state.websockets:
        try:
            ws.post(event, data)
        except:
            logger.debug('failed to send to ws %s %s %s', ws, event, data, exc_info=1)
