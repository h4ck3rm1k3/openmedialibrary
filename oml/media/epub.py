# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import sys
import xml.etree.ElementTree as ET
import zipfile
from StringIO import StringIO

import Image
import stdnum.isbn

from utils import normalize_isbn, find_isbns

def cover(path):
    img = Image.new('RGB', (80, 128))
    o = StringIO()
    img.save(o, format='jpeg')
    data = o.getvalue()
    o.close()
    return data

def info(epub):
    data = {}
    z = zipfile.ZipFile(epub)
    opf = [f.filename for f in z.filelist if f.filename.endswith('opf')]
    if opf:
        info = ET.fromstring(z.read(opf[0]))
        metadata = info.findall('{http://www.idpf.org/2007/opf}metadata')[0]
        for e in metadata.getchildren():
            if e.text:
                key = e.tag.split('}')[-1]
                key = {
                    'creator': 'author',
                }.get(key, key)
                value = e.text
                if key == 'identifier':
                    value = normalize_isbn(value)
                    if stdnum.isbn.is_valid(value):
                        data['isbn'] = value
                else:
                    data[key] = e.text
    text = extract_text(epub)
    data['textsize'] = len(text)
    if not 'isbn' in data:
        isbn = extract_isbn(text)
        if isbn:
            data['isbn'] = isbn
    return data

def extract_text(path):
    data = ''
    z = zipfile.ZipFile(path)
    for f in z.filelist:
        if f.filename.endswith('html'):
            data += z.read(f.filename)
    return data

def extract_isbn(data):
    isbns = find_isbns(data)
    if isbns:
        return isbns[0]

