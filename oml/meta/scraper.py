import json
from ox.cache import read_url
import ox.web.lookupbyisbn

from utils import normalize_isbn

import openlibrary as ol

def add_lookupbyisbn(item): 
    isbn = item.meta.get('isbn10', item.meta.get('isbn13'))
    if isbn:
        more = ox.web.lookupbyisbn.get_data(isbn)
        if more:
            for key in more:
                if more[key]:
                    value = more[key]
                    if isinstance(value, basestring):
                        value = ox.strip_tags(ox.decode_html(value))
                    elif isinstance(value, list):
                        value = [ox.strip_tags(ox.decode_html(v)) for v in value]
                    item.meta[key] = value

        if 'author' in item.meta and isinstance(item.meta['author'], basestring):
            item.meta['author'] = [item.meta['author']]
        if 'isbn' in item.meta:
            del item.meta['isbn']

def update_ol(item):
    info = ol.info(item.meta['olid'])
    for key in info:
        item.meta[key] = info[key]

