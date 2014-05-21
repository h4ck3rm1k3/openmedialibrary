# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import os
from utils import find_isbns
import tempfile
import subprocess

def cover(path):
    image = tempfile.mkstemp('.jpg')[1]
    cmd = ['python2', 'static/txt.js/txt.py', '-i', path, '-o', image]
    p = subprocess.Popen(cmd)
    p.wait()
    with open(image, 'rb') as fd:
        data = fd.read()
    os.unlink(image)
    return data

def info(path):
    data = {}
    data['title'] = os.path.splitext(os.path.basename(path))[0]
    text = extract_text(path)
    isbn = extract_isbn(text)
    if isbn:
        data['isbn'] = [isbn]
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
