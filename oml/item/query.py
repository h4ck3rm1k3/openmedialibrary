# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import settings
import models
import utils
import oxflask.query

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
    query['qs'] = oxflask.query.Parser(models.Item).find(data)
    if 'query' in query and 'conditions' in query['query'] and query['query']['conditions']:
        conditions = query['query']['conditions']
        condition = conditions[0]
        if condition['key'] == '*':
            value = condition['value'].lower()
            query['qs'] = models.Item.query.join(
                    models.Find, models.Find.item_id==models.Item.id).filter(
                            models.Find.value.contains(value))
    if not 'group' in query:
        query['qs'] = order(query['qs'], query['sort'])
    return query

def order(qs, sort, prefix='sort_'):
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
        qs = qs.order_by(*order_by)
    return qs
