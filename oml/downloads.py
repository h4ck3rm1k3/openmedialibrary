# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from threading import Thread
import time

import db
import state
import settings
import update

from websocket import trigger_event

import logging
logger = logging.getLogger(__name__)

class Downloads(Thread):

    def __init__(self):
        self._running = True
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def download_updates(self):
        now = int(time.mktime(time.gmtime()))
        if now > settings.server.get('last_update_check', 0) + 24*60*60:
            settings.server['last_update_check'] = now
            update.download()

    def download_next(self):
        import item.models
        self.download_updates()
        for t in item.models.Transfer.query.filter(
            item.models.Transfer.added!=None,
            item.models.Transfer.progress<1).order_by(item.models.Transfer.added):
            if not self._running:
                return False
            for u in t.item.users:
                if state.nodes.is_online(u.id):
                    logger.debug('DOWNLOAD %s %s', t.item, u)
                    r = state.nodes.download(u.id, t.item)
                    logger.debug('download ok? %s', r)
                    return True
        return False

    def run(self):
        time.sleep(2)
        with db.session():
            while self._running:
                self.download_next()
                time.sleep(0.5)

    def join(self):
        self._running = False
        return Thread.join(self)

class ScrapeThread(Thread):

    def __init__(self):
        self._running = True
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def scrape_queue(self):
        import item.models
        scraped = False
        for s in item.models.Scrape.query.filter(
            item.models.Scrape.added!=None,
        ).order_by(item.models.Scrape.added):
            if not self._running:
                return True
            logger.debug('scrape %s', s.item)
            try:
                if s.item.scrape():
                    for f in s.item.files:
                        f.move()
                    s.item.update_icons()
                    s.remove()
                    trigger_event('change', {})
                scraped = True
            except:
                logger.debug('scrape failed %s', s.item, exc_info=1)
        return scraped

    def run(self):
        time.sleep(2)
        with db.session():
            while self._running:
                if not self.scrape_queue():
                    time.sleep(1)

    def join(self):
        self._running = False
        return Thread.join(self)
