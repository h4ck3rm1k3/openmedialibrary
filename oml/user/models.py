# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import json

from oxflask.db import MutableDict
import oxflask.query

from changelog import Changelog
import settings
from settings import db

import state

import logging
logger = logging.getLogger('oml.user.models')

class User(db.Model):

    created = db.Column(db.DateTime())
    modified = db.Column(db.DateTime())
    id = db.Column(db.String(43), primary_key=True)
    info = db.Column(MutableDict.as_mutable(db.PickleType(pickler=json)))

    #nickname = db.Column(db.String(256), unique=True)
    nickname = db.Column(db.String(256))

    pending = db.Column(db.String(64)) # sent|received
    queued = db.Column(db.Boolean())
    peered = db.Column(db.Boolean())
    online = db.Column(db.Boolean())

    def __repr__(self):
        return self.id

    @classmethod
    def get(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def get_or_create(cls, id):
        user = cls.get(id)
        if not user:
            user = cls(id=id, peered=False, online=False)
            user.info = {}
            user.save()
        return user

    def save(self):
        db.session.add(self)
        db.session.commit()

    def json(self):
        j = {}
        if self.info:
            j.update(self.info)
        j['id'] = self.id
        if self.pending:
            j['pending'] = self.pending
        j['peered'] = self.peered
        j['online'] = self.check_online()
        j['nickname'] = self.nickname
        return j

    def check_online(self):
        return state.nodes and state.nodes.check_online(self.id)

    def lists_json(self):
        return [{
            'id': '%s:' % ('' if self.id == settings.USER_ID else self.nickname),
            'name': 'Library',
            'type': 'library',
            'items': self.items.count(),
            'user': self.nickname if self.id != settings.USER_ID else settings.preferences['username'],
        }] + [l.json() for l in self.lists.order_by('position')]

    def update_peering(self, peered, username=None):
        was_peering = self.peered
        self.queued = True
        if peered:
            self.pending = ''
            if username:
                self.info['username'] = username

            self.set_nickname(self.info.get('username', 'anonymous'))
            # FIXME: need to set peered to False to not trigger changelog event
            # before other side receives acceptPeering request
            self.peered = False
            self.save()
            if not was_peering:
                Changelog.record(state.user(), 'addpeer', self.id, self.nickname)
            self.peered = True
            self.save()
        else:
            self.pending = ''
            self.peered = False
            self.nickname = None
            self.save()
            List.query.filter_by(user_id=self.id).delete()
            for i in self.items:
                i.users.remove(self)
                if not i.users:
                    db.session.delete(i)
                else:
                    i.update_lists()
            Changelog.query.filter_by(user_id=self.id).delete()
            self.save()
            if was_peering:
                Changelog.record(state.user(), 'removepeer', self.id)
        self.save()

    def set_nickname(self, nickname):
        username = nickname
        n = 2
        while self.query.filter_by(nickname=nickname).filter(User.id!=self.id).first():
            nickname = '%s [%d]' % (username, n)
            n += 1
        self.nickname = nickname

list_items = db.Table('listitem',
    db.Column('list_id', db.Integer(), db.ForeignKey('list.id')),
    db.Column('item_id', db.String(32), db.ForeignKey('item.id'))
)

class List(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    position = db.Column(db.Integer())

    type = db.Column(db.String(64))
    _query = db.Column('query', MutableDict.as_mutable(db.PickleType(pickler=json)))

    user_id = db.Column(db.String(43), db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('lists', lazy='dynamic'))

    items = db.relationship('Item', secondary=list_items,
            backref=db.backref('lists', lazy='dynamic'))

    @classmethod
    def get(cls, user_id, name=None):
        if name is None:
            user_id, name = cls.get_user_name(user_id)
        return cls.query.filter_by(user_id=user_id, name=name).first()

    @classmethod
    def get_user_name(cls, user_id):
        nickname, name = user_id.split(':', 1)
        if nickname:
            user = User.query.filter_by(nickname=nickname).first()
            user_id = user.id
        else:
            user_id = settings.USER_ID
        return user_id, name

    @classmethod
    def get_or_create(cls, user_id, name=None, query=None):
        if name is None:
            user_id, name = cls.get_user_name(user_id)
        l = cls.get(user_id, name)
        if not l:
            l = cls.create(user_id, name, query)
        return l

    @classmethod
    def create(cls, user_id, name, query=None):
        prefix = name
        n = 2
        while cls.get(user_id, name):
            name = '%s [%s]' % (prefix, n)
            n += 1
        l = cls(user_id=user_id, name=name)
        l._query = query
        l.type = 'smart' if l._query else 'static'
        l.position = cls.query.filter_by(user_id=user_id).count()
        if user_id == settings.USER_ID:
            p = User.get(settings.USER_ID)
            if not l._query:
                Changelog.record(p, 'addlist', l.name)
        db.session.add(l)
        db.session.commit()
        return l

    def add_items(self, items):
        from item.models import Item
        for item_id in items:
            i = Item.get(item_id)
            if i:
                self.items.append(i)
                if self.user_id == settings.USER_ID:
                    i.queue_download()
                i.update()
        db.session.add(self)
        db.session.commit()
        for item_id in items:
            i = Item.get(item_id)
            if i:
                i.update_lists()
                db.session.add(i)
        db.session.commit()
        if self.user_id == settings.USER_ID:
            Changelog.record(self.user, 'addlistitems', self.name, items)

    def remove_items(self, items):
        from item.models import Item
        for item_id in items:
            i = Item.get(item_id)
            if i in self.items:
                self.items.remove(i)
            i.update()
        db.session.add(self)
        db.session.commit()
        for item_id in items:
            i = Item.get(item_id)
            i.update_lists()
            db.session.add(i)
        db.session.commit()
        db.session.commit()
        if self.user_id == settings.USER_ID:
            Changelog.record(self.user, 'removelistitems', self.name, items)

    def remove(self):
        if not self._query:
            for i in self.items:
                self.items.remove(i)
        if not self._query:
            if self.user_id == settings.USER_ID:
                Changelog.record(self.user, 'removelist', self.name)
        db.session.delete(self)
        db.session.commit()

    @property
    def public_id(self):
        id = ''
        if self.user_id != settings.USER_ID:
            id += self.user.nickname
        id = u'%s:%s' % (id, self.name)
        return id

    @property
    def find_id(self):
        id = ''
        if self.user_id != settings.USER_ID:
            id += self.user_id
        id = u'%s:%s' % (id, self.id)
        return id
    
    def __repr__(self):
        return self.public_id.encode('utf-8')

    def items_count(self):
        from item.models import Item
        if self._query:
            data = self._query
            return oxflask.query.Parser(Item).find({'query': data}).count()
        else:
            return len(self.items)

    def json(self):
        r = {
            'id': self.public_id,
            'user': self.user.nickname if self.user_id != settings.USER_ID else settings.preferences['username'],
            'name': self.name,
            'index': self.position,
            'items': self.items_count(),
            'type': self.type
        }
        if self.type == 'smart':
            r['query'] = self._query
        return r

    def save(self):
        db.session.add(self)
        db.session.commit()
