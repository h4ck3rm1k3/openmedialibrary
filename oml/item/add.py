# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import base64
import models

import ox

import scan

def add(path):
    info = scan.get_metadata(path)
    id = info.pop('id')
    item = models.Item.get_or_create(id)
    item.path = path
    item.info = info
    models.db.session.add(item)
    models.db.session.commit()

