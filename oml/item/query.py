# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import settings
import models
import utils
from queryparser import Parser


from sqlalchemy.sql.expression import nullslast

def parse(data):
    query = {}
    query['range'] = [0, 100]
    if not 'group' in data:
        query['sort'] = [{'key':'title', 'operator':'+'}]
    for key in ('keys', 'group', 'list', 'range', 'sort', 'query'):
        if key in data:
            query[key] = data[key]
    #print data
    query['qs'] = Parser(models.Item).find(data)
    if not 'group' in query:
        query['qs'] = order(query['qs'], query['sort'])
    return query

def order(qs, sort, prefix='sort.'):
    order_by = []
    if len(sort) == 1:
        additional_sort = settings.config['user']['ui']['listSort']
        key = utils.get_by_id(models.Item.item_keys, sort[0]['key'])
        for s in key.get('additionalSort', additional_sort):
            if s['key'] not in [e['key'] for e in sort]:
                sort.append(s)
    for e in sort:
        operator = e['operator']
        if operator != '-':
            operator = ''
        else:
            operator = ' DESC'
        key = {}.get(e['key'], e['key'])
        if key not in ('fixme', ):
            key = "%s%s" % (prefix, key)
        order = '%s%s' % (key, operator)
        order_by.append(order)
    if order_by:
        #nulllast not supported in sqlite, use IS NULL hack instead
        #order_by = map(nullslast, order_by)
        _order_by = []
        for order in order_by:
            nulls = "%s IS NULL" % order.split(' ')[0]
            _order_by.append(nulls)
            _order_by.append(order)
        order_by = _order_by
        qs = qs.join(models.Sort).order_by(*order_by)
    return qs
