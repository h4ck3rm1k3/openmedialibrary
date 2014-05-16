# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import models
from copy import deepcopy

def import_all():
    for i in models.items:
        item = models.Item.get_or_create(i['id'])
        item.path = i['path']
        item.info = deepcopy(i)
        del item.info['path']
        del item.info['id']
        item.meta = item.info.pop('meta', {})
        models.db.session.add(item)
    models.db.session.commit()
