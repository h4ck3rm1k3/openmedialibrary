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
        for i in item.models.Item.query.filter(
                item.models.Item.transferadded!=None).filter(
                item.models.Item.transferprogress<1).order_by(item.models.Item.transferadded):
            logger.debug('DOWNLOAD %s %s', i, i.users)
            for p in i.users:
                if state.nodes.check_online(p.id):
                    r = state.nodes.download(p.id, i)
                    logger.debug('download ok? %s', r)
                    return True
        return False

    def run(self):
        time.sleep(2)
        with self._app.app_context():
            while self._running:
                if state.online:
                    self.download_next()
                    time.sleep(10)
                else:
                    time.sleep(20)

    def join(self):
        self._running = False
        self._q.put(None)
        return Thread.join(self)

