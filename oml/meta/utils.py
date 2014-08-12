# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import re
import stdnum.isbn


def normalize_isbn(value):
    return ''.join([s for s in value if s.isdigit() or s == 'X'])

def find_isbns(text):
    matches = re.compile('\d[\d\-X\ ]+').findall(text)
    matches = [normalize_isbn(value) for value in matches]
    return [isbn for isbn in matches if stdnum.isbn.is_valid(isbn)
        and len(isbn) in (10, 13)
        and isbn not in (
        '0' * 10,
        '0' * 13,
    )]

