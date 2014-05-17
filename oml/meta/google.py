# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import ox.web.google
import stdnum.isbn

from .utils import find_isbns

import logging
logger = logging.getLogger('meta.google')


def find(title, author=None, publisher=None, date=None):
    logger.debug('find %s %s %s %s', title, author, publisher, date)
    query = title
    if author:
        if isinstance(author, list):
            author = ' '.join(author)
        query += ' ' + author
    query += ' isbn'
    isbns = []
    for r in ox.web.google.find(query):
        isbns += find_isbns(' '.join(r))
    logger.debug('isbns', isbns)
    results = []
    done = set()
    for isbn in isbns:
        if isbn not in done:
            key = 'isbn%d'%len(isbn)
            #r = lookup(key, isbn)
            #r['mainid'] = key
            r = {
                key: isbn,
                'mainid': key
            }
            results.append(r)
            done.add(isbn)
            if len(isbn) == 10:
                done.add(stdnum.isbn.to_isbn13(isbn))
            if len(isbn) == 13:
                done.add(stdnum.isbn.to_isbn10(isbn))
    return results
