# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import re
import hashlib

from ox.cache import read_url
import lxml.html
import stdnum.isbn

from .utils import normalize_isbn

import logging
logger = logging.getLogger('meta.worldcat')


base_url = 'http://www.worldcat.org'

def get_ids(key, value):
    ids = []
    if key == 'isbn':
        url = '%s/search?qt=worldcat_org_bks&q=%s' % (base_url, value)
        html = read_url(url).decode('utf-8')
        matches = re.compile('/title.*?oclc/(\d+).*?"').findall(html)
        if matches:
            info = lookup(matches[0])
            ids.append(('oclc', matches[0]))
            for v in info.get('isbn', []):
                if v != value:
                    ids.append(('isbn', v))
    elif key == 'oclc':
        info = lookup(value)
        if 'isbn' in info:
            for value in info['isbn']:
                ids.append(('isbn', value))
    if ids:
        logger.debug('get_ids %s %s', key, value)
        logger.debug('%s', ids)
    return ids

def lookup(id):
    data = {
        'oclc': [id]
    }
    url = '%s/oclc/%s' % (base_url, id)
    html = read_url(url).decode('utf-8')
    doc = lxml.html.document_fromstring(html)
    for e in doc.xpath("//*[contains(@id, 'bibtip')]"):
        key = e.attrib['id'].replace('bibtip_', '')
        value = e.text_content()
        data[key] = value
    info = doc.xpath('//textarea[@id="util-em-note"]')
    if info:
        info = info[0].text
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
                if not 'isbn' in data:
                    data['isbn'] = []
                if isbn not in data['isbn']:
                    data['isbn'].append(isbn)
    cover = doc.xpath('//img[@class="cover"]')
    if cover:
        data['cover'] = cover[0].attrib['src']
        if data['cover'].startswith('//'):
            data['cover'] = 'http:' + data['cover']
        cdata = read_url(data['cover'])
        if  hashlib.sha1(cdata).hexdigest() in (
            'd2e9ab0c87193d69a7d3a3c21ae4aa550f7dcf00',
            '70f16d3e077cdd47ef6b331001dbb1963677fa04'
        ):
            del data['cover']

    if 'author' in data:
        data['author'] = data['author'].split('; ')
    if 'title' in data:
        data['title'] = data['title'].replace(' : ', ': ')
    if 'publisher' in data:
        m = re.compile('(.+) : (.+), (\d{4})').findall(data['publisher'])
        if m:
            place, publisher, date = m[0]
            data['publisher'] = publisher
            data['date'] = date
            data['place'] = [place]
        elif ':' in data['publisher']:
            place, publisher = data['publisher'].split(':', 2)
            data['place'] = [place.strip()]
            data['publisher'] = publisher.split(',')[0].strip()
            m = re.compile('\d{4}').findall(publisher)
            if m:
                data['date'] = m[0]

    logger.debug('lookup %s => %s', id, list(data.keys()))
    return data

info = lookup

def find(title, author, year):
    return []

