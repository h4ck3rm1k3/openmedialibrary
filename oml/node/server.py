# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import os

import tornado
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import PeriodicCallback

from oxtornado import run_async
from utils import valid, get_public_ipv6
from websocket import trigger_event
import cert
import db
import directory
import json
import nodeapi
import settings
import state
import user

import logging
logger = logging.getLogger('oml.node.server')


class NodeHandler(tornado.web.RequestHandler):

    def initialize(self):
        pass

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        '''
            API
            pullChanges     [userid] from [to]
            pushChanges     [index, change]
            requestPeering  username message
            acceptPeering   username message
            rejectPeering   message
            removePeering   message

            ping            responds public ip
        '''
        key = str(self.request.headers['X-Ed25519-Key'])
        sig = str(self.request.headers['X-Ed25519-Signature'])
        data = self.request.body
        content = {}

        self.set_header('X-Node-Protocol', settings.NODE_PROTOCOL)
        if self.request.headers.get('X-Node-Protocol', None) > settings.NODE_PROTOCOL:
            state.update_required = True
        if self.request.headers.get('X-Node-Protocol', None) != settings.NODE_PROTOCOL:
            content = settings.release
        else:
            if valid(key, data, sig):
                action, args = json.loads(data)
                logger.debug('NODE action %s %s (%s)', action, args, key)
                if action == 'ping':
                    content = {
                        'ip': self.request.remote_addr
                    }
                else:
                    content = yield tornado.gen.Task(api_call, action, key, args)
                    if content is None:
                        content = {'status': 'not peered'}
                        logger.debug('PEER %s IS UNKNOWN SEND 403', key)
                        self.set_status(403)
        content = json.dumps(content)
        sig = settings.sk.sign(content, encoding='base64')
        self.set_header('X-Ed25519-Signature', sig)
        self.set_header('X-Node-Protocol', settings.NODE_PROTOCOL)
        self.write(content)

    def get(self):
        self.set_header('X-Node-Protocol', settings.NODE_PROTOCOL)
        if self.request.headers.get('X-Node-Protocol', None) > settings.NODE_PROTOCOL:
            state.update_required = True
        self.write('Open Media Library')

@run_async
def api_call(action, key, args, callback):
    with db.session():
        u = user.models.User.get(key)
        if action in (
            'requestPeering', 'acceptPeering', 'rejectPeering', 'removePeering'
        ) or (u and u.peered):
            content = getattr(nodeapi, 'api_' + action)(key, *args)
        else:
            if u and u.pending:
                logger.debug('ignore request from pending peer[%s] %s (%s)', key, action, args)
                content = {}
            else:
                content = None
    callback(content)

class ShareHandler(tornado.web.RequestHandler):

    def initialize(self):
        pass

    def get(self, id):
        import item.models
        with db.session():
            i = item.models.Item.get(id)
            if not i:
                self.set_status(404)
                return
            path = i.get_path()
            mimetype = {
                'epub': 'application/epub+zip',
                'pdf': 'application/pdf',
                'txt': 'text/plain',
            }.get(path.split('.')[-1], None)
            self.set_header('Content-Type', mimetype)
            logger.debug('GET file %s', id)
            with open(path, 'rb') as f:
                while 1:
                    data = f.read(16384)
                    if not data:
                        break
                    self.write(data)

def publish_node():
    update_online()
    if state.online:
        with db.session():
            for u in user.models.User.query.filter_by(queued=True):
                logger.debug('adding queued node... %s', u.id)
                state.nodes.queue('add', u.id)
    state.check_nodes = PeriodicCallback(check_nodes, 120000)
    state.check_nodes.start()
    state._online = PeriodicCallback(update_online, 60000)
    state._online.start()

def update_online():
    host = get_public_ipv6()
    if not host:
        if state.online:
            state.online = False
            trigger_event('status', {
                'id': settings.USER_ID,
                'online': state.online
            })
    else:
        if host != state.host:
            state.host = host
            online = directory.put(settings.sk, {
                'host': host,
                'port': settings.server['node_port'],
                'cert': settings.server['cert']
            })
            if online != state.online:
                state.online = online
                trigger_event('status', {
                    'id': settings.USER_ID,
                    'online': state.online
                })

def check_nodes():
    if state.online:
        with db.session():
            for u in user.models.User.query.filter_by(queued=True):
                if not state.nodes.is_online(u.id):
                    logger.debug('queued peering message for %s trying to connect...', u.id)
                    state.nodes.queue('add', u.id)

def start():
    application = Application([
        (r"/get/(.*)", ShareHandler),
        (r".*", NodeHandler),
    ], gzip=True)
    if not os.path.exists(settings.ssl_cert_path):
        settings.server['cert'] = cert.generate_ssl()

    http_server = HTTPServer(application, ssl_options={
        "certfile": settings.ssl_cert_path,
        "keyfile": settings.ssl_key_path
    })
    http_server.listen(settings.server['node_port'], settings.server['node_address'])
    state.main.add_callback(publish_node)
    return http_server
