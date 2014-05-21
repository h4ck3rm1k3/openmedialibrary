# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import stdnum.isbn
import ox

import abebooks
import loc
import lookupbyisbn
import openlibrary
import worldcat
import google
import duckduckgo

import logging
logger = logging.getLogger('meta')


providers = [
    ('openlibrary', 'olid'),
    ('loc', 'lccn'),
    ('worldcat', 'oclc'),
    ('lookupbyisbn', 'asin'),
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

def lookup(key, value):
    if not isvalid_id(key, value):
        return {}
    data = {key: [value]}
    ids = [(key, value)]
    provider_data = {}
    done = False
    while not done:
        done = True
        for provider, id in providers:
            for key, value in ids:
                for kv in globals()[provider].get_ids(key, value):
                    if not kv in ids:
                        ids.append(kv)
                        done = False
    logger.debug('FIXME: sort ids')
    ids.sort(key=lambda i: ox.sort_string(u''.join(i)))
    logger.debug('IDS %s', ids)
    for k, v in ids:
        for provider, id in providers:
            if id == k:
                if provider not in provider_data:
                    provider_data[provider] = {}
                for k_, v_ in globals()[provider].lookup(v).iteritems():
                    if k_ not in provider_data[provider]:
                        provider_data[provider][k_] = v_
    for provider in sorted(
        provider_data.keys(),
        key=lambda x: -len(provider_data[x])
    ):
        logger.debug('%s %s %s', provider, len(provider_data[provider]), provider_data[provider].keys())
        for k_, v_ in provider_data[provider].iteritems():
            if not k_ in data:
                data[k_] = v_
    for k, v in ids:
        if k not in data:
            data[k] = []
        if v not in data[k]:
            data[k].append(v)
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

