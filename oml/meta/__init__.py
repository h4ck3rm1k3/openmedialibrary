# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import stdnum.isbn
import ox

from . import abebooks
from . import loc
from . import lookupbyisbn
from . import openlibrary
from . import worldcat
from . import google
from . import duckduckgo

from oml import settings

import logging
logger = logging.getLogger(__name__)


providers = [
    ('openlibrary', 'olid'),
    ('loc', 'lccn'),
    ('worldcat', 'oclc'),
    ('worldcat', 'isbn'),
    ('lookupbyisbn', 'asin'),
    ('lookupbyisbn', 'isbn'),
    ('abebooks', 'isbn')
]

def find(query):
    #results = google.find(query)
    results = duckduckgo.find(query)
    '''
    results = openlibrary.find(query)
    for r in results:
        r['primaryid'] = 'olid'
    '''
    return results

def lookup_provider(arg):
    provider, id, ids, key, value = arg
    values = set()
    for key, value in ids:
        if key == id or provider in ('openlibrary', ):
            for kv in globals()[provider].get_ids(key, value):
                values.add(kv)
    return values

def lookup(key, value):
    if not isvalid_id(key, value):
        return {}
    data = {key: [value]}
    ids = set([(key, value)])
    provider_data = {}
    done = False

    while not done:
        done = True
        for provider, id in providers:
            result = lookup_provider((provider, id, ids, key, value))
            done = not result - ids
            ids.update(result)
    logger.debug('FIXME: sort ids')
    ids = sorted(ids, key=lambda i: ox.sort_string(''.join(i)))
    logger.debug('IDS %s', ids)
    for k, v in ids:
        for provider, id in providers:
            if id == k:
                if provider not in provider_data:
                    provider_data[provider] = {}
                for k_, v_ in globals()[provider].lookup(v).items():
                    if k_ not in provider_data[provider]:
                        provider_data[provider][k_] = v_
    for provider in sorted(
        list(provider_data.keys()),
        key=lambda x: -len(provider_data[x])
    ):
        logger.debug('%s %s %s', provider, len(provider_data[provider]), list(provider_data[provider].keys()))
        for k_, v_ in provider_data[provider].items():
            if not k_ in data:
                data[k_] = v_
    for k, v in ids:
        if k not in data:
            data[k] = []
        if v not in data[k]:
            data[k].append(v)
    for key in [k['id'] for k in settings.config['itemKeys'] if isinstance(k['type'], list)]:
        if key in data and not isinstance(data[key], list):
            data[key] = [data[key]]
    return data

def isvalid_id(key, value):
    if key == 'isbn':
        if len(value) not in (10, 13) or not stdnum.isbn.is_valid(value):
            return False
    if key == 'asin' and len(value) != 10:
        return False
    if key == 'olid' and not (value.startswith('OL') and value.endswith('M')):
        return False
    return True

