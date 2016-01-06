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
from ox import strip_tags, decode_html

from utils import normalize_isbn, find_isbns, get_language

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

    def use(filename):
        logger.debug('using %s', filename)
        return z.read(filename)

    for f in z.filelist:
        if 'cover' in f.filename.lower() and f.filename.split('.')[-1] in ('jpg', 'jpeg', 'png'):
            return use(f.filename)
    files = [f.filename for f in z.filelist]
    opf = [f for f in files if f.endswith('opf')]
    if opf:
        #logger.debug('opf: %s', z.read(opf[0]).decode())
        info = ET.fromstring(z.read(opf[0]))
        metadata = info.findall('{http://www.idpf.org/2007/opf}metadata')
        if metadata:
            metadata = metadata[0]
        manifest = info.findall('{http://www.idpf.org/2007/opf}manifest')
        if manifest:
            manifest = manifest[0]
        if metadata and manifest:
            for e in metadata.getchildren():
                if e.tag == '{http://www.idpf.org/2007/opf}meta' and e.attrib.get('name') == 'cover':
                    cover_id = e.attrib['content']
                    for e in manifest.getchildren():
                        if e.attrib['id'] == cover_id:
                            filename = unquote(e.attrib['href'])
                            filename = os.path.normpath(os.path.join(os.path.dirname(opf[0]), filename))
                            if filename in files:
                                return use(filename)
        if manifest:
            images = [e for e in manifest.getchildren() if 'image' in e.attrib['media-type']]
            if images:
                image_data = []
                for e in images:
                    filename = unquote(e.attrib['href'])
                    filename = os.path.normpath(os.path.join(os.path.dirname(opf[0]), filename))
                    if filename in files:
                        image_data.append((filename, z.read(filename)))
                if image_data:
                    image_data.sort(key=lambda i: len(i[1]))
                    data = image_data[-1][1]
                    logger.debug('using %s', image_data[-1][0])
                    return data
            for e in manifest.getchildren():
                if 'html' in e.attrib['media-type']:
                    filename = unquote(e.attrib['href'])
                    filename = os.path.normpath(os.path.join(os.path.dirname(opf[0]), filename))
                    html = z.read(filename).decode('utf-8', 'ignore')
                    img = re.compile('<img.*?src="(.*?)"').findall(html)
                    #svg image
                    img += re.compile('<image.*?href="(.*?)"').findall(html)
                    if img:
                        img = unquote(img[0])
                        img = os.path.normpath(os.path.join(os.path.dirname(filename), img))
                        if img in files:
                            return use(img)
    # fallback return black cover
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
        metadata = info.findall('{http://www.idpf.org/2007/opf}metadata')
        if metadata:
            metadata = metadata[0]
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
    if 'description' in data:
        data['description'] = strip_tags(decode_html(data['description']))
    text = extract_text(epub)
    data['textsize'] = len(text)
    if not 'isbn' in data:
        isbn = extract_isbn(text)
        if isbn:
            data['isbn'] = [isbn]
    if 'date' in data and 'T' in data['date']:
        data['date'] = data['date'].split('T')[0]
    if 'language' in data and isinstance(data['language'], str):
        data['language'] = get_language(data['language'])
    return data

def extract_text(path):
    data = ''
    z = zipfile.ZipFile(path)
    for f in z.filelist:
        if '/._' in f.filename or f.filename.startswith('._'):
            continue
        if f.filename.endswith('html'):
            data += z.read(f.filename).decode('utf-8', 'ignore')
    return data

def extract_isbn(data):
    isbns = find_isbns(data)
    if isbns:
        return isbns[0]

