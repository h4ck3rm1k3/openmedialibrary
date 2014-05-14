# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import sys
import tornado
from tornado.web import StaticFileHandler, Application, FallbackHandler
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback

import settings

import directory
import utils
import state
import user

import json
from ed25519_utils import valid
import api
import cert

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
                print key, 'action', action, args
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
                            content = getattr(api, 'api_' + action)(self.app, key, *args)
                        else:
                            print 'PEER', key, 'IS UNKNOWN SEND 403'
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
            print 'GET file', id
            with open(path, 'rb') as f:
                while 1:
                    data = f.read(16384)
                    if not data:
                        break
                    self.write(data)
            self.finish()


def start(app):
    application = tornado.web.Application([
        (r"/get/(.*)", ShareHandler, dict(app=app)),
        (r".*", NodeHandler, dict(app=app)),
    ])
    if not os.path.exists(settings.ssl_cert_path):
        settings.server['cert'] = cert.generate_ssl()

    http_server = tornado.httpserver.HTTPServer(application, ssl_options={
        "certfile": settings.ssl_cert_path,
        "keyfile": settings.ssl_key_path
    })
    http_server.listen(settings.server['node_port'], settings.server['node_address'])
    host = utils.get_public_ipv6()
    state.online = directory.put(settings.sk, {
        'host': host,
        'port': settings.server['node_port'],
        'cert': settings.server['cert']
    })
    return http_server
