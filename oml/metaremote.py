# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import json
from urllib.parse import urlencode

from ox.cache import read_url

import logging
logger = logging.getLogger('metaremote')

def request(action, data):
        data = urlencode({
            'action': action,
            'data': json.dumps(data)
        })
        url = 'http://meta.openmedialibrary.com/api/'
        try:
            return json.loads(read_url(url, data, timeout=60).decode('utf-8'))['data']
        except:
            return {}

def find(query):
    logger.debug('find %s', query)
    return request('findMetadata', {'query': query})['items']

def lookup(key, value):
    logger.debug('lookup %s %s', key, value)
    return request('getMetadata', {key: value})
