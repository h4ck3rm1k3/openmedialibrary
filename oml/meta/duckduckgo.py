# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import ox.web.duckduckgo
import stdnum.isbn

from .utils import find_isbns

import logging
logger = logging.getLogger('meta.duckduckgo')


def find(query):
    logger.debug('find %s', query)
    query += ' isbn'
    isbns = []
    for r in ox.web.duckduckgo.find(query):
        isbns += find_isbns(' '.join(r))
    results = []
    done = set()
    for isbn in isbns:
        if isbn not in done:
            r = {
                'isbn': [isbn],
                'primaryid': ['isbn', isbn]
            }
            results.append(r)
            done.add(isbn)
            if len(isbn) == 10:
                done.add(stdnum.isbn.to_isbn13(isbn))
            if len(isbn) == 13 and isbn.startswith('978'):
                done.add(stdnum.isbn.to_isbn10(isbn))
    return results
