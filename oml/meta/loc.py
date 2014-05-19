# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import ox
from ox.cache import read_url
import re
import xml.etree.ElementTree as ET

from utils import normalize_isbn
from marc_countries import COUNTRIES

import logging
logger = logging.getLogger('meta.loc')

def get_ids(key, value):
    ids = []
    if key in ['isbn10', 'isbn13']:
        url = 'http://www.loc.gov/search/?q=%s&all=true' % value
        html = ox.cache.read_url(url)
        match = re.search('"http://lccn.loc.gov/(\d+)"', html)
        if match:
            ids.append(('lccn', match.group(1)))
    if ids:
        logger.debug('get_ids %s,%s => %s', key, value, ids)
    return ids

def lookup(id):
    logger.debug('lookup %s', id)
    ns = '{http://www.loc.gov/mods/v3}'
    url = 'http://lccn.loc.gov/%s/mods' % id
    data = read_url(url)
    mods = ET.fromstring(data)

    info = {
        'lccn': id
    }
    title = mods.findall(ns + 'titleInfo')
    if not title:
        return {}
    info['title'] = ''.join([': ' + e.text.strip() if e.tag == ns + 'subTitle' else ' ' + e.text.strip() for e in title[0]]).strip()
    origin = mods.findall(ns + 'originInfo')
    if origin:
        info['place'] = []
        for place in origin[0].findall(ns + 'place'):
            terms = place.findall(ns + 'placeTerm')
            if terms and terms[0].attrib['type'] == 'text':
                e = terms[0]
                info['place'].append(e.text)
            elif terms and terms[0].attrib['type'] == 'code':
                e = terms[0]
                info['country'] = COUNTRIES.get(e.text, e.text)
        publisher = [e.text for e in origin[0].findall(ns + 'publisher')]
        if publisher:
            info['publisher'] = publisher[0]
        info['date'] = ''.join([e.text for e in origin[0].findall(ns + 'dateIssued')])
        for i in mods.findall(ns + 'identifier'):
            if i.attrib['type'] == 'oclc':
                info['oclc'] = i.text.replace('ocn', '')
            if i.attrib['type'] == 'lccn':
                info['lccn'] = i.text
            if i.attrib['type'] == 'isbn':
                isbn = normalize_isbn(i.text)
                info['isbn%s'%len(isbn)] = isbn
        for i in mods.findall(ns + 'classification'):
            if i.attrib['authority'] == 'ddc':
                info['classification'] = i.text
        info['author'] = []
        for a in mods.findall(ns + 'name'):
            if a.attrib.get('usage') == 'primary':
                info['author'].append(' '.join([e.text for e in a.findall(ns + 'namePart') if not e.attrib.get('type') in ('date', )]))
        info['author'] = [ox.normalize_name(a) for a in info['author']]
    toc = mods.findall(ns + 'tableOfContents')
    if toc:
        info['description'] = toc[0].text.strip()
    for key in info.keys():
        if not info[key]:
            del info[key]
    return info

info = lookup
