# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from Queue import Queue
from threading import Thread
import json
import socket
from StringIO import StringIO
import gzip
import urllib2
from datetime import datetime
import os

import ox
import ed25519
from tornado.ioloop import PeriodicCallback

import settings
import user.models
from changelog import Changelog

import directory
from websocket import trigger_event
from localnodes import LocalNodes
from ssl_request import get_opener

import logging
logger = logging.getLogger('oml.nodes')

ENCODING='base64'

class Node(object):
    _cert = None
    online = False
    download_speed = 0
    TIMEOUT = 3

    def __init__(self, nodes, user):
        self._nodes = nodes
        self._app = nodes._app
        self.user_id = user.id
        key = str(user.id)
        self.vk = ed25519.VerifyingKey(key, encoding=ENCODING)
        self.go_online()
        logger.debug('new Node %s online=%s', self.user_id, self.online)
        self._ping = PeriodicCallback(self.ping, 120000)
        self._ping.start()

    @property
    def url(self):
        local = self.get_local()
        if local:
            url = 'https://[%s]:%s' % (local['host'], local['port'])
        elif not self.host:
            return None
        else:
            if ':' in self.host:
                url = 'https://[%s]:%s' % (self.host, self.port)
            else:
                url = 'https://%s:%s' % (self.host, self.port)
        return url

    def resolve(self):
        r = directory.get(self.vk)
        if r:
            self.host = r['host']
            if 'port' in r:
                self.port = r['port']
            if r['cert'] != self._cert:
                self._cert = r['cert']
                self._opener = get_opener(self._cert)
        else:
            self.host = None
            self.port = 9851

    def get_local(self):
        if self._nodes and self._nodes._local:
            local = self._nodes._local.get(self.user_id)
            if local and local['cert'] != self._cert:
                self._cert = local['cert']
                self._opener = get_opener(self._cert)
            return local
        return None

    def request(self, action, *args):
        url = self.url
        if not url:
            self.resolve()
        url = self.url
        if not self.url:
            logger.debug('unable to find host %s', self.user_id)
            self.online = False
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
        self._opener.addheaders = zip(headers.keys(), headers.values())
        try:
            r = self._opener.open(url, data=content, timeout=self.TIMEOUT)
        except urllib2.HTTPError as e:
            if e.code == 403:
                logger.debug('REMOTE ENDED PEERING')
                if self.user.peered:
                    self.user.update_peering(False)
                    self.online = False
                return
            logger.debug('urllib2.HTTPError %s %s', e, e.code)
            self.online = False
            return None
        except urllib2.URLError as e:
            logger.debug('urllib2.URLError %s', e)
            self.online = False
            return None
        except:
            logger.debug('unknown url error', exc_info=1)
            self.online = False
            return None
        data = r.read()
        if r.headers.get('content-encoding', None) == 'gzip':
            data = gzip.GzipFile(fileobj=StringIO(data)).read()
        sig = r.headers.get('X-Ed25519-Signature')
        if sig and self._valid(data, sig):
            response = json.loads(data)
        else:
            logger.debug('invalid signature %s', data)
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

    def can_connect(self):
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect((self.host, self.port))
            s.close()
            return True
        except:
            pass
        return False

    def ping(self):
        with self._app.app_context():
            if self.online:
                self.online = self.can_connect()
            else:
                self.go_online()

    def go_online(self):
        self.resolve()
        u = self.user
        if u.peered or u.queued:
            try:
                self.online = False
                logger.debug('type to connect to %s', self.user_id)
                if self.can_connect():
                    self.online = True
                    if u.queued:
                        logger.debug('queued peering event pending=%s peered=%s', u.pending, u.peered)
                        if u.pending == 'sent':
                            self.peering('requestPeering')
                        elif u.pending == '' and u.peered:
                            self.peering('acceptPeering')
                        else:
                            #fixme, what about cancel/reject peering here?
                            self.peering('removePeering')
                    if self.online:
                        self.pullChanges()
                logger.debug('connected to %s', self.user_id)
            except:
                logger.debug('failed to connect to %s', self.user_id, exc_info=1)
                self.online = False
        else:
            self.online = False
        trigger_event('status', {
            'id': self.user_id,
            'online': self.online
        })

    def pullChanges(self):
        with self._app.app_context():
            last = Changelog.query.filter_by(user_id=self.user_id).order_by('-revision').first()
            from_revision = last.revision + 1 if last else 0
            changes = self.request('pullChanges', from_revision)
            if not changes:
                return False
            return Changelog.apply_changes(self.user, changes)

    def pushChanges(self, changes):
        logger.debug('pushing changes to %s %s', self.user_id, changes)
        try:
            r = self.request('pushChanges', changes)
        except:
            self.online = False
            trigger_event('status', {
                'id': self.user_id,
                'online': self.online
            })
            r = False
        logger.debug('pushedChanges %s %s', r, self.user_id)

    def peering(self, action):
        u = self.user
        if action in ('requestPeering', 'acceptPeering'):
            r = self.request(action, settings.preferences['username'], u.info.get('message'))
        else:
            r = self.request(action, u.info.get('message'))
        if r != None:
            u.queued = False
            if 'message' in u.info:
                del u.info['message']
            u.save()
        else:
            logger.debug('peering failed? %s %s', action, r)

        if action in ('cancelPeering', 'rejectPeering', 'removePeering'):
            self.online = False
        return True

    def download(self, item):
        url = '%s/get/%s' % (self.url, item.id)
        headers = {
            'User-Agent': settings.USER_AGENT,
        }
        t1 = datetime.now()
        logger.debug('download %s', url)
        '''
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = r.content
        '''
        self._opener.addheaders = zip(headers.keys(), headers.values())
        r = self._opener.open(url, timeout=self.TIMEOUT)
        if r.getcode() == 200:
            if r.headers.get('content-encoding', None) == 'gzip':
                content = gzip.GzipFile(fileobj=r).read()
            else:
                '''
                content = ''
                for chunk in iter(lambda: r.read(1024*1024), ''):
                    content += chunk
                    item.transferprogress = len(content) / item.info['size']
                    item.save()
                    trigger_event('transfer', {
                        'id': item.id, 'progress': item.transferprogress
                    })
                '''
                content = r.read()

            t2 = datetime.now()
            duration = (t2-t1).total_seconds()
            if duration:
                self.download_speed = len(content) / duration
            logger.debug('SPEED %s', ox.format_bits(self.download_speed))
            return item.save_file(content)
        else:
            logger.debug('FAILED %s', url)
            return False

    def download_upgrade(self, release):
        for module in release['modules']:
            path = os.path.join(settings.update_path, release['modules'][module]['name'])
            if not os.path.exists(path):
                url = '%s/oml/%s' % (self.url, release['modules'][module]['name'])
                sha1 = release['modules'][module]['sha1']
                headers = {
                    'User-Agent': settings.USER_AGENT,
                }
                self._opener.addheaders = zip(headers.keys(), headers.values())
                r = self._opener.open(url)
                if r.getcode() == 200:
                    with open(path, 'w') as fd:
                        fd.write(r.read())
                        if (ox.sha1sum(path) != sha1):
                            logger.error('invalid update!')
                            os.unlink(path)
                            return False
                else:
                    return False

class Nodes(Thread):
    _nodes = {}
    _local = None

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
        if target == 'all':
            nodes = self._nodes.values()
        elif target == 'peered':
            nodes = [n for n in self._nodes.values() if n.user.peered]
        elif target == 'online':
            nodes = [n for n in self._nodes.values() if n.online]
        else:
            nodes = [self._nodes[target]]
        for node in nodes:
            getattr(node, action)(*args)

    def _add(self, user_id):
        if user_id not in self._nodes:
            from user.models import User
            self._nodes[user_id] = Node(self, User.get_or_create(user_id))
        else:
            if not self._nodes[user_id].online:
                self._nodes[user_id].go_online()

    def run(self):
        with self._app.app_context():
            while self._running:
                args = self._q.get()
                if args:
                    if args[0] == 'add':
                        self._add(args[1])
                    else:
                        self._call(*args)

    def join(self):
        self._running = False
        self._q.put(None)
        return Thread.join(self)
