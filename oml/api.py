# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import subprocess
import json
import os

import ox
from oxtornado import actions


import settings

import item.api
import user.api


def selectFolder(data):
    '''
        returns {
            path
        }
    '''
    cmd = ['./ctl', 'ui', 'folder']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
    stdout, stderr = p.communicate()
    path = stdout.decode('utf-8').strip()
    return {
        'path': path
    }
actions.register(selectFolder, cache=False)


def selectFile(data):
    '''
        returns {
            path
        }
    '''
    cmd = ['./ctl', 'ui', 'file']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    path = stdout.decode('utf-8').strip()
    return {
        'path': path
    }
actions.register(selectFile, cache=False)



def autocompleteFolder(data):
    '''
        takes {
            path
        }
        returns {
            items
        }
    '''
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

def getVersion(data):
    '''
        check if new version is available
    '''
    response = {
        'current': settings.MINOR_VERSION,
        'upgrade': False,
    }
    if not os.path.exists(os.path.join(settings.updates_path, 'release.json')):
        return response
    if not os.path.exists(os.path.join(settings.config_path, 'release.json')):
        return response
    with open(os.path.join(settings.updates_path, 'release.json')) as fd:
        release = json.load(fd)
    current = settings.release['modules']['openmedialibrary']['version']
    response['current'] = current
    new = release['modules']['openmedialibrary']['version']
    response['new'] = new
    response['update'] = current < new
    return response
actions.register(getVersion, cache=False)

def restart(data):
    '''
        restart (and upgrade if upgrades are available)
    '''
    subprocess.Popen(['./ctl', 'restart'], close_fds=True)
    return {}
actions.register(restart, cache=False)
