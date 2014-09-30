# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import sys
import tempfile
import subprocess
import os
import shutil
from glob import glob

from PyPDF2 import PdfFileReader
import stdnum.isbn

import settings
from utils import normalize_isbn, find_isbns

import logging
logger = logging.getLogger('oml.meta.pdf')

def cover(pdf):
    if sys.platform == 'darwin':
        return ql_cover(pdf)
    else:
        return page(pdf, 1)

def ql_cover(pdf):
    tmp = tempfile.mkdtemp()
    cmd = [
        'qlmanage',
        '-t',
        '-s',
        '1024',
        '-o',
        tmp,
        pdf
    ]
    p = subprocess.Popen(cmd, close_fds=True)
    p.wait()
    image = glob('%s/*' % tmp)
    if image:
        image = image[0]
        with open(image, 'rb') as fd:
            data = fd.read()
    else:
        logger.debug('qlmanage did not create cover for %s', pdf)
        data = None
    shutil.rmtree(tmp)
    return data

def page(pdf, page):
    tmp = tempfile.mkdtemp()
    cmd = [
        'pdftocairo',
        pdf,
        '-jpeg',
        '-f',  str(page), '-l', str(page),
        '-scale-to', '1024', '-cropbox',
        os.path.join(tmp, 'page')
    ]
    p = subprocess.Popen(cmd, close_fds=True)
    p.wait()
    image = glob('%s/*' % tmp)
    if image:
        image = image[0]
        with open(image, 'rb') as fd:
            data = fd.read()
    else:
        logger.debug('pdftocairo %s %s', pdf, ' '.join(cmd))
        data = None
    shutil.rmtree(tmp)
    return data

'''
def page(pdf, page):
    image = tempfile.mkstemp('.jpg')[1]
    cmd = [
        'gs', '-q',
        '-dBATCH', '-dSAFER', '-dNOPAUSE', '-dNOPROMPT',
        '-dMaxBitmap=500000000',
        '-dAlignToPixels=0', '-dGridFitTT=2',
        '-sDEVICE=jpeg', '-dTextAlphaBits=4', '-dGraphicsAlphaBits=4',
        '-r72',
        '-dUseCropBox',
        '-dFirstPage=%d' % page,
        '-dLastPage=%d' % page,
        '-sOutputFile=%s' % image,
        pdf
    ]
    p = subprocess.Popen(cmd, close_fds=True)
    p.wait()
    with open(image, 'rb') as fd:
        data = fd.read()
    os.unlink(image)
    return data
'''

def info(pdf):
    data = {}
    with open(pdf, 'rb') as fd:
        try:
            pdfreader = PdfFileReader(fd)
            data['pages'] = pdfreader.numPages
            info = pdfreader.getDocumentInfo()
            if info:
                for key in info:
                    if info[key]:
                        data[key[1:].lower()] = info[key]
            xmp =pdfreader.getXmpMetadata()
            if xmp:
                for key in dir(xmp):
                    if key.startswith('dc_'):
                        value = getattr(xmp, key)
                        if isinstance(value, dict) and 'x-default' in value:
                            value = value['x-default']
                        elif isinstance(value, list):
                            value = [v.strip() for v in value if v.strip()]
                        _key = key[3:]
                        if value and _key not in data:
                            data[_key] = value
        except:
            logger.debug('FAILED TO PARSE %s', pdf, exc_info=1)

    '''
    cmd = ['pdfinfo', pdf]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    stdout, stderr = p.communicate()
    for line in stdout.strip().split('\n'):
        parts = line.split(':')
        key = parts[0].lower().strip()
        if key:
            data[key] = ':'.join(parts[1:]).strip()
    for key in data.keys():
        if not data[key]:
            del data[key]
    '''
    if 'identifier' in data:
        value = normalize_isbn(data['identifier'])
        if stdnum.isbn.is_valid(value):
            data['isbn'] = [value]
            del data['identifier']
    for key, value in data.items():
        if isinstance(value, dict):
            value = ' '.join(list(value.values()))
            data[key] = value
    text = extract_text(pdf)
    data['textsize'] = len(text)
    if settings.server['extract_text']:
        if not 'isbn' in data:
            isbn = extract_isbn(text)
            if isbn:
                data['isbn'] = [isbn]
    if 'isbn' in data and isinstance(data['isbn'], str):
        data['isbn'] = [data['isbn']]
    if 'date' in data and len(data['date']) == 8 and data['date'].isdigit():
        d = data['date']
        data['date'] = '%s-%s-%s' % (d[:4], d[4:6], d[6:])
    return data

'''
    #possbile alternative with gs
    tmp = tempfile.mkstemp('.txt')[1]
    cmd = ['gs', '-dBATCH', '-dNOPAUSE', '-sDEVICE=txtwrite', '-dFirstPage=3', '-dLastPage=5', '-sOutputFile=%s'%tmp, pdf]

'''
def extract_text(pdf):
    if sys.platform == 'darwin':
        cmd = ['/usr/bin/mdimport', '-d2', pdf]
    else:
        cmd = ['pdftotext', pdf, '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    stdout, stderr = p.communicate()
    stdout = stdout.decode()
    stderr = stderr.decode()
    if sys.platform == 'darwin':
        if 'kMDItemTextContent' in stderr:
            stdout = stderr.split('kMDItemTextContent = "')[-1].split('\n')[0][:-2]
        else:
            stdout = ''
    return stdout.strip()

def extract_isbn(text):
    isbns = find_isbns(text)
    if isbns:
        return isbns[0]
