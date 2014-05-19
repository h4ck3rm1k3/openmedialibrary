# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import os
from copy import deepcopy
import json

from oxtornado import actions


import models

from utils import update_dict

import settings
import state
from changelog import Changelog

import logging
logger = logging.getLogger('oml.user.api')


def init(data):
    '''
        takes {
        }
        returns {
            config
            user
                preferences
                ui
        }
    '''
    response = {}
    if os.path.exists(settings.oml_config_path):
        with open(settings.oml_config_path) as fd:
            config = json.load(fd)
    else:
        config = {}
    response['config'] = config
    response['user'] = deepcopy(config['user'])
    if settings.preferences:
        response['user']['preferences'] = settings.preferences
    response['user']['id'] = settings.USER_ID
    response['user']['online'] = state.online
    if settings.ui:
        response['user']['ui'] = settings.ui
    return response
actions.register(init)


def setPreferences(data):
    '''
        takes {
            key: value,
            'sub.key': value
        }
    '''
    update_dict(settings.preferences, data)
    return settings.preferences
actions.register(setPreferences)


def setUI(data):
    '''
        takes {
            key: value,
            'sub.key': value
        }
    '''
    update_dict(settings.ui, data)
    return settings.ui
actions.register(setUI)


def getUsers(data):
    '''
        returns {
            users: []
        }
    '''
    users = []
    for u in models.User.query.filter(models.User.id!=settings.USER_ID).all():
        users.append(u.json())
    return {
        "users": users
    }
actions.register(getUsers)


def getLists(data):
    '''
        returns {
            lists: []
        }
    '''
    from item.models import Item
    lists = []
    lists.append({
        'id': '',
        'items': Item.query.count(),
        'name': 'Libraries',
        'type': 'libraries',
        'user': '',
    })
    for u in models.User.query.filter((models.User.peered==True)|(models.User.id==settings.USER_ID)):
        lists += u.lists_json()
    return {
        'lists': lists
    }
actions.register(getLists)

def validate_query(query):
    for condition in query['conditions']:
        if not list(sorted(condition.keys())) in (
            ['conditions', 'operator'],
            ['key', 'operator', 'value']
        ):
            raise Exception('invalid query condition', condition)


def addList(data):
    '''
        takes {
            name
            items
            query
        }
    '''
    logger.debug('addList %s', data)
    user_id = settings.USER_ID
    if 'query' in data:
        validate_query(data['query'])
    if data['name']:
        l = models.List.create(user_id, data['name'], data.get('query'))
        if 'items' in data:
            l.add_items(data['items'])
        return l.json()
    else:
        raise Exception('name not set')
    return {}
actions.register(addList, cache=False)


def editList(data):
    '''
        takes {
            id
            name
            query
        }
    '''
    logger.debug('editList %s', data)
    l = models.List.get_or_create(data['id'])
    name = l.name
    if 'name' in data:
        l.name = data['name']
    if 'query' in data:
        validate_query(data['query'])
        l._query = data['query']
    if l.type == 'static' and name != l.name:
        Changelog.record(state.user(), 'editlist', name, {'name': l.name})
    l.save()
    return l.json()
actions.register(editList, cache=False)


def removeList(data):
    '''
        takes {
            id
        }
    '''
    l = models.List.get(data['id'])
    if l:
        l.remove()
    return {}
actions.register(removeList, cache=False)



def addListItems(data):
    '''
        takes {
            list
            items
        }
    '''
    if data['list'] == ':':
        from item.models import Item
        user = state.user()
        for item_id in data['items']:
            i = Item.get(item_id)
            if user not in i.users:
                i.queue_download()
    elif data['list']:
        l = models.List.get_or_create(data['list'])
        if l:
            l.add_items(data['items'])
            return l.json()
    return {}
actions.register(addListItems, cache=False)


def removeListItems(data):
    '''
        takes {
            list
            items
        }
    '''
    l = models.List.get(data['list'])
    if l:
        l.remove_items(data['items'])
        return l.json()
    return {}
actions.register(removeListItems, cache=False)


def sortLists(data):
    '''
        takes {
            ids
        }
    '''
    n = 0
    logger.debug('sortLists %s', data)
    for id in data['ids']:
        l = models.List.get(id)
        l.position = n
        n += 1
        models.db.session.add(l)
    models.db.session.commit()
    return {}
actions.register(sortLists, cache=False)


def editUser(data):
    '''
        takes {
            id
            nickname
        }
    '''
    if 'nickname' in data:
        p = models.User.get_or_create(data['id'])
        p.set_nickname(data['nickname'])
        p.save()
    return {}
actions.register(editUser, cache=False)


def dataPeering(data):
    '''
        takes {
            id
            message
        }
    '''
    if len(data.get('id', '')) != 43:
        logger.debug('invalid user id')
        return {}
    u = models.User.get_or_create(data['id'])
    u.pending = 'sent'
    u.queued = True
    u.info['message'] = data.get('message', '')
    u.save()
    state.nodes.queue('add', u.id)
    state.nodes.queue(u.id, 'peering', 'dataPeering')
    return {}
actions.register(dataPeering, cache=False)


def acceptPeering(data):
    '''
        takes {
            id
            message
        }
    '''
    if len(data.get('id', '')) != 43:
        logger.debug('invalid user id')
        return {}
    logger.debug('acceptPeering... %s', data)
    u = models.User.get_or_create(data['id'])
    u.info['message'] = data.get('message', '')
    u.update_peering(True)
    state.nodes.queue('add', u.id)
    state.nodes.queue(u.id, 'peering', 'acceptPeering')
    return {}
actions.register(acceptPeering, cache=False)


def rejectPeering(data):
    '''
        takes {
            id
            message
        }
    '''
    if len(data.get('id', '')) != 43:
        logger.debug('invalid user id')
        return {}
    u = models.User.get_or_create(data['id'])
    u.info['message'] = data.get('message', '')
    u.update_peering(False)
    state.nodes.queue('add', u.id)
    state.nodes.queue(u.id, 'peering', 'rejectPeering')
    return {}
actions.register(rejectPeering, cache=False)


def removePeering(data):
    '''
        takes {
            id
            message
        }
    '''
    if len(data.get('id', '')) != 43:
        logger.debug('invalid user id')
        return {}
    u = models.User.get_or_create(data['id'])
    u.info['message'] = data.get('message', '')
    u.update_peering(False)
    state.nodes.queue('add', u.id)
    state.nodes.queue(u.id, 'peering', 'removePeering')
    return {}
actions.register(removePeering, cache=False)


def cancelPeering(data):
    '''
        takes {
        }
    '''
    if len(data.get('id', '')) != 43:
        logger.debug('invalid user id')
        return {}
    u = models.User.get_or_create(data['id'])
    u.info['message'] = data.get('message', '')
    u.update_peering(False)
    state.nodes.queue('add', u.id)
    state.nodes.queue(u.id, 'peering', 'cancelPeering')
    return {}
actions.register(cancelPeering, cache=False)


def getActivity(data):
    '''
        return {
            activity
            progress
        }
    '''
    return state.activity
actions.register(getActivity, cache=False)

