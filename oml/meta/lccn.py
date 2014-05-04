# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import ox
from ox.cache import read_url
import xml.etree.ElementTree as ET

from utils import normalize_isbn
from marc_countries import COUNTRIES

def info(id):
    ns = '{http://www.loc.gov/mods/v3}'
    url = 'http://lccn.loc.gov/%s/mods' % id
    data = read_url(url)
    mods = ET.fromstring(data)

    info = {}
    info['title'] = ''.join([e.text for e in mods.findall(ns + 'titleInfo')[0]])
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
        info['publisher'] = ''.join([e.text for e in origin[0].findall(ns + 'publisher')])
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
            if a.attrib['usage'] == 'primary':
                info['author'].append(''.join([e.text for e in a.findall(ns + 'namePart')]))
        info['author'] = [ox.normalize_name(a[:-1]) for a in info['author']]
    for key in info.keys():
        if not info[key]:
            del info[key]
    return info
