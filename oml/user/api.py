# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import os
from copy import deepcopy
import subprocess
import json

from oxflask.api import actions
from oxflask.shortcuts import returns_json

import models

from utils import get_position_by_id

import settings
import state
from changelog import Changelog

@returns_json
def init(request):
    '''
        this is an init request to test stuff
    '''
    #print 'init', request
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

def update_dict(root, data):
    for key in data:
        keys = map(lambda p: p.replace('\0', '\\.'), key.replace('\\.', '\0').split('.'))
        value = data[key]
        p = root
        while len(keys)>1:
            key = keys.pop(0)
            if isinstance(p, list):
                p = p[get_position_by_id(p, key)]
            else:
                if key not in p:
                    p[key] = {}
                p = p[key]
        if value == None and keys[0] in p:
            del p[keys[0]]
        else:
            p[keys[0]] = value

@returns_json
def setPreferences(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    update_dict(settings.preferences, data)
    return settings.preferences
actions.register(setPreferences)

@returns_json
def setUI(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    update_dict(settings.ui, data)
    return settings.ui
actions.register(setUI)

@returns_json
def getUsers(request):
    users = []
    for u in models.User.query.filter(models.User.id!=settings.USER_ID).all():
        users.append(u.json())
    return {
        "users": users
    }
actions.register(getUsers)

@returns_json
def getLists(request):
    lists = []
    for u in models.User.query.filter((models.User.peered==True)|(models.User.id==settings.USER_ID)):
        lists += u.lists_json()
    return {
        'lists': lists
    }
actions.register(getLists)

@returns_json
def addList(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    user_id = settings.USER_ID
    l = models.List.get(user_id, data['name'])
    if not l:
        l = models.List.create(user_id, data['name'], data.get('query'))
        if 'items' in data:
            l.add_items(data['items'])
        return l.json()
    return {}
actions.register(addList, cache=False)

@returns_json
def removeList(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    l = models.List.get(data['id'])
    if l:
        l.remove()
    return {}
actions.register(removeList, cache=False)

@returns_json
def editList(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    l = models.List.get_or_create(data['id'])
    name = l.name
    if 'name' in data:
        l.name = data['name']
    if 'query' in data:
        l._query = data['query']
    if l.type == 'static' and name != l.name:
        Changelog.record(state.user(), 'editlist', name, {'name': l.name})
    l.save()
    return {}
actions.register(editList, cache=False)

@returns_json
def addListItems(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    l = models.List.get_or_create(data['list'])
    if l:
        l.add_items(data['items'])
        return l.json()
    return {}
actions.register(addListItems, cache=False)

@returns_json
def removeListItems(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    l = models.List.get(data['list'])
    if l:
        l.remove_items(data['items'])
        return l.json()
    return {}
actions.register(removeListItems, cache=False)

@returns_json
def sortLists(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    n = 0
    print 'sortLists', data
    for id in data['ids']:
        l = models.List.get(id)
        l.position = n
        n += 1
        models.db.session.add(l)
    models.db.session.commit()
    return {}
actions.register(sortLists, cache=False)

@returns_json
def editUser(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    if 'nickname' in data:
        p = models.User.get_or_create(data['id'])
        p.set_nickname(data['nickname'])
        p.save()
    return {}
actions.register(editUser, cache=False)

@returns_json
def requestPeering(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    if len(data.get('id', '')) != 43:
        print 'invalid user id'
        return {}
    p = models.User.get_or_create(data['id'])
    state.nodes.queue('add', p.id)
    state.nodes.queue(p.id, 'requestPeering', data.get('message', ''))
    return {}
actions.register(requestPeering, cache=False)

@returns_json
def acceptPeering(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    if len(data.get('id', '')) != 43:
        print 'invalid user id'
        return {}
    p = models.User.get_or_create(data['id'])
    state.nodes.queue('add', p.id)
    state.nodes.queue(p.id, 'acceptPeering', data.get('message', ''))
    return {}
actions.register(acceptPeering, cache=False)

@returns_json
def rejectPeering(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    if len(data.get('id', '')) != 43:
        print 'invalid user id'
        return {}
    p = models.User.get_or_create(data['id'])
    state.nodes.queue('add', p.id)
    state.nodes.queue(p.id, 'rejectPeering', data.get('message', ''))
    return {}
actions.register(rejectPeering, cache=False)

@returns_json
def removePeering(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    if len(data.get('id', '')) != 43:
        print 'invalid user id'
        return {}
    u = models.User.get_or_create(data['id'])
    state.nodes.queue('add', u.id)
    state.nodes.queue(u.id, 'removePeering', data.get('message', ''))
    return {}
actions.register(removePeering, cache=False)

@returns_json
def cancelPeering(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    if len(data.get('id', '')) != 43:
        print 'invalid user id'
        return {}
    p = models.User.get_or_create(data['id'])
    state.nodes.queue('add', p.id)
    state.nodes.queue(p.id, 'cancelPeering', data.get('message', ''))
    return {}
actions.register(cancelPeering, cache=False)

@returns_json
def getActivity(request):
    return state.activity
actions.register(getActivity, cache=False)

@returns_json
def selectFolder(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    cmd = ['./ctl', 'ui', 'folder']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    path = stdout.decode('utf-8').strip()
    return {
        'path': path
    }
actions.register(selectFolder, cache=False)

@returns_json
def selectFile(request):
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    cmd = ['./ctl', 'ui', 'file']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    path = stdout.decode('utf-8').strip()
    return {
        'path': path
    }
actions.register(selectFile, cache=False)
