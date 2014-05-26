# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from ox.cache import read_url
import re
import lxml.html

import logging
logger = logging.getLogger('meta.abebooks')

base = 'http://www.abebooks.com'

def get_ids(key, value):
    ids = []
    if key == 'isbn':
        url = '%s/servlet/SearchResults?isbn=%s&sts=t' % (base, id)
        data = read_url(url)
        urls = re.compile('href="(/servlet/BookDetailsPL[^"]+)"').findall(data)
        if urls:
            ids.append((key, value))
    if ids:
        logger.debug('get_ids %s %s => %s', key, value, ids)
    return ids

def lookup(id):
    logger.debug('lookup %s', id)
    data = {}
    url = '%s/servlet/SearchResults?isbn=%s&sts=t' % (base, id)
    html = read_url(url)
    urls = re.compile('href="(/servlet/BookDetailsPL[^"]+)"').findall(html)
    keys = {
        'pubdate': 'date'
    }
    if urls:
        details = '%s%s' % (base, urls[0])
        html = read_url(details)
        doc = lxml.html.document_fromstring(html)
        for e in doc.xpath("//*[contains(@id, 'biblio')]"):
            key = e.attrib['id'].replace('biblio-', '')
            value = e.text_content().strip()
            k = keys.get(key, key)
            if k == 'date' and value == 'Publication Date:':
                value = ''
            elif k == 'publisher' and value == 'Publisher:':
                value = ''
            if value and key not in ('bookcondition', 'binding', 'edition-amz'):
                data[k] = value
    return data
