# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from datetime import datetime
import os
import shutil
import time

import ox

from changelog import Changelog
from item.models import File, Scrape
from user.models import List
from utils import remove_empty_folders
from websocket import trigger_event
import db
import media
import settings
import state

import logging
logger = logging.getLogger('oml.item.scan')

extensions = ['epub', 'pdf', 'txt', 'cbr', 'cbz']

def remove_missing():
    dirty = False
    with db.session():
        prefs = settings.preferences
        prefix = os.path.join(os.path.expanduser(prefs['libraryPath']), 'Books/')
        if os.path.exists(prefix):
            for f in File.query:
                if not state.tasks.connected:
                    return
                path = f.item.get_path()
                if not os.path.exists(path):
                    dirty = True
                    f.item.remove_file()
            if dirty:
                state.db.session.commit()

def add_file(id, f, prefix, from_=None):
    user = state.user()
    path = f[len(prefix):]
    data = media.metadata(f, from_)
    print(path)
    file = File.get_or_create(id, data, path)
    item = file.item
    if 'primaryid' in file.info:
        del file.info['primaryid']
        state.db.session.add(file)
    if 'primaryid' in item.info:
        item.meta['primaryid'] = item.info.pop('primaryid')
        state.db.session.add(item)
    item.users.append(user)
    Changelog.record(user, 'additem', item.id, file.info)
    if item.meta.get('primaryid'):
        Changelog.record(user, 'edititem', item.id, dict([item.meta['primaryid']]))
    item.added = datetime.utcnow()
    item.update_icons()
    item.modified = datetime.utcnow()
    item.update()
    Scrape.get_or_create(item.id)
    return file

def run_scan():
    remove_missing()
    with db.session():
        prefs = settings.preferences
        prefix = os.path.join(os.path.expanduser(prefs['libraryPath']), 'Books/')
        if not prefix[-1] == '/':
            prefix += '/'
        assert isinstance(prefix, str)
        books = []
        for root, folders, files in os.walk(prefix):
            for f in files:
                if not state.tasks.connected:
                    return
                #if f.startswith('._') or f == '.DS_Store':
                if f.startswith('.'):
                    continue
                f = os.path.join(root, f)
                ext = f.split('.')[-1]
                if ext in extensions:
                    books.append(f)

        position = 0
        added = 0
        for f in ox.sorted_strings(books):
            if not state.tasks.connected:
                return
            position += 1
            id = media.get_id(f)
            file = File.get(id)
            if not file:
                file = add_file(id, f, prefix, f)
                added += 1
                trigger_event('change', {})

def run_import(options=None):
    options = options or {}

    with db.session():
        logger.debug('run_import')
        prefs = settings.preferences
        prefix = os.path.expanduser(options.get('path', prefs['importPath']))
        if os.path.islink(prefix):
            prefix = os.path.realpath(prefix)
        if not prefix[-1] == '/':
            prefix += '/'
        prefix_books = os.path.join(os.path.expanduser(prefs['libraryPath']), 'Books/')
        prefix_imported = os.path.join(prefix_books, 'Imported/')
        if prefix_books.startswith(prefix) or prefix.startswith(prefix_books):
            error = 'invalid path'
        elif not os.path.exists(prefix):
            error = 'path not found'
        elif not os.path.isdir(prefix):
            error = 'path must be a folder'
        else:
            error = None
        if error:
            trigger_event('activity', {
                'activity': 'import',
                'progress': [0, 0],
                'status': {'code': 404, 'text': error}
            })
            state.activity = {}
            return
        listname = options.get('list')
        if listname:
            listitems = []
        assert isinstance(prefix, str)
        books = []
        count = 0
        for root, folders, files in os.walk(prefix):
            for f in files:
                if not state.tasks.connected:
                    return
                #if f.startswith('._') or f == '.DS_Store':
                if f.startswith('.'):
                    continue
                f = os.path.join(root, f)
                ext = f.split('.')[-1]
                if ext in extensions:
                    books.append(f)
                    count += 1
                    if state.activity.get('cancel'):
                        state.activity = {}
                        return
                    if count % 1000 == 0:
                        state.activity = {
                            'activity': 'import',
                            'path': prefix,
                            'progress': [0, count],
                        }
                        trigger_event('activity', state.activity)
        state.activity = {
            'activity': 'import',
            'path': prefix,
            'progress': [0, len(books)],
        }
        trigger_event('activity', state.activity)
        position = 0
        added = 0
        last = 0
        for f in ox.sorted_strings(books):
            position += 1
            if not os.path.exists(f):
                continue
            id = media.get_id(f)
            file = File.get(id)
            if not file:
                f_import = f
                f = f.replace(prefix, prefix_imported)
                ox.makedirs(os.path.dirname(f))
                if options.get('mode') == 'move':
                    shutil.move(f_import, f)
                else:
                    shutil.copy(f_import, f)
                file = add_file(id, f, prefix_books, f_import)
                file.move()
                added += 1
            if listname:
                listitems.append(file.item.id)
            if time.time() - last > 5:
                last = time.time()
                state.activity = {
                    'activity': 'import',
                    'progress': [position, len(books)],
                    'path': prefix,
                    'added': added,
                }
                trigger_event('activity', state.activity)

            if state.activity.get('cancel'):
                state.activity = {}
                return
        if listname and listitems:
            l = List.get(settings.USER_ID, listname)
            if l:
                l.add_items(listitems)
        trigger_event('activity', {
            'activity': 'import',
            'progress': [position, len(books)],
            'path': prefix,
            'status': {'code': 200, 'text': ''},
            'added': added,
        })
        state.activity = {}
        remove_empty_folders(prefix_books)
        if options.get('mode') == 'move':
            remove_empty_folders(prefix)
