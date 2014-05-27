import time

class Cache(dict):

    def __init__(self, ttl=10):
        self._ttl = ttl
        self._added = {}

    def get(self, key):
        if key in self._added:
            if self._added[key] < time.time():
                del self._added[key]
                del self[key]
                return
            return dict.__getitem__(self, key)

    def set(self, key, value, ttl=None):
        ttl = ttl or self._ttl
        self._added[key] = time.time() + ttl
        dict.__setitem__(self, key, value)

    def delete(self, key):
        if key in self._addedd:
            del self._added[key]
            del self[key]
