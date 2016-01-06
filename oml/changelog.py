# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from datetime import datetime
import json

import sqlalchemy as sa

from utils import datetime2ts, ts2datetime
from websocket import trigger_event
import db
import settings
import state

import logging
logger = logging.getLogger(__name__)

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

        editmeta              key, value data (i.e. 'isbn', '0000000000', {title: 'Example'})
        resetmeta             key, value
    '''
    __tablename__ = 'changelog'
    id = sa.Column(sa.Integer(), primary_key=True)

    created = sa.Column(sa.DateTime())
    timestamp = sa.Column(sa.BigInteger())

    user_id = sa.Column(sa.String(43))
    revision = sa.Column(sa.BigInteger())
    data = sa.Column(sa.Text())
    sig = sa.Column(sa.String(96))

    @classmethod
    def record(cls, user, action, *args):
        c = cls()
        c.created = datetime.utcnow()
        c.timestamp = datetime2ts(c.created)
        c.user_id = user.id
        c.revision = cls.query.filter_by(user_id=user.id).count()
        c.data = json.dumps([action] + list(args), ensure_ascii=False)
        _data = str(c.revision) + str(c.timestamp) + c.data
        _data = _data.encode()
        state.db.session.add(c)
        state.db.session.commit()
        #if state.nodes:
        #    state.nodes.queue('peered', 'pushChanges', [c.json()])

    @classmethod
    def apply_changes(cls, user, changes):
        trigger = changes
        for change in changes:
            if not cls.apply_change(user, change, trigger=False):
                logger.debug('FAIL %s', change)
                trigger = False
                break
                return False
        if trigger:
            trigger_event('change', {});
        return True

    @classmethod
    def apply_change(cls, user, change, trigger=True):
        revision, timestamp, data = change
        last = cls.query.filter_by(user_id=user.id).order_by('-revision').first()
        next_revision = last.revision + 1 if last else 0
        if revision >= next_revision:
            c = cls()
            c.created = datetime.utcnow()
            c.timestamp = timestamp
            c.user_id = user.id
            c.revision = revision
            c.data = data
            args = json.loads(data)
            logger.debug('apply change from %s: %s', user.name, args)
            if getattr(c, 'action_' + args[0])(user, timestamp, *args[1:]):
                logger.debug('change applied')
                state.db.session.add(c)
                state.db.session.commit()
                if trigger:
                    trigger_event('change', {});
                return True
        else:
            logger.debug('revsion does not match! got %s expecting %s', revision, next_revision)
            return False

    def __repr__(self):
        return self.data

    def json(self):
        timestamp = self.timestamp or datetime2ts(self.created)
        return [self.revision, timestamp, self.data]

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
                fd.write(json.dumps(c.json(), ensure_ascii=False) + '\n')

    def action_additem(self, user, timestamp, itemid, info):
        from item.models import Item
        i = Item.get(itemid)
        if i:
            if user not in i.users:
                i.add_user(user)
                i.update()
        else:
            i = Item.get_or_create(itemid, info)
            i.modified = ts2datetime(timestamp)
            if user not in i.users:
                i.add_user(user)
            i.update()
        user.clear_smart_list_cache()
        return True

    def action_edititem(self, user, timestamp, itemid, meta):
        from item.models import Item
        i = Item.get(itemid)
        if not i:
            logger.debug('ignore edititem for unknown item %s %s', timestamp, itemid)
            return True
        if i.timestamp > timestamp:
            logger.debug('ignore edititem change %s %s %s', timestamp, itemid, meta)
            return True
        primary = None
        if 'primaryid' in meta:
            primary = meta['primaryid']
            key = primary[0]
        else:
            keys = [k for k in meta if k in Item.id_keys]
            if keys:
                key = keys[0]
                primary = [key, meta[key]]
        if primary:
            if not meta[key] and i.meta.get('primaryid', [''])[0] == key:
                logger.debug('remove id mapping %s %s', i.id, primary)
                i.update_primaryid(*primary, scrape=False)
                i.modified = ts2datetime(timestamp)
            elif meta[key] and i.meta.get('primaryid') != primary:
                logger.debug('edit mapping %s %s', i.id, primary)
                i.update_primaryid(*primary, scrape=False)
                i.modified = ts2datetime(timestamp)
        else:
            i.update_meta(meta)
            i.modified = ts2datetime(timestamp)
        i.save()
        user.clear_smart_list_cache()
        return True

    def action_removeitem(self, user, timestamp, itemid):
        from item.models import Item
        i = Item.get(itemid)
        if i:
            if user in i.users:
                i.users.remove(user)
            if i.users:
                i.update()
            else:
                i.delete()
        user.clear_list_cache()
        user.clear_smart_list_cache()
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
        user.clear_list_cache()
        return True

    def action_orderlists(self, user, timestamp, lists):
        from user.models import List
        idx = 0
        for name in lists:
            l = List.get_or_create(user.id, name)
            l.index_ = idx
            l.save()
            idx += 1
        return True

    def action_removelist(self, user, timestamp, name):
        from user.models import List
        l = List.get(user.id, name)
        if l:
            l.remove()
        user.clear_list_cache()
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
        from user.models import List
        old = user.nickname
        user.info['username'] = username
        user.update_name()
        if old != user.nickname:
            List.rename_user(old, user.nickname)
        user.save()
        return True

    def action_editcontact(self, user, timestamp, contact):
        user.info['contact'] = contact
        user.save()
        return True

    def action_addpeer(self, user, timestamp, peerid, username):
        if len(peerid) == 16:
            from user.models import User
            if not 'users' in user.info:
                user.info['users'] = {}
            user.info['users'][peerid] = username
            user.save()
            peer = User.get_or_create(peerid)
            if not 'username' in peer.info:
                peer.info['username'] = username
                peer.update_name()
                peer.save()
        return True

    def action_removepeer(self, user, timestamp, peerid):
        if 'users' in user.info and peerid in user.info['users']:
            del user.info['users'][peerid]
            user.save()
            #fixme, remove from User table if no other connection exists
        return True

    def action_editmeta(self, user, timestamp, key, value, data):
        from item.models import Metadata
        m = Metadata.get(key, value)
        if not m or m.timestamp < timestamp:
            if not m:
                m = Metadata.get_or_create(key, value)
            if m.edit(data):
                m.update_items()
        user.clear_smart_list_cache()
        return True

    def action_resetmeta(self, user, timestamp, key, value):
        from item.models import Metadata
        m = Metadata.get(key, value)
        if m and m.timestamp < timestamp:
            m.reset()
        user.clear_smart_list_cache()
        return True
