# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import json

class pdict(dict):
    def __init__(self, path, defaults=None):
        self._path = None
        self._defaults = defaults
        if os.path.exists(path):
            with open(path) as fd:
                _data = json.load(fd)
                for key in _data:
                    self[key] = _data[key]
        self._path = path

    def _save(self):
        if self._path:
            with open(self._path, 'w') as fd:
                json.dump(self, fd, indent=1)

    def get(self, key, default=None):
        if default == None and self._defaults:
            default = self._defaults.get(key)
        return dict.get(self, key, default)

    def __getitem__(self, key):
        if key not in self and self._defaults and key in self._defaults:
            return self._defaults[key]
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._save()

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._save()

