# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import os
import shutil
from datetime import datetime

import ox

from app import app
import settings
from settings import db
from item.models import File
from user.models import User

from changelog import Changelog

import media
from websocket import trigger_event

def remove_missing():
    dirty = False
    with app.app_context():
        user = User.get_or_create(settings.USER_ID)
        prefs = settings.preferences
        prefix = os.path.join(os.path.expanduser(prefs['libraryPath']), 'Books/')
        for f in File.query:
            if not os.path.exists(f.item.get_path()):
                dirty = True
                print 'file gone', f, f.item.get_path()
                f.item.users.remove(user)
                if not f.item.users:
                    print 'last user, remove'
                    db.session.delete(f.item)
                else:
                    f.item.update_lists()
                Changelog.record(user, 'removeitem', f.item.id)
                db.session.delete(f)
        if dirty:
            db.session.commit()

def run_scan():
    remove_missing()
    with app.app_context():
        prefs = settings.preferences
        prefix = os.path.join(os.path.expanduser(prefs['libraryPath']), 'Books/')
        if not prefix[-1] == '/':
            prefix += '/'
        user = User.get_or_create(settings.USER_ID)
        assert isinstance(prefix, unicode)
        extensions = ['pdf', 'epub', 'txt']
        books = []
        for root, folders, files in os.walk(prefix):
            for f in files:
                #if f.startswith('._') or f == '.DS_Store':
                if f.startswith('.'):
                    continue
                f = os.path.join(root, f)
                ext = f.split('.')[-1]
                if ext in extensions:
                    books.append(f)

        trigger_event('scan', {
            'path': prefix,
            'files': len(books)
        })
        position = 0
        added = 0
        for f in ox.sorted_strings(books):
            position += 1
            id = media.get_id(f)
            file = File.get(id)
            path = f[len(prefix):]
            if not file:
                data = media.metadata(f)
                ext = f.split('.')[-1]
                data['extension'] = ext
                data['size'] = os.stat(f).st_size
                file = File.get_or_create(id, data, path)
                item = file.item
                if 'mainid' in file.info:
                    del file.info['mainid']
                    db.session.add(file)
                if 'mainid' in item.info:
                    item.meta['mainid'] = item.info.pop('mainid')
                    item.meta[item.meta['mainid']] = item.info[item.meta['mainid']]
                    db.session.add(item)
                item.users.append(user)
                Changelog.record(user, 'additem', item.id, item.info)
                if item.meta.get('mainid'):
                    Changelog.record(user, 'edititem', item.id, {
                        item.meta['mainid']: item.meta[item.meta['mainid']]
                    })
                item.added = datetime.now()
                item.scrape()
                added += 1
            trigger_event('scan', {
                'position': position,
                'length': len(books),
                'path': path,
                'progress': position/len(books),
                'added': added,
            })
        trigger_event('scan', {
            'progress': 1,
            'added': added,
            'done': True
        })

def run_import():
    with app.app_context():
        prefs = settings.preferences
        prefix = os.path.expanduser(prefs['importPath'])
        prefix_books = os.path.join(os.path.expanduser(prefs['libraryPath']), 'Books/')
        prefix_imported = os.path.join(prefix_books, 'Imported/')
        if not prefix[-1] == '/':
            prefix += '/'
        user = User.get_or_create(settings.USER_ID)
        assert isinstance(prefix, unicode)
        extensions = ['pdf', 'epub', 'txt']
        books = []
        for root, folders, files in os.walk(prefix):
            for f in files:
                #if f.startswith('._') or f == '.DS_Store':
                if f.startswith('.'):
                    continue
                f = os.path.join(root, f)
                ext = f.split('.')[-1]
                if ext in extensions:
                    books.append(f)

        trigger_event('import', {
            'path': prefix,
            'files': len(books)
        })
        position = 0
        added = 0
        for f in ox.sorted_strings(books):
            position += 1
            id = media.get_id(f)
            file = File.get(id)
            path = f[len(prefix):]
            if not file:
                f_import = f
                f = f.replace(prefix, prefix_imported)
                ox.makedirs(os.path.dirname(f))
                shutil.move(f_import, f)
                path = f[len(prefix_books):]
                data = media.metadata(f)
                ext = f.split('.')[-1]
                data['extension'] = ext
                data['size'] = os.stat(f).st_size
                file = File.get_or_create(id, data, path)
                item = file.item
                if 'mainid' in file.info:
                    del file.info['mainid']
                    db.session.add(file)
                if 'mainid' in item.info:
                    item.meta['mainid'] = item.info.pop('mainid')
                    item.meta[item.meta['mainid']] = item.info[item.meta['mainid']]
                    db.session.add(item)
                item.users.append(user)
                Changelog.record(user, 'additem', item.id, item.info)
                if item.meta.get('mainid'):
                    Changelog.record(user, 'edititem', item.id, {
                        item.meta['mainid']: item.meta[item.meta['mainid']]
                    })
                item.scrape()
                added += 1
            trigger_event('import', {
                'position': position,
                'length': len(books),
                'path': path,
                'progress': position/len(books),
                'added': added,
            })
        trigger_event('import', {
            'progress': 1,
            'added': added,
            'done': True
        })
