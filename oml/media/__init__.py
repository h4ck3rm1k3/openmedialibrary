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

def get_id(f=None, data=None):
    if data:
        return base64.b32encode(hashlib.sha1(data).digest())
    else:
        return base64.b32encode(ox.sha1sum(f).decode('hex'))


def metadata(f):
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

    for key in (
        'title', 'author', 'date', 'publisher', 'isbn',
        'textsize', 'pages'
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

    if 'isbn' in data:
        data['primaryid'] = ['isbn', data['isbn'][0]]
    if 'author' in data:
        if isinstance(data['author'], basestring):
            data['author'] = data['author'].split('; ')
        if data['author'] in (['Administrator'], ['Default'], ['user']):
            del data['author']
    if not 'title' in data:
        data['title'] = os.path.splitext(os.path.basename(f))[0]
        if data['title'].startswith('Microsoft Word - '):
            data['title'] = data['title'][len('Microsoft Word - '):]
        for postfix in ('.doc', 'docx', '.qxd', '.indd'):
            if data['title'].endswith(postfix):
                data['title'] = data['title'][:-len(postfix)]
        if not data['title'].strip():
            del data['title']
    return data

