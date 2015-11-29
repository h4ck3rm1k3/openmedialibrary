# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import re

from ox.cache import read_url
from ox import find_re, strip_tags, decode_html
import stdnum.isbn

from .utils import find_isbns

import logging
logger = logging.getLogger(__name__)


base = 'http://www.lookupbyisbn.com'

def get_ids(key, value):
    ids = []

    def add_other_isbn(v):
        if len(v) == 10:
            ids.append(('isbn', stdnum.isbn.to_isbn13(v)))
        if len(v) == 13 and v.startswith('978'):
            ids.append(('isbn', stdnum.isbn.to_isbn10(v)))

    if key in ('isbn', 'asin'):
        url = '%s/Search/Book/%s/1' % (base, value)
        data = read_url(url).decode('utf-8')
        m = re.compile('href="(/Lookup/Book/[^"]+?)"').findall(data)
        if m:
            asin = m[0].split('/')[-3]
            if stdnum.isbn.to_isbn10(asin) or not stdnum.isbn.is_valid(asin):
                ids.append(('asin', asin))
    if key == 'isbn':
        add_other_isbn(value)
    if key == 'asin':
        if stdnum.isbn.is_valid(value):
            ids.append(('isbn', value))
            add_other_isbn(value)
        else:
            for isbn in amazon_lookup(value):
                if stdnum.isbn.is_valid(isbn):
                    ids.append(('isbn', isbn))
                    add_other_isbn(isbn)
    if ids:
        logger.debug('get_ids %s, %s => %s', key, value, ids)
    return ids

def lookup(id):
    logger.debug('lookup %s', id)
    r = {
        'asin': [id]
    }
    url = '%s/Lookup/Book/%s/%s/1' % (base, id, id)
    data = read_url(url).decode('utf-8')
    r["title"] = find_re(data, "<h2>(.*?)</h2>")
    if r["title"] == 'Error!':
        return {}
    keys = {
        'author': 'Author(s)',
        'publisher': 'Publisher',
        'date': 'Publication date',
        'edition': 'Edition',
        'binding': 'Binding',
        'volume': 'Volume(s)',
        'pages': 'Pages',
    }
    for key in keys:
        r[key] = find_re(data, '<span class="title">%s:</span>(.*?)</li>'% re.escape(keys[key]))
        if r[key] == '--' or not r[key]:
            del r[key]
        if key == 'pages' and key in r:
            r[key] = int(r[key])
    desc = find_re(data, '<h2>Description:<\/h2>(.*?)<div ')
    desc = desc.replace('<br /><br />', ' ').replace('<br /> ', ' ').replace('<br />', ' ')
    r['description'] = decode_html(strip_tags(desc))
    r['cover'] = find_re(data, '<img src="(.*?)" alt="Book cover').replace('._SL160_', '')
    for key in r:
        if isinstance(r[key], str):
            r[key] = decode_html(strip_tags(r[key])).strip()
    if 'author' in r and isinstance(r['author'], str) and r['author']:
        r['author'] = [r['author']]
    else:
        r['author'] = []
    if r['description'].lower() == 'Description of this item is not available at this time.'.lower():
        r['description'] = ''
    return r

def amazon_lookup(asin):
    url = 'http://www.amazon.com/dp/%s' % asin
    html = read_url(url, timeout=-1).decode('utf-8', 'ignore')
    return list(set(find_isbns(find_re(html, 'Formats</h3>.*?</table'))))
