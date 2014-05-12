# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from datetime import datetime

from flask import json
from oxflask.api import actions
from oxflask.shortcuts import returns_json

import query

import models
import settings
from changelog import Changelog
import re
import state

import utils

@returns_json
def find(request):
    '''
        find items
    '''
    response = {}
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    q = query.parse(data)
    if 'group' in q:
        response['items'] = []
        '''
        items = 'items'
        item_qs = q['qs']
        order_by = query.order_by_group(q)
        qs = models.Facet.objects.filter(key=q['group']).filter(item__id__in=item_qs)
        qs = qs.values('value').annotate(items=Count('id')).order_by(*order_by)

        if 'positions' in q:
            response['positions'] = {}
            ids = [j['value'] for j in qs]
            response['positions'] = utils.get_positions(ids, q['positions'])
        elif 'range' in data:
            qs = qs[q['range'][0]:q['range'][1]]
            response['items'] = [{'name': i['value'], 'items': i[items]} for i in qs]
        else:
            response['items'] = qs.count()
        '''
        _g = {}
        key = utils.get_by_id(settings.config['itemKeys'], q['group'])
        for item in q['qs']:
            i = item.json()
            if q['group'] in i:
                values = i[q['group']]
                if isinstance(values, basestring):
                    values = [values]
                for value in values:
                    if key.get('filterMap') and value:
                        value = re.compile(key.get('filterMap')).findall(value)
                        if value:
                            value = value[0]
                        else:
                            continue
                    if value not in _g:
                        _g[value] = 0
                    _g[value] += 1
        g = [{'name': k, 'items': _g[k]} for k in _g]
        if 'sort' in data: # parse adds default sort to q!
            g.sort(key=lambda k: k[q['sort'][0]['key']])
            if q['sort'][0]['operator'] == '-':
                g.reverse()
        if 'positions' in data:
            response['positions'] = {}
            ids = [k['name'] for k in g]
            response['positions'] = utils.get_positions(ids, data['positions'])
        elif 'range' in data:
            response['items'] = g[q['range'][0]:q['range'][1]]
        else:
            response['items'] = len(g)
    elif 'position' in data:
        ids = [i.id for i in q['qs']]
        response['position'] = utils.get_positions(ids, [data['qs'][0].id])[0]
    elif 'positions' in data:
        ids = [i.id for i in q['qs']]
        response['positions'] = utils.get_positions(ids, data['positions'])
    elif 'keys' in data:
        '''
        qs = qs[q['range'][0]:q['range'][1]]
        response['items'] = [p.json(data['keys']) for p in qs]
        '''
        response['items'] = []
        for i in q['qs'][q['range'][0]:q['range'][1]]:
            j = i.json()
            response['items'].append({k:j[k] for k in j if not data['keys'] or k in data['keys']})
    else:
        items = [i.json() for i in q['qs']]
        response['items'] = len(items)
        response['size'] = sum([i.get('size',0) for i in items])
    return response
actions.register(find)

@returns_json
def get(request):
    response = {}
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    item = models.Item.get(data['id'])
    if item:
        response = item.json(data['keys'] if 'keys' in data else None)
    return response
actions.register(get)

@returns_json
def edit(request):
    response = {}
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    print 'edit', data
    item = models.Item.get(data['id'])
    keys = filter(lambda k: k in models.Item.id_keys, data.keys())
    print item, keys
    if item and keys and item.json()['mediastate'] == 'available':
        key = keys[0]
        print 'update mainid', key, data[key]
        if key in ('isbn10', 'isbn13'):
            data[key] = utils.normalize_isbn(data[key])
        item.update_mainid(key, data[key])
        response = item.json()
    else:
        print 'can only edit available items'
        response = item.json()
    return response
actions.register(edit, cache=False)


@returns_json
def identify(request):
    '''
        takes {
            title: string,
            author: [string],
            publisher: string,
            date: string
        }
        returns {
            title: string,
            autor: [string],
            date: string,
        }
    '''
    response = {}
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    response = {
        'items': [
            {
                 u'title': u'Cinema',
                 u'author': [u'Gilles Deleuze'],
                 u'date': u'1986-10',
                 u'publisher': u'University of Minnesota Press',
                 u'isbn10': u'0816613990',
            },
            {
                u'title': u'How to Change the World: Reflections on Marx and Marxism',
                u'author': [u'Eric Hobsbawm'],
                u'date': u'2011-09-06',
                u'publisher': u'Yale University Press',
                u'isbn13': u'9780300176162',
            }
        ]
    }
    return response
actions.register(identify)

@returns_json
def download(request):
    response = {}
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    item = models.Item.get(data['id'])
    if item:
        item.queue_download()
        item.update()
        response = {'status': 'queued'}
    return response
actions.register(download, cache=False)

@returns_json
def cancelDownload(request):
    response = {}
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    item = models.Item.get(data['id'])
    if item:
        item.transferprogress = None
        item.transferadded = None
        p = state.user()
        if p in item.users:
            item.users.remove(p)
        for l in item.lists.filter_by(user_id=settings.USER_ID):
            l.remove(item)
        item.update()
        response = {'status': 'cancelled'}
    return response
actions.register(cancelDownload, cache=False)

@returns_json
def scan(request):
    state.main.add_callback(state.websockets[0].put, json.dumps(['scan', {}]))
    return {}
actions.register(scan, cache=False)

@returns_json
def _import(request):
    state.main.add_callback(state.websockets[0].put, json.dumps(['import', {}]))
    return {}
actions.register(_import, 'import', cache=False)
