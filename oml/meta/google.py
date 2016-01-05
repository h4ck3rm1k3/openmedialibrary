# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from ox.cache import get_json, store
import ox.web.google
import stdnum.isbn

from utils import get_language
from .utils import find_isbns

import logging
logger = logging.getLogger(__name__)


def find(query):
    logger.debug('find %s', query)
    query += ' isbn'
    isbns = []
    for r in ox.web.google.find(query):
        isbns += find_isbns(' '.join(r))
    logger.debug('isbns', isbns)
    results = []
    done = set()
    for isbn in isbns:
        if isbn not in done:
            r = {
                'isbn': isbn,
                'primaryid': ['isbn', isbn]
            }
            results.append(r)
            done.add(isbn)
            if len(isbn) == 10:
                done.add(stdnum.isbn.to_isbn13(isbn))
            if len(isbn) == 13 and isbn.startswith('978'):
                done.add(stdnum.isbn.to_isbn10(isbn))
    return results

def info(key, value):
    if key not in ('isbn', 'lccn', 'oclc'):
        raise IOError('unknwon key %s' % key)
    url = 'https://www.googleapis.com/books/v1/volumes?q=%s:%s' % (key, value)
    r = get_json(url, timeout=-1)
    if 'error' in r:
        store.delete(url)
        raise IOError(url, r)
    if not 'items' in r:
        print('unkown %s: %s [%s]' % (key, value, r))
        return {}
    _data = r['items'][0]['volumeInfo']
    data = {}
    for key in [
            'authors',
            'description',
            'pageCount',
            'publishedDate',
            'publisher',
            'title',
        ]:
        if key in _data:
            data[{
                'authors': 'author',
                'pageCount': 'pages',
                'publishedDate': 'date',
            }.get(key,key)] = _data[key]

    if 'subtitle' in _data:
        data['title'] = '{title}: {subtitle}'.format(**_data)
    if r['items'][0]['accessInfo']['viewability'] != 'NO_PAGES':
        data['cover'] = 'https://books.google.com/books?id=%s&pg=PP1&img=1&zoom=0&hl=en' % r['items'][0]['id']
    elif 'imageLinks' in _data:
        for size in ('extraLarge', 'large', 'medium', 'small', 'thumbnail', 'smallThumbnail'):
            if size in _data['imageLinks']:
                data['cover'] = _data['imageLinks'][size]
                break
    if 'industryIdentifiers' in _data:
        for k in _data['industryIdentifiers']:
            if k['type'].startswith('ISBN'):
                if not 'isbn' in data:
                    data['isbn'] = []
                data['isbn'].append(k['identifier'])
            else:
                print('unknown identifier', k)
    if 'language' in _data:
        data['language'] = get_language(_data['language'])
    return data

