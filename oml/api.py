# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import subprocess
import json
import os

import ox
from oxflask.api import actions
from oxflask.shortcuts import returns_json

import item.api
import user.api

@returns_json
def selectFolder(request):
    '''
        returns {
            path
        }
    '''
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
    '''
        returns {
            path
        }
    '''
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    cmd = ['./ctl', 'ui', 'file']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    path = stdout.decode('utf-8').strip()
    return {
        'path': path
    }
actions.register(selectFile, cache=False)


@returns_json
def autocompleteFolder(request):
    '''
        takes {
            path
        }
        returns {
            items
        }
    '''
    data = json.loads(request.form['data']) if 'data' in request.form else {}
    path = data['path']
    path = os.path.expanduser(path)
    if os.path.isdir(path):
        if path.endswith('/') and path != '/':
            path = path[:-1]
        folder = path
        name = ''
    else:
        folder, name = os.path.split(path)
    if os.path.exists(folder):
        prefix, folders, files = os.walk(folder).next()
        folders = [os.path.join(prefix, f) for f in folders if (not name or f.startswith(name)) and not f.startswith('.')]
        if prefix == path:
            folders = [path] + folders
    else:
        folders = []
    return {
        'items': ox.sorted_strings(folders)
    }
actions.register(autocompleteFolder, cache=False)
