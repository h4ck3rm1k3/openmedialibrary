# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import json
from urllib.parse import urlencode

from ox.cache import read_url

import settings

import logging
logger = logging.getLogger(__name__)

def request(action, data):
        data = urlencode({
            'action': action,
            'data': json.dumps(data)
        })
        url = 'http://meta.openmedialibrary.com/api/'
        try:
            return json.loads(read_url(url, data, timeout=60).decode('utf-8'))['data']
        except:
            logger.debug('metadata request failed', exc_info=1)
            return {}

def find(query):
    logger.debug('find %s', query)
    return request('findMetadata', {'query': query}).get('items', [])

def lookup(key, value):
    logger.debug('lookup %s %s', key, value)
    data = request('getMetadata', {key: value})
    for key in [k['id'] for k in settings.config['itemKeys'] if isinstance(k['type'], list)]:
        if key in data and not isinstance(data[key], list):
            data[key] = [data[key]]
    return data
