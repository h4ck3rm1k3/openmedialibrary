# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import json
import hashlib

from sqlalchemy.orm import load_only

from oxtornado import actions
from utils import cleanup_id
from websocket import trigger_event
import metaremote as meta
from . import models
from . import query
import settings
import state
import utils

import logging
logger = logging.getLogger('oml.item.api')


def find(data):
    '''
        takes {
            query {
                conditions [{}]
                operator   string
            }
            group string
            keys  [string]
            sort  [{}]
            range [int, int]
        }
    '''
    response = {}
    q = query.parse(data)
    if 'group' in q:
        names = {}
        groups = {}
        key = 'group:' + hashlib.sha1(json.dumps(data)).hexdigest()
        g = state.cache.get(key)
        if g is None:
            items = [i.id for i in q['qs'].options(load_only('id'))]
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
            else:
                g = []
            if 'sort' in q:
                g.sort(key=lambda k: k[q['sort'][0]['key']])
                if q['sort'][0]['operator'] == '-':
                    g.reverse()
            state.cache.set(key, g)
        if 'positions' in data:
            response['positions'] = {}
            ids = [k['name'] for k in g]
            response['positions'] = utils.get_positions(ids, data['positions'])
        elif 'range' in data:
            response['items'] = g[q['range'][0]:q['range'][1]]
        else:
            response['items'] = len(g)
    elif 'position' in data:
        ids = [i.id for i in q['qs'].options(load_only('id'))]
        response['position'] = utils.get_positions(ids, [data['qs'][0].id])[0]
    elif 'positions' in data:
        ids = [i.id for i in q['qs'].options(load_only('id'))]
        response['positions'] = utils.get_positions(ids, data['positions'])
    elif 'keys' in data:
        response['items'] = []
        for i in q['qs'][q['range'][0]:q['range'][1]]:
            j = i.json()
            response['items'].append({k:j[k] for k in j if not data['keys'] or k in data['keys']})
    else:
        size = [i.info.get('size', 0) for i in q['qs'].join(models.Sort).options(load_only('id', 'info'))]
        response['items'] = len(size)
        response['size'] = sum(size)
    return response
actions.register(find)


def get(data):
    '''
        takes {
            id
            keys
        }
    '''
    response = {}
    item = models.Item.get(data['id'])
    if item:
        response = item.json(data['keys'] if 'keys' in data else None)
    return response
actions.register(get)


def edit(data):
    '''
        takes {
            id
            ...
        }
        setting identifier or base metadata is possible not both at the same time
    '''
    response = {}
    item = models.Item.get(data['id'])
    if item and item.json()['mediastate'] == 'available':
        if 'primaryid' in data:
            if data['primaryid']:
                key, value = data['primaryid']
                logger.debug('update primaryid %s %s', key, value)
                value = cleanup_id(key, value)
                item.update_primaryid(key, value)
            else:
                item.update_primaryid()
            response = item.json()
        else:
            item.edit_metadata(data)
            response = item.json()
    else:
        logger.info('can only edit available items')
    return response
actions.register(edit, cache=False)


def remove(data):
    '''
        takes {
            id
        }
    '''
    logger.debug('remove files %s', data)
    if 'ids' in data and data['ids']:
        for i in models.Item.query.filter(models.Item.id.in_(data['ids'])):
            i.remove_file()
    return {
        'items': []
    }
actions.register(remove, cache=False)

def autocomplete(data):
    return {}
actions.register(remove, cache=False)

def findMetadata(data):
    '''
        takes {
            query: string,
        }
        returns {
            items: [{
                key: value
            }]
        }
        key is one of the supported identifiers: isbn10, isbn13...
    '''
    response = {}
    logger.debug('findMetadata %s', data)
    response['items'] = meta.find(data['query'])
    return response
actions.register(findMetadata)


def getMetadata(data):
    '''
        takes {
            key: value
            includeEdits: boolean
        }
        key can be one of the supported identifiers: isbn10, isbn13, oclc, olid,...
    '''
    logger.debug('getMetadata %s', data)
    if 'includeEdits' in data:
        include_edits = data.pop('includeEdits')
    else:
        include_edits = False
    key, value = next(iter(data.items()))
    value = cleanup_id(key, value)
    response = meta.lookup(key, value)
    if include_edits:
        response.update(models.Metadata.load(key, value))
    if response:
        response['primaryid'] = [key, value]
    return response
actions.register(getMetadata)


def resetMetadata(data):
    item = models.Item.get(data['id'])
    if item and 'primaryid' in item.meta:
        meta = models.Metadata.get(*item.meta['primaryid'])
        if meta:
            meta.reset()
    return {}
actions.register(resetMetadata)


def download(data):
    '''
        takes {
            id
        }
    '''
    response = {}
    item = models.Item.get(data['id'])
    if item:
        item.queue_download()
        item.update()
        response = {'status': 'queued'}
    return response
actions.register(download, cache=False)


def cancelDownloads(data):
    '''
        takes {
            ids
        }
    '''
    response = {}
    ids = data['ids']
    if ids:
        for item in models.Item.query.filter(models.Item.id.in_(ids)):
            t = models.Transfer.get(item.id)
            t.progress = None
            t.added = None
            t.save()
            p = state.user()
            if p in item.users:
                item.users.remove(p)
            for l in item.lists.filter_by(user_id=settings.USER_ID):
                l.items.remove(item)
            item.update()
        response = {'status': 'cancelled'}
    return response
actions.register(cancelDownloads, cache=False)


def scan(data):
    state.tasks.queue('scan', {})
    return {}
actions.register(scan, cache=False)


def _import(data):
    '''
        takes {
            path absolute path to import
            list listename (add new items to this list)
            mode copy|move
        }
    '''
    logger.debug('api.import %s', data)
    state.tasks.queue('import', data)
    return {}
actions.register(_import, 'import', cache=False)


def cancelImport(data):
    state.activity['cancel'] = True
    trigger_event('activity', {
        'activity': 'import',
        'progress': [0, 0],
        'status': {'code': 200, 'text': 'canceled'}
    })
    return {}
actions.register(cancelImport, cache=False)
