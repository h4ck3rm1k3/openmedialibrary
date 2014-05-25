# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import json
from ox.cache import read_url
from urllib import urlencode

import logging
logger = logging.getLogger('metaremote')

def request(action, data):
        data = urlencode({
            'action': action,
            'data': json.dumps(data)
        })
        url = 'http://meta.openmedialibrary.com/api/'
        try:
            return json.loads(read_url(url, data, timeout=60))['data']
        except:
            return {}

def find(query):
    logger.debug('find %s', query)
    return request('findMetadata', {'query': query})['items']

def lookup(key, value):
    logger.debug('lookup %s %s', key, value)
    return request('getMetadata', {key: value})
