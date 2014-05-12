# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from Queue import Queue
from threading import Thread
import json

from datetime import datetime
import os

import ox
import ed25519
import requests

import settings
import user.models
from changelog import Changelog

import directory
from websocket import trigger_event
from localnodes import LocalNodes

ENCODING='base64'

class Node(object):
    online = False
    download_speed = 0

    def __init__(self, nodes, user):
        self._nodes = nodes
        self._app = nodes._app
        self.user_id = user.id
        key = str(user.id)
        self.vk = ed25519.VerifyingKey(key, encoding=ENCODING)
        self.go_online()

    @property
    def url(self):
        local = self.get_local()
        if local:
            url = 'http://[%s]:%s' % (local['host'], local['port'])
            print 'using local peer discovery to access node', url
        else:
            if ':' in self.host:
                url = 'http://[%s]:%s' % (self.host, self.port)
            else:
                url = 'http://%s:%s' % (self.host, self.port)
        return url

    def resolve_host(self):
        r = directory.get(self.vk)
        if r:
            self.host = r['host']
            if 'port' in r:
                self.port = r['port']
        else:
            self.host = None
            self.port = 9851

    def get_local(self):
        if self._nodes and self._nodes._local:
            return self._nodes._local.get(self.user_id)
        return None

    def request(self, action, *args):
        if not self.host:
            self.resolve_host()
        if not self.host:
            return None
        content = json.dumps([action, args])
        sig = settings.sk.sign(content, encoding=ENCODING)
        headers = {
            'User-Agent': settings.USER_AGENT,
            'Accept': 'text/plain',
            'Accept-Encoding': 'gzip',
            'Content-Type': 'application/json',
            'X-Ed25519-Key': settings.USER_ID,
            'X-Ed25519-Signature': sig,
        }
        r = requests.post(self.url, data=content, headers=headers)
        if r.status_code == 403:
            print 'REMOTE ENDED PEERING'
            if self.user.peered:
                self.user.update_peering(False)
        data = r.content
        sig = r.headers.get('X-Ed25519-Signature')
        if sig and self._valid(data, sig):
            response = json.loads(data)
        else:
            response = None
        return response

    def _valid(self, data, sig):
        try:
            self.vk.verify(sig, data, encoding=ENCODING)
        #except ed25519.BadSignatureError:
        except:
            return False
        return True

    @property
    def user(self):
        return user.models.User.get_or_create(self.user_id)

    def go_online(self):
        self.resolve_host()
        if self.user.peered:
            try:
                self.online = False
                print 'type to connect to', self.user_id
                self.pullChanges()
                print 'connected to', self.user_id
                self.online = True
            except:
                import traceback
                traceback.print_exc()
                print 'failed to connect to', self.user_id
                self.online = False
        else:
            self.online = False
        trigger_event('status', {
            'id': self.user_id,
            'status': 'online' if self.online else 'offline'
        })

    def pullChanges(self):
        with self._app.app_context():
            last = Changelog.query.filter_by(user_id=self.user_id).order_by('-revision').first()
            from_revision = last.revision + 1 if last else 0
            changes = self.request('pullChanges', from_revision)
            if not changes:
                return False
            for change in changes:
                if not Changelog.apply_change(self.user, change):
                    print 'FAIL', change
                    break
                    return False
            return True

    def pushChanges(self, changes):
        print 'pushing changes to', self.user_id, changes
        try:
            r = self.request('pushChanges', changes)
        except:
            self.online = False
            trigger_event('status', {
                'id': self.user_id,
                'status': 'offline'
            })
            r = False
        print r

    def requestPeering(self, message):
        p = self.user
        p.pending = 'sent'
        p.save()
        r = self.request('requestPeering', settings.preferences['username'], message)
        return True

    def acceptPeering(self, message):
        r = self.request('acceptPeering', settings.preferences['username'], message)
        p = self.user
        p.update_peering(True)
        self.go_online()
        return True

    def rejectPeering(self, message):
        r = self.request('rejectPeering', message)
        p = self.user
        p.update_peering(False)
        return True

    def removePeering(self, message):
        r = self.request('removePeering', message)
        p = self.user
        p.update_peering(False)
        return True

    def download(self, item):
        url = '%s/get/%s' % (self.url, item.id)
        headers = {
            'User-Agent': settings.USER_AGENT,
        }
        t1 = datetime.now()
        print 'GET', url
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            t2 = datetime.now()
            duration = (t2-t1).total_seconds()
            if duration:
                self.download_speed = len(r.content) / duration
            print 'SPEED', ox.format_bits(self.download_speed)
            return item.save_file(r.content)
        else:
            print 'FAILED', url
            return False

    def download_upgrade(self):
        for module in settings.release['modules']:
            path = os.path.join(settings.update_path, settings.release['modules'][module]['name'])
            if not os.path.exists(path):
                url = '%s/oml/%s' % (self.url, settings.release['modules'][module]['name'])
                sha1 = settings.release['modules'][module]['sha1']
                headers = {
                    'User-Agent': settings.USER_AGENT,
                }
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    with open(path, 'w') as fd:
                        fd.write(r.content)
                        if (ox.sha1sum(path) != sha1):
                            print 'invalid update!'
                            os.unlink(path)
                            return False
                else:
                    return False

class Nodes(Thread):
    _nodes = {}

    def __init__(self, app):
        self._app = app
        self._q = Queue()
        self._running = True
        self._local = LocalNodes(app)
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def queue(self, *args):
        self._q.put(list(args))

    def check_online(self, id):
        return id in self._nodes and self._nodes[id].online

    def download(self, id, item):
        return id in self._nodes and self._nodes[id].download(item)

    def _call(self, target, action, *args):
        print 'call', target, action, args
        if target == 'all':
            nodes = self._nodes.values()
        elif target == 'online':
            nodes = [n for n in self._nodes.values() if n.online]
        else:
            nodes = [self._nodes[target]]
        for node in nodes:
            getattr(node, action)(*args)

    def _add_node(self, user_id):
        if user_id not in self._nodes:
            from user.models import User
            self._nodes[user_id] = Node(self, User.get_or_create(user_id))
        else:
            self._nodes[user_id].online = True
            trigger_event('status', {
                'id': user_id,
                'status': 'online'
            })

    def run(self):
        with self._app.app_context():
            while self._running:
                args = self._q.get()
                if args:
                    if args[0] == 'add':
                        self._add_node(args[1])
                    else:
                        print 'next', args
                        self._call(*args)

    def join(self):
        self._running = False
        self._q.put(None)
        return Thread.join(self)
