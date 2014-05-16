# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import abebooks
import loc
import lookupbyisbn
import openlibrary
import worldcat
import google

providers = [
    ('openlibrary', 'olid'),
    ('loc', 'lccn'),
    ('worldcat', 'oclc'),
    ('lookupbyisbn', 'asin'),
    ('abebooks', 'isbn10')
]

def find(title, author=None, publisher=None, date=None):
    results = google.find(title=title, author=author, publisher=publisher, date=date)
    '''
    results = openlibrary.find(title=title, author=author, publisher=publisher, date=date)
    for r in results:
        r['mainid'] = 'olid'
    '''
    return results

def lookup(key, value):
    data = {key: value}
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
    print 'lookup %s=%s =>' % ids[0], ids
    for k, v in ids:
        for provider, id in providers:
            if id == k and provider not in provider_data:
                provider_data[provider] = globals()[provider].lookup(v)
    for provider in sorted(
        provider_data.keys(),
        key=lambda x: -len(provider_data[x])
    ):
        print provider, len(provider_data[provider]), provider_data[provider].keys()
        for k_, v_ in provider_data[provider].iteritems():
            if not k_ in data:
                data[k_] = v_
    return data


