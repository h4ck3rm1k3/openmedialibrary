# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from ox.cache import read_url
import json

from marc_countries import COUNTRIES
from utils import normalize_isbn

def get_ids(key, value):
    ids = []
    if key == 'olid':
        data = lookup(value, True)
        for id in ('isbn10', 'isbn13', 'lccn', 'oclc'):
            if id in data:
                for v in data[id]:
                    if (id, v) not in ids:
                        ids.append((id, v))
    elif key in ('isbn10', 'isbn13'):
        print 'openlibraryid.get_ids', key, value
        r = find('isbn:%s' % value)
        for d in sorted(r.get('docs', []), key=lambda d: -d['last_modified_i']):
            if 'edition_key' in d:
                v = d['edition_key']
                if isinstance(v, list):
                    v = v[0]
                for kv in [('olid', v)] + get_ids('olid', v):
                    if kv not in ids:
                        ids.append(kv)
    if ids:
        print 'openlibraryid.get_ids', key, value
        print ids
    return ids

def lookup(id, return_all=False):
    #print 'openlibrary.lookup', id
    data = {
        'olid': id
    }
    url = 'https://openlibrary.org/books/%s.json' % id
    info = json.loads(read_url(url))
    keys = {
        'title': 'title',
        'authors': 'author',
        'publishers': 'publisher',
        'languages': 'language',
        'publish_places': 'place',
        'publish_country': 'country',
        'covers': 'cover',
        'isbn_10': 'isbn10',
        'isbn_13': 'isbn13',
        'lccn': 'lccn',
        'oclc_numbers': 'oclc',
        'dewey_decimal_class': 'classification',
        'number_of_pages': 'pages',
    }
    for key in keys:
        if key in info:
            value = info[key]
            if key == 'authors':
                value = authors(value)
            elif key == 'publish_country':
                value = COUNTRIES.get(value, value)
            elif key == 'covers':
                value = 'https://covers.openlibrary.org/b/id/%s.jpg' % value[0]
                value = COUNTRIES.get(value, value)
            elif key == 'languages':
                value = languages(value)
            elif not return_all and isinstance(value, list) and key not in ('publish_places'):
                value = value[0]
            if key in ('isbn_10', 'isbn_13'):
                if isinstance(value, list):
                    value = map(normalize_isbn, value)
                else:
                    value = normalize_isbn(value)
            data[keys[key]] = value
    return data

info = lookup

def find(query):
    url = 'https://openlibrary.org/search.json?q=%s' % query
    data = json.loads(read_url(url))
    return data

def authors(authors):
    return resolve_names(authors)

def resolve_names(objects, key='name'):
    r = []
    for o in objects:
        url = 'https://openlibrary.org%s.json' % o['key']
        data = json.loads(read_url(url))
        r.append(data[key])
    return r

def languages(languages):
    return resolve_names(languages)

