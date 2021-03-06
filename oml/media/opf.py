# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import xml.etree.ElementTree as ET

import stdnum.isbn

from utils import normalize_isbn, get_language
from ox import strip_tags
import ox.iso

import logging
logger = logging.getLogger(__name__)

def info(opf):
    data = {}
    try:
        with open(opf, 'rb') as fd:
            opf = ET.fromstring(fd.read().decode())
    except:
        logger.debug('failed to load opf %s', opf, exc_info=1)
        return data
    ns = '{http://www.idpf.org/2007/opf}'
    metadata = opf.findall(ns + 'metadata')[0]
    for e in metadata.getchildren():
        if e.text:
            key = e.tag.split('}')[-1]
            key = {
                'creator': 'author',
            }.get(key, key)
            value = e.text
            if key == 'identifier':
                isbn = normalize_isbn(value)
                if stdnum.isbn.is_valid(isbn):
                    if not 'isbn' in data:
                        data['isbn'] = [isbn]
                    else:
                        data['isbn'].append(isbn)
                if e.attrib.get(ns + 'scheme') == 'AMAZON':
                    if not 'asin' in data:
                        data['asin'] = [value]
                    else:
                        data['asin'].append(value)
            else:
                data[key] = strip_tags(e.text)
    #YYY-MM-DD
    if 'date' in data and len(data['date']) > 10:
        data['date'] =data['date'][:10]
    if 'language' in data:
        data['language'] = get_language(data['language'])
    return data
