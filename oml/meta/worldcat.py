# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from ox.cache import read_url
import lxml.html
import re
from utils import normalize_isbn
import stdnum.isbn

import logging
logger = logging.getLogger('meta.worldcat')

base_url = 'http://www.worldcat.org'

def get_ids(key, value):
    ids = []
    if key in ['isbn10', 'isbn13']:
        url = '%s/search?qt=worldcat_org_bks&q=%s' % (base_url, value)
        html = read_url(url)
        matches = re.compile('/title.*?oclc/(\d+).*?"').findall(html)
        if matches:
            info = lookup(matches[0])
            ids.append(('oclc', matches[0]))
            for k in ['isbn10', 'isbn13']:
                if k in info and k != key:
                    ids.append((k, info[k]))
    elif key == 'oclc':
        info = lookup(value)
        for k in ['isbn10', 'isbn13']:
            if k in info:
                ids.append((k, info[k]))
    if ids:
        logger.debug('get_ids %s %s', key, value)
        logger.debug('%s', ids)
    return ids

def lookup(id):
    data = {
        'oclc': id
    }
    url = '%s/oclc/%s' % (base_url, id)
    html = read_url(url).decode('utf-8')
    doc = lxml.html.document_fromstring(html)
    for e in doc.xpath("//*[contains(@id, 'bibtip')]"):
        key = e.attrib['id'].replace('bibtip_', '')
        value = e.text_content()
        data[key] = value
    info = doc.xpath('//textarea[@id="util-em-note"]')[0].text
    info = dict([i.split(':', 1) for i in info.split('\n\n')[1].split('\n')])
    for key in info:
        k = key.lower()
        data[k] = info[key].strip()
    for key in ('id', 'instance', 'mediatype', 'reclist', 'shorttitle'):
        if key in data:
            del data[key]
    if 'isxn' in data:
        for isbn in data.pop('isxn').split(' '):
            isbn = normalize_isbn(isbn)
            if stdnum.isbn.is_valid(isbn):
                data['isbn%d'%len(isbn)] = isbn
    if 'author' in data:
        data['author'] = [data['author']]
    logger.debug('lookup %s => %s', id, data.keys())
    return data

info = lookup

def find(title, author, year):
    return []

