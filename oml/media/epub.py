# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import os
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
import re

from PIL import Image
import stdnum.isbn

from utils import normalize_isbn, find_isbns

import logging
logger = logging.getLogger('oml.media.epub')

def cover(path):
    logger.debug('cover %s', path)
    z = zipfile.ZipFile(path)
    data = None
    for f in z.filelist:
        if 'cover' in f.filename.lower() and f.filename.split('.')[-1] in ('jpg', 'jpeg', 'png'):
            logger.debug('using %s', f.filename)
            data = z.read(f.filename)
            break
    if not data:
        opf = [f.filename for f in z.filelist if f.filename.endswith('opf')]
        if opf:
            info = ET.fromstring(z.read(opf[0]))
            manifest = info.findall('{http://www.idpf.org/2007/opf}manifest')[0]
            for e in manifest.getchildren():
                if 'image' in e.attrib['media-type']:
                    filename = e.attrib['href']
                    filename = os.path.normpath(os.path.join(os.path.dirname(opf[0]), filename))
                    data = z.read(filename)
                    break
                elif 'html' in e.attrib['media-type']:
                    filename = e.attrib['href']
                    filename = os.path.normpath(os.path.join(os.path.dirname(opf[0]), filename))
                    html = z.read(filename).decode('utf-8')
                    img = re.compile('<img.*?src="(.*?)"').findall(html)
                    if img:
                        img = os.path.normpath(os.path.join(os.path.dirname(filename), img[0]))
                        logger.debug('using %s', img)
                        data = z.read(img)
                        break
    if not data:
        img = Image.new('RGB', (80, 128))
        o = BytesIO()
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
                        data['isbn'] = [value]
                else:
                    data[key] = e.text
    text = extract_text(epub)
    data['textsize'] = len(text)
    if not 'isbn' in data:
        isbn = extract_isbn(text)
        if isbn:
            data['isbn'] = [isbn]
    if 'date' in data and 'T' in data['date']:
        data['date'] = data['date'].split('T')[0]
    return data

def extract_text(path):
    data = b''
    z = zipfile.ZipFile(path)
    for f in z.filelist:
        if f.filename.endswith('html'):
            data += z.read(f.filename)
    return data

def extract_isbn(data):
    isbns = find_isbns(data)
    if isbns:
        return isbns[0]

