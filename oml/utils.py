# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import Image
from StringIO import StringIO
import re
import stdnum.isbn

import ox

from meta.utils import normalize_isbn, find_isbns

def valid_olid(id):
    return id.startswith('OL') and id.endswith('M')

def get_positions(ids, pos):
    '''
    >>> get_positions([1,2,3,4], [2,4])
    {2: 1, 4: 3}
    '''
    positions = {}
    for i in pos:
        try:
            positions[i] = ids.index(i)
        except:
            pass
    return positions

def get_by_key(objects, key, value):
    obj = filter(lambda o: o.get(key) == value, objects)
    return obj and obj[0] or None

def get_by_id(objects, id):
    return get_by_key(objects, 'id', id)

def resize_image(data, width=None, size=None):
    source = Image.open(StringIO(data)).convert('RGB')
    source_width = source.size[0]
    source_height = source.size[1]
    if size:
        if source_width > source_height:
            width = size
            height = int(width / (float(source_width) / source_height))
            height = height - height % 2
        else:
            height = size
            width = int(height * (float(source_width) / source_height))
            width = width - width % 2

    else:
        height = int(width / (float(source_width) / source_height))
        height = height - height % 2

    width = max(width, 1)
    height = max(height, 1)

    if width < source_width:
        resize_method = Image.ANTIALIAS
    else:
        resize_method = Image.BICUBIC
    output = source.resize((width, height), resize_method)
    o = StringIO()
    output.save(o, format='jpeg')
    data = o.getvalue()
    o.close()
    return data

def sort_title(title):

    title = title.replace(u'Æ', 'Ae')
    if isinstance(title, str):
        title = unicode(title)
    title = ox.sort_string(title)

    #title
    title = re.sub(u'[\'!¿¡,\.;\-"\:\*\[\]]', '', title)
    return title.strip()

def get_position_by_id(list, key):
    for i in range(0, len(list)):
        if list[i]['id'] == key:
            return i
    return -1

