# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
import unicodedata

from oxtornado import actions
from queryparser import get_operator
from .person import Person


import logging
logger = logging.getLogger(__name__)


def parse(data, model):
    query = {}
    query['range'] = [0, 100]
    if not 'group' in data:
        query['sort'] = [{'key':'sortname', 'operator':'+'}]
    for key in ('keys', 'group', 'list', 'range', 'sort', 'query'):
        if key in data:
            query[key] = data[key]
    # print(data)
    query['qs'] = model.query
    if 'query' in data and data['query'].get('conditions'):
        conditions = []
        for c in data['query']['conditions']:
            op = get_operator(c['operator'])
            conditions.append(op(getattr(model, c['key']), c['value']))
        if data['query'].get('operator') == '|':
            q = conditions[0]
            for c in conditions[1:]:
                q = q | c
            q = [q]
        else:
            q = conditions
        for c in q:
            query['qs'] = query['qs'].filter(c)

    query['qs'] = order(query['qs'], query['sort'])
    return query

def order(qs, sort):
    order_by = []
    for e in sort:
        operator = e['operator']
        if operator != '-':
            operator = ''
        else:
            operator = ' DESC'
        key = {}.get(e['key'], e['key'])
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

def editName(data):
    '''
        takes {
            name     string
            sortanme string
        }
    '''
    response = {}
    person = Person.get(data['name'])
    person.sortname = unicodedata.normalize('NFKD', data['sortname'])
    person.save()
    response['name'] = person.name
    response['sortname'] = person.sortname
    return response
actions.register(editName)

def findNames(data):
    '''
        takes {
            query {
                conditions [{}]
                operator   string
            }
            keys  [string]
            sort  [{}]
            range [int, int]
        }
    '''
    response = {}
    q = parse(data, Person)
    if 'position' in data:
        pass
        #ids = [i.id for i in q['qs'].options(load_only('id'))]
        #response['position'] = utils.get_positions(ids, [data['qs'][0].id])[0]
        print('fixme', data)
    elif 'positions' in data:
        #ids = [i.id for i in q['qs'].options(load_only('id'))]
        #response['positions'] = utils.get_positions(ids, data['positions'])
        response['positions'] = []
        print('fixme', data)
    elif 'keys' in data:
        response['items'] = []
        for i in q['qs'][q['range'][0]:q['range'][1]]:
            j = i.json()
            response['items'].append({k:j[k] for k in j if not data['keys'] or k in data['keys']})
    else:
        response['items'] = q['qs'].count()
    return response
actions.register(findNames)
