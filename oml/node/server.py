# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import tornado
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import PeriodicCallback

import settings

import directory
import state
import user

import json
from utils import valid, get_public_ipv6
import nodeapi
import cert

import logging
logger = logging.getLogger('oml.node.server')

class NodeHandler(tornado.web.RequestHandler):

    def initialize(self, app):
        self.app = app


    def post(self):
        request = self.request
        if request.method == 'POST':
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
            key = str(request.headers['X-Ed25519-Key'])
            sig = str(request.headers['X-Ed25519-Signature'])
            data = request.body
            content = {}
            if valid(key, data, sig):
                action, args = json.loads(data)
                logger.debug('NODE action %s %s (%s)', action, args, key)
                if action == 'ping':
                    content = {
                        'ip': request.remote_addr
                    }
                else:
                    with self.app.app_context():
                        u = user.models.User.get(key)
                        if action in (
                            'requestPeering', 'acceptPeering', 'rejectPeering', 'removePeering'
                        ) or (u and u.peered):
                            content = getattr(nodeapi, 'api_' + action)(self.app, key, *args)
                        else:
                            if u and u.pending:
                                logger.debug('ignore request from pending peer[%s] %s (%s)', key, action, args)
                                content = {}
                            else:
                                logger.debug('PEER %s IS UNKNOWN SEND 403', key)
                                self.set_status(403)
                                content = {
                                    'status': 'not peered'
                                }
            content = json.dumps(content)
            sig = settings.sk.sign(content, encoding='base64')
            self.set_header('X-Ed25519-Signature', sig)
            self.write(content)
            self.finish()

    def get(self):
        self.write('Open Media Library')
        self.finish()

class ShareHandler(tornado.web.RequestHandler):

    def initialize(self, app):
        self.app = app

    def get(self, id):
        with self.app.app_context():
            import item.models
            i = item.models.Item.get(id)
            if not i:
                self.set_status(404)
                self.finish()
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
            self.finish()


def publish_node(app):
    host = get_public_ipv6()
    state.online = directory.put(settings.sk, {
        'host': host,
        'port': settings.server['node_port'],
        'cert': settings.server['cert']
    })
    if state.online:
        with app.app_context():
            for u in user.models.User.query.filter_by(queued=True):
                logger.debug('adding queued node... %s', u.id)
                state.nodes.queue('add', u.id)
    state.check_nodes = PeriodicCallback(lambda: check_nodes(app), 120000)
    state.check_nodes.start()

def check_nodes(app):
    if state.online:
        with app.app_context():
            for u in user.models.User.query.filter_by(queued=True):
                if not state.nodes.check_online(u.id):
                    logger.debug('queued peering message for %s trying to connect...', u.id)
                    state.nodes.queue('add', u.id)

def start(app):
    application = Application([
        (r"/get/(.*)", ShareHandler, dict(app=app)),
        (r".*", NodeHandler, dict(app=app)),
    ], gzip=True)
    if not os.path.exists(settings.ssl_cert_path):
        settings.server['cert'] = cert.generate_ssl()

    http_server = HTTPServer(application, ssl_options={
        "certfile": settings.ssl_cert_path,
        "keyfile": settings.ssl_key_path
    })
    http_server.listen(settings.server['node_port'], settings.server['node_address'])
    state.main.add_callback(publish_node, app)
    return http_server
