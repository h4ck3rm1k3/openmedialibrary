# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import os
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
import re
from urllib.parse import unquote

from PIL import Image
import stdnum.isbn

from utils import normalize_isbn, find_isbns

import logging
logger = logging.getLogger(__name__)

def cover(path):
    logger.debug('cover %s', path)
    data = None
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        logger.debug('invalid epub file %s', path)
        return data
    for f in z.filelist:
        if 'cover' in f.filename.lower() and f.filename.split('.')[-1] in ('jpg', 'jpeg', 'png'):
            logger.debug('using %s', f.filename)
            data = z.read(f.filename)
            break
    if not data:
        files = [f.filename for f in z.filelist]
        opf = [f for f in files if f.endswith('opf')]
        if opf:
            info = ET.fromstring(z.read(opf[0]))
            manifest = info.findall('{http://www.idpf.org/2007/opf}manifest')[0]
            for e in manifest.getchildren():
                if 'image' in e.attrib['media-type']:
                    filename = unquote(e.attrib['href'])
                    filename = os.path.normpath(os.path.join(os.path.dirname(opf[0]), filename))
                    if filename in files:
                        data = z.read(filename)
                        break
                elif 'html' in e.attrib['media-type']:
                    filename = unquote(e.attrib['href'])
                    filename = os.path.normpath(os.path.join(os.path.dirname(opf[0]), filename))
                    html = z.read(filename).decode('utf-8')
                    img = re.compile('<img.*?src="(.*?)"').findall(html)
                    #svg image
                    img += re.compile('<image.*?href="(.*?)"').findall(html)
                    if img:
                        img = unquote(img[0])
                        img = os.path.normpath(os.path.join(os.path.dirname(filename), img))
                        if img in files:
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
    try:
        z = zipfile.ZipFile(epub)
    except zipfile.BadZipFile:
        logger.debug('invalid epub file %s', epub)
        return data
    opf = [f.filename for f in z.filelist if f.filename.endswith('opf')]
    if opf:
        info = ET.fromstring(z.read(opf[0]))
        metadata = info.findall('{http://www.idpf.org/2007/opf}metadata')[0]
        for e in metadata.getchildren():
            if e.text and e.text.strip() and e.text not in ('unknown', 'none'):
                key = e.tag.split('}')[-1]
                key = {
                    'creator': 'author',
                }.get(key, key)
                value = e.text.strip()
                if key == 'identifier':
                    value = normalize_isbn(value)
                    if stdnum.isbn.is_valid(value):
                        data['isbn'] = [value]
                elif key == 'author':
                    data[key] = value.split(', ')
                else:
                    data[key] = value
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
    data = ''
    z = zipfile.ZipFile(path)
    for f in z.filelist:
        if '/._' in f.filename or f.filename.startswith('._'):
            continue
        if f.filename.endswith('html'):
            data += z.read(f.filename).decode()
    return data

def extract_isbn(data):
    isbns = find_isbns(data)
    if isbns:
        return isbns[0]

