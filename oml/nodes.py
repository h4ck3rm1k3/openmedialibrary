# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from queue import Queue
from threading import Thread
import json
import socket
from io import BytesIO
import gzip
import urllib.request, urllib.error, urllib.parse
from datetime import datetime
import os
import time

import ox
import ed25519
from tornado.ioloop import PeriodicCallback

import settings
import user.models
from changelog import Changelog

import directory
from websocket import trigger_event
from localnodes import LocalNodes
from tor_request import get_opener
import state
import db

import logging
logger = logging.getLogger(__name__)

ENCODING='base64'

class Node(Thread):
    _running = True
    _pulling = False
    host = None
    local = None
    _online = None
    download_speed = 0
    TIMEOUT = 5

    def __init__(self, nodes, user):
        self._nodes = nodes
        self.user_id = user.id
        self._opener = get_opener(self.user_id)
        self._q = Queue()
        Thread.__init__(self)
        self.daemon = True
        self.start()
        self._pull = PeriodicCallback(self.pull, 60000)
        self._pull.start()
        self.ping()

    def run(self):
        while self._running:
            action = self._q.get()
            if not self._running:
                break
            if action == 'go_online':
                if not self.online:
                    self._go_online()
            elif action == 'ping':
                self.online = self.can_connect()
            elif action == 'pull':
                self._pulling = True
                self.online = self.can_connect()
                self.pullChanges()
                self._pulling = False
            else:
                logger.debug('unknown action %s', action)

    def join(self):
        self._running = False
        self._q.put('')
        #return Thread.join(self)

    def pull(self):
        if state.online and not self._pulling:
            self._q.put('pull')

    def ping(self):
        if state.online:
            self._q.put('ping')

    def go_online(self):
        self._q.put('go_online')

    @property
    def url(self):
        url = None
        if self.local:
            if ':' in self.local:
                url = 'https://[%s]:%s' % (self.local, self.port)
            else:
                url = 'https://%s:%s' % (self.local, self.port)
        elif len(self.user_id) == 16:
            url = 'https://%s.onion:9851' % self.user_id
        return url

    @property
    def online(self):
        return self._online

    @online.setter
    def online(self, online):
        if self._online != online:
            self._online = online
            self.trigger_status()
        else:
            self._online = online

    def resolve(self):
        #logger.debug('resolve node %s', self.user_id)
        r = self.get_local()
        if r:
            self.local = r['host']
            if 'port' in r:
                self.port = r['port']
        else:
            self.local = None
            self.port = 9851
        if len(self.user_id) == 43:
            self.migrate_id()


    def migrate_id(self):
        key = self.user_id.encode()
        vk = ed25519.VerifyingKey(key, encoding=ENCODING)
        try:
            r = directory.get(vk)
        except:
            logger.debug('directory failed', exc_info=1)
            r = None
        if r and 'id' in r and len(r['id']) == 16:
            u = self.user
            self.user_id = r['id']
            u.migrate_id(self.user_id)
            self._opener = get_opener(self.user_id)

    def get_local(self):
        if self._nodes and self._nodes._local:
            return self._nodes._local.get(self.user_id)
        return None

    def request(self, action, *args):
        logger.debug('request[%s] %s%s', self.user_id, action, args)
        self.resolve()
        url = self.url
        if not url:
            logger.debug('unable to find host %s', self.user_id)
            self.online = False
            return None
        #logger.debug('url=%s', url)
        content = json.dumps([action, args]).encode()
        #sig = settings.sk.sign(content, encoding=ENCODING).decode()
        headers = {
            'User-Agent': settings.USER_AGENT,
            'X-Node-Protocol': settings.NODE_PROTOCOL,
            'Accept': 'text/plain',
            'Accept-Encoding': 'gzip',
            'Content-Type': 'application/json',
        }
        self._opener.addheaders = list(zip(headers.keys(), headers.values()))
        #logger.debug('headers: %s', self._opener.addheaders)
        try:
            self._opener.timeout = self.TIMEOUT
            r = self._opener.open(url, data=content)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                logger.debug('REMOTE ENDED PEERING')
                with db.session():
                    u = self.user
                    if u.peered:
                        u.update_peering(False)
                    self.online = False
                return
            logger.debug('urllib2.HTTPError %s %s', e, e.code)
            self.online = False
            return None
        except urllib.error.URLError as e:
            logger.debug('urllib2.URLError %s', e)
            self.online = False
            return None
        except:
            logger.debug('unknown url error', exc_info=1)
            self.online = False
            return None
        data = r.read()
        if r.headers.get('content-encoding', None) == 'gzip':
            data = gzip.GzipFile(fileobj=BytesIO(data)).read()

        version = r.headers.get('X-Node-Protocol', None)
        if version != settings.NODE_PROTOCOL:
            logger.debug('version does not match local: %s remote %s', settings.NODE_PROTOCOL, version)
            self.online = False
            if version > settings.NODE_PROTOCOL:
                state.update_required = True
            return None

        '''
        sig = r.headers.get('X-Node-Signature')
        if sig and self._valid(data, sig):
            response = json.loads(data.decode('utf-8'))
        else:
            logger.debug('invalid signature %s', data)
            response = None
        '''
        response = json.loads(data.decode('utf-8'))
        return response

    def _valid(self, data, sig):
        if isinstance(data, str):
            data = data.encode()
        try:
            self.vk.verify(sig, data, encoding=ENCODING)
        #except ed25519.BadSignatureError:
        except:
            return False
        return True

    @property
    def user(self):
        with db.session():
            return user.models.User.get_or_create(self.user_id)

    def can_connect(self):
        self.resolve()
        url = self.url
        try:
            if url:
                headers = {
                    'User-Agent': settings.USER_AGENT,
                    'X-Node-Protocol': settings.NODE_PROTOCOL,
                    'Accept-Encoding': 'gzip',
                }
                self._opener.addheaders = list(zip(headers.keys(), headers.values()))
                self._opener.timeout = 2
                r = self._opener.open(url)
                version = r.headers.get('X-Node-Protocol', None)
                if version != settings.NODE_PROTOCOL:
                    logger.debug('version does not match local: %s remote %s', settings.NODE_PROTOCOL, version)
                    return False
                c = r.read()
                logger.debug('can connect to: %s (%s)', url, self.user.nickname)
                return True
        except:
            logger.debug('can not connect to: %s (%s)', url, self.user.nickname)
            pass
        return False

    def is_online(self):
        return self.online or self.get_local() != None

    def _go_online(self):
        u = self.user
        if u.peered or u.queued:
            logger.debug('go_online peered=%s queued=%s %s (%s)', u.peered, u.queued, u.id, u.nickname)
            try:
                self.online = self.can_connect()
                if self.online:
                    logger.debug('connected to %s', self.url)
                    if u.queued:
                        logger.debug('queued peering event pending=%s peered=%s', u.pending, u.peered)
                        if u.pending == 'sent':
                            self.peering('requestPeering')
                        elif u.pending == '' and u.peered:
                            self.peering('acceptPeering')
                        else:
                            #fixme, what about cancel/reject peering here?
                            self.peering('removePeering')
            except:
                logger.debug('failed to connect to %s', self.user_id)
                self.online = False
        else:
            self.online = False

    def trigger_status(self):
        if self.online is not None:
            trigger_event('status', {
                'id': self.user_id,
                'online': self.online
            })

    def pullChanges(self):
        if not self.online or not self.user.peered:
            return True
        last = Changelog.query.filter_by(user_id=self.user_id).order_by('-revision').first()
        from_revision = last.revision + 1 if last else 0
        try:
            changes = self.request('pullChanges', from_revision)
        except:
            self.online = False
            logger.debug('%s went offline', self.user.name)
            return False
        if not changes:
            return False
        with db.session():
            r = Changelog.apply_changes(self.user, changes)
        return r

    def pushChanges(self, changes):
        logger.debug('pushing changes to %s %s', self.user_id, changes)
        if self.online:
            try:
                r = self.request('pushChanges', changes)
            except:
                self.online = False
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
        else:
            self.go_online()
        trigger_event('peering.%s'%action.replace('Peering', ''), u.json())
        return True

    def download(self, item):
        from item.models import Transfer
        self.resolve()
        url = '%s/get/%s' % (self.url, item.id)
        headers = {
            'X-Node-Protocol': settings.NODE_PROTOCOL,
            'User-Agent': settings.USER_AGENT,
        }
        t1 = datetime.utcnow()
        logger.debug('download %s', url)
        self._opener.addheaders = list(zip(headers.keys(), headers.values()))
        try:
            r = self._opener.open(url, timeout=self.TIMEOUT*2)
        except:
            logger.debug('openurl failed %s', url, exc_info=1)
            return False
        if r.getcode() == 200:
            try:
                fileobj = r
                if r.headers.get('content-encoding', None) == 'gzip':
                    fileobj = gzip.GzipFile(fileobj=r)
                content = b''
                ct = datetime.utcnow()
                size = 0
                for chunk in iter(lambda: fileobj.read(16*1024), b''):
                    content += chunk
                    size += len(chunk)
                    since_ct = (datetime.utcnow() - ct).total_seconds()
                    if since_ct > 1:
                        ct = datetime.utcnow()
                        t = Transfer.get(item.id)
                        t.progress = len(content) / item.info['size']
                        t.save()
                        trigger_event('transfer', {
                            'id': item.id, 'progress': t.progress
                        })
                        if state.bandwidth:
                            state.bandwidth.download(size/since_ct)
                            size = 0
                '''
                content = fileobj.read()
                '''
                if state.bandwidth:
                    state.bandwidth.download(size/since_ct)
                    size = 0

                t2 = datetime.utcnow()
                duration = (t2-t1).total_seconds()
                if duration:
                    self.download_speed = len(content) / duration
                logger.debug('SPEED %s', ox.format_bits(self.download_speed))
                return item.save_file(content)
            except:
                logger.debug('download failed %s', url, exc_info=1)
                return False
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
                self._opener.addheaders = list(zip(headers.keys(), headers.values()))
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

    def __init__(self):
        self._q = Queue()
        self._running = True
        with db.session():
            for u in user.models.User.query.filter_by(peered=True):
                if 'local' in u.info:
                    del u.info['local']
                    u.save()
                self.queue('add', u.id)
            for u in user.models.User.query.filter_by(queued=True):
                logger.debug('adding queued node... %s', u.id)
                self.queue('add', u.id)
        self._local = LocalNodes()
        self._cleanup = PeriodicCallback(lambda: self.queue('cleanup'), 120000)
        self._cleanup.start()
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def cleanup(self):
        if self._running and self._local:
            self._local.cleanup()

    def queue(self, *args):
        self._q.put(list(args))

    def is_online(self, id):
        return id in self._nodes and self._nodes[id].is_online()

    def download(self, id, item):
        return id in self._nodes and self._nodes[id].download(item)

    def _call(self, target, action, *args):
        if target == 'all':
            nodes = list(self._nodes.values())
        elif target == 'peered':
            nodes = [n for n in list(self._nodes.values()) if n.user.peered]
        elif target == 'online':
            nodes = [n for n in list(self._nodes.values()) if n.online]
        else:
            nodes = [self._nodes[target]]
        for node in nodes:
            r = getattr(node, action)(*args)
            logger.debug('call node api %s->%s%s = %s', node.user_id, action, args, r)

    def _add(self, user_id):
        if user_id not in self._nodes:
            from user.models import User
            with db.session():
                self._nodes[user_id] = Node(self, User.get_or_create(user_id))
        else:
            if not self._nodes[user_id].online:
                self._nodes[user_id].ping()

    def run(self):
        while self._running:
            args = self._q.get()
            if args:
                if args[0] == 'cleanup':
                    self.cleanup()
                elif args[0] == 'add':
                    self._add(args[1])
                else:
                    self._call(*args)

    def join(self):
        self._running = False
        self._q.put(None)
        for node in list(self._nodes.values()):
            node.join()
        if self._local:
            self._local.join()
        return Thread.join(self)

def publish_node():
    update_online()
    state.check_nodes = PeriodicCallback(check_nodes, 120000)
    state.check_nodes.start()
    state._online = PeriodicCallback(update_online, 60000)
    state._online.start()

def update_online():
    online = state.tor and state.tor.is_online()
    if online != state.online:
        state.online = online
        trigger_event('status', {
            'id': settings.USER_ID,
            'online': state.online
        })
    if not settings.server.get('migrated_id', False):
        r = directory.put(settings.sk, {
            'id': settings.USER_ID,
        })
        logger.debug('push id to directory %s', r)
        if r:
            settings.server['migrated_id'] = True

def check_nodes():
    if state.online:
        with db.session():
            for u in user.models.User.query.filter_by(queued=True):
                if not state.nodes.is_online(u.id):
                    logger.debug('queued peering message for %s trying to connect...', u.id)
                    state.nodes.queue('add', u.id)
