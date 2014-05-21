# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from urllib import urlencode
from ox.cache import read_url
import json

from marc_countries import COUNTRIES
from dewey import get_classification
from utils import normalize_isbn

import logging
logger = logging.getLogger('meta.openlibrary')

KEYS = {
    'authors': 'author',
    'covers': 'cover',
    'dewey_decimal_class': 'classification',
    'isbn_10': 'isbn',
    'isbn_13': 'isbn',
    'lccn': 'lccn',
    'number_of_pages': 'pages',
    'languages': 'language',
    'oclc_numbers': 'oclc',
    'publish_country': 'country',
    'publish_date': 'date',
    'publishers': 'publisher',
    'publish_places': 'place',
    'series': 'series',
    'title': 'title',
}

def find(query):
    query = query.strip()
    logger.debug('find %s', query)
    r = api.search(query)
    results = []
    ids = [b for b in r.get('result', []) if b.startswith('/books')]
    books = api.get_many(ids).get('result', [])
    for olid, value in books.iteritems():
        olid = olid.split('/')[-1]
        book = format(value)
        book['olid'] = [olid]
        book['primaryid'] = ['olid', olid]
        results.append(book)
    return results


def get_ids(key, value):
    ids = []
    if key == 'olid':
        data = lookup(value)
        for id in ('isbn', 'lccn', 'oclc'):
            if id in data:
                for v in data[id]:
                    if (id, v) not in ids:
                        ids.append((id, v))
    elif key in ('isbn', 'oclc', 'lccn'):
        logger.debug('get_ids %s %s', key, value)
        if key == 'isbn':
            key = 'isbn_%s'%len(value)
        r = api.things({'type': '/type/edition', key: value})
        for b in r.get('result', []):
            if b.startswith('/books'):
                olid = b.split('/')[-1]
                for kv in [('olid', olid)] + get_ids('olid', olid):
                    if kv not in ids:
                        ids.append(kv)
    if ids:
        logger.debug('get_ids %s %s => %s', key, value, ids)
    return ids

def lookup(id, return_all=False):
    #print 'openlibrary.lookup', id
    info = api.get('/books/' + id).get('result', {})
    #url = 'https://openlibrary.org/books/%s.json' % id
    #info = json.loads(read_url(url))
    data = format(info, return_all)
    if 'olid' not in data:
        data['olid'] = []
    if id not in data['olid']:
        data['olid'] = [id]
    logger.debug('lookup %s => %s', id, data.keys())
    return data

def format(info, return_all=False):
    data = {}
    if 'works' in info:
        work = api.get(info['works'][0]['key'])['result']
    else:
        work = None
    for key in KEYS:
        if key in info:
            value = info[key]
            if key == 'authors':
                if work:
                    value = resolve_names([r['author']
                        for r in work['authors'] if r['type']['key'] == '/type/author_role'])
                else:
                    value = resolve_names(value)
            elif key == 'publish_country':
                value = value.strip()
                value = COUNTRIES.get(value, value)
            elif key == 'covers':
                value = 'https://covers.openlibrary.org/b/id/%s.jpg' % value[0]
            elif key == 'languages':
                value = resolve_names(value)
            elif key in ('isbn_10', 'isbn_13'):
                if not isinstance(value, list):
                    value = [value]
                value = map(normalize_isbn, value)
                if KEYS[key] in data:
                    value = data[KEYS[key]] + value
            elif isinstance(value, list) and key not in ('publish_places', 'lccn', 'oclc_numbers'):
                value = value[0]
            data[KEYS[key]] = value
    if 'subtitle' in info:
        data['title'] += ' ' + info['subtitle']
    if 'classification' in data:
        value = data['classification']
        if isinstance(value, list):
            value = value[0]
        data['classification'] = get_classification(value.split('/')[0])
    return data

def resolve_names(objects, key='name'):
    r = []
    data = api.get_many([k['key'] for k in objects]).get('result', {})
    for k, value in data.iteritems():
        if 'location' in value and value.get('type', {}).get('key') == '/type/redirect':
            value = api.get(value['location']).get('result', {})
        r.append(value[key])
    return r

class API(object):
    base = 'https://openlibrary.org/api'

    def _request(self, action, data):
        for key in data:
            if not isinstance(data[key], basestring):
                data[key] = json.dumps(data[key])
        url = self.base + '/' + action + '?' + urlencode(data)
        result = json.loads(read_url(url))
        if 'status' in result and result['status'] == 'error' or 'error' in result:
            logger.info('FAILED %s %s', action, data)
            logger.info('URL %s', url)
        return result

    def get(self, key):
        data = self._request('get', {'key': key})
        return data

    def get_many(self, keys):
        data = self._request('get_many', {'keys': keys})
        return data

    def search(self, query):
        if isinstance(query, basestring):
            query = {
                'query': query
            }
        data = self._request('search', {'q': query})
        if 'status' in data and data['status'] == 'error':
            logger.info('FAILED %s', query)
        return data

    def things(self, query):
        data = self._request('things', {'query': query})
        return data

api = API()
