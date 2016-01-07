# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import json

import sqlalchemy as sa

from changelog import Changelog
from db import MutableDict
from queryparser import Parser
import db
import json_pickler
import settings
import state

import logging
logger = logging.getLogger(__name__)

class User(db.Model):
    __tablename__ = 'user'

    created = sa.Column(sa.DateTime())
    modified = sa.Column(sa.DateTime())

    id = sa.Column(sa.String(43), primary_key=True)
    info = sa.Column(MutableDict.as_mutable(sa.PickleType(pickler=json_pickler)))

    nickname = sa.Column(sa.String(256), unique=True)

    pending = sa.Column(sa.String(64)) # sent|received
    queued = sa.Column(sa.Boolean())
    peered = sa.Column(sa.Boolean())
    online = sa.Column(sa.Boolean())

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
            if state.nodes and state.nodes._local and id in state.nodes._local._nodes:
                user.info['local'] = state.nodes._local._nodes[id]
                user.info['username'] = user.info['local']['username']
            user.update_name()
            user.save()
        return user

    def save(self):
        state.db.session.add(self)
        state.db.session.commit()

    @property
    def name(self):
        name = self.nickname if self.id != settings.USER_ID else ''
        return name

    @property
    def library(self):
        l = List.get_or_create(self.id, '')
        if l.index_ != -1:
            l.index_ = -1
            l.save()
        return l

    def json(self):
        j = {}
        if self.info:
            j.update(self.info)
        j['id'] = self.id
        if self.pending:
            j['pending'] = self.pending
        j['peered'] = self.peered
        j['online'] = self.is_online()
        j['nickname'] = self.info.get('nickname')
        j['username'] = self.info.get('username') if self.id != settings.USER_ID else settings.preferences['username']
        j['name'] = self.name
        return j

    def is_online(self):
        return state.nodes and state.nodes.is_online(self.id)

    def lists_json(self):
        self.library
        return [l.json() for l in self.lists.order_by('index_')]

    def clear_list_cache(self):
        if self.id == settings.USER_ID:
            prefix = ':'
        else:
            prefix = self.id + ':'
        for key in list(settings.list_cache):
            if key.startswith(prefix):
                del settings.list_cache[key]

    def clear_smart_list_cache(self):
        qs = List.query.filter_by(type='smart')
        smart_lists = [':%d' % l.id for l in qs]
        for key in list(settings.list_cache):
            if key in smart_lists:
                del settings.list_cache[key]

    def update_peering(self, peered, username=None):
        was_peering = self.peered
        if peered:
            logging.debug('update_peering, pending: %s queued: %s', self.pending, self.queued)
            self.queued = self.pending != 'sent'
            self.pending = ''
            if username:
                self.info['username'] = username
            self.update_name()
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
            self.queued = False
            self.update_name()
            self.save()
            List.query.filter_by(user_id=self.id).delete()
            for i in self.items:
                i.users.remove(self)
                if not i.users:
                    i.delete()
            Changelog.query.filter_by(user_id=self.id).delete()
            if self.id in settings.ui['showFolder']:
                del settings.ui['showFolder'][self.id]
            self.clear_list_cache()
            self.save()
            if was_peering:
                Changelog.record(state.user(), 'removepeer', self.id)
        self.save()

    def update_name(self):
        if self.id == settings.USER_ID:
            name = settings.preferences.get('username', 'anonymous')
        else:
            name = self.info.get('nickname') or self.info.get('username') or 'anonymous'
        nickname = name
        n = 2
        while self.query.filter_by(nickname=nickname).filter(User.id!=self.id).first():
            nickname = '%s [%d]' % (name, n)
            n += 1
        self.nickname = nickname

    def migrate_id(self, service_id):
        if len(service_id) == 16:
            statements = [
                "DELETE FROM user WHERE id = '{nid}'",
                "UPDATE user SET id = '{nid}' WHERE id = '{oid}'",
                "UPDATE list SET user_id = '{nid}' WHERE user_id = '{oid}'",
                "UPDATE useritem SET user_id = '{nid}' WHERE user_id = '{oid}'",
                "UPDATE changelog SET user_id = '{nid}' WHERE user_id = '{oid}'",
            ]
            with db.session() as session:
                for sql in statements:
                    session.connection().execute(sql.format(oid=self.id, nid=service_id))
                session.commit()

list_items = sa.Table('listitem', db.metadata,
    sa.Column('list_id', sa.Integer(), sa.ForeignKey('list.id')),
    sa.Column('item_id', sa.String(32), sa.ForeignKey('item.id'))
)

class List(db.Model):
    __tablename__ = 'list'

    id = sa.Column(sa.Integer(), primary_key=True)
    name = sa.Column(sa.String())
    index_ = sa.Column(sa.Integer())

    type = sa.Column(sa.String(64))
    _query = sa.Column('query', MutableDict.as_mutable(sa.PickleType(pickler=json_pickler)))

    user_id = sa.Column(sa.String(43), sa.ForeignKey('user.id'))
    user = sa.orm.relationship('User', backref=sa.orm.backref('lists', lazy='dynamic'))

    items = sa.orm.relationship('Item', secondary=list_items,
            backref=sa.orm.backref('lists', lazy='dynamic'))

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
        l.index_ = cls.query.filter_by(user_id=user_id).count()
        state.db.session.add(l)
        state.db.session.commit()
        if user_id == settings.USER_ID:
            if not l._query:
                Changelog.record(state.user(), 'addlist', l.name)
        return l

    @classmethod
    def rename_user(cls, old, new):
        for l in cls.query.filter(cls._query!=None):

            def update_conditions(conditions):
                changed = False
                for c in conditions:
                    if 'conditions' in c:
                        changed = update_conditions(conditions)
                    else:
                        if c.get('key') == 'list' and c.get('value', '').startswith('%s:' % old):
                            c['value'] = '%s:%s' % new, c['value'].split(':', 1)[1]
                            changed = True
                return changed

            if update_conditions(l._query.get('conditions', [])):
                l.save()

    def add_items(self, items):
        from item.models import Item
        for item_id in items:
            i = Item.get(item_id)
            if i:
                self.items.append(i)
                if self.user_id == settings.USER_ID:
                    i.queue_download()
                i.update()
        state.db.session.add(self)
        state.db.session.commit()
        if self.user_id == settings.USER_ID:
            Changelog.record(self.user, 'addlistitems', self.name, items)
        self.user.clear_smart_list_cache()
        self.user.clear_list_cache()

    def get_items(self):
        if self.type == 'smart':
            from item.models import Item, user_items
            return Parser(Item, user_items).find({'query': self._query})
        else:
            return self.items

    def remove_items(self, items):
        from item.models import Item
        for item_id in items:
            i = Item.get(item_id)
            if i in self.items:
                self.items.remove(i)
            i.update()
        state.db.session.add(self)
        state.db.session.commit()
        if self.user_id == settings.USER_ID:
            Changelog.record(self.user, 'removelistitems', self.name, items)
        self.user.clear_smart_list_cache()
        self.user.clear_list_cache()

    def remove(self):
        if not self._query:
            for i in self.items:
                self.items.remove(i)
        if not self._query:
            if self.user_id == settings.USER_ID:
                Changelog.record(self.user, 'removelist', self.name)
        state.db.session.delete(self)
        state.db.session.commit()

    @property
    def public_id(self):
        id = ''
        if self.user_id != settings.USER_ID:
            id += self.user.nickname
        id = '%s:%s' % (id, self.name)
        return id

    @property
    def find_id(self):
        id = ''
        if self.user_id != settings.USER_ID:
            id += self.user_id
        id = '%s:%s' % (id, self.id)
        return id

    def __repr__(self):
        return self.public_id

    def items_count(self):
        key = self.find_id
        if key in settings.list_cache:
            value = settings.list_cache[key]
        else:
            if self.type == 'smart':
                value = self.get_items().count()
            else:
                value = len(self.items)
            settings.list_cache[key] = value
        return value

    def json(self):
        r = {
            'id': self.public_id,
            'user': self.user.name,
            'name': self.name,
            'index': self.index_,
            # to slow for many smart lists
            'items': 0, #self.items_count(),
            'type': self.type
        }
        if self.name == '':
            r['name'] = 'Library'
            r['type'] = 'library'
            del r['index']
        if self.type == 'smart':
            r['query'] = self._query
        return r

    def save(self):
        state.db.session.add(self)
        state.db.session.commit()
