import state
from websocket import trigger_event

import logging
logger = logging.getLogger(__name__)

class Bandwidth(object):
    up = 0
    down = 0
    _last = {}

    def __init__(self):
        self.update()

    def update(self):
        bandwidth = {'up': self.up, 'down': self.down}
        if bandwidth != self._last:
            trigger_event('bandwidth', bandwidth)
            self._last = bandwidth
        self.up = 0
        self.down = 0
        state.main.call_later(1, self.update)

    def download(self, amount):
        self.down += amount

    def upload(self, amount):
        self.up += amount

