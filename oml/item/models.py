# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import re
import base64
import json
import hashlib
from datetime import datetime
from StringIO import StringIO

import Image
import ox

import settings
from settings import db, config

from user.models import User

from person import get_sort_name

import media
from meta import scraper

import utils

from oxflask.db import MutableDict

from covers import covers
from changelog import Changelog
from websocket import trigger_event

class Work(db.Model):

    created = db.Column(db.DateTime())
    modified = db.Column(db.DateTime())

    id = db.Column(db.String(32), primary_key=True)

    meta = db.Column(MutableDict.as_mutable(db.PickleType(pickler=json)))

    def __repr__(self):
        return self.id

    def __init__(self, id):
        self.id = id
        self.created = datetime.now()
        self.modified = datetime.now()

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
        self.created = datetime.now()
        self.modified = datetime.now()

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
        self.created = datetime.now()
        self.modified = datetime.now()
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
        prefs = settings.preferences
        prefix = os.path.join(os.path.expanduser(prefs['libraryPath']), 'Books/')
        return os.path.join(prefix, f.path) if f else None

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
                setattr(self, 'sort_%s' % key['id'], value)

    def update_find(self):
        for key in config['itemKeys']:
            if key.get('find') or key.get('filter'):
                value = self.json().get(key['id'], None)
                if key.get('filterMap') and value:
                    value = re.compile(key.get('filterMap')).findall(value)[0]
                    print key['id'], value
                if value:
                    if isinstance(value, list):
                        Find.query.filter_by(item_id=self.id, key=key['id']).delete()
                        for v in value:
                            f = Find(item_id=self.id, key=key['id'])
                            f.value = v.lower()
                            db.session.add(f)
                    else:
                        f = Find.get_or_create(self.id, key['id'])
                        f.value = value.lower()
                        db.session.add(f)
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

    def update(self):
        users = map(str, list(self.users))
        self.meta['mediastate'] = 'available' # available, unavailable, transferring
        if self.transferadded and self.transferprogress < 1:
            self.meta['mediastate'] = 'transferring'
        else:
            self.meta['mediastate'] = 'available' if settings.USER_ID in users else 'unavailable'
        self.update_sort()
        self.update_find()
        self.update_lists()
        self.modified = datetime.now()
        self.save()

    def save(self):
        db.session.add(self)
        db.session.commit()

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
        print 'mainid', 'mainid' in self.meta, self.meta.get('mainid')
        print 'key', key, self.meta.get(key)
        # get metadata from external resources
        self.scrape()
        self.update()
        self.update_cover()
        db.session.add(self)
        db.session.commit()
        user = User.get_or_create(settings.USER_ID)
        if user in self.users:
            Changelog.record(user, 'edititem', self.id, record)

    def extract_cover(self):
        path = self.get_path()
        if not path:
            return getattr(media, self.meta['extensions']).cover(path)

    def update_cover(self):
        cover = None
        if 'cover' in self.meta:
            cover = ox.cache.read_url(self.meta['cover'])
            #covers[self.id] = requests.get(self.meta['cover']).content
            if cover:
                covers[self.id] = cover
        path = self.get_path()
        if not cover and path:
            cover = self.extract_cover()
            if cover:
                covers[self.id] = cover
        if cover:
            img = Image.open(StringIO(cover))
            self.meta['coverRatio'] = img.size[0]/img.size[1]
        for p in (':128', ':256'):
            del covers['%s%s' % (self.id, p)]
        return cover

    def scrape(self):
        mainid = self.meta.get('mainid')
        print 'scrape', mainid, self.meta.get(mainid)
        if mainid == 'olid':
            scraper.update_ol(self)
            scraper.add_lookupbyisbn(self)
        elif mainid in ('isbn10', 'isbn13'):
            scraper.add_lookupbyisbn(self)
        elif mainid == 'lccn':
            import meta.lccn
            info = meta.lccn.info(self.meta[mainid])
            for key in info:
                self.meta[key] = info[key]
        else:
            print 'FIX UPDATE', mainid
        self.update()

    def save_file(self, content):
        p = User.get(settings.USER_ID)
        f = File.get(self.id)
        if not f:
            path = 'Downloads/%s.%s' % (self.id, self.info['extension'])
            f = File.get_or_create(self.id, self.info, path=path)
            path = self.get_path()
            if not os.path.exists(path):
                ox.makedirs(os.path.dirname(path))
                with open(path, 'wb') as fd:
                    fd.write(content)
                if p not in self.users:
                    self.users.append(p)
                self.transferprogress = 1
                self.added = datetime.now()
                Changelog.record(p, 'additem', self.id, self.info)
                self.update()
                trigger_event('transfer', {
                    'id': self.id, 'progress': 1
                })
                return True
        else:
            print 'TRIED TO SAVE EXISTING FILE!!!'
            self.transferprogress = 1
            self.update()
        return False

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

Item.id_keys = ['isbn10', 'isbn13', 'lccn', 'olid', 'oclc']
Item.item_keys = config['itemKeys'] 
Item.filter_keys = []

class Find(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    item_id = db.Column(db.String(32), db.ForeignKey('item.id'))
    item = db.relationship('Item', backref=db.backref('find', lazy='dynamic'))
    key = db.Column(db.String(200), index=True)
    value = db.Column(db.Text())

    def __repr__(self):
        return (u'%s=%s' % (self.key, self.value)).encode('utf-8')

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
        self.created = datetime.now()
        self.modified = datetime.now()
