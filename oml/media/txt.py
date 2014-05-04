# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import sys
import os
from utils import find_isbns
from StringIO import StringIO
import Image

from pdf import ql_cover

def cover(path):
    if sys.platform == 'darwin':
        return ql_cover(path)
    img = Image.new('RGB', (80, 128))
    o = StringIO()
    img.save(o, format='jpeg')
    data = o.getvalue()
    o.close()
    return data

def info(path):
    data = {}
    data['title'] = os.path.splitext(os.path.basename(path))[0]
    text = extract_text(path)
    isbn = extract_isbn(text)
    if isbn:
        data['isbn'] = isbn
    data['textsize'] = len(text)
    return data

def extract_text(path):
    with open(path) as fd:
        data = fd.read()
    return data

def extract_isbn(text):
    isbns = find_isbns(text)
    if isbns:
        return isbns[0]
