# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import os
import re
import base64
import json
import hashlib
from datetime import datetime
from StringIO import StringIO
import shutil
import logging

import Image
import ox

import settings
from settings import db, config

from person import get_sort_name

import media
import meta

import state
import utils

from oxflask.db import MutableDict

from covers import covers
from changelog import Changelog
from websocket import trigger_event
from utils import remove_empty_folders

logger = logging.getLogger('oml.item.model')

class Work(db.Model):

    created = db.Column(db.DateTime())
    modified = db.Column(db.DateTime())

    id = db.Column(db.String(32), primary_key=True)

    meta = db.Column(MutableDict.as_mutable(db.PickleType(pickler=json)))

    def __repr__(self):
        return self.id

    def __init__(self, id):
        self.id = id
        self.created = datetime.utcnow()
        self.modified = datetime.utcnow()

class Edition(db.Model):

    created = db.Column(db.DateTime())
    modified = db.Column(db.DateTime())

    id = db.Column(db.String(32), primary_key=True)

    meta = db.Column(MutableDict.as_mutable(db.PickleType(pickler=json)))

    work_id = db.Column(db.String(32), db.ForeignKey('work.id'))
    work = db.relationship('Work', backref=db.backref('editions', lazy='dynamic'))

    def __repr__(self):
        return self.id

    def __init__(self, id):
        self.id = id
        self.created = datetime.utcnow()
        self.modified = datetime.utcnow()

user_items = db.Table('useritem',
    db.Column('user_id', db.String(43), db.ForeignKey('user.id')),
    db.Column('item_id', db.String(32), db.ForeignKey('item.id'))
)

class Item(db.Model):

    created = db.Column(db.DateTime())
    modified = db.Column(db.DateTime())

    id = db.Column(db.String(32), primary_key=True)

    info = db.Column(MutableDict.as_mutable(db.PickleType(pickler=json)))
    meta = db.Column(MutableDict.as_mutable(db.PickleType(pickler=json)))

    added = db.Column(db.DateTime()) # added to local library
    accessed = db.Column(db.DateTime())
    timesaccessed = db.Column(db.Integer())

    transferadded = db.Column(db.DateTime())
    transferprogress = db.Column(db.Float())

    users = db.relationship('User', secondary=user_items,
        backref=db.backref('items', lazy='dynamic'))

    edition_id = db.Column(db.String(32), db.ForeignKey('edition.id'))
    edition = db.relationship('Edition', backref=db.backref('items', lazy='dynamic'))

    work_id = db.Column(db.String(32), db.ForeignKey('work.id'))
    work = db.relationship('Work', backref=db.backref('items', lazy='dynamic'))

    @property
    def timestamp(self):
        return self.modified.strftime('%s')

    def __repr__(self):
        return self.id

    def __init__(self, id):
        if isinstance(id, list):
            id = base64.b32encode(hashlib.sha1(''.join(id)).digest())
        self.id = id
        self.created = datetime.utcnow()
        self.modified = datetime.utcnow()
        self.info = {}
        self.meta = {}

    @classmethod
    def get(cls, id):
        if isinstance(id, list):
            id = base64.b32encode(hashlib.sha1(''.join(id)).digest())
        return cls.query.filter_by(id=id).first()

    @classmethod
    def get_or_create(cls, id, info=None):
        if isinstance(id, list):
            id = base64.b32encode(hashlib.sha1(''.join(id)).digest())
        item = cls.query.filter_by(id=id).first()
        if not item:
            item = cls(id=id)
            if info:
                item.info = info
            db.session.add(item)
            db.session.commit()
        return item

    def json(self, keys=None):
        j  = {}
        j['id'] = self.id
        j['created'] = self.created
        j['modified'] = self.modified
        j['timesaccessed'] = self.timesaccessed
        j['accessed'] = self.accessed
        j['added'] = self.added
        j['transferadded'] = self.transferadded
        j['transferprogress'] = self.transferprogress
        j['users'] = map(str, list(self.users))

        if self.info:
            j.update(self.info)
        if self.meta:
            j.update(self.meta)

        for key in self.id_keys + ['mainid']:
            if key not in self.meta and key in j:
                del j[key]
        '''
        if self.work_id:
            j['work'] = {
                'olid': self.work_id
            }
            j['work'].update(self.work.meta)
        '''
        if keys:
            for k in j.keys():
                if k not in keys:
                    del j[k]
        return j

    def get_path(self):
        f = self.files.first()
        return f.fullpath() if f else None

    def update_sort(self):
        for key in config['itemKeys']:
            if key.get('sort'):
                value = self.json().get(key['id'], None)
                sort_type = key.get('sortType', key['type'])
                if value:
                    if sort_type == 'integer':
                        value = int(value)
                    elif sort_type == 'float':
                        value = float(value)
                    elif sort_type == 'date':
                        pass
                    elif sort_type == 'name':
                        if not isinstance(value, list):
                            value = [value]
                        value = map(get_sort_name, value)
                        value = ox.sort_string(u'\n'.join(value))
                    elif sort_type == 'title':
                        value = utils.sort_title(value).lower()
                    else:
                        if isinstance(value, list):
                            value = u'\n'.join(value)
                        if value:
                            value = unicode(value)
                            value = ox.sort_string(value).lower()
                elif isinstance(value, list): #empty list
                    value = ''
                setattr(self, 'sort_%s' % key['id'], value)

    def update_find(self):

        def add(k, v):
            f = Find(item_id=self.id, key=k)
            f.findvalue = v.lower().strip()
            f.value = v
            db.session.add(f)

        for key in config['itemKeys']:
            if key.get('find') or key.get('filter'):
                value = self.json().get(key['id'], None)
                if key.get('filterMap') and value:
                    value = re.compile(key.get('filterMap')).findall(value)
                    if value: value = value[0]
                if value:
                    Find.query.filter_by(item_id=self.id, key=key['id']).delete()
                    if not isinstance(value, list):
                        value = [value]
                    for v in value:
                        add(key['id'], v)
                else:
                    f = Find.get(self.id, key['id'])
                    if f:
                        db.session.delete(f)

    def update_lists(self):
        Find.query.filter_by(item_id=self.id, key='list').delete()
        for p in self.users:
            f = Find()
            f.item_id = self.id
            f.key = 'list'
            if p.id == settings.USER_ID:
                f.value = ':'
            else:
                f.value = '%s:' % p.id
            db.session.add(f)
        for l in self.lists:
            f = Find()
            f.item_id = self.id
            f.key = 'list'
            f.value = l.find_id
            db.session.add(f)

    def update(self):
        for key in ('mediastate', 'coverRatio'):
            if key in self.meta:
                if key not in self.info:
                    self.info[key] = self.meta[key]
                del self.meta[key]
        users = map(str, list(self.users))
        self.info['mediastate'] = 'available' # available, unavailable, transferring
        if self.transferadded and self.transferprogress < 1:
            self.info['mediastate'] = 'transferring'
        else:
            self.info['mediastate'] = 'available' if settings.USER_ID in users else 'unavailable'
        self.update_sort()
        self.update_find()
        self.update_lists()
        #self.modified = datetime.utcnow()
        self.save()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update_meta(self, data):
        if data != self.meta:
            self.meta = data
            self.update()
            self.modified = datetime.utcnow()
            self.save()
            user = state.user()
            if user in self.users:
                Changelog.record(user, 'edititem', self.id, data)

    def update_mainid(self, key, id):
        record = {}
        if id:
            self.meta[key] = id
            self.meta['mainid'] = key
            record[key] = id
        else:
            if key in self.meta:
                del self.meta[key]
            if 'mainid' in self.meta:
                del self.meta['mainid']
            record[key] = ''
        for k in self.id_keys:
            if k != key:
                if k in self.meta:
                    del self.meta[k]
        logger.debug('mainid %s %s', 'mainid' in self.meta, self.meta.get('mainid'))
        logger.debug('key %s %s', key, self.meta.get(key))

        # get metadata from external resources
        self.scrape()
        self.update()
        self.update_cover()
        self.modified = datetime.utcnow()
        self.save()
        user = state.user()
        if user in self.users:
            Changelog.record(user, 'edititem', self.id, record)

    def extract_cover(self):
        path = self.get_path()
        if path:
            return getattr(media, self.info['extension']).cover(path)

    def update_cover(self):
        cover = None
        if 'cover' in self.meta and self.meta['cover']:
            cover = ox.cache.read_url(self.meta['cover'])
            #covers[self.id] = requests.get(self.meta['cover']).content
            if cover:
                covers[self.id] = cover
        else:
            if covers[self.id]:
                del covers[self.id]
        path = self.get_path()
        if not cover and path:
            cover = self.extract_cover()
            if cover:
                covers[self.id] = cover
        if cover:
            img = Image.open(StringIO(cover))
            self.info['coverRatio'] = img.size[0]/img.size[1]
        for p in (':128', ':256', ':512'):
            del covers['%s%s' % (self.id, p)]
        return cover

    def scrape(self):
        mainid = self.meta.get('mainid')
        logger.debug('scrape %s %s', mainid, self.meta.get(mainid))
        if mainid:
            m = meta.lookup(mainid, self.meta[mainid])
            self.meta.update(m)
        self.update()

    def queue_download(self):
        u = state.user()
        if not u in self.users:
            self.transferprogress = 0
            self.transferadded = datetime.utcnow()
            self.users.append(u)

    def save_file(self, content):
        u = state.user()
        f = File.get(self.id)
        content_id = media.get_id(data=content)
        if content_id != self.id:
            logger.debug('INVALID CONTENT %s vs %s', self.id, content_id)
            return False
        if not f:
            path = 'Downloads/%s.%s' % (self.id, self.info['extension'])
            f = File.get_or_create(self.id, self.info, path=path)
            path = self.get_path()
            if not os.path.exists(path):
                ox.makedirs(os.path.dirname(path))
                with open(path, 'wb') as fd:
                    fd.write(content)
                if u not in self.users:
                    self.users.append(u)
                self.transferprogress = 1
                self.added = datetime.utcnow()
                Changelog.record(u, 'additem', self.id, self.info)
                self.update()
                f.move()
                self.update_cover()
                trigger_event('transfer', {
                    'id': self.id, 'progress': 1
                })
                return True
        else:
            logger.debug('TRIED TO SAVE EXISTING FILE!!!')
            self.transferprogress = 1
            self.update()
        return False

    def remove_file(self):
        for f in self.files.all():
            path = f.fullpath()
            logger.debug('remove file %s', path)
            if os.path.exists(path):
                os.unlink(path)
                remove_empty_folders(os.path.dirname(path))
            db.session.delete(f)
        user = state.user()
        if user in self.users:
            self.users.remove(user)
        for l in self.lists.filter_by(user_id=user.id):
            l.items.remove(self)
        db.session.commit()
        if not self.users:
            db.session.delete(self)
        else:
            self.update()
        Changelog.record(user, 'removeitem', self.id)

for key in config['itemKeys']:
    if key.get('sort'):
        sort_type = key.get('sortType', key['type'])
        if sort_type == 'integer':
            col = db.Column(db.BigInteger(), index=True)
        elif sort_type == 'float':
            col = db.Column(db.Float(), index=True)
        elif sort_type == 'date':
            col = db.Column(db.DateTime(), index=True)
        else:
            col = db.Column(db.String(1000), index=True)
        setattr(Item, 'sort_%s' % key['id'], col)

Item.id_keys = ['isbn10', 'isbn13', 'lccn', 'olid', 'oclc', 'asin']
Item.item_keys = config['itemKeys'] 
Item.filter_keys = [k['id'] for k in config['itemKeys'] if k.get('filter')]

class Find(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    item_id = db.Column(db.String(32), db.ForeignKey('item.id'))
    item = db.relationship('Item', backref=db.backref('find', lazy='dynamic'))
    key = db.Column(db.String(200), index=True)
    value = db.Column(db.Text())
    findvalue = db.Column(db.Text())

    def __repr__(self):
        return (u'%s=%s' % (self.key, self.findvalue)).encode('utf-8')

    @classmethod
    def get(cls, item, key):
        return cls.query.filter_by(item_id=item, key=key).first()

    @classmethod
    def get_or_create(cls, item, key):
        f = cls.get(item, key)
        if not f:
            f = cls(item_id=item, key=key)
            db.session.add(f)
            db.session.commit()
        return f

class File(db.Model):

    created = db.Column(db.DateTime())
    modified = db.Column(db.DateTime())

    sha1 = db.Column(db.String(32), primary_key=True)
    path = db.Column(db.String(2048))

    info = db.Column(MutableDict.as_mutable(db.PickleType(pickler=json)))

    item_id = db.Column(db.String(32), db.ForeignKey('item.id'))
    item = db.relationship('Item', backref=db.backref('files', lazy='dynamic'))

    @classmethod
    def get(cls, sha1):
        return cls.query.filter_by(sha1=sha1).first()

    @classmethod
    def get_or_create(cls, sha1, info=None, path=None):
        f = cls.get(sha1)
        if not f:
            f = cls(sha1=sha1)
            if info:
                f.info = info
            if path:
                f.path = path
            f.item_id = Item.get_or_create(id=sha1, info=info).id
            db.session.add(f)
            db.session.commit()
        return f

    def __repr__(self):
        return self.sha1

    def __init__(self, sha1):
        self.sha1 = sha1
        self.created = datetime.utcnow()
        self.modified = datetime.utcnow()

    def fullpath(self):
        prefs = settings.preferences
        prefix = os.path.join(os.path.expanduser(prefs['libraryPath']), 'Books/')
        return os.path.join(prefix, self.path)

    def move(self):
        def format_underscores(string):
            return re.sub('^\.|\.$|:|/|\?|<|>', '_', string)
        prefs = settings.preferences
        prefix = os.path.join(os.path.expanduser(prefs['libraryPath']), 'Books/')
        j = self.item.json()

        current_path = self.fullpath()
        author = '; '.join([ox.canonical_name(a) for a in j.get('author', [])])
        if not author:
            author = 'Unknown Author'
        title = j.get('title', 'Untitled')
        extension = j['extension']

        if len(title) > 100:
            title = title[:100]

        title = format_underscores(title)
        author = format_underscores(author)

        filename = '%s.%s' % (title, extension)
        new_path = os.path.join(author[0].upper(), author, filename)
        if self.path == new_path:
            return
        h = ''
        while os.path.exists(os.path.join(prefix, new_path)):
            h = self.sha1[:len(h)+1]
            filename = '%s.%s.%s' % (title, h, extension)
            new_path = os.path.join(author[0].upper(), author, filename)
            if current_path == os.path.join(prefix, new_path):
                break
        if self.path != new_path:
            path = os.path.join(prefix, new_path)
            ox.makedirs(os.path.dirname(path))
            shutil.move(current_path, path)
            self.path = new_path
            self.save()

    def save(self):
        db.session.add(self)
        db.session.commit()
