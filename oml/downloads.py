# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from threading import Thread
import time
import logging

import state

logger = logging.getLogger('oml.downloads')

class Downloads(Thread):

    def __init__(self, app):
        self._app = app
        self._running = True
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def download_next(self):
        import item.models
        for t in item.models.Transfer.query.filter(
            item.models.Transfer.added!=None,
            item.models.Transfer.progress<1).order_by(item.models.Transfer.added):
            for u in t.item.users:
                if state.nodes.is_online(u.id):
                    logger.debug('DOWNLOAD %s %s', t.item, u)
                    r = state.nodes.download(u.id, t.item)
                    logger.debug('download ok? %s', r)
                    return True
        return False

    def run(self):
        time.sleep(2)
        with self._app.app_context():
            while self._running:
                if state.online:
                    self.download_next()
                    time.sleep(0.5)
                else:
                    time.sleep(20)

    def join(self):
        self._running = False
        self._q.put(None)
        return Thread.join(self)

