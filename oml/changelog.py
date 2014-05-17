# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import logging

import json
from datetime import datetime

from ed25519_utils import valid

import settings
from settings import db
import state
from websocket import trigger_event

logger = logging.getLogger('oml.changelog')

class Changelog(db.Model):
    '''
        additem               itemid    metadata from file (info) + OLID
        edititem              itemid    name->id (i.e. olid-> OL...M)
        removeitem            itemid
        addlist               name
        editlist              name {name: newname}
        orderlists            [name, name, name]
        removelist            name
        addlistitems          listname [ids]
        removelistitems       listname [ids]
        editusername          username
        editcontact           string
        addpeer               peerid peername
        removepeer            peerid peername
    '''
    id = db.Column(db.Integer(), primary_key=True)

    created = db.Column(db.DateTime())

    user_id = db.Column(db.String(43))
    revision = db.Column(db.BigInteger())
    data = db.Column(db.Text())
    sig = db.Column(db.String(96))

    @classmethod
    def record(cls, user, action, *args):
        c = cls()
        c.created = datetime.now()
        c.user_id = user.id
        c.revision = cls.query.filter_by(user_id=user.id).count()
        c.data = json.dumps([action, args])
        timestamp = c.timestamp
        _data = str(c.revision) + str(timestamp) + c.data
        c.sig = settings.sk.sign(_data, encoding='base64')
        db.session.add(c)
        db.session.commit()
        if state.online:
            state.nodes.queue('peered', 'pushChanges', [c.json()])

    @property
    def timestamp(self):
        return self.created.strftime('%s')

    @classmethod
    def apply_changes(cls, user, changes):
        for change in changes:
            if not Changelog.apply_change(user, change, trigger=False):
                logger.debug('FAIL %s', change)
                break
                return False
        if changes:
            trigger_event('change', {});
        return True

    @classmethod
    def apply_change(cls, user, change, rebuild=False, trigger=True):
        revision, timestamp, sig, data = change
        last = Changelog.query.filter_by(user_id=user.id).order_by('-revision').first()
        next_revision = last.revision + 1 if last else 0
        if revision == next_revision:
            _data = str(revision) + str(timestamp) + data
            if rebuild:
                sig = settings.sk.sign(_data, encoding='base64')
            if valid(user.id, _data, sig):
                c = cls()
                c.created = datetime.now()
                c.user_id = user.id
                c.revision = revision
                c.data = data
                c.sig = sig
                action, args = json.loads(data)
                logger.debug('apply change %s %s', action, args)
                if getattr(c, 'action_' + action)(user, timestamp, *args):
                    logger.debug('change applied')
                    db.session.add(c)
                    db.session.commit()
                    if trigger:
                        trigger_event('change', {});
                    return True
            else:
                logger.debug('INVLAID SIGNATURE ON CHANGE %s', change)
                raise Exception, 'invalid signature'
        else:
            logger.debug('revsion does not match! got %s expecting %s', revision, next_revision)
            return False

    def __repr__(self):
        return self.data

    def verify(self):
        _data = str(self.revision) + str(self.timestamp) + self.data
        return valid(self.user_id, _data, self.sig)

    @classmethod
    def _rebuild(cls):
        for c in cls.query.filter_by(user_id=settings.USER_ID):
            _data = str(c.revision) + str(c.timestamp) + c.data
            c.sig = settings.sk.sign(_data, encoding='base64')
            db.session.add(c)
        db.session.commit()

    def json(self):
        return [self.revision, self.timestamp, self.sig, self.data]

    @classmethod
    def restore(cls, user_id, path=None):
        from user.models import User
        user = User.get_or_create(user_id)
        if not path:
            path = '/tmp/oml_changelog_%s.json' % user_id
        with open(path, 'r') as fd:
            for change in fd:
                change = json.loads(change)
                cls.apply_change(user, change, user_id == settings.USER_ID)

    @classmethod
    def export(cls, user_id, path=None):
        if not path:
            path = '/tmp/oml_changelog_%s.json' % user_id
        with open(path, 'w') as fd:
            for c in cls.query.filter_by(user_id=user_id).order_by('revision'):
                fd.write(json.dumps(c.json()) + '\n')

    def action_additem(self, user, timestamp, itemid, info):
        from item.models import Item
        i = Item.get(itemid)
        if i and i.timestamp > timestamp:
            return True
        if not i:
            i = Item.get_or_create(itemid, info)
        i.users.append(user)
        i.update()
        return True

    def action_edititem(self, user, timestamp, itemid, meta):
        from item.models import Item
        i = Item.get(itemid)
        if i.timestamp > timestamp:
            return True
        key = meta.keys()[0]
        if not meta[key] and i.meta.get('mainid') == key:
            logger.debug('remove id mapping %s currenrlt %s', key, meta[key], i.meta[key])
            i.update_mainid(key, meta[key])
        elif meta[key] and (i.meta.get('mainid') != key or meta[key] != i.meta.get(key)):
            logger.debug('new mapping %s %s currently %s %s', key, meta[key], i.meta.get('mainid'), i.meta.get(i.meta.get('mainid')))
            i.update_mainid(key, meta[key])
        return True

    def action_removeitem(self, user, timestamp, itemid):
        from item.models import Item
        i = Item.get(itemid)
        if not i or i.timestamp > timestamp:
            return True
        if user in i.users:
            i.users.remove(user)
        if i.users:
            i.update()
        else:
            db.session.delete(i)
            db.session.commit()
        return True

    def action_addlist(self, user, timestamp, name, query=None):
        from user.models import List
        l = List.create(user.id, name)
        return True

    def action_editlist(self, user, timestamp, name, new):
        from user.models import List
        l = List.get_or_create(user.id, name)
        if 'name' in new:
            l.name = new['name']
        l.save()
        return True

    def action_orderlists(self, user, timestamp, lists):
        from user.models import List
        position = 0
        for name in lists:
            l = List.get_or_create(user.id, name)
            l.position = position
            l.save()
            position += 1
        return True

    def action_removelist(self, user, timestamp, name):
        from user.models import List
        l = List.get(user.id, name)
        if l:
            l.remove()
        return True

    def action_addlistitems(self, user, timestamp, name, ids):
        from user.models import List
        l = List.get_or_create(user.id, name)
        l.add_items(ids)
        return True

    def action_removelistitems(self, user, timestamp, name, ids):
        from user.models import List
        l = List.get(user.id, name)
        if l:
            l.remove_items(ids)
        return True

    def action_editusername(self, user, timestamp, username):
        user.info['username'] = username
        user.save()
        return True

    def action_editcontact(self, user, timestamp, contact):
        user.info['contact'] = contact
        user.save()
        return True

    def action_addpeer(self, user, timestamp, peerid, username):
        from user.models import User
        if not 'users' in user.info:
            user.info['users'] = {}
        user.info['users'][peerid] = username
        user.save()
        peer = User.get_or_create(peerid)
        if not 'username' in peer.info:
            peer.info['username'] = username
            peer.save()
        return True

    def action_removepeer(self, user, timestamp, peerid):
        if 'users' in user.info and peerid in user.info['users']:
            del user.info['users'][peerid]
            user.save()
            #fixme, remove from User table if no other connection exists
        return True
