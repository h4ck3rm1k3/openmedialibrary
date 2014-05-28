# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import base64
import hashlib
import os

import ox

import pdf
import epub
import txt
import opf

def get_id(f=None, data=None):
    if data:
        return base64.b32encode(hashlib.sha1(data).digest())
    else:
        return base64.b32encode(ox.sha1sum(f, cached=True).decode('hex'))


def metadata(f, from_=None):
    ext = f.split('.')[-1]
    data = {}
    data['extension'] = ext
    data['size'] = os.stat(f).st_size

    if ext == 'pdf':
        info = pdf.info(f)
    elif ext == 'epub':
        info = epub.info(f)
    elif ext == 'txt':
        info = txt.info(f)

    opf_info = {}
    metadata_opf = os.path.join(os.path.dirname(from_ or f), 'metadata.opf')
    if os.path.exists(metadata_opf):
        opf_info = opf.info(metadata_opf)

    for key in (
        'title', 'author', 'date', 'publisher',
        'language', 'textsize', 'pages',
        'isbn', 'asin'
    ):
        if key in info:
            value = info[key]
            if isinstance(value, str):
                try:
                    value = value.decode('utf-8')
                except:
                    value = None
            if value:
                data[key] = info[key]
        if key in opf_info:
            data[key] = opf_info[key]
        if key in data:
            if isinstance(data[key], basestring):
                data[key] = data[key].replace('\x00', '')
            elif isinstance(data[key], list):
                data[key] = [e.replace('\x00', '') if isinstance(e, basestring) else e for e in data[key]]
    if 'isbn' in data:
        data['primaryid'] = ['isbn', data['isbn'][0]]
    elif 'asin' in data:
        data['primaryid'] = ['asin', data['asin'][0]]
    if 'author' in data:
        if isinstance(data['author'], basestring):
            if data['author'].strip():
                data['author'] = data['author'].strip().split('; ')
            else:
                del data['author']
        if data['author'] in (['Administrator'], ['Default'], ['user']):
            del data['author']
    if not 'title' in data:
        data['title'] = os.path.splitext(os.path.basename(f))[0]
        if data['title'].startswith('Microsoft Word - '):
            data['title'] = data['title'][len('Microsoft Word - '):]
        for postfix in ('.doc', 'docx', '.qxd', '.indd', '.tex'):
            if data['title'].endswith(postfix):
                data['title'] = data['title'][:-len(postfix)]
        if not data['title'].strip():
            del data['title']
    return data

