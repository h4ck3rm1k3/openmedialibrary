# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from datetime import datetime
from io import BytesIO
import base64
import hashlib
import os
import re
import shutil
import unicodedata

from PIL import Image
import ox
import sqlalchemy as sa

from changelog import Changelog
from db import MutableDict
import json_pickler
from .icons import icons
from .person import get_sort_name
from settings import config
from utils import remove_empty_folders
from websocket import trigger_event
import db
import media
import metaremote as meta
import settings
import state
import utils

import logging
logger = logging.getLogger(__name__)

user_items = sa.Table('useritem', db.metadata,
    sa.Column('user_id', sa.String(43), sa.ForeignKey('user.id')),
    sa.Column('item_id', sa.String(32), sa.ForeignKey('item.id'))
)

class Item(db.Model):
    __tablename__ = 'item'

    created = sa.Column(sa.DateTime())
    modified = sa.Column(sa.DateTime())

    id = sa.Column(sa.String(32), primary_key=True)

    info = sa.Column(MutableDict.as_mutable(sa.PickleType(pickler=json_pickler)))
    meta = sa.Column(MutableDict.as_mutable(sa.PickleType(pickler=json_pickler)))

    # why is this in db and not in i.e. info?
    added = sa.Column(sa.DateTime()) # added to local library
    accessed = sa.Column(sa.DateTime())
    timesaccessed = sa.Column(sa.Integer())

    users = sa.orm.relationship('User', secondary=user_items,
        backref=sa.orm.backref('items', lazy='dynamic'))

    @property
    def timestamp(self):
        return utils.datetime2ts(self.modified)

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
            state.db.session.add(item)
            state.db.session.commit()
        return item

    def json(self, keys=None):
        j  = {}
        j['id'] = self.id
        j['created'] = self.created
        j['modified'] = self.modified
        j['timesaccessed'] = self.timesaccessed
        j['accessed'] = self.accessed
        j['added'] = self.added
        t = Transfer.get(self.id)
        if t:
            j['transferadded'] = t.added
            j['transferprogress'] = t.progress
        j['users'] = list(map(str, list(self.users)))

        if self.info:
            j.update(self.info)
        if self.meta:
            j.update(self.meta)

        for key in self.id_keys + ['primaryid']:
            if key not in self.meta and key in j:
                del j[key]
        if keys:
            for k in list(j):
                if k not in keys:
                    del j[k]
        for key in [k['id'] for k in settings.config['itemKeys'] if isinstance(k['type'], list)]:
            if key in j and not isinstance(j[key], list):
                j[key] = [j[key]]
        return j

    def get_path(self):
        f = self.files.first()
        return f.fullpath() if f else None

    def update_sort(self):
        update = False
        s = Sort.get_or_create(self.id)
        for key in config['itemKeys']:
            if key.get('sort'):
                value = self.json().get(key['id'], None)
                sort_type = key.get('sortType', key['type'])
                if value:
                    if sort_type == 'integer':
                        if isinstance(value, str):
                            value = int(re.sub('[^0-9]', '', value))
                        else:
                            value = int(value)
                    elif sort_type == 'float':
                        value = float(value)
                    elif sort_type == 'date':
                        pass
                    elif sort_type == 'person':
                        if not isinstance(value, list):
                            value = [value]
                        value = list(map(get_sort_name, value))
                        value = ox.sort_string('\n'.join(value)).lower()
                    elif sort_type == 'title':
                        if isinstance(value, dict):
                            value = list(value.values())
                        if isinstance(value, list):
                            value = ''.join(value)
                        value = ox.get_sort_title(value)
                        value = utils.sort_title(value).lower()
                    else:
                        if isinstance(value, list):
                            value = '\n'.join(value)
                        if value:
                            value = str(value)
                            value = ox.sort_string(value).lower()
                elif isinstance(value, list): #empty list
                    value = ''
                if getattr(s, key['id']) != value:
                    setattr(s, key['id'], value)
                    update = True
        if update:
            state.db.session.add(s)

    def update_find(self):

        def add(k, v):
            f = Find.query.filter_by(item_id=self.id, key=k, value=v).first()
            if not f:
                f = Find(item_id=self.id, key=k)
            if f.value != v:
                f.findvalue = unicodedata.normalize('NFKD', v).lower()
                f.value = v
                state.db.session.add(f)

        keys = []
        for key in config['itemKeys']:
            if key.get('find') or key.get('filter') or key.get('type') in [['string'], 'string']:
                value = self.json().get(key['id'], None)
                if key.get('filterMap') and value:
                    value = re.compile(key.get('filterMap')).findall(value)
                    if value: value = value[0]
                if value:
                    keys.append(key['id'])
                    if isinstance(value, dict):
                        value = ' '.join(list(value.values()))
                    if not isinstance(value, list):
                        value = [value]
                    value = [
                        v.decode('utf-8') if isinstance(v, bytes) else v
                        for v in value
                    ]
                    for v in value:
                        add(key['id'], v)
                    for f in Find.query.filter_by(item_id=self.id,
                            key=key['id']).filter(Find.value.notin_(value)):
                        state.db.session.delete(f)
        for f in Find.query.filter_by(item_id=self.id).filter(Find.key.notin_(keys)):
            state.db.session.delete(f)

    def update(self):
        for key in ('mediastate', 'coverRatio', 'previewRatio'):
            if key in self.meta:
                if key not in self.info:
                    self.info[key] = self.meta[key]
                del self.meta[key]
        users = list(map(str, list(self.users)))
        self.info['mediastate'] = 'available' # available, unavailable, transferring
        t = Transfer.get(self.id)
        if t and t.added and t.progress < 1:
            self.info['mediastate'] = 'transferring'
        else:
            self.info['mediastate'] = 'available' if settings.USER_ID in users else 'unavailable'
        if 'primaryid' in self.meta:
            # self.meta.update does not trigger db update!
            m = Metadata.load(*self.meta['primaryid'])
            for key in m:
                if key == 'id':
                    continue
                self.meta[key] = m[key]
        self.modified = datetime.utcnow()
        self.update_sort()
        self.update_find()
        #self.modified = datetime.utcnow()
        self.save()

    def save(self):
        state.db.session.add(self)
        state.db.session.commit()

    def delete(self, commit=True):
        Sort.query.filter_by(item_id=self.id).delete()
        Transfer.query.filter_by(item_id=self.id).delete()
        Scrape.query.filter_by(item_id=self.id).delete()
        state.db.session.delete(self)
        if commit:
            state.db.session.commit()

    meta_keys = (
        'title', 'author', 'date', 'publisher', 'edition',
        'language', 'description', 'classification'
    )

    def update_meta(self, data):
        update = False
        record = {}
        for key in self.meta_keys:
            if key in data:
                if self.meta.get(key) != data[key]:
                    record[key] = data[key]
                    self.meta[key] = data[key]
                    update = True
        for key in list(self.meta):
            if key not in self.meta_keys:
                del self.meta[key]
                update = True
        if update:
            self.update()
            self.modified = datetime.utcnow()
            self.save()
            user = state.user()
            if record and user in self.users:
                Changelog.record(user, 'edititem', self.id, record)

    def update_primaryid(self, key=None, id=None, scrape=True):
        if key is None and id is None:
            if 'primaryid' not in self.meta:
                return
            else:
                key = self.meta['primaryid'][0]
        record = {}
        if id:
            if not key in self.meta or not key in self.meta[key]:
                self.meta[key] = list(set([id] + self.meta.get(key, [])))
            self.meta['primaryid'] = [key, id]
            record[key] = id
        else:
            if key in self.meta:
                del self.meta[key]
            if 'primaryid' in self.meta:
                del self.meta['primaryid']
            record[key] = ''
        for k in self.id_keys:
            if k != key:
                if k in self.meta:
                    del self.meta[k]
        logger.debug('set primaryid %s %s', key, id)

        # get metadata from external resources
        if scrape:
            self.scrape()
        self.update_icons()
        self.modified = datetime.utcnow()
        self.save()
        #if not scrape:
        #    Scrape.get_or_create(self.id)
        for f in self.files.all():
            f.move()
        user = state.user()
        if user in self.users:
            Changelog.record(user, 'edititem', self.id, record)

    def edit_metadata(self, data):
        Scrape.query.filter_by(item_id=self.id).delete()
        if 'primaryid' in self.meta:
            logger.debug('m: %s', self.meta['primaryid'])
            m = Metadata.get_or_create(*self.meta['primaryid'])
            if m.edit(data):
                self.update()
        else:
            self.update_meta(data)
        for f in self.files.all():
            f.move()

    def extract_preview(self):
        path = self.get_path()
        if path:
            return getattr(media, self.info['extension']).cover(path)

    def update_icons(self):
        def get_ratio(data):
            img = Image.open(BytesIO(data))
            return img.size[0]/img.size[1]
        key = 'cover:%s'%self.id
        cover = None
        if 'cover' in self.meta and self.meta['cover']:
            try:
                cover = ox.cache.read_url(self.meta['cover'])
            except:
                logger.debug('unable to read cover url %s', self.meta['cover'])
                cover = None
            if cover:
                icons[key] = cover
                self.info['coverRatio'] = get_ratio(cover)
        else:
            if icons[key]:
                del icons[key]
        path = self.get_path()
        key = 'preview:%s'%self.id
        if path:
            preview = self.extract_preview()
            if preview:
                icons[key] = preview
                self.info['previewRatio'] = get_ratio(preview)
                if not cover:
                    self.info['coverRatio'] = self.info['previewRatio']
        elif cover:
            self.info['previewRatio'] = self.info['coverRatio']
        for key in ('cover', 'preview'):
            key = '%s:%s' % (key, self.id)
            for resolution in (128, 256, 512):
                del icons['%s:%s' % (key, resolution)]

    def scrape(self):
        primaryid = self.meta.get('primaryid')
        logger.debug('scrape %s', primaryid)
        if primaryid:
            m = meta.lookup(*primaryid)
            if m:
                m['primaryid'] = primaryid
                self.meta = m
                self.modified = datetime.utcnow()
                self.update()
                return True
            return False
        return True

    def queue_download(self):
        u = state.user()
        if not u in self.users:
            t = Transfer.get_or_create(self.id)
            logger.debug('queue %s for download', self.id)
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
            info = self.info.copy()
            for key in ('mediastate', 'coverRatio', 'previewRatio'):
                if key in info:
                    del info[key]
            f = File.get_or_create(self.id, info, path=path)
            path = self.get_path()
            if not os.path.exists(path):
                ox.makedirs(os.path.dirname(path))
                with open(path, 'wb') as fd:
                    fd.write(content)
                if u not in self.users:
                    self.users.append(u)
                t = Transfer.get_or_create(self.id)
                t.progress = 1
                t.save()
                self.added = datetime.utcnow()
                Changelog.record(u, 'additem', self.id, f.info)
                self.update()
                f.move()
                self.update_icons()
                self.save()
                trigger_event('transfer', {
                    'id': self.id, 'progress': 1
                })
                return True
        else:
            logger.debug('TRIED TO SAVE EXISTING FILE!!!')
            t = Transfer.get_or_create(self.id)
            t.progress = 1
            t.save()
            self.update()
        return False

    def remove_file(self):
        for f in self.files.all():
            path = f.fullpath()
            if os.path.exists(path):
                os.unlink(path)
                remove_empty_folders(os.path.dirname(path))
            state.db.session.delete(f)
        user = state.user()
        if user in self.users:
            self.users.remove(user)
        for l in self.lists.filter_by(user_id=user.id):
            l.items.remove(self)
        state.db.session.commit()
        if not self.users:
            self.delete()
        else:
            self.update()
        Transfer.query.filter_by(item_id=self.id).delete()
        Changelog.record(user, 'removeitem', self.id)

class Sort(db.Model):
    __tablename__ = 'sort'

    item_id = sa.Column(sa.String(32), sa.ForeignKey('item.id'), primary_key=True)
    item = sa.orm.relationship('Item', backref=sa.orm.backref('sort', lazy='dynamic'))

    def __repr__(self):
        return '%s_sort' % self.item_id

    @classmethod
    def get(cls, item_id):
        return cls.query.filter_by(item_id=item_id).first()

    @classmethod
    def get_or_create(cls, item_id):
        f = cls.get(item_id)
        if not f:
            f = cls(item_id=item_id)
            state.db.session.add(f)
            state.db.session.commit()
        return f

for key in config['itemKeys']:
    if key.get('sort'):
        sort_type = key.get('sortType', key['type'])
        if sort_type == 'integer':
            col = sa.Column(sa.BigInteger(), index=True)
        elif sort_type == 'float':
            col = sa.Column(sa.Float(), index=True)
        elif sort_type == 'date':
            col = sa.Column(sa.DateTime(), index=True)
        else:
            col = sa.Column(sa.String(1000), index=True)
        setattr(Sort, '%s' % key['id'], col)

Item.id_keys = ['isbn', 'lccn', 'olid', 'oclc', 'asin']
Item.item_keys = config['itemKeys'] 
Item.filter_keys = [k['id'] for k in config['itemKeys'] if k.get('filter')]

class Find(db.Model):
    __tablename__ = 'find'

    id = sa.Column(sa.Integer(), primary_key=True)
    item_id = sa.Column(sa.String(32), sa.ForeignKey('item.id'))
    item = sa.orm.relationship('Item', backref=sa.orm.backref('find', lazy='dynamic'))
    key = sa.Column(sa.String(200), index=True)
    value = sa.Column(sa.Text())
    findvalue = sa.Column(sa.Text(), index=True)

    def __repr__(self):
        return '%s=%s' % (self.key, self.findvalue)

    @classmethod
    def get(cls, item, key):
        return cls.query.filter_by(item_id=item, key=key).first()

    @classmethod
    def get_or_create(cls, item, key):
        f = cls.get(item, key)
        if not f:
            f = cls(item_id=item, key=key)
            state.db.session.add(f)
            state.db.session.commit()
        return f

class File(db.Model):
    __tablename__ = 'file'

    created = sa.Column(sa.DateTime())
    modified = sa.Column(sa.DateTime())

    sha1 = sa.Column(sa.String(32), primary_key=True)
    path = sa.Column(sa.String(2048))

    info = sa.Column(MutableDict.as_mutable(sa.PickleType(pickler=json_pickler)))

    item_id = sa.Column(sa.String(32), sa.ForeignKey('item.id'))
    item = sa.orm.relationship('Item', backref=sa.orm.backref('files', lazy='dynamic'))

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
            state.db.session.add(f)
            state.db.session.commit()
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
        if not os.path.exists(current_path):
            logger.debug('file is missing. %s', current_path)
            return
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
        first = unicodedata.normalize('NFD', author[0].upper())[0].upper()
        new_path = os.path.join(first, author, filename)
        new_path = new_path.replace('\x00', '')
        if self.path == new_path:
            return
        h = ''
        while os.path.exists(os.path.join(prefix, new_path)):
            h = self.sha1[:len(h)+1]
            filename = '%s.%s.%s' % (title, h, extension)
            first = unicodedata.normalize('NFD', author[0].upper())[0].upper()
            new_path = os.path.join(first, author, filename)
            if current_path == os.path.join(prefix, new_path):
                break
        if self.path != new_path:
            path = os.path.join(prefix, new_path)
            ox.makedirs(os.path.dirname(path))
            shutil.move(current_path, path)
            self.path = new_path
            self.save()

    def save(self):
        state.db.session.add(self)
        state.db.session.commit()

class Scrape(db.Model):

    __tablename__ = 'scrape'

    item_id = sa.Column(sa.String(32), sa.ForeignKey('item.id'), primary_key=True)
    item = sa.orm.relationship('Item', backref=sa.orm.backref('scraping', lazy='dynamic'))

    added = sa.Column(sa.DateTime())

    def __repr__(self):
        return '='.join(map(str, [self.item_id, self.added]))

    @classmethod
    def get(cls, item_id):
        return cls.query.filter_by(item_id=item_id).first()

    @classmethod
    def get_or_create(cls, item_id):
        t = cls.get(item_id)
        if not t:
            t = cls(item_id=item_id)
            t.added = datetime.utcnow()
            t.save()
        return t

    def save(self):
        state.db.session.add(self)
        state.db.session.commit()

    def remove(self):
        state.db.session.delete(self)
        state.db.session.commit()

class Transfer(db.Model):
    __tablename__ = 'transfer'

    item_id = sa.Column(sa.String(32), sa.ForeignKey('item.id'), primary_key=True)
    item = sa.orm.relationship('Item', backref=sa.orm.backref('transfer', lazy='dynamic'))

    added = sa.Column(sa.DateTime())
    progress = sa.Column(sa.Float())

    def __repr__(self):
        return '='.join(map(str, [self.item_id, self.progress]))

    @classmethod
    def get(cls, item_id):
        return cls.query.filter_by(item_id=item_id).first()

    @classmethod
    def get_or_create(cls, item_id):
        t = cls.get(item_id)
        if not t:
            t = cls(item_id=item_id)
            t.added = datetime.utcnow()
            t.progress = 0
            t.save()
        return t

    def save(self):
        state.db.session.add(self)
        state.db.session.commit()

class Metadata(db.Model):
    __tablename__ = 'metadata'

    created = sa.Column(sa.DateTime())
    modified = sa.Column(sa.DateTime())

    id = sa.Column(sa.Integer(), primary_key=True)

    key = sa.Column(sa.String(256))
    value = sa.Column(sa.String(256))

    data = sa.Column(MutableDict.as_mutable(sa.PickleType(pickler=json_pickler)))

    def __repr__(self):
        return '='.join([self.key, self.value])

    @property
    def timestamp(self):
        return utils.datetime2ts(self.modified)

    @classmethod
    def get(cls, key, value):
        return cls.query.filter_by(key=key, value=value).first()

    @classmethod
    def get_or_create(cls, key, value):
        m = cls.get(key, value)
        if not m:
            m = cls(key=key, value=value)
            m.created = datetime.utcnow()
            m.data = {}
            m.save()
        return m

    def save(self):
        self.modified = datetime.utcnow()
        state.db.session.add(self)
        state.db.session.commit()

    def reset(self):
        user = state.user()
        Changelog.record(user, 'resetmeta', self.key, self.value)
        state.db.session.delete(self)
        state.db.session.commit()
        self.update_items()

    def edit(self, data):
        changed = {}
        for key in data:
            if key == 'id':
                continue
            if data[key] != self.data.get(key):
                self.data[key] = data[key]
                changed[key] = data[key]
        if changed:
            self.save()
            user = state.user()
            Changelog.record(user, 'editmeta', self.key, self.value, changed)
        return changed

    def update_items(self):
        for f in Find.query.filter_by(key=self.key, value=self.value):
            if f.item:
                f.item.scrape()

    @classmethod
    def load(self, key, value):
        m = self.get(key, value)
        if m:
            if 'id' in m.data:
                del m.data['id']
            return m.data
        return {}
