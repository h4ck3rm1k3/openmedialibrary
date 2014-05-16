# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

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

import meta

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
        names = {}
        groups = {}
        items = [i.id for i in q['qs']]
        qs = models.Find.query.filter_by(key=q['group'])
        if items:
            qs = qs.filter(models.Find.item_id.in_(items))
        for f in qs.values('value', 'findvalue'):
            value = f[0]
            findvalue = f[1]
            if findvalue not in groups:
                groups[findvalue] = 0
            groups[findvalue] += 1
            names[findvalue] = value
        g = [{'name': names[k], 'items': groups[k]} for k in groups]
        if 'sort' in q:
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
        response['items'] = q['qs'].count()
        #from sqlalchemy.sql import func
        #models.db.session.query(func.sum(models.Item.sort_size).label("size"))
        #response['size'] = x.scalar()
        response['size'] = sum([i.sort_size or 0 for i in q['qs']])
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
def findMetadata(request):
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
    print 'findMetadata', data
    response['items'] = meta.find(**data)
    return response
actions.register(findMetadata)

@returns_json
def getMetadata(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    print 'getMetadata', data
    key, value = data.iteritems().next()
    if key in ('isbn10', 'isbn13'):
        value = utils.normalize_isbn(value)
    response = meta.lookup(key, value)
    response['mainid'] = key
    return response
actions.register(getMetadata)

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
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    print 'api.import', data
    state.main.add_callback(state.websockets[0].put, json.dumps(['import', data]))
    return {}
actions.register(_import, 'import', cache=False)
