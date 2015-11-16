# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from queue import Queue
from threading import Thread

from websocket import trigger_event


import logging
logger = logging.getLogger('oml.tasks')

class Tasks(Thread):

    def __init__(self):
        self.q = Queue()
        self.connected = True
        Thread.__init__(self)
        self.daemon = True
        self.start()
        self.queue('scan')

    def run(self):
        import item.scan
        while self.connected:
            m = self.q.get()
            if m:
                try:
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
                except:
                    logger.debug('task failed', exc_info=1)
            self.q.task_done()

    def join(self):
        self.connected = False
        self.q.put(None)
        self.q.join()
        return Thread.join(self)

    def queue(self, action, data=None):
        self.q.put((action, data))

