# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import json
from datetime import datetime

from ed25519_utils import valid

import settings
from settings import db
import state
from websocket import trigger_event

class Changelog(db.Model):
    '''
        additem               itemid    metadata from file (info) + OLID
        edititem              itemid    name->id (i.e. olid-> OL...M)
        removeitem            itemid
        addlist               name
        editlist              name {name: newname}
        orderlists            [name, name, name]
        removelist            name
        additemtolist         listname itemid
        removeitemfromlist    listname itemid
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
            state.nodes.queue('online', 'pushChanges', [c.json()])

    @property
    def timestamp(self):
        return self.created.strftime('%s')

    @classmethod
    def apply_change(cls, user, change, rebuild=False):
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
                print 'apply change', action
                if getattr(c, 'action_' + action)(user, timestamp, *args):
                    print 'change applied'
                    db.session.add(c)
                    db.session.commit()
                    return True
            else:
                print 'INVLAID SIGNATURE ON CHANGE', change
                raise Exception, 'invalid signature'
        else:
            print 'revsion does not match! got', revision, 'expecting', next_revision
            return False

    def __repr__(self):
        return self.data

    def verify(self):
        _data = str(self.revision) + str(self.timestamp) + self.data
        return valid(self.user_id, _data, self.sig)

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
            print 'remove id mapping', key, meta[key], 'currently', i.meta[key]
            i.update_mainid(key, meta[key])
        elif meta[key] and (i.meta.get('mainid') != key or meta[key] != i.meta.get(key)):
            print 'new mapping', key, meta[key], 'currently', i.meta.get('mainid'), i.meta.get(i.meta.get('mainid'))
            i.update_mainid(key, meta[key])
        return True

    def action_removeitem(self, user, timestamp, itemid):
        from item.models import Item
        i = Item.get(itemid)
        if not i or i.timestamp > timestamp:
            return True
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

    def action_addlistitem(self, user, timestamp, name, itemid):
        from item.models import Item
        from user.models import List
        l = List.get(user.id, name)
        i = Item.get(itemid)
        if l and i:
            i.lists.append(l)
            i.update()
        return True

    def action_removelistitem(self, user, timestamp, name, itemid):
        from item.models import Item
        from user.models import List
        l = List.get(user.id, name)
        i = Item.get(itemid)
        if l and i:
            i.lists.remove(l)
            i.update()
        return True

    def action_editusername(self, user, timestamp, username):
        user.info['username'] = username
        user.save()
        return True

    def action_editcontact(self, user, timestamp, contact):
        user.info['contact'] = contact
        user.save()
        return True

    def action_adduser(self, user, timestamp, peerid, username):
        from user.models import User
        if not 'users' in user.info:
            user.info['users'] = {}
        user.info['users'][peerid] = username
        user.save()
        User.get_or_create(peerid)
        #fixme, add username to user?
        return True

    def action_removeuser(self, user, timestamp, peerid):
        if 'users' in user.info and peerid in user.info['users']:
            del user.info['users'][peerid]
            user.save()
            #fixme, remove from User table if no other connection exists
        return True
