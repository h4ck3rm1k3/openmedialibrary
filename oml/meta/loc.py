# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from ox.cache import read_url
import ox
import re
import xml.etree.ElementTree as ET

from .dewey import get_classification
from .marc_countries import COUNTRIES
from .utils import normalize_isbn

import logging
logger = logging.getLogger(__name__)


def get_ids(key, value):
    ids = []
    if key == 'isbn':
        url = 'http://www.loc.gov/search/?q=%s&all=true' % value
        html = ox.cache.read_url(url).decode('utf-8', 'ignore')
        match = re.search('"http://lccn.loc.gov/(\d+)"', html)
        if match:
            ids.append(('lccn', match.group(1)))
    elif key == 'lccn':
        info = lookup(value)
        for key in ('oclc', 'isbn'):
            if key in info:
                for value in info[key]:
                    ids.append((key, value))
    if ids:
        logger.debug('get_ids %s %s => %s', key, value, ids)
    return ids

def lookup(id):
    logger.debug('lookup %s', id)
    ns = '{http://www.loc.gov/mods/v3}'
    url = 'http://lccn.loc.gov/%s/mods' % id
    info = {
        'lccn': [id]
    }
    try:
        data = read_url(url).decode('utf-8')
        mods = ET.fromstring(data)
    except:
        try:
            data = read_url(url, timeout=0).decode('utf-8')
            mods = ET.fromstring(data)
        except:
            logger.debug('lookup for %s url: %s failed', id, url, exc_info=1)
            return info

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
        info['date'] = ''.join([e.text
            for e in origin[0].findall(ns + 'dateIssued') if e.attrib.get('encoding') == 'marc'])
        for i in mods.findall(ns + 'identifier'):
            key = i.attrib['type']
            value = i.text
            if key in ('oclc', 'lccn', 'isbn'):
                if i.attrib['type'] == 'oclc':
                    value = value.replace('ocn', '').replace('ocm', '')
                if i.attrib['type'] == 'isbn':
                    value = normalize_isbn(i.text)
                if not key in info:
                    info[key] = []
                if value not in info[key]:
                    info[key].append(value)
        for i in mods.findall(ns + 'classification'):
            if i.attrib['authority'] == 'ddc':
                info['classification'] = get_classification(i.text.split('/')[0])
        info['author'] = []
        for a in mods.findall(ns + 'name'):
            if a.attrib.get('usage') == 'primary':
                info['author'].append(' '.join([e.text for e in a.findall(ns + 'namePart') if not e.attrib.get('type') in ('date', )]))
        info['author'] = [ox.normalize_name(a) for a in info['author']]
    toc = mods.findall(ns + 'tableOfContents')
    if toc:
        info['description'] = toc[0].text.strip()
    for key in list(info.keys()):
        if not info[key]:
            del info[key]
    return info

info = lookup
